"""Nucleotide-level re-masking for DNABERT-2's variable-length BPE vocabulary.

    python -m pilot2.recon_bpe --root outputs/bpe_human --restarts 16 --score fixed --gpu 0

Each nucleotide candidate re-segments the window. With --score fixed (default),
candidates are scored over a common boundary-aligned interval, with no division.
The historical --score pernt path divides by each candidate's covered span;
that candidate-dependent divisor introduces a letter prior. It remains available
only to reproduce the historical campaign, not as a correction for length bias.
Products of masked-token marginals need not be joint sequence probabilities.

LOO supplies all other true target nucleotides. Its accuracy and per-record power
are conditional-prediction diagnostics, not certified recovery bounds. The JSON
field `loo_bound` is retained for compatibility. Search uses batched candidates
whereas LOO uses a single-row path; zero exact recovery does not validate a bound.
Restarts are batched and positions are swept sequentially up to the stated cap;
truth-free selection and any-restart oracle results are reported separately.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from .data import PROBE_LEN, PROBE_OFFSET, WINDOW, Probe, decode, random_dna
from .dnabert2 import BpeVocab, _logits, load_model
from .real_data import DATA_PATHS, build_real_dataset

RUN = re.compile(r"dnabert2bpe_.*$")
NTS = "ACGT"


@torch.no_grad()
def nt_dist_bpe(model, voc: BpeVocab, wins: np.ndarray, j: int, device, chunk: int = 128):
    """log2 p(letter at j | the rest of the window), shape (B, 4), one row per window in `wins`.

    For each candidate the window is re-tokenised, every token whose span covers j is masked, and the
    score is the summed log-probability of those tokens' true identities divided by the nucleotides
    they cover. This historical score introduces a candidate-dependent letter prior; use
    nt_dist_bpe_fixed for the common-interval comparison. Retained for reproducing old runs.
    """
    B = wins.shape[0]
    jobs, meta = [], []
    for b in range(B):
        for a in range(4):
            w = wins[b].copy()
            w[j] = a + 1
            ids, spans = voc.encode_str(decode(w))
            cover = [t for t, (s, e) in enumerate(spans) if s <= j < e]
            if not cover:                                 # j fell outside every span: cannot happen
                jobs.append(ids); meta.append((b, a, [], 1)); continue
            nts = sum(spans[t][1] - spans[t][0] for t in cover)
            masked = list(ids)
            true = [ids[t + 1] for t in cover]            # +1 for [CLS]
            for t in cover:
                masked[t + 1] = voc.mask
            jobs.append(masked)
            meta.append((b, a, [(t + 1, tid) for t, tid in zip(cover, true)], nts))

    out = torch.full((B, 4), float("-inf"), device=device)
    for c0 in range(0, len(jobs), chunk):
        sl = slice(c0, c0 + chunk)
        ids, am = voc.pad_batch(jobs[sl], device)
        lp = F.log_softmax(_logits(model, ids, am), dim=-1) / math.log(2.0)
        for r, (b, a, pos_tok, nts) in enumerate(meta[sl]):
            tot = 0.0
            for p, tid in pos_tok:
                tot += float(lp[r, p, tid])
            out[b, a] = tot / max(1, nts)
    return out


def union_span(voc: BpeVocab, base: str, j: int, max_iter: int = 8):
    """A nucleotide interval containing j, token-boundary aligned under all four candidates at j.

    Grow [j, j+1) until, for every letter written at j, the tokens that overlap the interval begin
    exactly at its start and end exactly at its end. The interval only grows and is bounded by the
    window, so this terminates; in practice it settles in one or two rounds.

    The point of the interval is that it does not depend on which letter sits at j. Scoring the same
    nucleotides for every candidate is what makes the four numbers comparable, and it is what the
    division this replaces was trying and failing to do.
    """
    lo, hi = j, j + 1
    for _ in range(max_iter):
        nlo, nhi = lo, hi
        for a in NTS:
            _, spans = voc.encode_str(base[:j] + a + base[j + 1:])
            cov = [(s, e) for (s, e) in spans if s < hi and e > lo]
            if cov:
                nlo = min(nlo, min(s for s, _ in cov))
                nhi = max(nhi, max(e for _, e in cov))
        if (nlo, nhi) == (lo, hi):
            break
        lo, hi = nlo, nhi
    return lo, hi


@torch.no_grad()
def nt_dist_bpe_fixed(model, voc: BpeVocab, wins: np.ndarray, j: int, device, chunk: int = 128,
                      diag: list | None = None):
    """log2 p(nucleotides of a fixed interval around j | the rest), shape (B, 4). No division.

    WHY THIS REPLACES nt_dist_bpe. That function masked the tokens covering j and divided the
    summed log-probability by the nucleotides those tokens covered. The divisor depends on the
    candidate, and a log-probability is negative, so the candidate whose tokens happen to span more
    nucleotides is pulled towards zero, which is towards winning. Measured on the released
    DNABERT-2 vocabulary over 1,435 positions where the four divisors differ, the largest divisor
    falls on A 707 times against 359 expected (pilot2/diag_bpe_denominator.py). Iterated over 48
    positions that prior is enough to make a run of A the fixed point the decoder reports, and the
    truth-free selection then prefers it to restarts six nucleotides closer to the truth.

    Here the interval is chosen first, independently of the candidate (`union_span`), and every
    candidate is scored on exactly those nucleotides: the masked event is "this interval reads
    thus", the conditioning is the identical remainder of the window, and the four events differ
    only at j. Summed log-probabilities are then directly comparable and nothing is divided. The
    update is a block conditional on the interval rather than a single-site one, which is a
    stronger ICM proposal, not a weaker one.

    WHAT IS NOT FIXED. Candidates still decompose the interval into different numbers of tokens,
    and a product of masked-token marginals is not the joint, so a segmentation with fewer factors
    is still mildly favoured. That residual is in the same direction as the old bias but is no
    longer multiplied by the span. `diag`, when given a list, collects (candidate, n_masked_tokens,
    interval width) per row so the residual can be measured rather than assumed.
    """
    B = wins.shape[0]
    jobs, meta = [], []
    for b in range(B):
        base = decode(wins[b])
        lo, hi = union_span(voc, base, j)
        for a in range(4):
            ids, spans = voc.encode_str(base[:j] + NTS[a] + base[j + 1:])
            cover = [t for t, (s, e) in enumerate(spans) if s < hi and e > lo]
            masked = list(ids)
            true = [ids[t + 1] for t in cover]            # +1 for [CLS]
            for t in cover:
                masked[t + 1] = voc.mask
            jobs.append(masked)
            meta.append((b, a, [(t + 1, tid) for t, tid in zip(cover, true)], hi - lo))

    out = torch.full((B, 4), float("-inf"), device=device)
    for c0 in range(0, len(jobs), chunk):
        sl = slice(c0, c0 + chunk)
        ids, am = voc.pad_batch(jobs[sl], device)
        lp = F.log_softmax(_logits(model, ids, am), dim=-1) / math.log(2.0)
        for r, (b, a, pos_tok, width) in enumerate(meta[sl]):
            tot = 0.0
            for p, tid in pos_tok:
                tot += float(lp[r, p, tid])
            out[b, a] = tot
            if diag is not None:
                diag.append({"letter": NTS[a], "n_masked": len(pos_tok), "width": int(width),
                             "score": tot})
    return out


@torch.no_grad()
def icm_bpe(model, voc: BpeVocab, win: np.ndarray, offset: int, device, k_nt: int = 48,
            restarts: int = 16, sweeps: int = 4, seed: int = 0, scorer="fixed"):
    """Reveal win[:offset+k_nt]; recover the next 48 nucleotides by ICM in nucleotide space.

    scorer="fixed"  the fixed-interval conditional, nothing divided (default since 27 Oct)
    scorer="pernt"  the original: tokens covering j, divided by the nucleotides they cover.
                   Kept so the submitted numbers stay reproducible; it carries the letter
                   prior documented on nt_dist_bpe_fixed and should not be used for new
                   measurements.
    """
    # NB: the body below binds `score` to the truth-free selection array, which is why the
    # parameter is `scorer`.
    dist = nt_dist_bpe if scorer == "pernt" else nt_dist_bpe_fixed
    start, end = offset + k_nt, offset + PROBE_LEN
    target = list(range(start, end))
    truth = win[start:end].copy()
    g = np.random.default_rng(seed)

    cur = np.tile(win[None, :], (restarts, 1)).copy()
    cur[0, start:end] = 1
    if restarts > 1:
        cur[1:, start:end] = g.integers(1, 5, size=(restarts - 1, end - start))

    n_sweeps = 0
    for _ in range(sweeps):
        changed, n_sweeps = 0, n_sweeps + 1
        for j in target:
            d = dist(model, voc, cur, j, device)
            new = (d.argmax(1) + 1).cpu().numpy()
            changed += int((new != cur[:, j]).sum())
            cur[:, j] = new
        if changed == 0:
            break

    # truth-free selection: the summed per-nucleotide score of the fixed point it converged to
    score = np.zeros(restarts)
    for j in target:
        d = dist(model, voc, cur, j, device).cpu().numpy()
        score += d[np.arange(restarts), cur[:, j] - 1]
    best = int(np.argmax(score))
    ham = [int((cur[r, start:end] != truth).sum()) for r in range(restarts)]

    # leave-one-out: every other target nucleotide at its TRUE value, one unknown
    tw = win.copy()[None, :]
    tw[0, start:end] = truth
    hits, bits = [], 0.0
    for j in target:
        d = dist(model, voc, tw, j, device)[0]
        hits.append(bool(int(d.argmax()) + 1 == int(tw[0, j])))
        bits -= float(d[int(tw[0, j]) - 1])
    loo = float(np.mean(hits))
    return {"protocol": f"icm-bpe-{scorer}-r{restarts}", "scorer": scorer,
            "sweeps_used": n_sweeps, "restarts": restarts,
            "n_generated_nt": len(target), "exact": bool(ham[best] == 0), "hamming_nt": ham[best],
            "oracle_exact": bool(min(ham) == 0), "ham_by_restart": ham,
            "loo_top1": loo, "loo_bits_per_nt": bits / len(target),
            # The two scorers do not measure the same thing here and the division is only a
            # per-nucleotide one for the first. "pernt" scores one nucleotide's covering tokens, so
            # the sum over the target divided by its length is bits per nucleotide. "fixed" scores a
            # whole token-aligned interval per position, so the same division gives bits per
            # interval per target nucleotide, which is several times larger and is NOT comparable to
            # any other bits/nt figure in this project. Only loo_top1 and the Hamming distances
            # compare across the two.
            "loo_bits_unit": "bits/nt" if scorer == "pernt" else "bits/interval per target nt",
            "loo_bound": loo ** len(target),
            "pred_nt": decode(cur[best, start:end]), "truth_nt": decode(truth)}


def rebuild(d: Path, device, ckpt: str):
    a = json.loads((d / "args.json").read_text(encoding="utf-8"))
    model, voc = load_model(device, causal=(a.get("objective") == "causal"))
    model.load_state_dict(torch.load(d / ckpt, map_location=device))
    model.eval()
    tiers = tuple(int(t) for t in str(a["tiers"]).split(","))
    # dnabert2.py hardcodes n_val=n_test=200 without recording it; a wrong value would relocate
    # every probe host into a window the model never trained on
    ds = build_real_dataset(a.get("fasta") or DATA_PATHS[a["data"]], a["n_train"], 200, 200,
                            a["probes_per_tier"], tiers, a["n_nonmember"], a["data_seed"],
                            offset_mode=a["probe_offset"], canary_npz=a.get("canary_npz"))
    return model, voc, ds, a


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", nargs="+", required=True)
    ap.add_argument("--gpu", type=int, default=0)
    ap.add_argument("--tiers", default="1,4,16")
    ap.add_argument("--max_probes", type=int, default=20)
    ap.add_argument("--restarts", type=int, default=16)
    ap.add_argument("--sweeps", type=int, default=4)
    ap.add_argument("--ckpt", default="final.pt")
    ap.add_argument("--name", default="recon_bpe")
    ap.add_argument("--score", choices=("fixed", "pernt"), default="fixed",
                    help="fixed: the fixed-interval conditional. pernt: the original "
                         "divided-by-covered-nucleotides score, which carries a letter prior")
    args = ap.parse_args(argv)
    device = torch.device(f"cuda:{args.gpu}" if torch.cuda.is_available() else "cpu")
    tiers = [int(t) for t in args.tiers.split(",")]

    rows = []
    for root in args.root:
        rd = Path(root)
        dirs = [rd] if (rd / "args.json").exists() else sorted(p for p in rd.iterdir() if p.is_dir())
        for d in dirs:
            if not ((d / "args.json").exists() and (d / args.ckpt).exists() and RUN.fullmatch(d.name)):
                continue
            model, voc, ds, a = rebuild(d, device, args.ckpt)
            rng = np.random.default_rng(10_000 + a["seed"])
            real_hosts = getattr(ds, "fresh_hosts", None)
            per, cells = defaultdict(lambda: defaultdict(list)), []
            for tier in tiers + [0]:
                ps = [p for p in ds.probes if p.repetitions == tier][:args.max_probes]
                for p in ps:
                    if tier > 0:
                        host, off = ds.train[p.host_rows[0]].copy(), p.offsets[0]
                    else:
                        host = (real_hosts[p.probe_id % len(real_hosts)].copy()
                                if real_hosts is not None else random_dna(rng, 1, WINDOW)[0])
                        off = PROBE_OFFSET
                    win = host.copy()
                    win[off:off + PROBE_LEN] = p.seq
                    r = icm_bpe(model, voc, win, off, device, restarts=args.restarts,
                                sweeps=args.sweeps, seed=1000 * int(p.probe_id) + tier,
                                scorer=args.score)
                    v = per[tier]
                    for key in ("exact", "oracle_exact"):
                        v[key].append(float(r[key]))
                    v["ham"].append(r["hamming_nt"])
                    v["loo_top1"].append(r["loo_top1"])
                    v["loo_bits"].append(r["loo_bits_per_nt"])
                    v["loo_bound"].append(r["loo_bound"])
                    cells.append({"tier": tier, "probe_id": p.probe_id, "icm_bpe": r})
            (d / f"{args.name}.json").write_text(
                json.dumps({"run": d.name, "data": a.get("data"), "seed": a["seed"],
                            "ckpt": args.ckpt, "scorer": args.score, "cells": cells}, indent=1),
                encoding="utf-8")
            for t in sorted(per, reverse=True):
                m = lambda key: float(np.mean(per[t][key])) if per[t][key] else float("nan")
                rows.append(dict(run=d.name, data=a.get("data"), seed=a["seed"], tier=t,
                                 n=len(per[t]["exact"]), exact=m("exact"), ham=m("ham"),
                                 oracle=m("oracle_exact"), loo_top1=m("loo_top1"),
                                 loo_bits=m("loo_bits"), loo_bound=m("loo_bound")))
                r = rows[-1]
                print(f"  {d.name:26s} r={t:<3d} n={r['n']:3d} | loo top1 {r['loo_top1']:.2f} "
                      f"bits {r['loo_bits']:5.3f} power diag. {r['loo_bound']:.3f} | icm-bpe "
                      f"{100*r['exact']:5.1f}% (ham {r['ham']:4.1f}) | oracle {100*r['oracle']:5.1f}%",
                      flush=True)
            del model
            torch.cuda.empty_cache()

    if not rows:
        print("no DNABERT-2 cells with a checkpoint under", args.root)
        return 1
    md = [f"# Re-masking in nucleotide space on DNABERT-2's BPE vocabulary — {args.name}", "",
          f"Scorer: `{args.score}`. `fixed` scores all four candidates on a common aligned "
          "interval without division; historical `pernt` divides by each candidate's covered "
          "span and carries a letter prior. LOO supplies all other true target nucleotides. "
          "Its per-record power is a conditional-prediction diagnostic, not a recovery "
          "probability or certified bound. JSON `loo_bound` retains its historical name and "
          "values. LOO score units are bits/nt for `pernt` and bits/interval per target nt "
          "for `fixed`; these scores are not directly comparable. Search selects within its "
          "restart/pass budget, and zero exact recovery does not validate a bound.", "",
          "| run | data | seed | tier | n | LOO top1 | LOO score | LOO power diag. | ICM-bpe exact | ham | any-restart |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['run']} | {r['data']} | {r['seed']} | r={r['tier']} | {r['n']} | "
                  f"{r['loo_top1']:.2f} | {r['loo_bits']:.3f} | {r['loo_bound']:.3f} | "
                  f"**{100*r['exact']:.0f}%** | {r['ham']:.1f} | {100*r['oracle']:.0f}% |")
    p = Path(args.root[0]) / f"{args.name}.md"
    p.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"-> {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
