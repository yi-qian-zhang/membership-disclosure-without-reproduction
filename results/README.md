# Published aggregate measurements

`figure_data.csv` supplies the main quantitative figure trajectories. Rows identify
the campaign (`group`), run, checkpoint, repetition tier and host condition. Other
JSON/Markdown summaries supply additional appendix tables and diagnostics, including
`kcurve_per_nt.json` for teacher-forced target surprise. Figure 1 is an editable
illustration; it is not generated from this CSV alone.

Use `python -m pilot2.figures_main10 --out reproduced/figures` and
`python -m pilot2.appendix_tables --results results --out reproduced/tables` from the
repository root. These read the committed measurements without retraining models.
Regenerating `figure_data.csv` itself requires the original run outputs and is a
different operation; do not overwrite the published CSV while checking the paper.

`rank1_rate` measures candidate ranking and `exact_rate` prefix exact recovery.
Never-trained controls have tier 0. Their ranking rates are not universally zero;
the paper distinguishes host conditions, checkpoints and repetition-matched donors.
Synthetic runs may contain metadata for randomly generated strings. The release
does not include the consolidated human canary NPZ, human sample-linking metadata,
or fine-tuned model weights. These are not promised as public downloads.

The historical positional human records are a mixture of haplotypes and composites,
not uniformly individual haplotypes. See `human_canary_haplotype_audit.json` and the
current paper for the distinction. The BPE historical scorer, its common-interval
audit and the numerical-basis campaigns have different coverage; preserve their
provenance when quoting values. Decoder budgets also differ by family/campaign.

Three training seeds re-use the same record set. Repeated checkpoint rows do not
create additional independent records. A six-percentage-point extraction change in
one arithmetic replay is a reproducibility qualification, not a general uncertainty
interval. The paper's measurement appendix and dated notes describe these boundaries.

## Interpretation of historical conditional-prediction fields (2 November 2026)

Fields named `loo_bound` and historical report columns named `LOO bound` or `ceiling`
retain their original measured values. In the manuscript these per-record power
summaries are now **conditional-prediction diagnostics**, not certified bounds on
48-nucleotide recovery. `recon_audit.py` scores exact recovery on the hidden crop
but probes complete covering tokens, and search/probe batch shapes can differ.
Early stopping alone does not validate the old bound interpretation. The correction
also applies to masked controlled-backbone outputs from that routine. BPE and
overlapping probes are nucleotide-level diagnostics. See manuscript Methods and
`notes/31_loo_correction_appendix_revision_20261102.md`; raw data are unchanged.


The decoder report generators now use diagnostic labels in prose, tables and console
output. The historical JSON keys `exact_upper_bound`, `bound` and `loo_bound` remain
unchanged. Teacher-forced prefix powers likewise do not bound arbitrary decoders.
Archived reports preserve their original text; the interpretation above supersedes
those explanations. See `notes/32_claim_scope_cleanup_20261102.md` for the final
corpus/tier and reporting corrections. No raw measurement has been rewritten.
