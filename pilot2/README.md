# Implementation map

[Repository home](../README.md) · [Reproduction guide](../docs/REPRODUCING.md)

Run modules from the repository root with `python -m pilot2.<module>`.

| Purpose | Entry points |
| --- | --- |
| Current main quantitative figures | `figures_main10.py`, using `figures_privacy.py` and `figure_fonts.py` |
| Appendix tables | `appendix_tables.py`, `appendix_source_cells.py` |
| Full-precision utility aggregation | `analyze_downstream.py` |
| Hidden 48-nt evaluation | `target48.py`, `refresh_target48.py` |
| Released-model training and prefix evaluation | `dnabert.py`, `dnabert2.py`, `nt.py`, `hyena.py` |
| Controlled-backbone experiments | `run_pilot.py`, `train.py`, `model.py`, `tokenizers.py`, `sweep.sh` |
| Re-masking reconstruction | `recon_audit.py`, `recon_overlap.py`, `recon_bpe.py` |
| Scoring and downstream probes | `score.py`, `rescore.py`, `downstream.py`, `utility_at_leak.py` |
| Human record construction/audit | `human_canary.py`, `canary_census.py`, `canary_haplotype_audit.py` |
| CSV export from original runs | `export_figure_data.py` (requires original outputs) |

## Historical and supporting code

The dated `queue_*.sh` files record original invocations; inspect their paths,
device selections and dependencies before running them on another machine.
They are provenance, not a universal one-command reproduction launcher.

Earlier plotting tools such as `figures_proposal.py`, `figures_paper.py` and
`plot_e2.py`, and the remaining audit modules, are retained for the dated notebooks.
The root README identifies the current figure command. Do not remove
`figures_privacy.py`: the current plotting implementation imports it.

The neighboring [pilot/](../pilot/) is a frozen earlier implementation.
No historical module or measurement was deleted during the documentation cleanup.
