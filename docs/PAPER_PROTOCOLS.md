# Paper protocols, commands, and evidence map

This guide accompanies the compact scientific supplement introduced on 3 November
2026. It moves operational documentation out of the paper; it does not change the
experiments. Start with [REPRODUCING.md](REPRODUCING.md) for installation and public
input preparation. The [long-appendix snapshot](appendix_reference_20261103/README.md)
preserves the complete pre-compression text and all original tables. Its old table
numbers are historical; use the scientific names and labels below.

## Where each result comes from

| Paper topic / persistent label | Measured artifacts and generators | Scope |
| --- | --- | --- |
| Principal configurations (`app:config`, `sec:basis`) | `outputs/*/args.json`, `train_summary.json`; archived configuration section | Do not merge the 50-epoch causal and 150-epoch masked overlapping-DNABERT campaigns. |
| Variant-derived construction (`app:haplo`, `app:resources`) | `pilot2/human_canary.py`, `canary_census.py`, `carrier_audit.py`; `results/human_canary_haplotype_audit.json` | The original 400 windows are not the later phased reconstruction; 69 and 73 non-SNV sites refer to different collections. |
| Matched hosts (`app:bh`) | original borrowed-host runs and their exported control rows in `results/figure_data.csv`; archived matched-control section | Own controls borrow tier-matched training hosts; fresh controls have independently drawn hosts and offsets. |
| DNABERT-2 trajectories (`tab:ident`) | `results/figure_data.csv`; `pilot2/appendix_tables.py`, `figures_main10.py` | Six checkpoints, three seeds, 50 records per tier; include sixteen-copy fresh-window ranks. |
| Hidden-48 errors (`tab:target48`) | `results/target48_audit.json`; `pilot2/target48.py`, `export_figure_data.py` | Crop saved predictions by nucleotide coordinates. `legacy_variable` rows without predictions cannot be recropped. |
| Tokenizer sweep (`tab:slots`) | `results/kcurve300/`, `results/kcurve/`; `pilot2/kcurve_report.py`, `figures_privacy.py` | Main 300-nt and replication 288-nt windows are separate. Matched loss is interpolated in loss order per run. |
| Parameter and placement controls (`tab:capacity`, `tab:placement`) | `results/figure_data.csv`; archived `t_capacity.tex`, `t_placement.tex`; `pilot2/appendix_tables.py` | Fixed placement, 20 records per tier and one or two seeds; not an equal-capacity drawn-offset experiment. |
| Decoder cost and diagnostics (`tab:cost`, `tab:loo`) | Archived released-model tables; original `outputs/chr22_rerun/` campaign, `results/nt_ckpt/`, `results/nt_seeds/` | Report decoder, target, copy tier, record count and access condition together. |
| HyenaDNA and overlap source cells (`tab:hyena30`, `tab:overlap50`) | `results/appendix_source_cells.json`; `pilot2/appendix_source_cells.py` | Hashes and source paths are in the JSON. Uniform-background HyenaDNA `scores_final.json` records actual epoch 30. |
| Scorer audit (`app:measurement`, `app:bpenorm`) | `bpe_divisor_final.json`, corresponding E. coli reports; archived measurement definitions | 2,000 evaluations include tier 0. Pooled 500-control rates are not the three headline 50-record controls. |
| Utility (`tab:a6`, `sec:blind`) | `results/dnabert_gue_ds/utility_downstream.json`, `utility_at_leak.json`; `pilot2/appendix_tables.py`, `figures_privacy.py` | Deduplicate configuration/checkpoint rows before combining task panels; retain zero MCC. Frozen and fine-tuned heads are different probes. |
| Edge-conditioned decoding | `results/human_mlm/infill_audit.md`; archived `t_infill_summary.tex`, `t_infill_cells.csv` | 88 configurations, 264 tier rows, 20 records each. Full grouped rows moved to this repository. |
| Split redraw / corpus size | Archived `t_draws.tex`, practitioner section; `results/scale22/`, `results/big20x/` | More windows are not more independently sampled participants. The 20-fold dataset also changes update count. |

`outputs/` denotes original run directories and checkpoints, not files promised in
this public checkout. The consolidated rare-record collection and fine-tuned weights
are withheld as described in REPRODUCING.md. Published aggregate reports remain in
`results/`; source-path manifests identify the original run artifacts without claiming
they are distributed. See the long snapshot for exact original paths and campaign
exceptions rather than inferring a command from a paper table number.

## Decoder commands and historical protocol selection

Run from the repository root after setting `GLMEXT_DATA` to your public-data root.
Noninteractive shells do not necessarily source `.bashrc`; export the variable in
the shell that launches the job. Paths below require reconstructed local runs.
Use new output names or an isolated copy to avoid overwriting historical artifacts.

