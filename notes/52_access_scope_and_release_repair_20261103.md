# 52. Access-condition and public release repair (3 November 2026)

Author-approved factual corrections, with no new training and no changed historical measurements.

- The controlled synthetic 16-copy, 300-nt, matched-loss 2.40 result is own-window
  prefix recovery: 2-mer 0%; 6-mer mean 0.9192013445 (rounded 92%). Qualifiers now
  accompany the abstract, introduction, results, figures and table descriptions.
  The same fresh-window comparison is 0% versus 0.3333333333%, with 6-mer seeds
  1%, 0%, 0%. This supports contextual dependence in this experiment, not a
  universal claim that tokenization effects require access to the training window.
- Corpus-size Table A12 uses each run's best held-out-loss checkpoint and subsequent
  checkpoints. This is a table-specific branch restriction, not a change to the
  global controlled-sweep interpolation rule. Existing values remain unchanged.
- Fixed English/Chinese README fences and the haplotype-audit filename. The Methods
  measurement-campaigns link now points to a rendered heading. Both guides have
  17 headings and 10 matching executable code blocks; shell syntax checks pass.
- Census defaults now follow GLMEXT_DATA (data fallback); examples use explicit input
  and reproduced output paths. NT instructions specify its separate recorded library
  environment, upstream model IDs, local layout and NT_ROOT. No weights downloaded
  and no new environment installation or GPU training was claimed by this check.
- At the author's explicit request, removed paper/ and the old appendix source archive
  from the latest public repository. The author explicitly chose to retain Git history;
  previous commits may still expose those removed files. Private manuscripts and their
  editable illustrations remain maintained separately. A local Git bundle preserves
  the public pre-removal state.
- The compact table formatter no longer reads manuscript/archive TeX. A new public
  compact_table_cells.json preserves the existing rounded aggregate cells, units,
  conditions and emphasis metadata without manuscript text. No source experiment
  measurements were removed. All 22 generated TeX fragments plus the 264-row CSV
  match the retained manuscript data (three tables differ only in alignment spaces).
- F1 modifies only its native panel-c heading; F3 labels explicitly state own-window.
  Fonts, scientific drawings and plotted values are retained. The unexpected two-slide
  F1 was backed up outside the repositories; its second slide was the old version.
  Export now operates on an isolated copy and selects the verified revised first slide.

Validation so far: a standalone public snapshot with neither paper/ nor the appendix
source archive regenerates Figures 2-3, 22 TeX fragments and one CSV; eight regression
checks pass. Rendered F1 minimum font is 10.53pt and F3 10.2pt, unchanged. Submission
build remains title1 + main10 + references3 + appendix8 = 22 pages, with zero errors,
undefined references or Overfull warnings and one existing bibliography Underfull.
Full version remains 50 pages and is not compressed; the pre-existing oversized-F1
float warning is retained. Final remote receipt will be appended after synchronization.

## Final remote verification

Implementation: collaboration glmex8374552; public releasea11c0d3. Submission Overleaf
32a1ebd; full Overleaf7fdf390. Both were freshly cloned from the actual Overleaf remotes
with checkout line-ending conversion disabled, then recompiled from clean sources.

- Submission:22 pages = title1 + main10 + references3 + appendix8;0 errors,
  0 undefined,0 Overfull,1 existing bibliography Underfull.28/28 active reference
  targets resolve.53/53 tracked source files match local bytes; all page text matches
  the local build. All3 rendered README links pin the repaired publica11c0d3 snapshot.
- Full:50 pages = title1 + main18 + references3 + appendix28;0 errors,
  0 undefined,0 Overfull,2 Underfull.44/44 active reference targets resolve;
  42/42 source files and all page text match local. The existing oversized-F1 float
  warning remains (146.94266pt); the full manuscript was not compressed.
- Live GitHub rendering of the pinned README confirms normal headings/tables after
  the repaired fence. A regenerated public Figure3 has identical text and dimensions
  to the manuscript figure; PDF byte differences reflect export metadata.
- Only the new aggregate display manifest was added under results/; all existing
  result files remain unchanged. No training run or fresh dependency installation
  was performed. The published aggregate-only reproduction path and8 existing
  regression checks passed in a separate server snapshot without manuscript sources.

Machine-readable receipt:52_access_scope_remote_validation_20261103.json.
