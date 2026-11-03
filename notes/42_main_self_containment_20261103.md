# Main-paper self-containment and source-cell repair — 2026-11-03

User authorized the verified small-revision plan: promote the essential evidence
and method definitions to the submission body, repair appendix pointers and code
comments, retain HyenaDNA's four-background epoch-30 65–100% result, carry factual
changes into the full version without compressing it, compile, and synchronize.
Baseline: project 85a8c7d; submission Overleaf 4a8579f; full Overleaf 9048ce4.

## Changes and evidence boundaries

- The final chr22 fresh-window scorer comparison now reports seeds 0/1/2 explicitly:
  members 18/22/26% reported versus 22/22/28% span-matched; controls 0/0/0% versus 2/0/0%.
  Each cell has 50 records. The separate 500-evaluation pooled control rates are
  explicitly mapped to reported=.014, span-matched=.014, undivided=.016.
  All five ablation files include tier 0; the 2000 evaluations comprise five
  run/checkpoint pairs, controls plus 1/4/16-copy members, two host conditions,
  and 50 records per group. Span-matched/no-divisor rank-1 changes remain 33/20.
- Prefix decoding is one greedy continuation per record/context with predicted
  feedback, admissible outputs, no beam/sampling/restarts. It is not one model
  forward pass. The re-masking formula is explicitly restricted to masked
  non-overlapping backbones; HyenaDNA's reported recovery uses causal prefix decoding.
- The Methods state round=epoch, the first indexed repeated-record host after
  training-row shuffling, uniform controlled background windows, and unplanted
  held-out test windows (DNABERT-2 chr22: 200; controlled sweeps: 500).
- Controlled interpolation sorts saved points by loss, interpolates per seed,
  averages available seed results, and does not extrapolate. Numbered epochs
  1/2/3/5/8/12/20/30 include the endpoint. The separately labeled final evaluation
  duplicates epoch 30. All 33 controlled runs have matching ep30/final floors,
  full probe lists and training summaries; adding the duplicate changes every
  current 2.40-bit/nt mean by 0. A previous figures_privacy.py comment asserting a
  1–2-point change is corrected; interpolation code and plot data are unchanged.
- Main prose gives the tokenizer seed ranges and spaced-control sample sizes
  (20 member records/tier; one or two training seeds), without claiming equal
  capacity or slot count as the unique mechanism.
- Overlapping DNABERT's seed 0/epoch 120/n50 sixteen-copy prefix own counts
  0/1/3/25 and fresh counts 0/1/1/18 now point to a dedicated source table.
  The raw sources are scores_ep120_n50.json, not the older n10 CSV cells.
- HyenaDNA's 65–100% uses only medium-160k at lr 2e-5, actual epoch 30,
  synthetic 96nt canaries, sixteen copies, own-window hidden 48nt recovery,
  and 20 records per seed. Uniform-background final files explicitly record
  epoch 30; other backgrounds use scores_ep30. No small-model or alternate-lr
  variant enters the range. The independent chr22 single-copy 0–8% campaign
  remains distinguished. Its comparison does not isolate architecture effects.
- The allele-count contrast retains 27/78 and 6/72 descriptive scorings:
  26 and 24 distinct records evaluated by three training seeds, not 78/72
  independent records or pooled binomial confidence intervals.
- Frozen linear-probe MCC=.798–.801 at round 15 versus .782–.787 at final is
  reported beside own-window membership 4% versus 92–96%. This is a within-probe
  comparison, not benchmark equivalence or proof that a lab would deploy final.

## Reproducibility and preservation

New Tables A17/A18 are generated from results/appendix_source_cells.json by
pilot2/appendix_source_cells.py. The same reader can recount original server
outputs and records source hashes. The published manifest contains aggregate
counts/configuration only, without sequences or per-record identifiers.
Tables are appended after existing tables; earlier table numbers and literal
cross-references are preserved.

Both manuscript versions receive factual corrections. The full manuscript retains
its expanded narrative and equations; it is not compressed. Abstracts, both
bibliography sources, all figure assets and results/figure_data.csv are unchanged.
Figure font sizes, family, geometry, data and captions are not altered in this round.

## Compilation and visual checks

First clean builds: submission 38 pages = title 1 + body 10 + references 3 + appendix 24.
References start on physical page 12. Main Figures 1/2/3 remain on physical pages 3/7/9.
Full version 49 pages, body 18, references start on physical page 20, appendix 27.
Both: 0 errors, 0 undefined references/citations, 0 Overfull, 2 existing Underfull.
Submission has 0 oversized floats. Full version retains the previously documented
F1 long-caption oversized-float warning 134.94266pt; this predates this patch.
Literal cross-reference checks pass 4/4 and 5/5. Final source verification and
remote synchronization receipts will be appended after publication.

中文：本轮补的是不读附录也应能判断的关键条件和证据，不改两条主结果。
HyenaDNA 的四类背景第30轮65–100%有原始元数据支持；final是标签，不是另一轮。
投稿版正文保持10页，新增两张可追溯表使附录增加到24页；完整版只同步事实，
保留完整叙述。没有新增训练实验，没有改图、字号、注册摘要、参考文献或主CSV。
