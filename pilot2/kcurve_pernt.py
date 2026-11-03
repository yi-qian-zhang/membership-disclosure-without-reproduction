"""A2: read the k-sweep per-nucleotide probe, and say whether both ends know the record equally.

Section 6 closes with "Both ends of Table tab:slots learn a planted record to the same
per-nucleotide accuracy", and the abstract says models "differing only in tokenisation answer any
single hidden nucleotide identically". queue_1028c.sh produced the measurement those sentences
need; this reads it.

WHAT IS COMPARABLE ACROSS TOKENIZERS, AND WHAT IS NOT. These runs are autoregressive, so the
leave-one-out conditional tab:loo reports does not exist for them (extract_icm returns None for
causal models). What target_surprise gives is:

  target_bits_per_nt   teacher-forced covering-token surprise divided by 48 target nucleotides.
                       Leading revealed letters constrain the softmax; trailing host letters
                       in the final token remain scored. A common divisor does not make this
                       a strictly cropped 48-nucleotide event across tokenizers.
  top1_rate            teacher-forced argmax accuracy PER TOKEN. A 6-mer step covers six
                       nucleotides and a character step covers one, so 0.9 means very different
                       things in the two, and this column must never be called a per-nucleotide
                       accuracy. It is printed here because it is what the run recorded, labelled
                       for what it is.

So the honest test of the closing sentence is target_bits_per_nt: if the character end and the
6-mer end sit at the same bits per nucleotide on planted records while extraction goes from 0% to
92%, the sentence holds. If the character end is far worse per nucleotide, it does not.

MATCHED LOSS. tab:slots is read at held-out 2.05/2.10/2.20/2.40 and no saved checkpoint sits on
any of them: the table interpolates between saved epochs. This prints the probe at each saved
epoch with its held-out loss, and interpolates to the four comparison points the same way, so the
two are read on one footing. The character model never exceeds 2.044, so its interpolated columns
are empty above that -- which is itself the finding, and the reason the closing sentence cannot be
read "at matched loss" across the whole sweep.

    python -m pilot2.kcurve_pernt [--root outputs/kcurve300] [--tier 16]
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

TOKS = ["char", "2mer", "3mer", "4mer", "5mer", "6mer"]
TARGETS = [2.05, 2.10, 2.20, 2.40]
SLOTS = {"char": 48.0, "2mer": 24.0, "3mer": 16.0, "4mer": 12.0, "5mer": 9.6, "6mer": 8.0}


def heldout_by_epoch(fig_csv, group):
    """epoch -> held-out bits/nt, per (tokenizer, seed), from the published table."""
    out = defaultdict(dict)
    with open(fig_csv) as fh:
        for r in csv.DictReader(fh):
            if r["group"] != group:
                continue
            out[(r["tokenizer"], r["seed"])][r["epoch"]] = float(r["heldout_bits_per_nt"])
    return out


def interp(points, target):
    """Linear interpolation of y at x=target from (x, y) pairs, or None if target is outside."""
    pts = sorted(points)
    if not pts or target < pts[0][0] or target > pts[-1][0]:
        return None
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= target <= x1:
            if x1 == x0:
                return y0
            return y0 + (y1 - y0) * (target - x0) / (x1 - x0)
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="outputs/kcurve300")
    ap.add_argument("--group", default="kcurve300")
    ap.add_argument("--fig_csv", default="results/figure_data.csv")
    ap.add_argument("--tier", type=int, default=16)
    ap.add_argument("--out", default="results/kcurve_per_nt.json")
    args = ap.parse_args(argv)

    hl = heldout_by_epoch(args.fig_csv, args.group)

    # (tokenizer, seed, epoch) -> the probe readings, from the recon_audit json the queue wrote
    rows = []
    for f in sorted(Path(args.root).glob("*/recon_ep*.json")):
        run = f.parent.name
        tok = run.split("_")[0]
        seed = run.split("_s")[-1]
        ep = f.stem[len("recon_ep"):]
        d = json.loads(f.read_text(encoding="utf-8"))
        per = defaultdict(list)
        for c in d.get("cells", []):
            if c.get("host") != "train" or int(c.get("tier", -1)) != args.tier:
                continue
            t = c.get("target") or {}
            per["bits"].append(t.get("target_bits_per_nt"))
            per["top1"].append(t.get("top1_rate"))
            pre = c.get("prefix") or {}
            per["pre_exact"].append(float(bool(pre.get("exact"))))
        ctl = defaultdict(list)
        for c in d.get("cells", []):
            if int(c.get("tier", -1)) != 0:
                continue
            t = c.get("target") or {}
            ctl["bits"].append(t.get("target_bits_per_nt"))
            ctl["top1"].append(t.get("top1_rate"))
        if not per["bits"]:
            continue
        rows.append({"tokenizer": tok, "seed": seed, "epoch": ep,
                     "slots": SLOTS.get(tok),
                     "heldout": hl.get((tok, seed), {}).get(ep),
                     "n": len(per["bits"]),
                     "target_bits_per_nt": float(np.mean(per["bits"])),
                     "top1_per_token": float(np.mean(per["top1"])),
                     "prefix_exact": float(np.mean(per["pre_exact"])),
                     "control_bits_per_nt": (float(np.mean(ctl["bits"])) if ctl["bits"]
                                             else None),
                     "control_top1_per_token": (float(np.mean(ctl["top1"])) if ctl["top1"]
                                                else None)})

    if not rows:
        raise SystemExit("no recon_ep*.json under %s" % args.root)

    # per tokenizer: the curve over held-out loss, and the four interpolated comparison points
    by_tok = defaultdict(list)
    for r in rows:
        if r["heldout"] is not None:
            by_tok[r["tokenizer"]].append(r)

    table = []
    for tok in TOKS:
        rs = by_tok.get(tok)
        if not rs:
            continue
        pts_bits = [(r["heldout"], r["target_bits_per_nt"]) for r in rs]
        pts_top1 = [(r["heldout"], r["top1_per_token"]) for r in rs]
        pts_ext = [(r["heldout"], r["prefix_exact"]) for r in rs]
        row = {"tokenizer": tok, "slots": SLOTS.get(tok), "n_cells": len(rs),
               "heldout_min": round(min(p[0] for p in pts_bits), 3),
               "heldout_max": round(max(p[0] for p in pts_bits), 3),
               "control_bits_per_nt": round(float(np.mean(
                   [r["control_bits_per_nt"] for r in rs
                    if r["control_bits_per_nt"] is not None])), 3),
               "at": {}}
        for t in TARGETS:
            b, o, e = interp(pts_bits, t), interp(pts_top1, t), interp(pts_ext, t)
            row["at"]["%.2f" % t] = {
                "target_bits_per_nt": (None if b is None else round(b, 3)),
                "top1_per_token": (None if o is None else round(o, 3)),
                "prefix_exact": (None if e is None else round(e, 3))}
        # the end of training, where each tokenizer is at its own loss
        last = max(rs, key=lambda r: r["heldout"])
        row["end_of_training"] = {
            "epoch": last["epoch"], "heldout": round(last["heldout"], 3),
            "target_bits_per_nt": round(last["target_bits_per_nt"], 3),
            "top1_per_token": round(last["top1_per_token"], 3),
            "prefix_exact": round(last["prefix_exact"], 3)}
        table.append(row)

    out = {"root": args.root, "tier": args.tier, "n_rows": len(rows),
           "note": ("target_bits_per_nt is per nucleotide and comparable across tokenizers; "
                    "top1_per_token is per TOKEN and is not. The leave-one-out conditional of "
                    "tab:loo does not exist for these runs, which are autoregressive."),
           "per_tokenizer": table, "cells": rows}
    Path("results").mkdir(exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8")

    print("tier %d, host=train, %d (tokenizer, seed, epoch) cells\n" % (args.tier, len(rows)))
    print("%-6s %5s | %-13s | %s" % ("tok", "slots", "end of training",
                                     "  ".join("@%.2f" % t for t in TARGETS)))
    print("%-6s %5s | %-13s | %s" % ("", "", "bits/nt  ext",
                                     "  ".join("bits  ext " for _ in TARGETS)))
    for r in table:
        e = r["end_of_training"]
        cells = []
        for t in TARGETS:
            a = r["at"]["%.2f" % t]
            if a["target_bits_per_nt"] is None:
                cells.append("  ---      ")
            else:
                cells.append("%5.3f %4.0f%% " % (a["target_bits_per_nt"],
                                                 100 * a["prefix_exact"]))
        print("%-6s %5.1f | %5.3f %4.0f%%  | %s"
              % (r["tokenizer"], r["slots"], e["target_bits_per_nt"],
                 100 * e["prefix_exact"], " ".join(cells)))
    print()
    print("never-trained control, target bits/nt:")
    for r in table:
        print("   %-6s %5.3f   (held-out range %.3f to %.3f)"
              % (r["tokenizer"], r["control_bits_per_nt"], r["heldout_min"], r["heldout_max"]))
    print()
    print("per-TOKEN top-1 at end of training (NOT comparable across tokenizers):")
    for r in table:
        print("   %-6s %.3f" % (r["tokenizer"], r["end_of_training"]["top1_per_token"]))
    print("-> %s" % args.out)


if __name__ == "__main__":
    raise SystemExit(main())
