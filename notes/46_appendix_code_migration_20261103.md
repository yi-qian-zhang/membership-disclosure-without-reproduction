# 46. Appendix-only compression and repository migration (3 November 2026)

## Authorized scope and baseline

The author requested no main-text edits, an appendix at most ten pages if feasible,
and migration of commands and code-oriented descriptions into the public codebase.
Baseline collaboration branch: `2f46ddf`; submission Overleaf: `2fdd9af`.
The freshly compiled baseline has 39 physical pages, main text 10, references starting
at physical page 12, appendix starting at 15 (25 appendix pages).

Backup tag: `appendix-before-code-migration-20261103`. A local ZIP and all tracked
manuscript hashes are under `work/appendix10_20261103`. The exact long-appendix
source and all its table fragments are archived in `docs/appendix_reference_20261103`
with SHA-256 manifest. `paper_full/` is unchanged and uncompressed.

## Presentation changes

Only `paper/sections/p11_appendix.tex` changes among existing manuscript sources.
The main input tree, abstract, bibliography, main figures, original generated table
fragments and every measured result remain unchanged. Appendix reference numbers
are automatically updated. The compact supplement has seven scientific sections,
twelve tables and one utility visualization. All main-text appendix targets remain.

Retained: full six-checkpoint/three-seed DNABERT-2 trajectories and Hamming SEs;
both-window tokenizer sweeps; capacity/placement controls; released-model decoder
comparisons and explicit source cells; utility evidence; genotype construction,
matched controls, scorer audit, budgets and non-bound diagnostic interpretation.
Other robustness experiments retain conditions and findings; their full rows and
long explanations remain in the public reference snapshot. Commands, filenames,
implementation/provenance narratives and development history moved to the codebase.
Data-release identifiers remain scientific metadata in the supplement, because the
frozen body explicitly points there for the reference filename and release dates.

`docs/PAPER_PROTOCOLS.md` supplies a reader-facing evidence map, operational commands,
compatibility notes and links to the preserved long source. English and simplified-
Chinese public READMEs link to it. `pilot2.compact_appendix` formats numeric cells
from existing tables without reweighting or recomputation. `paper/check_xrefs.py`
now follows the active TeX input tree; obsolete command-list literal-number checks
were replaced by checking every active reference against compiled labels.

## Verification

Local compile: 23 physical pages = title 1 + main 10 + bibliography 3 + appendix 9.
References begin at physical 12; appendix at 15. No errors, undefined references or
Overfull boxes; known bibliography Underfull warnings remain. All 28 active reference
targets resolve. Main-source and full-version SHA-256 hashes are unchanged.
The two large seed tables fit together by changing row spacing only; font sizes
were not reduced. Tables stay next to their scientific sections rather than drifting
to detached float pages. Appendix PDF has no .py/.sh/.json/.csv identifiers or command
blocks; the source-data release filenames are intentional.

In isolated server checkout `/tmp/glm-appendix-compact-o74rdi3g/repo`, ran the published
aggregate table generator, verified-source-cell generator and new compact formatter.
All three exit 0; all seven generated compact tables equal the manuscript fragments
byte for byte. No training, inference, experimental results or statistical estimates
were changed. No data or full-manuscript files were pushed to the public repository.

Remote receipts are appended after synchronization.

## Final remote verification

- Collaboration manuscript commit: `3279f45` on `glmex`; backup tag pushed.
- Public codebase: `08b4614` on `main`; the PDF links to this exact guide revision.
- Submission Overleaf: `16f269d`. A new clone of the actual remote was compiled.
- Remote result: 23 pages, main 10, bibliography 3, appendix 9; references begin
  at physical page 12 and appendix at 15. Errors/undefined/Overfull: 0/0/0; one
  existing bibliography Underfull warning. All 28 active reference targets resolve.
- Remote/local source parity: 51/51 files, byte-identical. Main-source hashes and
  every full-version hash unchanged. PDF main text matches after normalizing appendix
  numbers and page breaks; shorter reference numbers move one line from physical
  page 6 to 5, without changing content or the ten-page main-body count.
- Full-length Overleaf was intentionally not modified: this is an appendix-only
  presentation change, not a scientific correction.

Machine-readable checks: `notes/46_appendix_remote_validation_20261103.json`.
