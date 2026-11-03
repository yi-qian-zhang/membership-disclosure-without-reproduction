# Membership Disclosure without Sequence Reproduction

**English** | [简体中文](README.zh-CN.md)

Code and measurements for *Membership Disclosure without Sequence Reproduction:
Privacy Leakage from Fine-Tuned Genomic Language Models*.

We study candidate-record membership ranking and exact sequence recovery in
fine-tuned genomic language models, comparing contextual access, scoring, decoding,
and tokenization across eight released checkpoints and a controlled transformer.

## Main findings

| Experiment | Reported result | Scope |
| --- | --- | --- |
| DNABERT-2, chr22, single-copy records | Fresh-window rank-1: **18–26%**; matched controls: **0%** | Final checkpoint, three training seeds, 50 records per seed, 100 alternatives |
| Controlled synthetic canaries | 2-mer / 6-mer exact recovery: **0% / 92%** | Sixteen insertions, matched held-out loss **2.40 bits/nt** |

In the reported DNABERT-2 single-copy evaluations, neither tested decoder recovers
the hidden 48-nt target; their checkpoint coverage differs. This is not a universal
zero: separate NT experiments recover single-copy targets at 8% (250M) and 12–18%
(500M). Candidate ranking is **not personal identification or calibrated low-FPR
membership inference**. Training seeds reuse the same records. Matched background
loss does not establish equal target predictability or slot count as the sole mechanism.

## Quick start: regenerate figures and tables

Run from a fresh clone. This path needs no GPU, model weights or genomic downloads.

```bash
git clone https://github.com/yi-qian-zhang/membership-disclosure-without-reproduction.git
cd membership-disclosure-without-reproduction
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-analysis.txt
python -m pilot2.figures_main10 --out reproduced/figures
python -m pilot2.appendix_tables --results results --out reproduced/tables
python -m pilot2.appendix_source_cells --summary results/appendix_source_cells.json --tables-out reproduced/tables
python -m pilot2.compact_appendix --tables reproduced/tables --out reproduced/tables
```

**Fonts:** the plotting command requires Arial. Install it, or set
`GLMEXT_FONT_DIR` to a local directory containing the regular, bold, italic and
bold-italic TTF files. Fonts are not bundled. Table generation does not require Arial.

The commands regenerate **Figures 2–3 and 13 table fragments** from committed
measurements, writing to ignored `reproduced/`. Figure 1 is a separate editable
PowerPoint figure; its [source and export instructions](paper/figures/F1_source.md)
are included. This repository's `paper/` contains figure assets, not a complete
LaTeX manuscript.

## Choose a reproduction path

- **Inspect a reported number:** [measurement guide](results/README.md).
- **Rebuild plots, tables or model measurements:** [reproduction guide](docs/REPRODUCING.md).
- **Find an implementation:** [code map](pilot2/README.md).
- **Understand current versus historical material:** [repository guide](docs/REPOSITORY.md).
- **Trace corrections and prior experiments:** [dated notes](notes/README.md).

## Release boundaries

All source inputs are public. The release includes aggregate measurements and
redacted evaluation records, but not the consolidated human canary collection,
sample-linking metadata or fine-tuned weights. Reconstructing inputs and retraining
are separate from replaying the published tables.

Historical JSON fields such as `loo_bound` retain their names for compatibility.
Their power summaries are **conditional-prediction diagnostics, not certified
bounds on 48-nt recovery**, for all reported model families. Historical reports
and logs can contain superseded interpretations; consult the measurement guide.

## Credit and license

Built on Alexander Nemecek's GLM-Memorization framework and released genomic-model
backends. The predecessor is Nemecek et al., *Quantifying memorization and privacy
risks in genomic language models*, ACM-BCB 2026.
Licensed under [Apache License 2.0](LICENSE).

See [paper protocols and the evidence map](docs/PAPER_PROTOCOLS.md) for commands and details relocated from the appendix, with a preserved long-appendix snapshot.
