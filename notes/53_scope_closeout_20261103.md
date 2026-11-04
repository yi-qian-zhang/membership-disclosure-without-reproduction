# 53. Scientific scope and reproduction closeout (3 November 2026)

Author-authorized local corrections following the final read-only scope review.
No new training, no changes to measured data, table cells, abstracts or references.

- The endpoint surprise comparison is explicitly planted records in own training
  windows versus never-trained controls in fresh windows. Its difference is a
  descriptive control-relative predictive advantage under those access conditions,
  not an isolated target-specific learning effect. The 0.824/0.0052 absolute values,
  2.44/2.79 differences, own 0%/92%, and fresh 0%/0.33% are unchanged.
- Methods limits borrowed-host matching to the human membership audit. F1's native
  endpoint heading and both manuscript captions state the mixed-context comparison.
  Only two native F1 text strings changed; numbers, shape geometry, fonts and sizes
  are unchanged. The minimum effective paper-size label remains 10.53 pt.
- The utility table identifies its separate causal, uniform-canary, GUE-promoter/
  yeast campaign: sixteen copies, own-window greedy prefix, hidden 48 nt, 20 records
  per tier. The scale table adds own-window and fixed offset 96 nt while retaining
  the per-run best-loss-and-subsequent interpolation branch. Existing cells stay fixed.
- The 145 records and their reported subsets are called chromosome-compatible at
  audited sites. This does not establish complete haplotype authenticity at unresolved
  indel/multiallelic sites. All original subgroup counts remain unchanged.
- English/Chinese public README commands now generate the utility appendix plot
  separately. figures_privacy defaults to this plot; historical main layouts require
  explicit selection. The explicit record schematic now describes variant-derived
  records, nominal prefix input, candidate-record ranking and LOO as a diagnostic,
  not a recovery bound. The existing inactive private schematic export was refreshed.
- Public implementation is f1f63aa; the submission's three README links pin it.
  Only README/code files were included in that public implementation commit. Public
  paper and old appendix sources remain absent from the latest tree; history was not
  rewritten. Manuscript/PPTX files are confined to the collaboration and Overleaf copies.
- Facts are mirrored to the full manuscript without compression. Its existing long
  F1 caption was visibly cropped; splitting it into a continued caption preserves
  every sentence and removes the oversized-float warning. The full version is now
  51 pages; no content was removed to fit a submission budget.

## Validation before synchronization

The isolated public snapshot uses the prior fresh Python 3.10 analysis-only venv,
with declared matplotlib dependencies and externally supplied Arial. All documented
main/appendix generation commands pass; default and probe invocations no longer
overwrite main outputs. Main/utility PNGs and all 22 table fragments plus the CSV
are unchanged from baseline. Eight existing regression tests pass. Explicit schematic
rendering has no intersecting text boxes. No GPU training or upstream-weight
download was performed.

Windows latexmk could not find Perl, so builds used pdflatex, BibTeX and repeated
pdflatex passes directly. Clean local-source builds:

- Submission: title 1 + main 10 + references 3 + appendix 8 = 22 pages;
  zero errors, undefined references, Overfull or float-size warnings; one existing
  bibliography Underfull; 28/28 active reference targets resolve.
- Full: title 1 + main 19 + references 3 + appendix 28 = 51 pages;
  zero errors, undefined references, Overfull or float-size warnings; two Underfull.
  The full version's separate spelled-out-reference checker passes.

The submission fit is maintained by removing repeated caption wording, with all
new conditions and scientific quantities retained. Typeface, font sizes, margins
and all measured values are unchanged. Final remote verification is appended below.

## Verified remote synchronization

- Collaboration implementation: `ee1e8f3` on `glmex`; public README/code implementation:
  `f1f63aa` on `main`. The paper README pins remain at that implementation snapshot.
- Submission Overleaf: `64d1811`; fresh clone matches the collaboration manuscript
  byte-for-byte for all 53 tracked files. Recompiled to 22 pages: title 1, main 10,
  references 3, appendix 8. Zero errors, undefined references, Overfull or oversized
  floats; one existing bibliography Underfull. All 28 active references resolve.
- Full Overleaf: `3a7a8b0`; fresh clone matches all 42 tracked files byte-for-byte.
  Recompiled to 51 pages: title 1, main 19, references 3, appendix 28. Zero errors,
  undefined references, Overfull or oversized floats; two Underfull. All five
  spelled-out-reference checks pass. The continued F1 caption is visually complete
  and shares its continuation page with Methods; no full-manuscript compression.
- Both remote-build PDFs have the same per-page extracted text as the local builds,
  all fonts embedded, and no CR line endings in tracked text sources. User-facing
  local PDFs were refreshed from these verified remote builds.
- Independent final diff review found no changed measurement/table cells, abstracts,
  bibliography, or missing scientific conditions. Final public-tree audit found no
  paper directory, full-manuscript directory, old appendix sources, TeX or PPTX files.
  Both rendered README anchors are present, all ten bilingual command blocks agree,
  and fenced blocks close correctly.

Machine-readable counts and hashes: `53_remote_validation_20261103.json`.
