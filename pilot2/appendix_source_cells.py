"""Read the saved cells supporting recovery tables and the scorer-sensitivity audit.

Run from the project root on the machine holding outputs/:
    python -m pilot2.appendix_source_cells --root .

By default this is a read-only audit: JSON is printed to stdout, no model is loaded and no
scores are recomputed. The bundled results/appendix_source_cells.json preserves
the aggregate evidence and source hashes when outputs/ is unavailable.
Regenerate just the table fragments from that public summary:
    python -m pilot2.appendix_source_cells --summary results/appendix_source_cells.json \
        --tables-out paper/tables
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def read(path):
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def cell(d, tier, host):
    rows = [p for p in d["probes"] if p["repetitions"] == tier]
    values = [p["extract"][host] for p in rows]
    assert values and all(x["n_generated_nt"] == 48 for x in values)
    hits = sum(bool(x["exact"]) for x in values)
    return {"tier": tier, "host": host, "n": len(values), "hits": hits,
            "rate": hits / len(values), "evaluation_endpoint_nt": 48}


def scorer_audit(root):
    """Aggregate candidate-ranking outcomes, retaining no candidate sequence or ID."""
    rules = ("current", "span_matched", "raw_total")
    pairs = [("bpe_human", f"dnabert2bpe_human_s{s}", "final", s)
             for s in range(3)] + [
                 ("dnabert_long", "dnabert2bpe_ecoli_s0", "ep30", 0),
                 ("dnabert_long", "dnabert2bpe_ecoli_s0", "final", 0)]
    files, headline = [], []
    totals = {"n": 0, "span_matched_differences": 0, "raw_total_differences": 0}
    pooled_controls = {"n": 0, "hits": dict.fromkeys(rules, 0)}
    for group, run, tag, seed in pairs:
        directory = Path("outputs") / group / run
        source = directory / f"bpe_divisor_{tag}.json"
        data, source_hash = read(root / source)
        args, args_hash = read(root / directory / "args.json")
        rows = data["cells"]
        tiers, hosts = sorted({r["tier"] for r in rows}), sorted({r["host"] for r in rows})
        assert len(rows) == 400 and tiers == [0, 1, 4, 16]
        assert len(hosts) == 2 and "fresh" in hosts
        diffs = {rule: sum((r[rule]["rank"] == 1) != (r["current"]["rank"] == 1)
                          for r in rows) for rule in rules[1:]}
        cells = []
        for tier in tiers:
            for host in hosts:
                subset = [r for r in rows if r["tier"] == tier and r["host"] == host]
                assert len(subset) == 50
                hits = {rule: sum(r[rule]["rank"] == 1 for r in subset) for rule in rules}
                cells.append({"tier": tier, "host": host, "n": len(subset), "hits": hits,
                              "rates": {rule: count / len(subset) for rule, count in hits.items()}})
                if tier == 0:
                    pooled_controls["n"] += len(subset)
                    for rule in rules:
                        pooled_controls["hits"][rule] += hits[rule]
        totals["n"] += len(rows)
        totals["span_matched_differences"] += diffs["span_matched"]
        totals["raw_total_differences"] += diffs["raw_total"]
        epoch = args["epochs"] if tag == "final" else int(tag.removeprefix("ep"))
        files.append({"source": source.as_posix(), "source_sha256": source_hash,
                      "args_sha256": args_hash, "seed": seed, "epoch": epoch,
                      "file_checkpoint_label": tag, "n": len(rows), "tiers": tiers,
                      "hosts": hosts, "rank1_differences_from_current": diffs, "cells": cells})
        if group == "bpe_human":
            member = next(c for c in cells if c["tier"] == 1 and c["host"] == "fresh")
            control = next(c for c in cells if c["tier"] == 0 and c["host"] == "fresh")
            assert member["hits"]["current"] == (9, 11, 13)[seed]
            assert member["hits"]["span_matched"] == (11, 11, 14)[seed]
            assert control["hits"]["current"] == 0
            assert control["hits"]["span_matched"] == (1, 0, 0)[seed]
            headline.append({"seed": seed, "epoch": epoch, "member": member, "control": control})
    assert totals == {"n": 2000, "span_matched_differences": 33, "raw_total_differences": 20}
    assert pooled_controls["n"] == 500
    assert pooled_controls["hits"] == {"current": 7, "span_matched": 7, "raw_total": 8}
    pooled_controls["rates"] = {rule: count / pooled_controls["n"]
                                 for rule, count in pooled_controls["hits"].items()}
    return {"rules": list(rules), "files": files, "totals": totals,
            "pooled_controls_all_files_both_hosts": pooled_controls,
            "chr22_final_single_copy_fresh": headline}


def audit(root):
    hyena = []
    groups = [("uniform", "hyena", "", (0, 1, 2), "final", (14, 19, 13)),
              ("ecoli", "hyena_ecoli", "_ecoli", (0, 1), "ep30", (17, 14)),
              ("yeast", "hyena_yeast", "_yeast", (0, 1, 2), "ep30", (18, 16, 20)),
              ("gue", "hyena_gue", "_gue", (0, 1, 2), "ep30", (16, 17, 13))]
    for corpus, group, suffix, seeds, tag, expected in groups:
        for seed, hits in zip(seeds, expected):
            run = Path("outputs") / group / f"hyena_medium-160k{suffix}_s{seed}"
            args, args_hash = read(root / run / "args.json")
            source = run / f"scores_{tag}.json"
            data, score_hash = read(root / source)
            assert args["model"] == "hyenadna-medium-160k-seqlen-hf"
            assert args["lr"] == 2e-5 and args["seed"] == seed
            assert not args.get("canary_npz") and data["epoch"] == 30
            member = cell(data, 16, "train")
            assert member["n"] == 20 and member["hits"] == hits
            hyena.append({"background": corpus, "model": args["model"],
                          "seed": seed, "learning_rate": args["lr"],
                          "epoch": data["epoch"], "file_checkpoint_label": tag,
                          "canaries": "uniform iid 96-nucleotide DNA",
                          "configuration": {k: args.get(k) for k in
                                            ("epochs", "n_train", "batch", "accum",
                                             "data_seed", "probe_offset", "save_epochs")},
                          "source": source.as_posix(), "source_sha256": score_hash,
                          "args_sha256": args_hash, "member": member,
                          "never_trained_fresh": cell(data, 0, "fresh")})

    overlap = []
    for k, own_hits, fresh_hits in zip((3, 4, 5, 6), (0, 1, 3, 25), (0, 1, 1, 18)):
        run = Path("outputs/dnabert_long") / f"dnabert{k}_nt0.05_lr0.0001_human_s0"
        args, args_hash = read(root / run / "args.json")
        source = run / "scores_ep120_n50.json"
        data, score_hash = read(root / source)
        assert data["objective"] == "mlm" and data["checkpoint"] == "ep120.pt"
        own, fresh = cell(data, 16, "train"), cell(data, 16, "fresh")
        assert own["n"] == fresh["n"] == 50
        assert (own["hits"], fresh["hits"]) == (own_hits, fresh_hits)
        overlap.append({"k": k, "seed": 0, "epoch": 120,
                        "objective": data["objective"], "learning_rate": args["lr"],
                        "canaries": "human-variant-derived chromosome-22 records",
                        "source": source.as_posix(), "source_sha256": score_hash,
                        "args_sha256": args_hash, "own": own, "fresh": fresh})
    return {"schema_version": 1, "recovery_decoder": "one greedy prefix continuation",
            "hyena_epoch30": hyena, "overlap_epoch120_n50": overlap,
            "candidate_scorer_audit": scorer_audit(root),
            "scope": "Saved evaluation cells; no training or model inference performed."}


def render_tables(evidence):
    """Render only verified aggregate cells; no model outputs are needed here."""
    hyena_rows = []
    labels = {"uniform": "Uniform DNA", "ecoli": r"\emph{E.~coli}",
              "yeast": "Yeast", "gue": "GUE promoters"}
    for corpus, label in labels.items():
        rows = [r for r in evidence["hyena_epoch30"] if r["background"] == corpus]
        seeds = ", ".join(str(r["seed"]) for r in rows)
        members = ", ".join(f'{r["member"]["hits"]}/{r["member"]["n"]}' for r in rows)
        controls = [f'{r["never_trained_fresh"]["hits"]}/{r["never_trained_fresh"]["n"]}' for r in rows]
        control = controls[0] + " in each seed" if len(set(controls)) == 1 else ", ".join(controls)
        hyena_rows.append(f"{label} & {seeds} & {members} & {control} " + r"\\")
    hyena = r"""% Verified by pilot2.appendix_source_cells; source hashes in results/appendix_source_cells.json.
