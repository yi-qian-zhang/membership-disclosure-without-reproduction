"""Flatten every scored snapshot into one tidy table, so the figures can be redrawn
without the 750 MB of raw score files behind them.

    python -m pilot2.export_figure_data --root outputs --out results/figure_data.csv

WHY. Each `scores_ep*.json` is a few hundred kilobytes of per-probe detail, and there are
three thousand of them. Every figure in the paper reads the same handful of fields out of
them: where the run sat in held-out loss at that snapshot, and what fraction of the planted
records came back at each repetition tier. Publishing the raw files would add three quarters
of a gigabyte to the repository for a reader who wants a curve; publishing this table lets
them redraw every curve, and the raw files remain on request.

One row per (run, snapshot, tier, host). `host=train` is the window the record was planted
in and `host=fresh` is a window the model never saw; those are two READING CONDITIONS, not a
result and its control. The control is `tier=0`, a never-trained record of identical
construction, and it is read in both conditions -- in the fresh window always, and in a
borrowed training row wherever a `scores_*_bh.json` exists. The sentence here used to call
`host=fresh` "the control", which is the conflation the whole 27 Oct correction was about.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from .target48 import target48

# `group` is the sweep directory the run sits in. Without it the table is ambiguous: the
# same run name (3mer_ar_s0) exists under both kcurve and kcurve300, and several released
# cells repeat across nt/, nt_ckpt/ and nt_opt/.
FIELDS = [
    "group", "run", "tokenizer", "objective", "seed", "data", "window", "n_train",
    "epoch", "heldout_bits_per_nt", "tier", "host", "n_probes",
    "exact_rate", "mean_hamming_nt", "rank1_rate", "evaluation_endpoint",
]


def _runs(root: Path):
    """Every directory holding at least one scored snapshot."""
    seen = set()
    for f in root.rglob("scores_*.json"):
        if f.parent not in seen:
            seen.add(f.parent)
            yield f.parent


def _meta(d: Path) -> dict:
    out = {}
    for name, keys in (("args.json", ("tokenizer", "objective", "seed", "data", "size", "k", "n_train")),
                       ("data_meta.json", ("window", "n_train"))):
        f = d / name
        if not f.exists():
            continue
        try:
            a = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        for k in keys:
            if a.get(k) is not None and out.get(k) is None:
                out[k] = a[k]
    # released checkpoints record their family under a different key than our own runs
    if out.get("tokenizer") is None:
        out["tokenizer"] = out.pop("size", None) or (f"{out['k']}mer" if out.get("k") else None)
    out.pop("size", None)
    out.pop("k", None)
    return out


def _rows(d: Path, meta: dict, group: str):
    # A checkpoint can have up to three score files for the same weights: the one written during
    # the run, a re-scoring with the full probe set on one numerical basis (scores_<ep>_rb.json),
    # and a re-scoring that also builds the own-host control (scores_<ep>_bh.json). They describe
    # the same weights, so the later one supersedes the earlier rather than adding a row beside
    # it, and the order is _bh > _rb > the original.
    #
    # _bh was NOT in this pattern until 28 Oct, so every borrowed-host scoring was silently
    # skipped and figure_data.csv contained no `tier=0, host=train` row at all -- 3,950 tier-0
    # rows, every one of them host=fresh. The own-host control existed in the raw files and in
    # results/borrowed_host.json and reached no figure, including the one whose caption claims it.
    #
    # It is added WITHOUT superseding anything. Letting _bh win outright was tried first and it
    # moved eleven published cells in nt250m_mlm_human_s0: mean Hamming by up to 0.9 nt and one
    # 16-copy extraction rate from 0.10 to 0.12, which is one record in fifty. The ranking cells
    # did not move at all. That is the paper's own "rankings are stable, extraction rates wobble"
    # finding showing up here, and it is not a reason to let a re-scoring quietly rewrite a
    # measured number. So _bh contributes exactly the rows nothing else can supply -- the
    # never-trained records read in a borrowed training row -- and every other cell stays as the
    # run that produced it left it.
    chosen: dict = {}
    for f in sorted(d.glob("scores_*.json")):
        m = re.search(r"scores_(ep\d+|final)(_rb)?\.json$", f.name)
        if not m:
            continue
        if m.group(2) or m.group(1) not in chosen:
            chosen[m.group(1)] = f
    bh = {}
    for f in sorted(d.glob("scores_*_bh.json")):
        m = re.search(r"scores_(ep\d+|final)_bh\.json$", f.name)
        if m:
            bh[m.group(1)] = f
    # (file, keep only the tier-0 own-host rows from it?)
    todo = [(tag, f, False) for tag, f in sorted(chosen.items())]
    todo += [(tag, f, True) for tag, f in sorted(bh.items())]
    for epoch_tag, f, control_only in todo:
        m = re.match(r"(ep\d+|final)", epoch_tag)
        try:
            s = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        floor = (s.get("floors") or [{}])[0].get("bits_per_nt_mean")
        probes = s.get("probes") or []
        # (tier, host) -> [exact, hamming, rank1]
        acc: dict[tuple, list[list]] = {}
        for p in probes:
            tier = p.get("repetitions")
            for host, ex in (p.get("extract") or {}).items():
                if not isinstance(ex, dict):
                    continue
                # Early unused archives omitted strings; never relabel them as 48nt.
                legacy = int(ex.get('n_generated_nt',48)) != 48 and 'pred_nt' not in ex
                if not legacy:
                    ex = target48(ex)
                ranks = p.get("ranks") or {}
                r1 = next((1.0 if v.get("rank") == 1 else 0.0)
                          for k, v in ranks.items() if k.endswith("/" + host)) \
                    if any(k.endswith("/" + host) for k in ranks) else None
                acc.setdefault((tier, host), []).append(
                    [1.0 if ex.get("exact") else 0.0, ex.get("hamming_nt"), r1,
                     'legacy_variable' if legacy else 'hidden48'])
        for (tier, host), vals in sorted(acc.items(), key=lambda kv: (str(kv[0][0]), kv[0][1])):
            if control_only and not (tier == 0 and host == "train"):
                continue
            ex = [v[0] for v in vals]
            ham = [v[1] for v in vals if v[1] is not None]
            r1 = [v[2] for v in vals if v[2] is not None]
            yield {
                "group": group, "run": d.name, "tokenizer": meta.get("tokenizer"),
                "objective": meta.get("objective"), "seed": meta.get("seed"),
                "data": meta.get("data"), "window": meta.get("window"),
                "n_train": meta.get("n_train"),
                "epoch": m.group(1).replace("ep", ""),
                "heldout_bits_per_nt": None if floor is None else round(floor, 6),
                "tier": tier, "host": host, "n_probes": len(vals),
                "exact_rate": round(sum(ex) / len(ex), 6) if ex else None,
                "mean_hamming_nt": round(sum(ham) / len(ham), 3) if ham else None,
                "rank1_rate": round(sum(r1) / len(r1), 6) if r1 else None,
                "evaluation_endpoint": 'legacy_variable' if any(v[3]=='legacy_variable' for v in vals) else 'hidden48',
            }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="outputs")
    ap.add_argument("--out", default="results/figure_data.csv")
    args = ap.parse_args(argv)
    root = Path(args.root)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    n_runs = n_rows = 0
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for d in sorted(_runs(root)):
            meta = _meta(d)
            got = 0
            group = d.parent.relative_to(root).as_posix() if d.parent != root else "."
            for row in _rows(d, meta, group):
                w.writerow(row)
                got += 1
            if got:
                n_runs += 1
                n_rows += got
    print(f"{n_rows} rows from {n_runs} runs -> {out} ({out.stat().st_size/1048576:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
