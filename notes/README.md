# Working logs

The dated record of how the measurements in the paper were produced — every experiment, every
bug, and what each one changed. The paper's availability statement points here.

| | |
|---|---|
| `07_gate1_raw_reports.md` | The first gate: the reports that decided whether the full grid was worth running |
| `08_experiment_log_week1_EN.md` | Week 1 |
| `09_experiment_log_week2_EN.md` | Week 2 |
| `17_experiment_log_week3_EN.md` | Week 3, and the longest — the released-model arms, the four decoders, the human chromosome-22 arm, and the single-basis re-measurement |
| `18_reviewer_experiments_20261030.md` | Independent calibration and strict phased-haplotype replication; frozen design, restartable launches and execution record |
| `19_robustness_experiments_20261030.md` | Original-pool data redraw and ten-background robustness; frozen design, validation and execution record |
| `20_chr21_mlm_experiments_20261031.md` | Three-seed chr21 replication of the current native-MLM main protocol; frozen inputs, validation and execution record |
| `23_ten_page_revision_20261031.md` | Executed v4 manuscript compression, protected evidence, decoder coverage and final synchronization |
| `24_full_manuscript_factcheck_20261031.md` | Separate full manuscript, transferred factual corrections, preservation checks and new Overleaf project |
| `25_f1_source_revision_20261031.md` | Direct revision of the original editable F1, PowerPoint export, scientific scope and page-count verification |
| `26_f1_style_surprise_20261031.md` | DIME-inspired styling of the native F1, restored endpoint surprise comparison, original-source archive and validation |
| `27_f1_target_signal_20261101.md` | Absolute target surprise in F1 and Results, neutral target color, typography and page-count validation |
| `28_submission_closeout_review_20261101.md` | Claim/protocol consistency, public reproduction entry point, five-seat review and focused verification |
| `29_dual_version_fact_sync_20261102.md` | Factual corrections carried to the full manuscript, README scope, restored motivation/effect sizes and bounded prose |
| `31_loo_correction_appendix_revision_20261102.md` | LOO diagnostic interpretation repaired in both manuscripts; submission appendix reduced to 23 pages with full audit data retained |
| `42_main_self_containment_20261103.md` | Main-text evidence and method definitions, source-cell tables, duplicate-checkpoint audit, and factual parity with the full manuscript |
| `figures/` | The generated per-sweep reports and trajectory plots the logs quote |

Entries are numbered `§<week>.<n>` and dated. A claim in the paper can be traced through a log
entry to the run directory under [`../results/`](../results/) that produced it, and from there to
the `args.json` the run was launched with.

## What these are, and are not

They are a laboratory notebook, written as the work happened and not rewritten afterwards. They
record results that did not survive, numbers that were wrong before they were right, and the
reasons for each change. Several entries exist only because a measurement was found to be wrong —
the single-basis re-measurement of 19–23 October is the largest of them, and the paper reports the
re-measured values throughout.

A recurring theme, recorded because it cost the most time: **the failures in this project are
silent.** A `.bashrc` that a non-interactive SSH never reads; a bare `%` eating a table row; a
dispatch keyed on a path; an exporter blind to re-scored files; a status line reporting the exit
code of `date`; a `\ref` that lost its backslash and printed as ordinary text through a clean
compile. None of them raised an error. The practice that catches them is the same every time:
count the output files, and read the output rather than the log.

Project planning, correspondence and talk material are not part of the record and are not
published here.
