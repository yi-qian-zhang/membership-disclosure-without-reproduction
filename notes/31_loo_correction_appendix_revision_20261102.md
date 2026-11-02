# LOO interpretation repair and moderate appendix reduction — 2 November 2026

The author authorized the factual corrections in both manuscripts, moderate compression
of the submission appendix only, figure checks, compilation, and GitHub/Overleaf sync.
Baseline: GitHub `fb90714`; submission Overleaf `021f9f5`; full Overleaf `71e652a`.
The baseline is preserved by tag `paper-before-loo-appendix-20261102`.

## Scientific correction

- All empirical per-record LOO power summaries are conditional-prediction diagnostics,
  not certified recovery bounds. Numeric values and legacy `loo_bound` JSON keys remain
  unchanged. The restricted complete-state fixed-point implication is retained with
  identical state, constraints, tie-breaking and numerical evaluation as prerequisites;
  it is explicitly not a certificate for the historical experimental outputs.
- `recon_audit.py` checks cropped hidden48 exactness but full covering-token LOO identity.
  Its leading revealed letters are constrained, its trailing boundary fragment is not.
  This affects NT and controlled masked-backbone runs using that routine. Search and
  LOO also differ in batch shape. Aligned discrepancies are reported without claiming
  their numerical cause has been demonstrated. No new decoder replay or training ran.
- Early stopping remains an observed stopping statistic. The manuscript no longer turns
  the 95.8% sub-cap count into validation of the necessary condition. The observed lack
  of aggregate exceedance in six checked human seed-0 NT files is not a proof.
- Table A12 correctly identifies NT as token-level and BPE/overlapping DNABERT as
  nucleotide-level (48 positions). Existing table data are unchanged; `ceiling` headings
  become `power diag.`. Both versions' A6/A10/A16 and the full version's contribution,
  Methods, tokenizer discussion and Discussion are consistent with that interpretation.
- A17 identifies 8/8/14% and 66–76% as 16-copy results. A further source check found that
  the earlier 2.128/2.115 bits/nt values were also 16-copy, despite the single-copy
  paragraph heading. Both manuscripts now distinguish the round-3 seed-1/2 observations:
  single-copy surprise 2.168/2.154, respective controls 2.112/2.110, and 16-copy
  surprise 2.128/2.115. Token-level LOO top-1 is 0.00 for single-copy and 0.01 for
  16-copy/control after rounding; both tested decoders return zero at those checkpoints.
  Sources: `results/nt_seeds/nt250m_mlm_ecoli_s{1,2}/recon_n50_ep3.{json,md}`.
- AC/AN is allele frequency; carrier counts come from genotypes. Rank 1 defines a rule,
  but supplies no transferable low-FPR calibration. RoPE shows the placement effect is
  not specific to learned absolute embeddings. Downloadability is attributed to the
  public starting weights, not the withheld fine-tuned checkpoints. Universal claims
  about checkpoint selection and early stopping were scoped to measured comparisons.

## Submission appendix only

- Appendix: **27 → 23 physical pages**. Main body stays **9 pages**, physical 2–10;
  references start at 11, appendix at 14. Total PDF: **40 → 36 pages**.
- Table A8 now groups all 264 reported tier rows into 40 dataset/tokenizer/mask-rate
  groups (88 model configurations). Every row still evaluates 20 records; seed counts,
  tiers 0/1/16, all-zero exact recovery and separate prefix/infill Hamming means remain.
  Means are computed from the published report's per-seed Hamming values. The full
  rows are preserved verbatim as `paper/tables/t_infill_cells.csv`, in the original
  `t_infill.tex`, and in `results/human_mlm/infill_audit.md`. No independent-trial
  interpretation or pooled confidence interval is introduced.
- `pilot2/appendix_tables.py` generates the full table, compact summary, and CSV;
  regeneration reproduces all 11 committed table/CSV artifacts exactly modulo EOL.
- A6 centralizes decoder access/budgets; A19 refers to it. A21 retains the mathematical
  definitions and the new diagnostic qualification. A1/A18 summarize provenance,
  and redundant development-history prose/caption text is removed. All section/table
  labels remain available; the four hard-coded submission references still agree.
- Appendix floats permit nearby float pages, preventing the large tokenizer table
  from blocking the later tables until the end. Font sizes and page geometry are unchanged.
- Preserved: biological construction/subset audits, donor-tier controls, A2/A3 per-seed
  evidence, corrected-BPE coverage, placement/parameter controls, split sensitivity,
  failed overlap prediction, campaign distinctions, exact commands and data release IDs.

## Full manuscript and figures

- `paper_full/` receives factual repairs only, no appendix compression or float changes.
  It retains the 264-row table and detailed narrative. PDF remains **44 pages**:
  title 1, body 16, references 3, appendix 24. All five hard-coded references agree.
- Inspected the actual F1/F3-variance/F5/F6/F7 PDFs in both versions and the native
  F1 slide text. No affected upper-bound labels occur in those active figures. Their
  source/PDF/PNG bytes remain unchanged. Rejected/archived figures were not regenerated.
- Table A3 contains measured prefix recovery, not the erroneous LOO certificate;
  it remains byte-identical. Scope is determined by metric provenance, not family name.

## Validation and release

Both local builds: zero errors, undefined references and overfull boxes, with two
underfull notices each. Visual checks cover the new summary table, diagnostic equations,
changed result paragraphs and final appendix layout. Abstract body text, bibliography,
active figures, raw result data, and all existing table data rows are unchanged.
1,835 pre-existing tracked files in the protected snapshot are byte-identical; the
20 changed files at the initial factual-check stage are manuscript files, two generated
table labels/captions per version, the table generator and results documentation.

The historical reports retain old headings. `results/README.md` explicitly supersedes
their bound interpretation rather than rewriting experimental records. The same notice
and compact-table generation are synchronized to the public code repository without
copying unrelated staged work from the older public checkout.

Final commit IDs, clean remote build counts and exact file comparisons are recorded in
`31_loo_appendix_validation_20261102.json` after synchronization.

Final release receipt: GitHub manuscript `a5de548` (factual repair `c914ab9`), public
code/data `b0af7a4`, submission Overleaf `cf54fae`, full Overleaf `13ce514`.
Actual remotes were freshly cloned and compiled: short 36 total / 9 main / 23 appendix;
full 44 total / 16 main / 24 appendix. Both have 0 errors, undefined and overfull,
and 2 underfull notices. All 41 short / 39 full tracked files match local content;
only short `main.tex` differs in line endings. Every rendered remote page matches
the corresponding local build. Final validation JSON accompanies this note.
