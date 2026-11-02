# Claim-scope cleanup and Figure A2 correction — 2 November 2026

Authorized scope: implement the agreed local corrections, inspect absolute wording,
update affected figures, mirror factual changes into the uncompressed full manuscript,
compile, log, and synchronize GitHub and both Overleaf projects. Baseline `5fc264c`
is preserved by tag `paper-before-claim-cleanup-20261102`.

## Corrections in both manuscripts

- A16 now separates chr22 single-copy final-checkpoint LOO (93–95%, power 0.21–0.39,
  both tested decoders zero) from E. coli sixteen-copy prefix 30% / re-masking zero.
- A13 no longer says the character model memorizes nothing or the 3-mer is at chance.
  At final own-window evaluation, character rank-1 and recovery are zero for both seeds;
  3-mer sixteen-copy rank-1 is 0% / 20% in seeds 0 / 1, while exact recovery is zero.
  The 100,000-window result points to `results/big20x/gate1_report_final.md` and
  `trajectory.md`; Table A7 is explicitly the separate parameterization experiment.
  Capacity/interference confounding and the extrapolated nature of 3.6 bits/parameter remain.
- Figure A2 prose reports DNABERT-2 single-copy own-window rank-1 4% at round15,
  92–96% at final, with round15 matched controls 2% / 0% / 2%. The final seed0
  control of 4% is not reused as an early baseline. Seeds reuse records, not 150
  independent trials. This supersedes the 22:00 log's contrary control interpretation.
- A2 defines exact-recovery rates rather than all rates; A14 names tiers 0/1/16;
  A17 limits its 2.20-bit statement to the three corpus sizes that reach that loss;
  A19 scopes principal campaign settings and names 20-record/fixed-placement exceptions.

## Newly verified Figure A2 plotting defect

Visual checking exposed an additional source mismatch. The figure generator read
`utility_at_leak.json:r1_recognition`. NT's entries 0.04/0.17/0.35 are historical
mixed-host summaries; BPE's earlier entries also use the old 10-record scoring passes
and falsely kept rounds15–50 at zero. The current table uses 50-record own-window cells.

`figures_privacy.fig_blind` now joins MCC from the unchanged utility files to
`figure_data.csv` by run and epoch, restricted to group bpe_human/nt_ckpt, tier1,
host=train, n_probes=50. Missing or conflicting inputs do not silently fall back.
The NT seed0 curve is **0.08 / 0.30 / 0.64** at rounds15/30/50. Its caption now says
seed0 and 8%; the prose gives the three-seed 4–8% range. BPE begins at 4% in all three
seeds and ends at 94/92/96%. Intermediate points now match Table A2 too.
The axis/legend explicitly say own-window rank-1. Only F7 PDF/PNG is regenerated in
both manuscripts; F1 and the main result figures are unchanged. MCC values are unchanged.

## Directed absolute-wording check

The broader pattern (all/every/none/nothing/only/always/never/superlatives/cannot/proof)
finds 184 non-comment candidate lines in the submission appendix and its two included
sections. This is a keyword inventory, not 184 errors and not directly comparable to
the earlier narrower 76-line scan. The inventory is retained beside this note.

Additional scoped repairs:

| Passage | Decision and source basis |
|---|---|
| A3 “Nothing about the leakage measurement depends...” | State that the record-membership question is well posed; measured rates can differ by biological subset. `human_canary_haplotype_audit.json`, status audit, A3 and main subgroup counts. |
| A4/A21 “no sequence ... merely for being read there” | Low controls argue against a generic host advantage as sole explanation; finite observations do not prove a universal zero. `borrowed_host.json`, Table A2. |
| A5 “members did not separate ... at all” | Retain 34.9/32.1/34.6 Hamming errors without denying their differences; corrected means are 30.1/30.6/35.8. The correction audit remains 60 cells, exact zero, no whole-record certificate. |
| A9 “only exclusion anywhere” | Restrict to the downstream movement statistic, preserving four excluded runs and their values. `downstream` reports and Table A4. |
| A11 “a ranking flips only...” | Say small numerical changes can flip near-tied ranks; do not assert a universal numerical mechanism. |
| A13 “survives every variant” / “inflates everything” | Refer to the measured main-sweep character/3-mer comparison and large fixed-placement effects within the reported controls. Tables A3/A6/A7. |
| A14 “strongest form” / “every released masked checkpoint” | State the second tested decoding protocol and use NT's measured recovery as the counterexample to generalizing from-scratch zeros. Table A8 and human NT table. |
| A19 “every rate ... [listed epochs]” | Describe principal schedules; supplementary configurations remain separately specified. |
| A21 overlapping token update “cannot ... no string at all” | An independent update can violate neighbor consistency; avoid claiming every possible update does. The nucleotide update is unchanged. |
| A17 “leaking at all” and “only quantity” | Restrict to measured exact recovery and the stated loss trajectory. Membership and recovery need not start together. |

Retained keyword hits include algorithmic quantifiers, explicit limitations, complete-state
lemma premises, and empirical all-zero/all-seed statements scoped to named tables and
campaigns. No new statistical significance test or population-wide absence claim is added.
This was a targeted scope/source check, not a fresh audit of every historical measurement.

## Decoder reports and compatibility

Rewrote explanatory docstrings, Markdown prose/table headers, and console labels in
`recon_audit.py`, `recon_bpe.py`, `recon_overlap.py`. Both teacher-forced prefix powers
and LOO powers are diagnostics. `exact_upper_bound`, `bound`, `loo_bound` keep their
JSON names and numeric definitions. An AST comparison, excluding docstrings, the
report-header assignment and changed console labels, confirms identical executable
calculation and JSON structure in all three decoders. No GPU computation ran.

The BPE generated report now states its selected scorer: default fixed common interval
versus historical pernt divisor with letter prior; it no longer describes pernt as a
correct normalization irrespective of the actual option. LOO units are distinguished.
Archived report files are preserved; results/README.md supersedes their old explanation.

## Validation and release

Both local builds preserve page counts: submission36 total / 9 main / 23 appendix;
full44 total / 16 main / 24 appendix. No errors, undefined references or overfull boxes;
two existing underfull warnings in each. Hard-coded references agree (4 short, 5 full).
All existing tables, bibliography, abstract, raw result measurements and F1 are unchanged.
Full manuscript factual scope repairs do not compress its sections or tables.

The final validation receipt records commits, clean remote builds, exact content parity,
protected-file checks and plotted values. main.tex LF normalization is a separate
format-only commit after scientific changes; its non-EOL bytes are asserted identical.


Final release receipt: manuscript `f506930`, decoder report text `e499131`, LF-only
`7ed9a1e`; initial notes `b7cad3d`; public code `ff722d9`. Submission Overleaf
`e803509`, full Overleaf `2bc7c82`. Both actual remotes were freshly cloned and built:
short36/main9/appendix23; full44/main16/appendix24; errors/undefined/overfull all0,
underfull2 each. All41 short and39 full tracked files are now byte-identical to local,
including main.tex; every rendered page matches the local build. Hard-coded references
pass4/4 and5/5. Final PDFs and checks are in work/claim_cleanup_20261102.
