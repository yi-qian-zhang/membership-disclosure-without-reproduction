"""Unique-checkpoint downstream summaries, with explicit available-case coverage.

python -m pilot2.analyze_downstream --root outputs/dnabert_gue_ds \
    outputs/dnabert_gue_ds2 outputs/dnabert_yeast_ds outputs/hyena_gue_ds \
    outputs/hyena_gue_ds2 outputs/hyena_yeast_ds --out-dir results/dnabert_gue_ds

Repeated task panels are merged before averaging. Conflicting measurements and
unresolved variable-length endpoints fail. JSON preserves precise aggregates,
configuration identities, source hashes and counts, but no record sequences/IDs.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean

from .target48 import target48

RUN = re.compile(r"(?P<model>dnabert\d|dnabert2bpe|hyena_[a-z0-9-]+?|bpe\d+|char|\d+mer(?:sp)?)"
                 r"(?P<var>_[A-Za-z0-9._-]+?)?_s(?P<seed>\d+)$")
LABEL = {"dnabert3": "DNABERT 3-mer", "dnabert4": "DNABERT 4-mer", "dnabert5": "DNABERT 5-mer",
         "dnabert6": "DNABERT 6-mer", "dnabert2bpe": "DNABERT-2 BPE", "hyena_medium-160k": "HyenaDNA medium"}
TASK = {"prom_300_all": "promoter detection (human)", "prom_core_all": "core promoter (human)",
        "human_tf_0": "TF binding (human)", "splice_reconstructed": "splice sites (human, 3-class)",
        "emp_H3": "histone H3 (yeast)", "emp_H3K4me3": "histone H3K4me3 (yeast)"}
ORDER = list(TASK)
# Exclude only output locations, downstream panels and snapshot schedules.
# Training/data arguments and scorer settings (e.g. pool, stride) remain identity fields.
NONIDENTITY_ARGS = {"out", "gpu", "downstream", "downstream_tasks", "save_epochs",
                    "snapshot_probes", "score_epoch0", "keep_ckpt", "drop_ckpt",
                    "save_ckpt", "no_save_ckpt"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def epoch_of(path, doc):
    match = re.fullmatch(r"scores_ep(\d+)", path.stem)
    stored = doc.get("epoch", doc.get("train_summary", {}).get("epochs"))
    if match:
        epoch = int(match[1])
        if stored is not None and int(stored) != epoch:
            raise ValueError(f"Checkpoint epoch conflict: {path}")
        return epoch
    if stored is None:
        raise ValueError(f"Missing checkpoint epoch: {path}")
    return int(stored)


def merge_equal(left, right, where):
    """Union additional fields, never silently choose conflicting evidence."""
    if isinstance(left, dict) and isinstance(right, dict):
        for key, value in right.items():
            left[key] = merge_equal(left[key], value, f"{where}.{key}") if key in left else deepcopy(value)
        return left
    if left != right:
        # Avoid printing record content in errors.
        raise ValueError(f"Conflicting duplicate measurement: {where}")
    return left


def without_timing(value):
    if isinstance(value, dict):
        return {k: without_timing(v) for k, v in value.items() if k != "sec"}
    if isinstance(value, list):
        return [without_timing(v) for v in value]
    return value


def downstream_tasks(doc, source):
    downstream = doc.get("downstream") or {}
    if downstream.get("tasks"):
        panels = downstream["tasks"]
    elif downstream.get("task"):
        panels = {downstream["task"]: {k: v for k, v in downstream.items() if k != "task"}}
    else:
        return {}
    tasks = {}
    for name, metrics in panels.items():
        name = "prom_300_all" if name == "gue_prom_300_all" else name
        merge_equal(tasks, {name: without_timing(metrics)}, f"{source}.downstream")
    return tasks


def source_name(path):
    resolved = path.resolve()
    try:
        return resolved.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def collect(roots):
    """Unique configuration/checkpoint cells; skipped sources are explicit."""
    cells, seen, skipped = {}, set(), []
    for root in sorted({str(Path(p).resolve()) for p in roots}):
        root = Path(root)
        if not root.is_dir():
            raise ValueError(f"Missing input root: {root}")
        for directory in sorted(root.iterdir()):
            match = RUN.fullmatch(directory.name) if directory.is_dir() else None
            if not match:
                continue
            files = sorted(directory.glob("scores_ep*.json")) + [directory / "scores_final.json"]
            for path in files:
                if not path.exists() or path.resolve() in seen:
                    continue
                seen.add(path.resolve())
                source = source_name(path)
                raw = path.read_bytes()
                doc = json.loads(raw)
                tasks = downstream_tasks(doc, source)
                if not tasks:
                    skipped.append({"source": source, "reason": "no downstream task measurements"})
                    continue
                args = json.loads((directory / "args.json").read_text(encoding="utf-8"))
                for required in ("seed", "data", "data_seed"):
                    if required not in args:
                        raise ValueError(f"Missing identity argument {required}: {source}")
                if int(args["seed"]) != int(match["seed"]):
                    raise ValueError(f"Directory/argument seed conflict: {source}")
                config = {k: v for k, v in args.items() if k not in NONIDENTITY_ARGS and v is not None}
                identity = {"model": match["model"], "arguments": config}
                config_id = digest(identity)
                epoch = epoch_of(path, doc)
                key = (config_id, epoch)
                if key not in cells:
                    cells[key] = {"config_id": config_id, "identity": identity, "epoch": epoch,
                                  "sources": [], "probes": {}, "tasks": {}, "measurement": {}}
                cell = cells[key]
                measurement = {k: doc[k] for k in ("kind", "k", "objective", "pool_size", "stride", "floors")
                               if k in doc}
                merge_equal(cell["measurement"], measurement, source)
                ids = [p["probe_id"] for p in doc["probes"]]
                if len(set(ids)) != len(ids):
                    raise ValueError(f"Repeated probe_id within one source: {source}")
                for probe in doc["probes"]:
                    merge_equal(cell["probes"], {probe["probe_id"]: probe}, f"{source}.probes")
                merge_equal(cell["tasks"], tasks, f"{source}.tasks")
                cell["sources"].append({"path": source, "sha256": hashlib.sha256(raw).hexdigest(),
                                        "probe_rows": len(ids), "tasks": sorted(tasks)})
    return [cells[key] for key in sorted(cells)], skipped


def canary(cell, tier=16):
    probes = list(cell["probes"].values())
    rank_key = next((k for k in ("causal/train", "ar/train", "span_pll/train", "pll/train")
                     if any(k in p["ranks"] for p in probes)), None)
    selected = [p for p in probes if p["repetitions"] == tier]
    if not selected or rank_key is None or any(rank_key not in p["ranks"] for p in selected):
        raise ValueError(f"Missing member ranks: {cell['config_id']} round {cell['epoch']}")
    exact, hamming = [], []
    native_only = cropped = changed = 0
    for probe in selected:
        ex = probe["extract"]["train"]
        n = ex.get("n_generated_nt")
        if n is None:
            raise ValueError(f"Missing recovery interval: {cell['config_id']}")
        if "pred_nt" in ex and "truth_nt" in ex:
            truth, pred = ex["truth_nt"], ex["pred_nt"]
            ham = sum(a != b for a, b in zip(pred[:int(n)], truth)) + max(0, int(n) - len(pred))
            if len(truth) != int(n) or ham != ex["hamming_nt"] or bool(ham == 0) != ex["exact"]:
                raise ValueError(f"Saved prediction/summary conflict: {cell['config_id']}")
        elif int(n) == 48:
            native_only += 1
        try:
            result = target48(ex)
        except ValueError as error:
            raise ValueError(f"Unresolved legacy endpoint: {cell['config_id']} round {cell['epoch']}; {error}") from error
        cropped += int(n) != 48
        changed += result["exact"] != ex["exact"]
        exact.append(bool(result["exact"]))
        hamming.append(result["hamming_nt"])
    ranks = [p["ranks"][rank_key] for p in selected]
    top1 = [float(r["rank"] == 1) if "rank" in r else float(r["top1"]) for r in ranks]
    return {"tier": tier, "host": "train", "evaluation_endpoint": "hidden48", "rank_key": rank_key,
            "record_evaluations": len(selected), "exact_count": sum(exact), "exact_rate": mean(exact),
            "rank1_rate": mean(top1), "bits_per_nt": mean(r["probe_bits_per_nt"] for r in ranks),
            "mean_hamming_nt": mean(hamming), "native48_summary_only_count": native_only,
            "coordinate_cropped_count": cropped, "exact_changed_count": changed}


def summarize(cells, skipped):
    runs, grouped = [], defaultdict(list)
    for cell in cells:
        args = cell["identity"]["arguments"]
        tasks = {t: {"linear_probe_mcc": v.get("linear_probe", {}).get("mcc"),
                     "finetune_mcc": v.get("finetune", {}).get("mcc")}
                 for t, v in sorted(cell["tasks"].items())}
        run = {"config_id": cell["config_id"], "identity": cell["identity"], "epoch": cell["epoch"],
               "corpus": args["data"], "seed": args["seed"], "data_seed": args["data_seed"],
               "sources": sorted(cell["sources"], key=lambda s: s["path"]),
               "all_tier_probe_rows": len(cell["probes"]),
               "heldout_bits_per_nt": cell["measurement"]["floors"][0]["bits_per_nt_mean"],
               "canary": canary(cell), "tasks": tasks}
        runs.append(run)
        grouped[cell["identity"]["model"]].append(run)
    models = []
    for model in sorted(grouped, key=lambda m: (not m.startswith("dnabert"), m)):
        rows = []
        for epoch in sorted({r["epoch"] for r in grouped[model]}):
            part = [r for r in grouped[model] if r["epoch"] == epoch]
            task_names = {t for r in part for t in r["tasks"]}
            tasks = {}
            for task in sorted(task_names, key=lambda t: (ORDER.index(t) if t in ORDER else len(ORDER), t)):
                contributors = [r for r in part if task in r["tasks"]]
                metrics = {}
                for metric in ("linear_probe_mcc", "finetune_mcc"):
                    available = [r for r in contributors if r["tasks"][task][metric] is not None]
                    metrics[metric] = mean(r["tasks"][task][metric] for r in available) if available else None
                    metrics[metric + "_n_configurations"] = len(available)
                tasks[task] = {**metrics, "n_configurations": len(contributors),
                               "coverage": [{k: r[k] for k in ("config_id", "corpus", "seed", "data_seed")}
                                            for r in contributors]}
            rows.append({"epoch": epoch, "n_configurations": len(part),
                         "config_ids": [r["config_id"] for r in part],
                         "n_source_files": sum(len(r["sources"]) for r in part),
                         "record_evaluations": sum(r["canary"]["record_evaluations"] for r in part),
                         "exact_count": sum(r["canary"]["exact_count"] for r in part),
                         "heldout_bits_per_nt": mean(r["heldout_bits_per_nt"] for r in part),
                         "canary": {k: mean(r["canary"][k] for r in part)
                                    for k in ("bits_per_nt", "rank1_rate", "exact_rate", "mean_hamming_nt")},
                         "tasks": tasks})
        best = min(rows, key=lambda r: (r["heldout_bits_per_nt"], r["epoch"]))
        candidates = [(mean(t["finetune_mcc"] for t in r["tasks"].values() if t["finetune_mcc"] is not None),
                       r["epoch"]) for r in rows if r["epoch"] > 0
                      and any(t["finetune_mcc"] is not None for t in r["tasks"].values())]
        best_task = min(candidates, key=lambda p: (-p[0], p[1])) if candidates else (None, None)
        last = rows[-1]
        deltas = {t: last["tasks"][t]["linear_probe_mcc"] - best["tasks"][t]["linear_probe_mcc"]
                  for t in last["tasks"] if t in best["tasks"]
                  and last["tasks"][t]["linear_probe_mcc"] is not None
                  and best["tasks"][t]["linear_probe_mcc"] is not None}
        ft_deltas = {t: last["tasks"][t]["finetune_mcc"] - best["tasks"][t]["finetune_mcc"]
                     for t in last["tasks"] if t in best["tasks"]
                     and last["tasks"][t]["finetune_mcc"] is not None
                     and best["tasks"][t]["finetune_mcc"] is not None}
        models.append({"model": model, "label": LABEL.get(model, model), "rows": rows,
                       "selection": {"first_epoch": rows[0]["epoch"], "best_heldout_epoch": best["epoch"],
                                     "last_epoch": last["epoch"], "best_downstream_epoch": best_task[1],
                                     "best_downstream_mean_mcc": best_task[0]},
                       "best_to_last_linear_probe_deltas": deltas,
                       "best_to_last_max_abs_linear_probe_delta": max(map(abs, deltas.values())) if deltas else None,
                       "best_to_last_finetune_deltas": ft_deltas})
    return {"schema_version": 1, "evaluation_endpoint": "hidden48",
            "aggregation": {"weighting": "equal weight per unique training configuration/seed/checkpoint; tasks use their available configurations",
                            "coverage": "available-case, not a balanced or paired panel; record counts and seed coverage may differ by checkpoint and task",
                            "dedup_identity": "model plus all non-null args except the explicitly excluded operational/task-panel fields, then checkpoint epoch",
                            "excluded_identity_arguments": sorted(NONIDENTITY_ARGS),
                            "duplicate_policy": "union agreeing probe fields and task panels; conflicting measurements fail; source paths counted once",
                            "legacy_policy": "normalize single-task schema; merge saved strings before hidden48 cropping; unresolved variable-length endpoints fail",
                            "independence": "record evaluations reuse canaries across seeds/checkpoints and are not independent trials"},
            "n_unique_checkpoint_configurations": len(runs),
            "n_source_files": sum(len(r["sources"]) for r in runs),
            "skipped_sources": skipped, "models": models, "checkpoint_configurations": runs}


def markdown(report, name):
    md = [f"# Downstream utility against leakage — {name}", "",
          "MCC on each task's full test split: ft is the fine-tuned head and probe the frozen linear probe. "
          "Each task averages its available training configurations/seeds. Loss and canary statistics "
          "give equal weight to each unique configuration/seed/checkpoint across the human and yeast arms. "
          "Repeated task panels are merged before averaging; old single-task reports are included. "
          "Canary extraction evaluates the hidden 48 nucleotides of the 16-copy tier in its training host.", "",
          "These are available-case descriptive summaries, not a balanced or paired panel: seed coverage "
          "and record counts vary across checkpoints and tasks. Repeated record evaluations are not independent trials. "
          f"{name}_downstream.json retains unrounded selection values, source hashes, "
          "configuration identities, per-checkpoint record counts and per-task seed coverage.", ""]
    for model in report["models"]:
        tasks = list(model["rows"][0]["tasks"])
        tasks += sorted({t for r in model["rows"] for t in r["tasks"]} - set(tasks))
        md += [f"## {model['label']}", "",
               "| round | held-out loss | canary bits/nt | recognised | extracted | "
               + " | ".join(TASK.get(t, t) for t in tasks) + " |",
               "|---|---|---|---|---|" + "---|" * len(tasks)]
        for row in model["rows"]:
            scores = []
            for task in tasks:
                values = row["tasks"].get(task, {})
                ft, pr = values.get("finetune_mcc"), values.get("linear_probe_mcc")
                scores.append((f"{ft:.3f}" if ft is not None else "—") + (f" ({pr:.3f})" if pr is not None else ""))
            c = row["canary"]
            md.append(f"| {row['epoch']} | {row['heldout_bits_per_nt']:.3f} | {c['bits_per_nt']:.2f} | "
                      f"{100*c['rank1_rate']:.0f}% | {100*c['exact_rate']:.1f}% | " + " | ".join(scores) + " |")
        md += ["", "Coverage (unique configurations / 16-copy record evaluations): "
               + "; ".join(f"round {r['epoch']}: {r['n_configurations']}/{r['record_evaluations']}"
                           for r in model["rows"]) + ".", ""]
        for row in model["rows"]:
            md.append(f"Task coverage, round {row['epoch']}: " + "; ".join(
                f"{TASK.get(t, t)}: " + ", ".join(f"{c['corpus']} seed {c['seed']}" for c in v["coverage"])
                for t, v in row["tasks"].items()) + ".")
        md.append("")
    md += ["## What a practitioner's stopping rule would pick", "",
           "| model | best held-out loss | canary there | best downstream | canary there | last round | canary there |",
           "|---|---|---|---|---|---|---|"]
    for model in report["models"]:
        selection = model["selection"]
        rows = {r["epoch"]: r for r in model["rows"]}
        best, last = rows[selection["best_heldout_epoch"]], rows[selection["last_epoch"]]
        ds = rows.get(selection["best_downstream_epoch"])
        if ds is None:
            continue
        ext = lambda r: f"{100*r['canary']['exact_rate']:.1f}% extracted"
        md.append(f"| {model['label']} | round {best['epoch']} ({best['heldout_bits_per_nt']:.3f}) | {ext(best)} "
                  f"| round {ds['epoch']} (MCC {selection['best_downstream_mean_mcc']:.3f}) | {ext(ds)} "
                  f"| round {last['epoch']} | {ext(last)} |")
    return "\n".join(md) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", nargs="+", required=True)
    ap.add_argument("--name", default="utility")
    ap.add_argument("--out-dir", type=Path, help="directory for Markdown and JSON (default: first input root)")
    args = ap.parse_args(argv)
    cells, skipped = collect(args.root)
    if not cells:
        raise ValueError("No downstream measurements in the input roots")
    report = summarize(cells, skipped)
    out = args.out_dir or Path(args.root[0])
    out.mkdir(parents=True, exist_ok=True)
    stem = out / f"{args.name}_downstream"
    stem.with_suffix(".json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    stem.with_suffix(".md").write_text(markdown(report, args.name), encoding="utf-8", newline="\n")
    print(f"{len(cells)} unique checkpoint configurations from {report['n_source_files']} source files")
    print(f"-> {stem}.md\n-> {stem}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
