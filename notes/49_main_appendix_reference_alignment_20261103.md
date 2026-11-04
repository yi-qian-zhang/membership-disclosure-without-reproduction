# 49. Main-to-appendix semantic reference audit (3 November 2026)

The user correctly required checking reference meaning after appendix migration,
not just resolving LaTeX labels. Audited all 28 main-to-appendix occurrences across
17 targets against the active compact supplement, generated tables and PDF links.
Two independent read-only checks complemented the root source/PDF inspection.

## Three destination descriptions corrected

- Methods: A1 summarizes measurement provenance; the detailed chronology/source
  documentation is in the repository README. Added a direct pinned hyperlink to
  its Measurement campaigns and conditional diagnostics subsection.
- Methods: A3.1 now specifies decoder budgets and conditioning, replacing the
  broader description implementation details. Code documentation remains in README.
- Discussion: reproduction instructions are in the repository README, replacing
  the outdated attribution to the configuration appendix. Added a direct pinned
  Quick start hyperlink.

Only these three textual pointers in p03_setup and p08_discussion changed. No
scientific numbers, formulas, claims, table/figure files, bibliography or full
manuscript files changed. The README links pin b5ae1a2, which contains the migrated
material. This is a reference-alignment exception to the previous body freeze.

## Semantic support map

| Target(s) | Current location | Retained support |
| --- | --- | --- |
| app:config, sec:basis | A1 | Campaign configurations, interpolation policy, measurement scope/replay summary; full chronology now explicitly README |
| app:haplo | A2 | Record construction, 145/20/235 and 124/20/194 counts, distinct 69/73 site collections |
| app:bh | A2 | Context-matched controls, tier matching, rates and retrained-control qualifications |
| app:resources | A2 | Release dates and reference filename |
| app:measurement | A3 | Held-out score definition, decoder coverage, BPE scorer audit and LOO limitations |
| sec:decoders | A3.1 | Budgets, conditioning, crop, admissibility normalization and restart selection |
| app:bpenorm | A3.2 | Search and membership scorer sensitivity, distinct audit scopes and pooled controls |
| tab:ident | Table A2 | All six checkpoints, three seeds, own/fresh membership, controls and plotted prefix recovery |
| tab:target48 | Table A3 | Hidden-48 Hamming and SEs in all 18 seed/checkpoint cells |
| tab:slots | Table A4, continued | All 33 tokenizer rows; 300-nt and 288-nt panels share the table number |
| app:capacity | A5 | Parameter counts, capacity/placement qualifications |
| tab:capacity | Table A5 | Ordinary/spaced controls and all referenced matched-loss columns |
| tab:cost | Table A7 | E. coli recovery costs and unequal 10/20 versus 50-record coverage |
| tab:hyena30 | Table A9 | Four background rows and seed-specific epoch-30 measurements |
| tab:overlap50 | Table A10 | Own 0/2/6/50 and fresh 0/2/2/36 percent with counts |
| sec:blind | A7 | Frozen-probe trajectory, best/final utility table and corpus-size evidence |

The removed six initial utility rows and the relocated fine-tuned-head benchmark
comparison are not required by any main-text reference. Main-text downstream
claims concern frozen probes and retained best/final cells. No quantitative
reference was redirected to a table missing its supporting values.

## Validation and synchronization

Manuscript commit 62f34df; submission Overleaf ab92453. Compiled the committed
Overleaf checkout: 22 total pages, main 10, appendix 8; 0 errors, undefined or
Overfull boxes and one pre-existing bibliography Underfull. All 46 compiled label
numbers/pages are unchanged. All 28 main-to-appendix PDF links land correctly;
the continued Table A4 link lands on its first panel. The two new README anchors
match headings in the pinned file. All 28 active unique LaTeX targets resolve.
53/53 Overleaf/local files are byte-identical. Bibliography and appendix PDF page
text is unchanged; all 42 tracked paper_full files retain their earlier hashes.

The prior 28/28 checker result meant label existence, not semantic correspondence;
this distinction is why the present audit was necessary. Stale non-rendering
main.tex comments about old p04/p07 inputs were noted but left outside this narrow
textual-reference repair. The full-version Overleaf was not changed.