\begin{table}[tbp]
\centering
\caption{HyenaDNA medium-160k at epoch 30, learning rate $2\times10^{-5}$.
Exact recovery of the hidden 48\nt{} by one greedy prefix continuation.
Canaries are uniform synthetic 96\nt{} DNA; members are planted sixteen times at random offsets.
Member results use the own window, with 20 records
per seed. Counts follow the listed seed order; fresh-window controls are never trained.}
\label{tab:hyena30}
\begin{tabular}{lllc}
\toprule
Background & Seeds & Member hits/evaluated & Control hits/evaluated \\
\midrule
""" + "\n".join(hyena_rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    overlap_rows = []
    for row in evidence["overlap_epoch120_n50"]:
        own, fresh = row["own"], row["fresh"]
        overlap_rows.append(
            f'{row["k"]} & {own["hits"]}/{own["n"]} & {100*own["rate"]:g}' + r"\% & "
            + f'{fresh["hits"]}/{fresh["n"]} & {100*fresh["rate"]:g}' + r"\% \\")
    overlap = r"""% Verified by pilot2.appendix_source_cells; source hashes in results/appendix_source_cells.json.
\begin{table}[tbp]
\centering
\caption{Overlapping DNABERT, masked fine-tuning on chromosome 22, epoch 120,
seed 0: one greedy prefix continuation, with exactness evaluated on the hidden 48\nt{}.
Each tokenizer evaluates the same 50 sixteen-copy human-variant-derived records in both
access conditions. These are the full \texttt{scores\_ep120\_n50.json} evaluations.}
\label{tab:overlap50}
\begin{tabular}{ccccc}
\toprule
$k$ & Own hits/evaluated & Own rate & Fresh hits/evaluated & Fresh rate \\
\midrule
""" + "\n".join(overlap_rows) + r"""
\bottomrule
\end{tabular}
\end{table}
"""
    return {"a17_hyena_epoch30.tex": hyena, "a18_overlap_prefix50.tex": overlap}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--summary", type=Path, help="read bundled aggregate evidence instead of outputs/")
    parser.add_argument("--tables-out", type=Path, help="write the two reproducible LaTeX table fragments")
    args = parser.parse_args()
    evidence = read(args.summary)[0] if args.summary else audit(args.root)
    if args.tables_out:
        args.tables_out.mkdir(parents=True, exist_ok=True)
        for name, content in render_tables(evidence).items():
            (args.tables_out / name).write_text(content, encoding="utf-8", newline="\n")
            print(args.tables_out / name)
    else:
        print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
