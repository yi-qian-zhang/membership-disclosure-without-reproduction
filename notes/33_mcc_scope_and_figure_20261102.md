# Linear-probe checkpoint selection and Figure A2 — 2 November 2026

Author-authorized scope: align the practice paragraph, Table A13 and Figure A2;
mirror factual corrections into the uncompressed manuscript; regenerate, compile,
log and synchronize both Overleaf projects and GitHub. Baseline: 7d647f1;
submission Overleaf e803509; full Overleaf 2bc7c82.

## Source check and interpretation

Read the three unchanged bpe_human/dnabert2bpe_human_s*/utility_at_leak.json files.
Mean linear-probe MCC selects round15; individual seeds0/1 select round15,
seed2 round50. Seed2 MCC is 0.801003300170049 at round15 and
0.8023638016821206 at round50. The corresponding own-window single-copy
rank-1 rates are 4% and22%. The figure already computed the seed mean; only
its label was ambiguous. No statistical significance is inferred from the MCC gap.

The text now names mean linear-probe MCC, lists individual-seed selections, and
removes the general reassuring statement that the metric is not misleading.
Table A13 states DNABERT-2 MCC min–max over three seeds and NT seed0; the BPE
checkpoint label is best mean MCC. Its two-line cell avoids widening the table.
Figure A2 labels the BPE point best mean MCC and retains best MCC for NT seed0.
The caption specifies both mean curves and the MCC min–max band. The shared
legend is moved to empty upper-left space; the BPE annotation is below its
curve. The rendered figure has no legend/curve collision. Fine-tuned-task MCC
is not substituted for the explicitly reported frozen linear-probe protocol.

## Preservation and local validation

Only the two p07_practice.tex files, F7 PDF/PNG in both manuscripts, and
pilot2/figures_privacy.py change before notes. Input data, plotted values,
abstracts, bibliographies, other figures and all other manuscript sections are
unchanged by SHA-256 checks. The full manuscript is not compressed.

Clean local output directories: submission36 pages, main9, appendix23;
full44 pages, main16, appendix24. Both have errors0, undefined0, overfull0,
underfull2 (existing). Hard-coded cross-reference checks pass4/4 and5/5.
Rendered submission pages29/30 and full page40 were visually checked, plus
the figure export. MiKTeX latexmk initially lacked Perl on PATH; adding the
installed Git Perl directory resolved the environment issue without source changes.
Remote synchronization and clean-build receipts will be appended after completion.


## Final synchronization receipt

Paper/code commit6213180; public figure code 627f258; submission Overleaf
d244fe2; full Overleaf 1c52c83. Fresh clones of both actual Overleaf
remotes built successfully:36/44pages, main9/16, appendix23/24, errors0,
undefined0, overfull0, existing underfull2 each. All41/39 tracked files are
byte-identical to local. Every rendered page matches its local build.
Local xref checks pass4/4 and5/5; the same source and remote aux are checked
before final release. Both new validation notes use LF. No measurements changed.
Final PDFs are in work/mcc_scope_20261102.
