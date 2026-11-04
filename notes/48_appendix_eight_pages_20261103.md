# 48. Eight-page supplement with preserved evidence (3 November 2026)

Authorized scope: refine the submission appendix, leave main text and the full
manuscript untouched, repair the two interpretation issues, and merge migrated
details into both public READMEs. No experiments or measurements were changed.

## Scientific content and migration

- Shortened duplicate settings, control-subset narration and decoder descriptions.
  Main-text evidence, construction counts (including distinct 69/73 collections),
  controls, restart budgets, BPE scorer sensitivity, diagnostic limitations,
  capacity/placement checks and robustness conclusions remain.
- Removed six initial-checkpoint rows from the compact utility display only.
  All twelve best/final rows retain identical numeric cells; model labels were
  moved to the best row. The canonical 18-row source table is unchanged.
- Retained all 33 tokenizer-sweep rows. The 300-nt and 288-nt panels are separate
  fragments of the same continued Table A4, enabling natural page breaks without
  reducing type size. No main figures or supplementary plot were edited.
- Moved reduced-recipe fine-tuned-head comparisons, measurement chronology,
  illustrative LOO aggregation and detailed redraw regressions to both READMEs.
  The frozen-probe utility evidence remains in the appendix.
- Removed the undefined `excess` term from the compact appendix. Both READMEs now
  define it as non-member minus member surprise in bits/nt at the same checkpoint,
  following pilot2/analyze_matched.py; it is not personal identification or a
  causal attribution of the entire score difference to membership.
- Replaced the implication that matched loss controls update count: matching loss
  compares predictive-loss levels, while update count remains confounded with
  corpus size. Participant composition is not manipulated.

## Reproduction and checks

Public documentation/formatter commit: b5ae1a2. Nine bilingual bash blocks match;
45 local README links/anchors resolve. Quick start now generates 22 TeX fragments
(13 canonical and nine display fragments). Ran appendix_tables,
appendix_source_cells and compact_appendix in an isolated server snapshot; the
three changed/new compact table outputs match manuscript SHA-256 values exactly.
The source archive and original measurements are unchanged.

Submission manuscript commit: 35c502f (collaboration glmex).
Submission Overleaf: 80b7b06, freshly cloned with core.autocrlf=false and compiled.
22 physical pages = title 1 + main 10 + references 3 + appendix 8.
References start at physical page 12; appendix at 15. Zero compilation errors,
undefined references or Overfull boxes; one pre-existing bibliography Underfull.
All 28 active reference targets resolve. 53/53 Overleaf/local source files are
byte-identical. Rendered title, main and bibliography page text is identical to
the preceding 23-page build. All 42 tracked paper_full files retain their prior
hashes; the full-version Overleaf was not touched.

Inspected rendered appendix pages, including the Table A4 continuation and final
utility/robustness page: no overlaps, clipped table cells or reduced fonts.
Twelve numbered tables and one supplementary figure remain.

The prior version remains at collaboration commit 1e11d2f and Overleaf 24877bf;
the earlier long supplement remains in docs/appendix_reference_20261103.
Verification receipt: notes/appendix8_20261103_validation.json.
