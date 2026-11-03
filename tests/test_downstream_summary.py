"""Provenance, duplicate handling and endpoint checks for downstream reports."""
import json
from pathlib import Path
import tempfile
import unittest

from pilot2.analyze_downstream import ORDER, collect, main, summarize
from pilot2.appendix_tables import table_downstream


class DownstreamSummaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def write_source(self, panel, *, task="prom_300_all", mcc=0.4, legacy=False,
                     strings=True, n=49, lr=0.00002, epoch=3, loss=1.9004):
        root = self.base / panel
        run = root / "dnabert2bpe_causal_gue_s0"
        run.mkdir(parents=True, exist_ok=True)
        args = {"seed": 0, "data": "gue", "data_seed": 1234, "lr": lr,
                "objective": "causal", "pool": 100, "out": str(root),
                "downstream_tasks": task, "snapshot_probes": 10}
        (run / "args.json").write_text(json.dumps(args))
        extraction = {"n_generated_nt": n, "exact": False, "hamming_nt": 1}
        if strings:
            extraction.update(pred_nt="C" + "A" * (n - 1), truth_nt="A" * n)
        metrics = {"linear_probe": {"mcc": mcc, "sec": 12}, "finetune": {"mcc": mcc + 0.1}}
        downstream = {"task": task, **metrics} if legacy else {"tasks": {task: metrics}}
        doc = {"epoch": epoch, "kind": "bpe", "objective": "causal", "pool_size": 100,
               "floors": [{"bits_per_nt_mean": loss, "n_windows": 200}],
               "probes": [{"probe_id": 7, "repetitions": 16,
                           "ranks": {"causal/train": {"rank": 1, "probe_bits_per_nt": 2.0}},
                           "extract": {"train": extraction}, "train_offsets": [96]}],
               "downstream": downstream}
        path = run / f"scores_ep{epoch}.json"
        path.write_text(json.dumps(doc))
        return root, path

    def test_overlap_panels_legacy_alias_and_coordinate_crop(self):
        a, _ = self.write_source("a", task="gue_prom_300_all", legacy=True, strings=False)
        b, _ = self.write_source("b", task="prom_core_all")
        cells, skipped = collect([a, b, a, b.resolve()])
        report = summarize(cells, skipped)
        self.assertEqual((len(cells), report["n_source_files"]), (1, 2))
        row = report["models"][0]["rows"][0]
        self.assertEqual(set(row["tasks"]), {"prom_300_all", "prom_core_all"})
        self.assertEqual(row["record_evaluations"], 1)
        self.assertEqual(row["exact_count"], 1)  # Only the revealed boundary letter was wrong.
        self.assertEqual(report["checkpoint_configurations"][0]["canary"]["exact_changed_count"], 1)
        self.assertEqual(report["models"][0]["selection"]["best_downstream_mean_mcc"], 0.5)
        encoded = json.dumps(report)
        for forbidden in ('"probe_id"', '"probe_ids"', '"pred_nt"', '"truth_nt"'):
            self.assertNotIn(forbidden, encoded)

    def test_duplicate_task_conflicts_fail(self):
        a, _ = self.write_source("a", task="gue_prom_300_all", legacy=True)
        b, _ = self.write_source("b", mcc=0.9)
        with self.assertRaisesRegex(ValueError, "Conflicting duplicate measurement"):
            collect([a, b])

    def test_alias_conflicts_within_panel_fail(self):
        root, path = self.write_source("a")
        doc = json.loads(path.read_text())
        doc["downstream"]["tasks"]["gue_prom_300_all"] = {"linear_probe": {"mcc": 0.9}}
        path.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError, "Conflicting duplicate measurement"):
            collect([root])

    def test_duplicate_probe_provenance_conflicts_fail(self):
        a, _ = self.write_source("a")
        b, path = self.write_source("b", task="prom_core_all")
        doc = json.loads(path.read_text())
        doc["probes"][0]["train_offsets"] = [97]
        path.write_text(json.dumps(doc))
        with self.assertRaisesRegex(ValueError, "Conflicting duplicate measurement"):
            collect([a, b])

    def test_distinct_training_configurations_are_not_merged(self):
        a, _ = self.write_source("a")
        b, _ = self.write_source("b", lr=0.00003)
        cells, _ = collect([a, b])
        self.assertEqual(len(cells), 2)

    def test_unresolved_legacy_endpoint_fails_instead_of_exclusion(self):
        root, _ = self.write_source("a", strings=False)
        cells, skipped = collect([root])
        self.assertEqual(len(cells), 1)
        self.assertEqual(skipped, [])
        with self.assertRaisesRegex(ValueError, "Unresolved legacy endpoint"):
            summarize(cells, skipped)

    def test_native48_summary_only_is_explicit(self):
        root, _ = self.write_source("a", strings=False, n=48)
        report = summarize(*collect([root]))
        canary = report["checkpoint_configurations"][0]["canary"]
        self.assertEqual(canary["native48_summary_only_count"], 1)
        self.assertEqual(canary["record_evaluations"], 1)
        self.assertEqual(canary["exact_count"], 0)

    def test_regeneration_is_idempotent_and_selects_unrounded_loss(self):
        a, _ = self.write_source("a", epoch=3, loss=1.9004)
        _, path = self.write_source("a", epoch=8, loss=1.9003)
        for source in path.parent.glob("scores_*.json"):
            doc = json.loads(source.read_text())
            metrics = doc["downstream"]["tasks"]["prom_300_all"]
            doc["downstream"]["tasks"] = {task: metrics for task in ORDER}
            source.write_text(json.dumps(doc))
        out = self.base / "results" / "dnabert_gue_ds"
        argv = ["--root", str(a), str(a), "--out-dir", str(out)]
        main(argv)
        first = {p.name: p.read_bytes() for p in out.iterdir()}
        main(argv)
        self.assertEqual(first, {p.name: p.read_bytes() for p in out.iterdir()})
        report = json.loads((out / "utility_downstream.json").read_text())
        self.assertEqual(report["models"][0]["selection"]["best_heldout_epoch"], 8)
        tables = self.base / "tables"
        tables.mkdir()
        table_downstream(self.base / "results", tables)
        table = (tables / "a6_downstream.tex").read_text()
        self.assertIn("8 (best held-out)", table)
        self.assertIn("100.0\\%", table)
        saved = (tables / "a6_downstream.tex").read_bytes()
        table_downstream(self.base / "results", tables)
        self.assertEqual(saved, (tables / "a6_downstream.tex").read_bytes())


if __name__ == "__main__":
    unittest.main()
