"""Audit prefix recovery, target surprise and token-level re-masking on saved checkpoints.

    python -m pilot2.recon_audit --root outputs/human_mlm_long --tiers 1,4,16 --gpu 1

Teacher-forced target surprise and top-1 accuracy condition on true target context.
Their per-record powers are conditional-prediction diagnostics, not probabilities
or certified bounds on recovery by this or another decoder. The historical JSON
fields `exact_upper_bound`, `bound` and `loo_bound` retain their names and values for compatibility.

Re-masking updates covering tokens sequentially from multiple initializations,
stopping at a fixed point of the search computation or at the sweep cap. The
attack selects by pseudo-log-likelihood without knowing the target; any-restart
success uses the truth and is an oracle comparison over the same restart set.
Exact recovery is scored on the hidden 48-nt crop, whereas LOO tests full original
token identities. Leading revealed letters are constrained; trailing host letters
within a covering token are not. Search is batched and LOO uses a single-row pass.
Thus even early-stopped exact outputs do not certify the separate probe's premise.

The routine reads saved checkpoints and leaves the training/scoring implementation
unchanged. Zero tested recovery does not establish an absence of retained signal.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from .data import PROBE_LEN, PROBE_OFFSET, WINDOW, Probe, decode, random_dna, window_of
from .model import Backbone
from .real_data import DATA_PATHS, build_real_dataset
from .score import _cover, _kmer_letters, extract_infill, extract_prefix
from .tokenizers import get_tokenizer
from .train import parse_objective, with_bos

try:                                     # synthetic cells only
    from .data import build_dataset
except ImportError:                      # pragma: no cover
    build_dataset = None

# accepts the plain cells and the --init_from / --lora_r ones, which run_pilot names <tok>_<obj>_ft_s<n>
RUN = re.compile(r"(?P<tok>char|\d+mer(?:sp)?)_(?P<obj>ar|mlm[0-9.]+)(?:_ft)?(?:_lora\d+)?_s(?P<seed>\d+)$")
# released Nucleotide Transformer cells, e.g. nt250m_mlm_ecoli_s0, which pilot2/nt.py names itself
NT_RUN = re.compile(r"nt\d+m_(?:ar|mlm)_[a-z0-9]+_s\d+$")


def rebuild(d: Path, device, ckpt="final.pt"):
    """(model, tok, kind, ds, args) for one run directory, from its own args.json and checkpoint.

    Reads the backbone geometry out of args.json. Without that, every cell of queue_1012a -- which
    is the 59.9M (768/8/12) and 201M (1024/16/16) arm -- dies in load_state_dict.
    """
    a = json.loads((d / "args.json").read_text(encoding="utf-8"))
    is_nt = "size" in a                  # a released Nucleotide Transformer cell, not our backbone
    kind = _kind_of(a)
    tok = _nt_vocab(a["size"]) if is_nt else get_tokenizer(a["tokenizer"], window_of(d))
    tiers = tuple(int(t) for t in str(a["tiers"]).split(","))
    n_val, n_test = _split_sizes(a)
    if a.get("data", "synthetic") != "synthetic":
        ds = build_real_dataset(a.get("fasta") or DATA_PATHS[a["data"]], a["n_train"], n_val,
                                n_test, a["probes_per_tier"], tiers, a["n_nonmember"],
                                a["data_seed"], offset_mode=a["probe_offset"],
                                canary_npz=a.get("canary_npz"))
    else:
        ds = build_dataset(a["n_train"], n_val, n_test, a["probes_per_tier"], tiers,
                           a["n_nonmember"], a["data_seed"], offset_mode=a["probe_offset"],
                           enrich_k=a.get("enrich_k"), enrich_factor=a.get("enrich_factor", 1.0))
    if is_nt:
        # The 95-100 % reconstruction result is measured on our own from-scratch backbone. Asking a
        # RELEASED masked checkpoint the same question is the obvious next thing a reader wants, and
        # it needs the fine-tuned weights, which pilot2/nt.py now writes under --save_ckpt.
        from . import nt as ntmod
        model, _ = ntmod.load(a["size"], False, device)
        model.hf.load_state_dict(torch.load(d / ckpt, map_location=device))
        model.eval()
        return model, tok, kind, ds, a
    kw = {k: v for k, v in (("d_model", a.get("d_model")), ("n_layers", a.get("n_layers")),
                            ("n_heads", a.get("n_heads")), ("d_ff", a.get("d_ff")),
                            ("emb_rank", a.get("emb_rank"))) if v}
    if a.get("pos_enc", "abs") != "abs":
        kw["pos_enc"] = a["pos_enc"]
    model = Backbone(tok.vocab_size, tok.n_tokens + 1, causal=(kind == "ar"), **kw).to(device)
    sd = torch.load(d / ckpt, map_location=device)
    sd = {k.replace("base_model.model.", "").replace(".base_layer", ""): v for k, v in sd.items()}
    model.load_state_dict(sd, strict=False) if any("lora" in k for k in sd) else model.load_state_dict(sd)
    model.eval()
    return model, tok, kind, ds, a


def _nt_vocab(size: str):
    from pathlib import Path as _P

    from . import nt as ntmod
    return ntmod.NTVocab(_P(ntmod.ROOT) / ntmod.SIZES[size])


def _kind_of(a: dict) -> str:
    """'mlm' or 'ar', from whatever spelling the wrapper that produced this run happened to use.

    `parse_objective` is our backbone's parser and demands "mlm@<rate>"; it raises on the bare
    "mlm" that pilot2/nt.py writes and on the "causal" that pilot2/dnabert.py writes. Calling it
    unguarded here meant every released cell died before the decoder ever ran.
    """
    obj = a.get("objective")
    if obj is None:                       # pilot2/hyena.py records no objective; it is causal-only
        return "ar"
    if obj in ("causal", "ar"):
        return "ar"
    if obj == "mlm":
        return "mlm"
    return parse_objective(obj)[0]


# The wrappers that hardcode their validation and test split sizes instead of recording them.
# Guessing here is worse than crashing: real_data.py draws every probe HOST from the windows after
# n_train + n_val + n_test, so a wrong value silently moves every canary into a window the model
# never trained on, and the decoder would then report a number for the wrong sequence.
_HARDCODED_SPLIT = 200


def _split_sizes(a: dict):
    n_val, n_test = a.get("n_val"), a.get("n_test")
    if n_val is not None and n_test is not None:
        return n_val, n_test
    assert "size" not in a, "NT records its split sizes; a missing one means something else is wrong"
    # dnabert.py, dnabert2.py and hyena.py all pass n_val=n_test=200 and do not write it down
    return (n_val if n_val is not None else _HARDCODED_SPLIT,
            n_test if n_test is not None else _HARDCODED_SPLIT)


def _span(tok, offset, k_nt):
    start_nt, end_nt = offset + k_nt, offset + PROBE_LEN
    lo, hi = _cover(tok, start_nt, end_nt)
    return start_nt, end_nt, lo, hi, tok.nt_to_tok(lo), tok.nt_to_tok(hi)


def _allowed_fn(tok, win, start_nt, letters, content, device):
    """Content-token mask keeping the already-revealed letters of a partly-revealed token."""
    def allowed(pos):
        if letters is None:
            return None
        nt0 = pos if hasattr(tok, "fill_id") else pos * tok.k
        known = [(i, int(win[nt0 + i])) for i in range(tok.k) if nt0 + i < start_nt]
        if not known:
            return None
        m = torch.ones(len(content), dtype=torch.bool, device=device)
        for i, v in known:
            m &= letters[:, i] == v
        return m
    return allowed


@torch.no_grad()
def target_surprise(model, tok, kind, probe: Probe, host, device, k_nt=48, offset=PROBE_OFFSET):
    """Teacher-forced surprise of the TRUE target half under the extractor's own conditioning.

    Returns bits per TARGET nucleotide (not per canary nucleotide: the revealed half is excluded,
    which is the whole point), the fraction of steps whose argmax is the true token, and its
    per-record power. The legacy `exact_upper_bound` key stores this diagnostic; it does not
    certify all-48-exact recovery by any decoder.
    """
    content = tok.content_ids.to(device)
    start_nt, end_nt, lo, hi, start, end = _span(tok, offset, k_nt)
    win = np.asarray(host).copy()
    win[offset:offset + PROBE_LEN] = probe.seq
    xt = torch.from_numpy(tok.encode(win[None]))[0].to(device)
    letters = _kmer_letters(tok, device) if lo < start_nt else None
    allowed = _allowed_fn(tok, win, start_nt, letters, content, device)

    def step_logp(logits, pos):
        lc = logits[content]
        m = allowed(pos)
        if m is not None:
            lc = lc.masked_fill(~m, float("-inf"))
        lp = F.log_softmax(lc.float(), dim=-1) / math.log(2.0)
        true = int((content == xt[pos]).nonzero()[0, 0])
        return float(lp[true]), bool(int(lc.argmax()) == true)

    bits, hits = 0.0, []
    if kind == "ar":
        ctx = with_bos(xt[None, :start], tok.bos_id)
        for pos in range(start, end):
            if hasattr(tok, "is_fill") and tok.is_fill(pos):
                ctx = torch.cat([ctx, xt[pos].view(1, 1)], dim=1)
                continue
            with torch.autocast("cuda", dtype=torch.bfloat16):
                logits = model(ctx)[0, -1].float()
            lp, hit = step_logp(logits, pos)
            bits -= lp
            hits.append(hit)
            ctx = torch.cat([ctx, xt[pos].view(1, 1)], dim=1)   # teacher forcing
    else:
        cur = xt.clone()
        cur[start:] = tok.mask_id
        xb = with_bos(cur[None], tok.bos_id)
        for pos in range(start, end):
            if hasattr(tok, "is_fill") and tok.is_fill(pos):
                xb[0, pos + 1] = xt[pos]
                continue
            with torch.autocast("cuda", dtype=torch.bfloat16):
                logits = model(xb)[0, pos + 1].float()
            lp, hit = step_logp(logits, pos)
            bits -= lp
            hits.append(hit)
            xb[0, pos + 1] = xt[pos]                            # teacher forcing
    n = max(1, len(hits))
    rate = float(np.mean(hits))
    return {"target_bits_per_nt": bits / (end_nt - start_nt), "target_bits_total": bits,
            "top1_rate": rate, "n_steps": n, "exact_upper_bound": rate ** n}


@torch.no_grad()
def extract_icm(model, tok, kind, probe: Probe, host, device, k_nt=48, offset=PROBE_OFFSET,
                sweeps: int = 6, init: str = "confidence", restarts: int = 1, chunk: int = 64):
    """Iterated conditional modes: re-mask ONE target token at a time, sweep to a fixed point.

    The conditional used here (1 of ~48 tokens masked, the rest at their current values) is the one
    the model was trained on and the one the surprise and recognition rulers read, which neither
    shipped extraction protocol ever enters. Returns None for causal models.

    The restarts run as one batch. They are independent and follow the same schedule, so the only
    thing that changed is how many forward passes it takes: one per (position, sweep, chunk)
    instead of one per (position, sweep, restart). Everything the function returns is unchanged --
    the random initialisations are still drawn per restart from the same per-probe seeds in the
    same order, the sweep is still Gauss-Seidel within a pass (position p sees p-1 already updated
    in this pass), and the per-restart sweep counts, scores and Hamming distances are still
    reported individually. `chunk` only bounds the batch so the logits tensor stays small; it does
    not affect any result.
    """
    if kind == "ar":
        return None
    content = tok.content_ids.to(device)
    start_nt, end_nt, lo, hi, start, end = _span(tok, offset, k_nt)
    win = np.asarray(host).copy()
    win[offset:offset + PROBE_LEN] = probe.seq
    xt = torch.from_numpy(tok.encode(win[None]))[0].to(device)
    truth_nt = torch.from_numpy(win[start_nt:end_nt]).to(device)
    letters = _kmer_letters(tok, device) if lo < start_nt else None
    allowed = _allowed_fn(tok, win, start_nt, letters, content, device)

    # the shipped edge-conditioned decode, reported beside ICM so the gain is attributable
    seed_pred = extract_infill(model, tok, kind, probe, host, device, k_nt=k_nt, offset=offset,
                               order=init)
    base = xt.clone()
    base[start:end] = tok.mask_id
    xb0 = with_bos(base[None], tok.bos_id)
    todo = []
    for pos in range(start, end):
        if hasattr(tok, "is_fill") and tok.is_fill(pos):
            xb0[0, pos + 1] = tok.fill_id
        else:
            todo.append(pos)

    def masked_logits(xb, pos):
        """Single-row conditional, used by the leave-one-out probe below."""
        keep = xb[0, pos + 1].clone()
        xb[0, pos + 1] = tok.mask_id
        with torch.autocast("cuda", dtype=torch.bfloat16):
            out = model(xb)[0, pos + 1].float()
        xb[0, pos + 1] = keep
        lc = out[content]
        m = allowed(pos)
        return lc.masked_fill(~m, float("-inf")) if m is not None else lc

    # Masks and admissible index lists depend only on the position, so they are built once rather
    # than per restart; `inv` turns a vocabulary id back into its row in `content` without the
    # 4096-wide comparison and device sync the inner loop used to pay on every single step.
    masks = {pos: allowed(pos) for pos in todo}
    inv = torch.full((int(content.max()) + 1,), -1, dtype=torch.long, device=device)
    inv[content] = torch.arange(len(content), device=device)

    def masked_logits_batch(XB, pos):
        """(R, |content|) conditional for every restart at once."""
        keep = XB[:, pos + 1].clone()
        XB[:, pos + 1] = tok.mask_id
        with torch.autocast("cuda", dtype=torch.bfloat16):
            out = model(XB)[:, pos + 1].float()
        XB[:, pos + 1] = keep
        lc = out[:, content]
        m = masks[pos]
        return lc.masked_fill(~m, float("-inf")) if m is not None else lc

    R = max(1, restarts)
    XB = xb0.repeat(R, 1)
    if R > 1:                                        # admissible choices, per position, once
        adm = {}
        for pos in todo:
            m = masks[pos]
            adm[pos] = (torch.arange(len(content)) if m is None
                        else torch.nonzero(m.cpu())[:, 0])
    # restart 0 is the published initialisation: one joint pass over the all-masked row
    with torch.autocast("cuda", dtype=torch.bfloat16):
        joint = model(xb0)[0].float()
    for pos in todo:
        lc = joint[pos + 1][content]
        m = masks[pos]
        if m is not None:
            lc = lc.masked_fill(~m, float("-inf"))
        XB[0, pos + 1] = content[int(lc.argmax())]
    for r in range(1, R):                            # random admissible starts, seeded per probe
        g = torch.Generator(device="cpu").manual_seed(1000 * int(probe.probe_id) + r)
        for pos in todo:
            idx = adm[pos]
            XB[r, pos + 1] = content[int(idx[torch.randint(len(idx), (1,), generator=g)])]

    # Sweep every restart together. A restart that has reached a fixed point cannot move again, so
    # carrying it through the remaining passes changes nothing; only its reported sweep count has
    # to be the pass at which it first stopped moving, which is tracked per row.
    used = torch.full((R,), sweeps, dtype=torch.long, device=device)
    settled = torch.zeros(R, dtype=torch.bool, device=device)
    last, clean = {}, torch.zeros(R, dtype=torch.bool, device=device)
    for s in range(sweeps):
        changed = torch.zeros(R, dtype=torch.bool, device=device)
        for pos in todo:
            lc = torch.cat([masked_logits_batch(XB[i:i + chunk], pos)
                            for i in range(0, R, chunk)], 0)
            new_tok = content[lc.argmax(-1)]
            changed |= new_tok != XB[:, pos + 1]
            XB[:, pos + 1] = new_tok
            last[pos] = lc
        clean = ~changed
        used = torch.where(clean & ~settled, torch.full_like(used, s + 1), used)
        settled |= clean
        if bool(settled.all()):                      # the loop's only host sync, once per pass
            break

    # A pass that changed nothing left the state it scored identical to the final state, so its
    # logits are exactly what the pseudo-likelihood needs and the extra pass can be skipped.
    if not bool(clean.all()):
        for pos in todo:
            last[pos] = torch.cat([masked_logits_batch(XB[i:i + chunk], pos)
                                   for i in range(0, R, chunk)], 0)
    # float64, because the pre-batching code summed these per-position terms as Python floats:
    # accumulating the same float32 values in float32 instead moved the total by ~1e-7 relative,
    # which is enough to reorder two restarts whose pseudo-likelihoods are nearly tied.
    score = torch.zeros(R, dtype=torch.float64, device=device)
    for pos in todo:
        lp = F.log_softmax(last[pos], dim=-1) / math.log(2.0)
        score += lp.gather(1, inv[XB[:, pos + 1]].view(-1, 1)).squeeze(1).double()

    pred_all = tok.decode_t(XB[:, start + 1:end + 1])[:, start_nt - lo:end_nt - lo]
    ham_all = (pred_all != truth_nt).sum(1)
    score_l, ham_l = score.tolist(), ham_all.tolist()
    used_l, pred_l = used.tolist(), pred_all.cpu().numpy()
    results = [{"score": score_l[r], "ham": int(ham_l[r]), "exact": int(ham_l[r]) == 0,
                "sweeps": int(used_l[r]), "pred": decode(pred_l[r])} for r in range(R)]

    best = max(results, key=lambda d: d["score"])    # the attack's own choice, truth-free
    ham, n_sweeps = best["ham"], best["sweeps"]
    oracle = any(d["exact"] for d in results)

    # LOO supplies all other true tokens. Its power is diagnostic only: the
    # crop/full-token endpoints and the search/probe numerical maps can differ.
    xb = xb0.clone()
    for q in todo:
        xb[0, q + 1] = xt[q]
    loo_hits, loo_bits = [], 0.0
    for pos in todo:
        lc = masked_logits(xb, pos)
        true = int((content == xt[pos]).nonzero()[0, 0])
        lp = F.log_softmax(lc.float(), dim=-1) / math.log(2.0)
        loo_bits -= float(lp[true])
        loo_hits.append(bool(int(lc.argmax()) == true))
    loo_rate = float(np.mean(loo_hits)) if loo_hits else float("nan")
    return {"protocol": f"icm-{init}-r{restarts}", "sweeps_used": n_sweeps,
            "k_revealed_nt": k_nt, "restarts": int(max(1, restarts)),
            "offset": int(offset), "n_generated_nt": int(end_nt - start_nt),
            "exact": bool(ham == 0), "hamming_nt": ham,
            "oracle_exact": bool(oracle), "best_score": float(best["score"]),
            "ham_by_restart": [d["ham"] for d in results],
            "loo_top1": loo_rate, "loo_bits_per_nt": loo_bits / (end_nt - start_nt),
            "loo_bound": loo_rate ** max(1, len(loo_hits)), "n_target_tok": len(todo),
            "seed_exact": bool(seed_pred["exact"]), "seed_hamming_nt": int(seed_pred["hamming_nt"]),
            "pred_nt": best["pred"], "truth_nt": decode(truth_nt.cpu().numpy())}


def fresh_views(ds, seed, pool_size):
    """The same fresh hosts and offsets score_run uses, so the control is phase-matched.

    score_run draws the candidate pool from this generator first when the canaries are synthetic, so
    the pool size has to be replayed or every fresh host would differ from the one actually scored.
    """
    rng = np.random.default_rng(10_000 + seed)
    real_pool = getattr(ds, "pool_seqs", None)
    if real_pool is None:
        random_dna(rng, pool_size, PROBE_LEN)                            # keep the rng in step
    real_hosts = getattr(ds, "fresh_hosts", None)
    hosts = {p.probe_id: (random_dna(rng, 1, WINDOW)[0] if real_hosts is None
                          else real_hosts[i % len(real_hosts)].copy())
             for i, p in enumerate(ds.probes)}
    off_rng = np.random.default_rng(20_000 + seed)
    offs = {p.probe_id: int(off_rng.integers(0, WINDOW - PROBE_LEN + 1)) for p in ds.probes}
    return hosts, offs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", nargs="+", required=True)
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--tiers", default="1,4,16")
    ap.add_argument("--max_probes", type=int, default=25, help="per tier")
    ap.add_argument("--sweeps", type=int, default=6)
    ap.add_argument("--restarts", type=int, default=1,
                    help="ICM restarts; >1 adds random admissible starts and picks the fixed point "
                         "with the best pseudo-log-likelihood, which an attacker can compute")
    ap.add_argument("--ckpt", default="final.pt")
    ap.add_argument("--name", default="recon_audit")
    ap.add_argument("--no_icm", action="store_true", help="target surprise only, no ICM decode")
    ap.add_argument("--chunk", type=int, default=64,
                    help="restarts per forward pass. Results are algorithmically independent of "
                         "this, but bf16 picks different kernels per batch shape, so --chunk 1 is "
                         "the setting that reproduces the pre-batching code's arithmetic exactly.")
    args = ap.parse_args(argv)
    device = torch.device(f"cuda:{args.gpu}" if torch.cuda.is_available() else "cpu")
    tiers = [int(t) for t in args.tiers.split(",")]

    rows = []
    for root in args.root:
        rd = Path(root)
        dirs = [rd] if (rd / "args.json").exists() else sorted(p for p in rd.iterdir() if p.is_dir())
        for d in dirs:
            if not ((d / "args.json").exists() and (d / args.ckpt).exists()
                    and (RUN.fullmatch(d.name) or NT_RUN.fullmatch(d.name))):
                continue
            model, tok, kind, ds, a = rebuild(d, device, args.ckpt)
            tok = tok.to(device) if hasattr(tok, "to") else tok
            fh, fo = fresh_views(ds, a["seed"], a.get("pool", 500))
            out = {"run": d.name, "ckpt": args.ckpt, "data": a.get("data", "synthetic"),
                   "objective": a["objective"], "tokenizer": a.get("tokenizer", a.get("size")),
                   "seed": a["seed"],
                   "d_model": a.get("d_model"), "n_layers": a.get("n_layers"), "cells": []}
            per = defaultdict(lambda: defaultdict(list))
            for tier in tiers + [0]:
                ps = [p for p in ds.probes if p.repetitions == tier][:args.max_probes]
                for i_p, p in enumerate(ps, 1):
                    t_probe = time.time()
                    if tier > 0:
                        host, off, hname = ds.train[p.host_rows[0]], p.offsets[0], "train"
                    else:
                        host, off, hname = fh[p.probe_id], fo[p.probe_id], "fresh"
                    ts = target_surprise(model, tok, kind, p, host, device, offset=off)
                    pre = extract_prefix(model, tok, kind, p, host, device, offset=off)
                    icm = (None if args.no_icm else
                           extract_icm(model, tok, kind, p, host, device, offset=off,
                                       sweeps=args.sweeps, restarts=args.restarts,
                                       chunk=args.chunk))
                    # These cells run for hours and used to print nothing until a tier finished,
                    # so a stalled run looked exactly like a slow one.
                    note = "" if icm is None else (
                        " icm exact" if icm["exact"] else f" icm ham {icm['hamming_nt']}")
                    print(f"    [{d.name} r={tier}] probe {i_p}/{len(ps)} "
                          f"{time.time() - t_probe:5.1f}s{note}", flush=True)
                    v = per[tier]
                    v["tgt_bits"].append(ts["target_bits_per_nt"])
                    v["top1"].append(ts["top1_rate"])
                    v["bound"].append(ts["exact_upper_bound"])
                    v["pre_exact"].append(float(pre["exact"]))
                    v["pre_ham"].append(pre["hamming_nt"])
                    if icm:
                        v["icm_exact"].append(float(icm["exact"]))
                        v["icm_ham"].append(icm["hamming_nt"])
                        v["seed_exact"].append(float(icm["seed_exact"]))
                        v["seed_ham"].append(icm["seed_hamming_nt"])
                        v["loo_top1"].append(icm["loo_top1"])
                        v["loo_bound"].append(icm["loo_bound"])
                        v["loo_bits"].append(icm["loo_bits_per_nt"])
                        v["oracle"].append(float(icm["oracle_exact"]))
                    out["cells"].append({"tier": tier, "host": hname, "probe_id": p.probe_id,
                                         "target": ts, "prefix": pre, "icm": icm})
            (d / f"{args.name}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
            for t in sorted(per, reverse=True):
                m = lambda k: float(np.mean(per[t][k])) if per[t][k] else float("nan")
                rows.append(dict(run=d.name, data=out["data"],
                                 tok=a.get("tokenizer", a.get("size")), obj=a["objective"],
                                 seed=a["seed"], tier=t, n=len(per[t]["tgt_bits"]),
                                 tgt_bits=m("tgt_bits"), top1=m("top1"), bound=m("bound"),
                                 pre_exact=m("pre_exact"), pre_ham=m("pre_ham"),
                                 icm_exact=m("icm_exact"), icm_ham=m("icm_ham"),
                                 seed_exact=m("seed_exact"), seed_ham=m("seed_ham"),
                                 loo_top1=m("loo_top1"), loo_bound=m("loo_bound"),
                                 loo_bits=m("loo_bits"), oracle=m("oracle")))
                r = rows[-1]
                print(f"  {d.name:28s} r={t:<3d} n={r['n']:3d} | target {r['tgt_bits']:5.3f} b/nt "
                      f"top1 {r['top1']:.2f} power diag. {r['bound']:.3f} | prefix {100*r['pre_exact']:5.1f}% "
                      f"(ham {r['pre_ham']:4.1f}) | icm {100*r['icm_exact']:5.1f}% "
                      f"(ham {r['icm_ham']:4.1f}) | loo top1 {r['loo_top1']:.2f} "
                      f"power diag. {r['loo_bound']:.3f} bits {r['loo_bits']:5.3f} | "
                      f"oracle {100*r['oracle']:5.1f}%", flush=True)
            del model
            torch.cuda.empty_cache()

    if not rows:
        print("no runs with a checkpoint under", args.root)
        return 1
    md = [f"# Reconstruction audit — {args.name}", "",
          "`target` is teacher-forced surprise over the hidden 48 nucleotides, in bits per "
          "nucleotide. `top1` supplies true preceding target context; `LOO` supplies the other "
          "true target tokens. Their per-record powers are conditional-prediction diagnostics, "
          "not recovery probabilities or certified bounds for any decoder. JSON keys `exact_upper_bound`, `bound` "
          "and `loo_bound` retain their historical names and numeric values for compatibility. "
          "`ICM exact` scores the hidden nucleotide crop after selecting a restart by "
          "pseudo-log-likelihood without the answer. Full-token LOO identity differs from this "
          "cropped endpoint, and batched search can differ numerically from single-row LOO. "
          "Early stopping does not certify the probe's necessary condition. Outputs can also "
          "reach the sweep cap. `any-restart` uses the answer to choose among the same restarts; "
          "it is an oracle comparison, not an executable attack selection rule.", "",
          "| run | data | tok | obj | tier | n | target b/nt | top1 | prefix | LOO b/nt | LOO top1 | LOO power diag. | ICM exact | ICM ham | any-restart |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['run']} | {r['data']} | {r['tok']} | {r['obj']} | r={r['tier']} | {r['n']} | "
                  f"{r['tgt_bits']:.3f} | {r['top1']:.2f} | "
                  f"{100*r['pre_exact']:.0f}% | {r['loo_bits']:.3f} | {r['loo_top1']:.2f} | "
                  f"{r['loo_bound']:.3f} | **{100*r['icm_exact']:.0f}%** | {r['icm_ham']:.1f} | "
                  f"{100*r['oracle']:.0f}% |")
    mem = [r for r in rows if r["tier"] > 0]
    non = [r for r in rows if r["tier"] == 0]
    if mem and non:
        md += ["", f"Members: target surprise {np.mean([r['tgt_bits'] for r in mem]):.3f} b/nt against "
                   f"{np.mean([r['tgt_bits'] for r in non]):.3f} for the matched non-member control; "
                   f"ICM extraction at worst {100*max(r['icm_exact'] for r in mem):.0f}%."]
    p = Path(args.root[0]) / f"{args.name}.md"
    p.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[-2:]))
    print(f"-> {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