```bash
export GLMEXT_DATA=/path/to/glm_data
NT=outputs/nt_ckpt/nt250m_mlm_human_s0
DB5=outputs/dnabert_long/dnabert5_nt0.05_lr0.0001_human_s0
BPE=outputs/bpe_human/dnabert2bpe_human_s0

python -m pilot2.recon_audit --root "$NT" --ckpt ckpt_ep50.pt \
    --restarts 128 --max_probes 50 --name reproduction_rb_ep50
python -m pilot2.recon_overlap --root "$DB5" --ckpt ep120.pt \
    --restarts 16 --max_probes 50 --name reproduction_rb_ep120
python -m pilot2.recon_bpe --root "$BPE" --ckpt ep120.pt \
    --restarts 16 --max_probes 50 --score pernt --name reproduction_rb_ep120
```

The last command reproduces the **historical divided BPE scorer**, not the
common-interval correction. Use `--score fixed` for that separate audit and a
different output name. Its paper coverage is only 60 seed-0 final cells, not the
whole three-seed trajectory. Earlier reconstruction runs used 32 restarts; the
reported chromosome-22 nucleotide searches use 16, while token re-masking uses 128.
`--chunk 1` on the token re-masking path reproduces the historical single-row
arithmetic; larger bf16 batches can change near-tied argmaxes. This is not a claim
that every platform is bitwise reproducible.

Prefix decoding is greedy over admissible tokens: one left-to-right generation
pass, one model evaluation per generated slot, with no beam or restart. It feeds
back predictions. The 48-nt endpoint does not imply that its token-boundary input
reveals exactly 48 nt or that whole boundary tokens are evaluated for exactness.

## Controlled sweep and regenerated outputs

```bash
EXTRA="--epochs 30 --tiers 1,4,16 --probe_offset random"
EXTRA="$EXTRA --probes_per_tier 100 --n_nonmember 100"
EXTRA="$EXTRA --save_epochs 1,2,3,5,8,12,20,30 --score_snapshots"
PILOT2_WINDOW=300 bash pilot2/sweep.sh outputs/kcurve300 "ar" "0 1 2" \
    "$EXTRA" "char 2mer 3mer 4mer 5mer 6mer"
python -m pilot2.kcurve_report --root outputs/kcurve300

python -m pilot2.rescore --root outputs/bpe_human/dnabert2bpe_human_s0 \
    --ckpt ep120.pt --name reproduction_ep120 --compare scores_ep120.json

# Requires original reconstructed run artifacts; do not replace published CSVs blindly.
python -m pilot2.export_figure_data --root outputs --out reproduced/figure_data.csv

# These consume the published measurements in results/.
python -m pilot2.figures_privacy --out reproduced/figures
python -m pilot2.figures_main10 --out reproduced/figures
python -m pilot2.appendix_tables --out reproduced/tables
python -m pilot2.appendix_source_cells --summary results/appendix_source_cells.json --tables-out reproduced/tables
python -m pilot2.compact_appendix --tables reproduced/tables --out reproduced/tables
```

`sweep.sh` activates the recorded `glm` environment; adapt its environment setup
for another installation. A new run is costly and is not part of the aggregate-only
checks above. The compact-table formatter copies numeric cells, changes presentation
labels, and removes code filenames from table notes; it performs no reweighting or
statistical estimation. The two cross-family source tables are copied from the
verified reference snapshot when original outputs are unavailable.

## What left the PDF, and what stayed

- **Stayed:** all main-text sources and main figures; full DNABERT-2 seed trajectories
  and hidden-48 SEs; both tokenizer-window sweeps; matched-control design and ranges;
  decoder budgets and conditional-prediction limitations; scorer sensitivity; release
  identifiers; capacity/placement controls; released-model comparisons; downstream
  utility tables/visualization; scientific summaries of remaining robustness checks.
- **Moved here:** shell commands; JSON/CSV/script names; file-level provenance;
  operational details, numerical optimization history and correction chronology;
  redundant prose; full 19-cell decoder audit, grouped infilling cells, split-draw
  and census tables; placement variance visualization duplicated by direct controls.
- **Preserved separately:** the full-length manuscript was not shortened. The long
  submission appendix is archived verbatim at the snapshot link above. Historical
  prose is labeled as such; the compact supplement governs the submitted narrative.

## Diagnostic fields are not bounds

Legacy JSON fields such as `bound` and `loo_bound` keep their names and numeric
values for compatibility. They are conditional-prediction power summaries, not
certified recovery bounds. Search scores cropped 48-nt recovery while token LOO may
score complete covering tokens, and batched versus single-row numerical paths can
differ. Aligned counterexamples also exist. Early stopping does not rescue the
recordwise claim; zero exact recovery in BPE does not validate it either. The
abstract complete-state implication in the historical supplement requires identical
update maps, constraints, arithmetic and tie-breaking and does not certify the
reported outputs.
