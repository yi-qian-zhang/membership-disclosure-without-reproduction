# 3 November 2026: consistency corrections and unique-checkpoint utility summaries

Author authorization: implement the independently verified consistency repairs,
regenerate the utility table, propagate factual repairs to the uncompressed full
manuscript, compile the submission within ten main pages, and synchronize notes,
GitHub and both Overleaf projects. Baseline: eecef06 (paper changes at 0d25f6f).

## Utility aggregation repair

The old collector counted each score file as a seed observation. The GUE ds and
ds2 directories contain different downstream task panels for the same training
configuration/seed/checkpoint, so their repeated canary and held-out measurements
received extra weight. Old single-task downstream records were also omitted.

pilot2/analyze_downstream.py now identifies a configuration from the model and
training/data/scoring arguments, excluding explicit output, task-panel and snapshot
bookkeeping arguments. It merges agreeing measurements and task panels before
averaging, canonicalizes the promoter task alias, supports the old schema, and
fails on conflicting duplicate observations. Repeated input roots are counted once.
Saved strings are merged before applying pilot2.target48. Variable-length archival
endpoints without enough information fail; native-48 summary-only rows are counted
explicitly. Raw evaluations and model weights were not modified or regenerated.

The new results/dnabert_gue_ds/utility_downstream.json contains full-precision
aggregates, source SHA-256 hashes, configuration identities, record-evaluation
counts and per-task seed coverage. It contains no sequences or individual record
identifiers. The Markdown report is regenerated from the same aggregate object;
the LaTeX table now reads JSON, not rounded Markdown. Best-loss selection uses the
unrounded values, and recovery percentages are displayed to one decimal place.

Final source coverage is 238 unique configuration/checkpoint cells from 280 source
files, including 28 legacy-schema files. Model summaries give each unique
configuration equal weight; each task uses its available configurations. Coverage
varies across tasks and checkpoints, so these are descriptive available-case means,
not a fully paired panel. At the k-mer optima, the yeast seed-1 intermediate result
is absent (seeds 0 and 2 are available); the final means include all three seeds.

| Model | Best-loss round | Recovery there | Final recovery |
|---|---:|---:|---:|
| DNABERT-2 | 3 | 0.0% | 100.0% |
| DNABERT 3-mer | 30 | 6.0% | 36.7% |
| DNABERT 4-mer | 15 | 0.0% | 50.8% |
| DNABERT 5-mer | 15 | 0.0% | 84.2% |
| DNABERT 6-mer | 15 | 0.0% | 95.0% |
| HyenaDNA | 3 | 0.0% | 82.5% |

HyenaDNA's old final 81% represented 113/140 repeated file-level evaluations;
deduplication gives 99/120 = 82.5%. These denominators count evaluations, not
independent records. BPE held-out means change to 2.688 / 1.943 / 2.589 at first,
best and final; HyenaDNA to 1.967 / 1.915 / 2.746. Restored promoter seed-0 scores
also change some k-mer promoter means. Best-loss epochs do not change; the 3-mer
best-downstream selection changes from round 30 to 50 in the report. Maximum
best-to-final frozen-probe changes are 0.0239960602 for the k-mer models and
0.0831212274 for the other two. BPE fine-tuned MCC still rises on four of six tasks.
The corresponding prose now reports available means and 0--6% to 36.7--100%.

All-round BPE endpoint checking crops 309 record evaluations (36 each at rounds
0/1/3/8/15/30 and 93 at final), changing zero exact-recovery outcomes. There are
640 native-48 summary-only evaluations in the whole utility collection. The two
headline paper results and the separate chr22 downstream figure are unaffected.

## Other verified corrections in both manuscripts

- Keep 69 and 73: they belong to different collections. Recounting the source VCF
  at the original NPZ coordinates gives 69 non-biallelic-SNV sites in 62 windows;
  the separately generated phased NPZ gives 73 in 67 windows. Both sets contain
  400 windows but share only six start coordinates. The 37 common alleles written
  by the phased constructor do not explain the difference. The original historical
  seed/scan-limit invocation was not recovered, so its cause is not asserted.
- State haplotype proportions as 145/400 = 36.25% and 124/338 = 36.69%, replacing
  the inaccurate "37% either way" wording.
- Edge-conditioned audit: members have 122937/3520 = 34.9253 prefix errors and
  124040/3520 = 35.2386 infilling errors; controls have 62245/1760 = 35.3665 and
  62767/1760 = 35.6631. Report 34.9/35.2 versus 35.4/35.7, respectively. All
  5,280 record evaluations per protocol still have zero exact recovery.
- Describe the figure label as rank-1 rate; point the short-version BPE boundary
  explanation directly to the measurement appendix.
- NT configuration snapshots are a union, 3/15/30/50. Chr22 250M saves 15/30/50;
  500M saves 3/15/50. E. coli 250M seed0 uses 15/30/50, seeds1/2 use 3/15/50;
  E. coli 500M seed0 uses 3/15/50. These exceptions are now explicit.

The audit report used several old table numbers: the utility fragment's label
tab:a6 currently prints A5, tab:a7 prints A6, and tab:a10 prints A9. Manuscript
cross-references remain label-based. The numerical pool50/pool200 comparison was
verified against all ten raw files and was not changed. Its maximal displacement
remains eight percentage points.

## Validation and release

- Eight focused unit tests pass: duplicate/task merging, configuration separation,
  conflicts, legacy schema, hidden48 and unrounded table selection.
- Reversing and repeating input roots reproduces JSON, Markdown and both table
  fragments byte for byte.
- A separate raw-JSON reconstruction matches all 42 aggregate rows, per-task
  means/coverage, 18 printed table rows and source/count statistics. Eleven further
  invariant/failure probes pass; public JSON contains no record IDs or sequences.
- The complete public appendix-table command regenerates all 11 table fragments
  byte-identically. Both manuscript utility fragments are identical.
- Local final compilation: submission 38 physical pages, main 10, references
  starting physical12, appendix24. Full manuscript50 physical pages, main18,
  references starting physical20, appendix28. No content compression was applied.
- Both builds have zero errors, undefined references or Overfull boxes. Submission
  has no float-size warning; full retains its pre-existing F1 float-size warning
  (134.94266pt). Both retain two existing Underfull boxes. Literal-reference checks
  pass4/4 and5/5. Table and last-main-page renders were visually inspected.
- Submission page10 has content ending near537pt within a text area ending720pt:
  it uses the permitted tenth page but is not physically full. No font or margin
  changes were made. Abstracts, bibliographies, all figure assets and figure_data.csv
  retain baseline bytes. The full manuscript retains its expanded content.

Companion build and remote receipts record PDF hashes, source parity and exact
remote commits. The final receipt commit changes notes only.

中文：本轮修复效用表按文件重复加权，并恢复被漏读的旧格式任务结果；生成器、公开
聚合、两份表格和相关论述一并更新。69/73分别属于不同集合，全部保留并写清；其他
Hamming、比例、标签和快照勘误同步到完整版。没有新训练，没有压缩完整版，没有改图。
