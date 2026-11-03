# Repository layout and retention decisions

[English home](../README.md) · [简体中文首页](../README.zh-CN.md)

This is the public analysis artifact, not the private collaboration checkout.
The main [README](../README.md#contents) combines the overview, setup, commands
and evidence map. A complete [simplified-Chinese version](../README.zh-CN.md) is available.

| Material | Decision | Reason |
| --- | --- | --- |
| `pilot2/` current analysis, training and decoder code | Keep paths | Importable implementations and reproducibility entry points |
| `results/` CSV, aggregate manifests and redacted evaluations | Keep all | Measurement provenance, controls, negative results and sensitivity checks |
| `tests/` | Keep | Regression checks for utility merging and endpoint handling |
| `paper/figures/`, PPTX/PDF and source archive | Keep | Editable current Figure 1 and preserved original |
| `notes/` dated logs and `notes/figures/` | Keep, improve index | Historical reasoning and corrections; not all entries are current claims |
| `pilot/`, old plotting modules, dated queues | Keep as historical | Referenced by notebooks; moving them can break paths or imports |
| Setup, commands and paper protocols | Merge into bilingual READMEs | One maintained entry point, with contents links; old guide URLs remain as forwarding pages |
| Identical model requirement lists | One source, compatibility wrapper | `requirements.txt` includes `requirements-paper.txt` |
| Lightweight plotting requirements | Separate file | No GPU/model stack needed to rebuild public figures |
| Missing entries in notebook index | Remove from index | Do not advertise unpublished files |
| Generated `reproduced/` output | Ignore in Git | Avoid accidental commits or overwriting the released measurements |

No source measurements, historical experiments or negative results were removed.
No Git history was rewritten. This is navigation and documentation cleanup rather
than a claim that every archived script is portable or every historical claim current.

## Evidence entry points

- Figures 2–3 trajectories: [figure_data.csv](../results/figure_data.csv).
- Covering-token target surprise: [kcurve_per_nt.json](../results/kcurve_per_nt.json).
- Six-task utility means and coverage:
  [utility_downstream.json](../results/dnabert_gue_ds/utility_downstream.json).
- Additional source-cell tables and scorer audit:
  [appendix_source_cells.json](../results/appendix_source_cells.json).
- Endpoint correction: [target48_audit.json](../results/target48_audit.json).
- Historical bound terminology: [results guide](../results/README.md).

Directory names alone do not identify objective, checkpoint, placement or access
conditions. Use the recorded arguments and the manuscript's campaign definitions.
