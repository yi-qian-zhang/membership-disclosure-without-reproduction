# Public repository cleanup — 3 November 2026

The author requested a clearer public release and an optional Simplified Chinese
README. Work starts from public main b4de086. A fresh clone was used because the
older local release checkout contains uncommitted work; that work was preserved.

## Changes

- Reduce the English landing page to 489 whitespace-delimited words, retaining
  the main measured findings and their experimental boundaries.
- Add README.zh-CN.md with reciprocal language links and identical quick-start
  commands. Detailed technical documentation remains in English.
- Move detailed reproduction instructions and interpretation into docs/REPRODUCING.md.
- Add docs/REPOSITORY.md and pilot2/README.md for current entry points and retention decisions.
- Replace notebook-index entries for absent files with links to shipped Markdown notes.
- Clarify that paper/ distributes Figure 1 assets, not the complete TeX manuscript;
  remove references to unpublished local figure tooling from the export guide.
- Add requirements-analysis.txt for plotting; retain requirements.txt as a
  compatibility include of the unchanged requirements-paper.txt.
- Ignore reproduced/ outputs and remove the duplicate .DS_Store ignore entry.
- Align results/README.md with the manuscript's corrected inclusion rule:
  252 aggregate cells / 476 fine-tuning evaluations; zeros remain included.
  Clarify that conditional-prediction powers are diagnostics for all model families.

All measured results, code implementations, tests, source figures, old experiments
and dated logs retain their paths and contents. No Git history was rewritten.
Historical queues and plots are indexed as historical rather than deleted; they
remain evidence for the notebook and may still be imported by current modules.

## Validation

- All relative links in added/modified Markdown resolve in the public checkout.
- English/Chinese quick-start code blocks are identical.
- Reproduction used an isolated copy of the public checkout in the recorded
  Python environment with Matplotlib3.9.2, no GPU training or model download.
- The figure command produces F6_ident.pdf/png and F5_slots.pdf/png (Figures2/3).
  Arial was supplied privately for validation, not committed or distributed.
- Both table commands produce13 fragments; every fragment is byte-identical to
  the current manuscript table.
- All8 existing downstream-summary regression tests pass.
- git diff --check passes.
