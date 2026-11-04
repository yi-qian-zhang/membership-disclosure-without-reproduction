# Experiment Log — Week 3 (5–11 October 2026)

**Project:** tokenizer × objective (× position encoding) in GLM memorization — paper 1, target RECOMB 2027 (abstract 28 Oct, full paper 4 Nov; checkpoint 21 Oct; fallback ISMB/ECCB, 7 Jan)
**Owner:** Spencer Zong · **Branch:** `glmex`, commits `ba174a0` → `7d16e5f`
**Compute:** TJU_6004, 4 × RTX 4090, conda `glm`
**Meetings this week:** Alex 1:1 on 4 Oct (`16_meeting_Alex_1004.md`); Erman's venue suggestion on 4 Oct (RECOMB / ISMB)

Running log; each step is appended when it happens. Numbers in this file are read from the server outputs named in each entry.

---

## 1. Decisions carried into the week

- Framing (Alex): "a more in-depth analysis of what prior work left open", not an "ablation"; drop "architecture was not the variable".
- Scope (Alex): toy model + HyenaDNA + DNABERT family; Evo out.
- Venue (Erman + Alex): bioinformatics conference first. Decision 7 Oct: aim RECOMB 2027, go/no-go on 21 Oct based on the DNABERT family result; fallback ISMB/ECCB 2027.
- Random canary placement is now the default for every new run (`--probe_offset random`).

---

## 2. Step log

### 2.1 (8 Oct, 01:53) core100 — core AR grid with 100 canaries per tier, 3 seeds, random placement

`tmux core100` → `outputs/core100/`. `pilot2/sweep.sh outputs/core100 ar "0 1 2" "--epochs 30 --tiers 1,4,16 --probes_per_tier 100 --n_nonmember 100 --save_epochs 1,2,3,5,8,12,20,30 --score_snapshots --probe_offset random" "char 3mer 6mer"`. 9 runs, ~15 min.

**Result (per cell 300 probe judgements, so about ±5 points on a rate):**

| | char | 3mer | 6mer |
|---|---|---|---|
| r=1 canary bits/nt at matched held-out floor 2.20 (train host) | — (char reaches only 2.03–2.05 in 30 epochs) | 1.63 | **0.76** |
| r=16 canary in a new host at a new offset: rank-1 | 0% | 2% | **39%** (in-phase, n=285) |
| non-member false positives (fresh host) | 0% | 1% | 0% |
| r = 1 / 4 / 16 at own training host, epoch 30 (bits/nt) | 1.95 / 1.95 / 1.95 | 0.02 / 0.01 / 0.02 | 0.03 / 0.03 / 0.03 |

Reading: with 100 canaries everything from week 2 holds: tokenizer order 6 > 3 > 1 at matched floor; under random placement the repetition tiers collapse onto one value at the training host (whole-example memorization), and recognition in a new context survives only for 6mer and only when the k-mer phase matches. Files: `outputs/core100/trajectory.md`, `offset_report.md`.

### 2.2 (8 Oct) Private repo check — `/data/wh/yqdata/PLM-Memorization` (read-only)

Core `src/` identical to the public repo. Resolved all 11 questions; details in `16_meeting_Alex_1004.md` §6. Key points for our methods section: his "extraction success" = rank ≤ 100 among 1,000 random sequences (chance 10%); Table 3 = max of three normalized scores (`compute_risk_scores.py`); canaries are standalone 64-nt sequences among 256-nt ones (his own comment, `canary_detectability.py:212`), padded to 512, MIA loss not pad-masked. No checkpoints exist.

### 2.3 (8 Oct) DNABERT family pipeline — `pilot2/dnabert.py` (commit `12cfc48`), `pilot2/analyze_dnabert.py` (`c1fbc06`)

- Data: the same pilot2 windows and canaries (288 nt, random offsets).
- Tokenization: DNABERT's overlapping k-mers from its own `vocab.txt`.
- Fine-tuning: **native MLM head**, DNABERT-style span masking (k consecutive tokens, ~15% of tokens), AdamW lr 2e-5, wd 0.01, 10% warm-up then constant, effective batch 16, grad clip 1.0 (the published config values), 30 epochs, snapshots at 1/3/8/15/30, plus the pretrained model scored before fine-tuning (epoch 0).
- Scoring: per-nucleotide span-masked PLL (mask the k tokens covering nt j; read the token starting at j, restricted to k-mers consistent with the visible neighbours, marginalized to the letter at j); probes scored every 3rd nucleotide (32 positions); rank vs a 100-sequence random pool; left-to-right extraction from a 48-nt prefix with consistent-k-mer decoding.
- Smoke test: pretrained 6-mer on uniform DNA = 2.05–2.11 bits/nt (chance), pipeline end-to-end in 43 s.
- Launched 02:09, `tmux dnabert1` → `outputs/dnabert/dnabert{3,4,5,6}_s{0,1}/`. Training ≈ 13–15 min per model; each snapshot score ≈ 5 min; ≈ 55 min per run; two runs per GPU.
- Pre-registered prediction: memorization at matched held-out floor increases 3 < 4 < 5 < 6.

### 2.4 (8 Oct) E. coli arm wired in — commit `7d16e5f`

`pilot2/real_data.py` gained `offset_mode`; `pilot2/run_pilot.py` gained `--data ecoli --fasta ...`. Smoke test passes in both modes. Note: on real DNA the held-out score can be below 2.0 (structure to learn), so the scorer's `floor_ok` flag is expected to read VIOLATION there; it is informational only.

### 2.5 (8 Oct, 02:54) Overnight queue — `pilot2/queue_1008.sh`, `tmux night`, log `outputs/night_1008.log`

Waits for `DNABERT1_DONE`, then:

| GPU | Runs | Output |
|---|---|---|
| 0 | E. coli, AR × {char, 3mer, 6mer} × seeds {0,1}, 50 probes/tier, random placement, snapshots; then E. coli MLM@0.15 / @0.5 × 3 tokenizers, seed 0 (40 probes/tier, pool 300) | `outputs/ecoli_ar/`, `outputs/ecoli_mlm/` |
| 1, 2 | Synthetic MLM@0.15 / @0.5 × 3 tokenizers × seeds 0 / 1, 40 probes/tier, pool 300, random placement | `outputs/core_mlm/` |
| 3 | DNABERT seed 2 for k = 3..6; then RoPE char × 2 seeds, 100 epochs, random placement | `outputs/dnabert/`, `outputs/rope_char100/` |

Ends with `NIGHT_DONE` in the log.

### 2.6 (8 Oct, 04:00) DNABERT family, first result: essentially no memorization at the published setting

`outputs/dnabert/dnabert_report.md` (seeds 0 and 1, native MLM head, 15% token masking, lr 2e-5, 30 epochs):

| k | held-out floor at epoch 30 | r=16 canary, training host (bits/nt / rank-1 / exact) | r=16, new host | false positives |
|---|---|---|---|---|
| 3 | 2.002 | 2.00 / 0.00 / 0.00 | 2.00 / 0.00 / 0.00 | 0.01 |
| 4 | 2.005 | 1.99 / 0.10 / 0.00 | 1.99 / 0.10 / 0.00 | 0.03 |
| 5 | 2.009 | 1.98 / 0.00 / 0.00 | 1.99 / 0.00 / 0.00 | 0.00 |
| 6 | 2.017 | 1.96 / 0.10 / 0.00 | 1.96 / 0.08 / 0.00 | 0.01 |

Reading. None of the four models memorizes the canaries in 30 epochs: canary bits stay at 1.96–2.00, rank-1 ≤ 10%, extraction 0, and the held-out floor never leaves 2.00–2.02 (no overfitting at all). The pretrained models (epoch 0) sit at 2.09–2.11 on uniform DNA, as expected. There is a faint 6 < 5 < 4 < 3 ordering at r=16 (1.96 < 1.98 < 1.99 < 2.00), in the predicted direction but within noise. So the pre-registered test is **not decided** by this run.

Why the pressure was too weak (diagnosis, not a result): with overlapping k-mers, hiding one nucleotide requires masking k consecutive tokens, so a 15% *token* mask rate hides only ~15%/k of the *nucleotides* (5% for k=3, 2.5% for k=6). Each sequence therefore supervises very few nucleotides per epoch, and lr 2e-5 is small. This also makes the standard setting unfair across k (smaller k hides more nucleotides per epoch). The published pipeline instead supervised every position with a next-token head.

Two corrected variants, implemented in `pilot2/dnabert.py` (commit after `c1fbc06`; `--objective causal`, `--mask_nt_rate`), both smoke-tested:

- **causal**: next-token prediction with a causal attention mask on the encoder and the native head (no new head, no bidirectional leak). With overlapping k-mers each next token adds exactly one nucleotide, so this is nucleotide-level AR over k-mer embeddings and per-nt scoring is exact (restrict to the 4 k-mers consistent with the k−1 known letters). lr 2e-5 as published. Pretrained model under a causal mask starts far off (4.8 bits/nt) and reaches ~2.04 after one smoke epoch.
- **nt0.05_lr1e-4**: MLM with the *hidden-nucleotide* rate fixed at 5% for every k (token rate = 5% × k), lr 1e-4.

Launched 04:08, `tmux dnabert2` (GPU 3: causal k=3..6 and nt-variant k=3,4; GPU 0: nt-variant k=5,6), seed 0, same snapshots; ends with `DNABERT2_DONE`. The seed-2 runs of the original setting were stopped (uninformative) and their partial outputs removed.

### 2.7 (8 Oct, 04:20) HyenaDNA downloaded and load-tested (no experiment yet)

`/data/wh/yqdata/models/HyenaDNA/{hyenadna-tiny-1k-seqlen-hf, hyenadna-small-32k-seqlen-hf}` via hf-mirror (curl). Both load under transformers 4.29 with `trust_remote_code`, as `HyenaDNAForCausalLM`: tiny 0.44M params, small 3.28M. Character vocabulary (A/C/G/T = ids 7–10, 16 logits), causal, the tokenizer appends `[SEP]` and no BOS. The 14.2M HyenaDNA in the BCB paper is a larger checkpoint (medium); to fetch if needed. Plan: a thin wrapper so the pilot2 AR scorer runs on it unchanged (1-mer, causal, pretrained unembedding kept).

### 2.8 (8 Oct, 07:30–08:30) Morning launches: DNABERT causal seeds 1–2 and 100 epochs; HyenaDNA pipeline

- **`tmux dnabert3`** (GPU 1, 2): `--objective causal`, k = 3..6, seeds 1 and 2, 30 epochs — robustness of §3.1. Ends `DNABERT3_DONE`.
- **`tmux dnabert4`** (GPU 0, 3): `--objective causal`, k = 3..6, seed 0, **100 epochs**, snapshots 15/30/50/75/100 → `outputs/dnabert_e100/`. Question: do k = 3, 4 catch up (sooner vs more at the real-model scale)? Ends `DNABERT4_DONE`.
- **`pilot2/hyena.py`** (commit after `f8fa2ba`): pretrained HyenaDNA (character model, causal) on the same data, native unembedding kept, [BOS] prepended; per-nt scoring from the four ACGT logits; pool 500; greedy extraction. Published config: lr 2e-5, wd 0.01, 10% warm-up, batch 8 × 2. Models downloaded via hf-mirror: tiny (0.45M), small (4.07M), **medium-160k (6.55M learnable; the checkpoint named in the BCB config)**. [The 20 Oct correction that stood here was wrong and is withdrawn 2 Nov; it had replaced 6.55M with 14.24M on the grounds that the smaller count omitted the implicit Hyena filter MLPs. Those MLPs total 199,168 values and are already inside 6.55M. The real gap is `mixer.filter_fn.pos_emb.t` and `.z`, 7,680,096 values: `t` is a uniform ramp from 0.0 to 1.0 of length 160,002 and `z` five positional features of it, both byte-identical across all eight layers while the learned `implicit_filter` weights are not, and sized by `max_seq_len: 160002` in `config.json` rather than by capacity. The registered buffers are those 7,680,096 plus 2,048 in `filter_fn.modulation.deltas`, so 14,236,768 - 7,682,144 = 6,554,624 exactly; the eight `filter_fn.bias` tensors are trainable and already inside that count. See 3.58(i).] Smoke: pretrained medium on uniform DNA = 2.10 bits/nt (chance); one epoch → 2.00.
- **`tmux hyena1`** (GPU 1, 2): medium × seeds 0/1/2 at lr 2e-5; medium at lr 1e-4; small at 2e-5; 30 epochs, snapshots, epoch-0 baseline → `outputs/hyena/`. Ends `HYENA1_DONE`.
- Combined random-placement decomposition built as `outputs/core_all/` (symlinks to core100 seeds 0–1 and core_mlm) and reported in §3.3.

### 2.9 (8 Oct, 11:00) Real models on the real genome: memorisation vs utility in one run

Erman asked for a utility metric next to memorisation. Design: fine-tune the pretrained models on **real E. coli windows** with planted canaries (the realistic threat: fine-tuning on a sensitive real cohort). The held-out loss on unseen E. coli windows is then the utility measure, and it is recorded at every snapshot together with the canary scores, so one run gives the memorisation-vs-utility trajectory. `--data ecoli` added to `pilot2/dnabert.py` and `pilot2/hyena.py` (commit after `3cfb6e9`), smoke-tested.

Launched `tmux real1` → `outputs/dnabert_ecoli/` (DNABERT causal, k = 3..6, seed 0, 50 epochs, snapshots 1/3/8/15/30/50, epoch-0 baseline; one k per GPU) and `outputs/hyena_ecoli/` (HyenaDNA medium, seeds 0 and 1, same schedule). Ends `REAL1_DONE`.

### 2.10 (8 Oct, 12:00) Figures for the proposal update and the paper — `pilot2/figures_proposal.py`

Five figures built from the saved reports (copies in `notes/figures/proposal/`):

| file | what it shows | source |
|---|---|---|
| F1_variance.png | share of variance (tokenizer / objective / interaction / seed), fixed vs random placement | tok1, core_all |
| F2_matched_floor.png | r=1 canary memorised vs held-out loss, synthetic and E. coli, 3 tokenizers | core100, ecoli_ar |
| F3_dnabert_family.png | DNABERT 3/4/5/6-mer: r=16 recognised at epoch 30 (training host / new host, 3 seeds); 100-epoch trajectories | dnabert, dnabert_e100 |
| F4_position.png | r=16 canary in a new sequence: absolute+fixed / absolute+random / RoPE+random, from-scratch backbone | off1, core100, rope_rand |
| F5_real_models.png | r=16 memorised over fine-tuning: HyenaDNA medium vs DNABERT 3-mer / 6-mer (causal) | hyena, dnabert |

- F6_utility.png: memorisation vs utility on E. coli for the real models (added 8 Oct, 14:00; source dnabert_ecoli, hyena_ecoli).

Each figure carries a one-line explanation for Alex to drop into Aims 1.1 / 1.2 (to be written with the figure captions once the E. coli real-model runs finish).

### 2.11 (8 Oct, 18:20) Three additions after the user's review: E. coli seeds, DNABERT-2 (BPE), all of Alex's real datasets

Decision (user, 8 Oct evening): paper writing waits until the experiments are complete. Three items added.

**(1) DNABERT causal on E. coli, seeds 1 and 2** — same settings as seed 0 (3.9): `tmux ecoli_s12`, `pilot2/queue_ecoli_s12.sh`, one k per GPU, seeds in sequence, then `analyze_dnabert` over `outputs/dnabert_ecoli`. About 1 h per run.

**(2) DNABERT-2 = the BPE member of the real-model family** — `pilot2/dnabert2.py` (commit e29fb56). Model `zhihan1996/DNABERT-2-117M` (117M, BPE vocab 4096, ALiBi, non-overlapping tokens 1–32 nt, mostly 5–8), downloaded with curl via hf-mirror to `/data/wh/yqdata/models/DNABERT2` (the repo has no `special_tokens_map.json`; the first attempt saved a 404 page under that name, deleted). Load test: tokenizer round-trips, the MLM head is in the checkpoint (`cls.predictions.*`), masked-token prediction works (log p = −0.04 for an easy token). Triton flash attention fails on the server (`libcuda.so` stub), so the module's exact PyTorch attention path is forced.
  * Scoring is per TOKEN, converted to bits per nucleotide by dividing by the nucleotides the scored tokens cover (there is no exact per-nt probability with variable-length tokens). Probe score = tokens overlapping the 96-nt span; floor = whole window.
  * `--objective causal` folds a causal mask into the ALiBi bias (upper triangle −1e4); verified that changing the last 5 tokens leaves earlier logits unchanged (max diff 0.0). `--objective mlm` = native head, 15 % token masking, PLL scoring.
  * Extraction reveals the tokens ending at or before offset+48 (the recorded `k_revealed_nt` is ≤ 48, typically 44–48), then decodes greedily. For mlm the unknown region keeps the true token layout (number and length of masked slots), a mild advantage to the model; stated here and to be stated in the paper.
  * Output files have the same shape as `dnabert.py`; out dirs `dnabert2bpe[_causal][_<data>]_s<seed>`; `analyze_dnabert.py` lists them as k = "BPE" after the 6-mer.
  * Smoke tests pass (causal E. coli: floor 2.74 → 2.10 after one epoch; mlm synthetic 2.04 → 1.95).

**(3) All real datasets from Alex's configs** (`config/*.yaml`, `src/data/real_data_loader.py`): E. coli (have), **yeast S288C R64** (GCF_000146045.2, 12.1 Mb, 17 chromosomes → 42,212 windows; downloaded from NCBI), **GUE human promoters prom_300_all** (`leannmlindsey/GUE`, 47,357 train rows of 300 nt, centre-cropped to 288 → 47,356 windows; csv fetched from hf-mirror because `datasets` fails to import on the server (libsndfile)). GRCh38 is listed in his loader but his paper uses GUE for human; not downloaded (3 GB). `real_data.py` now has `DATA_PATHS` / `load_windows` (FASTA → windows, CSV → one window per row) and all three CLIs plus `run_pilot.py` take `--data ecoli|yeast|gue` (`--fasta` only overrides). Order-0 entropy of the windows: E. coli 1.9998, GUE 1.983, yeast 1.959 bits/nt.

Launched `tmux bpe_real` (`pilot2/queue_1008b.sh`) and `tmux bpe_ecoli` (the BPE E. coli line relaunched after a wrong `--stride` flag), alongside `ecoli_s12`:

| GPU | jobs (in order) | out |
|---|---|---|
| 0 | DNABERT-2 causal, E. coli, seeds 0/1/2, 50 ep | `outputs/dnabert_ecoli/dnabert2bpe_causal_ecoli_s*` |
| 1 | DNABERT 3/4/5/6 causal + DNABERT-2 causal on **yeast**, seed 0, 50 ep | `outputs/dnabert_yeast` |
| 2 | same on **GUE** | `outputs/dnabert_gue` |
| 3 | HyenaDNA medium yeast, GUE (50 ep); DNABERT-2 causal **synthetic** seeds 0/1/2 (30 ep, joins `outputs/dnabert`); DNABERT-2 **native MLM** E. coli seed 0 | `outputs/hyena_yeast`, `outputs/hyena_gue`, `outputs/dnabert`, `outputs/dnabert_ecoli` |
| 2+3 | toy backbone AR × char/3mer/6mer × 2 seeds on yeast and GUE (as `ecoli_ar`) | `outputs/yeast_ar`, `outputs/gue_ar` |

Ends with `ECOLI_S12_DONE` / `QUEUE_1008B_DONE` in `outputs/dnabert_ecoli/queue_s12.log` / `outputs/queue_1008b.log`. Expected finish: E. coli seeds ~4 h; yeast / GUE DNABERT lines ~6–8 h (shared GPUs); all by the morning of 9 Oct.

### 2.12 (8 Oct, 22:00) Downstream utility = GUE promoter detection, DNABERT's own benchmark — `pilot2/downstream.py` (e2a0d5f)

User's question "what is utility, which metric?" → answer: held-out bits/nt on unseen windows of the same genome, i.e. language-model utility, not a downstream task. User's decision: since GUE prom_300_all is the benchmark the DNABERT papers themselves use, add it.

Design (`--downstream` flag in `dnabert.py`, `dnabert2.py`, `hyena.py`; evaluated at epoch 0, every snapshot and the final model, stored under `downstream` in the score json):
  * **linear probe** — frozen mean-pooled last hidden state → logistic regression; cheap; representation quality.
  * **fine-tune** — DNABERT-2 recipe scaled down: deep copy of the model + linear head, AdamW 3e-5, batch 32, 2 epochs on 20k labelled train rows (paper: 3 epochs on all 47k); the copy is discarded, the memorisation run is untouched.
  * Metric: accuracy and **MCC** (the GUE metric) on the full 5,920-row test split, which is disjoint from the training file.
  * Smoke test (10k rows / 1 epoch / 1k test) before any fine-tuning: MCC 0.45–0.48 for all three families (DNABERT-3 causal-masked, DNABERT-2 causal, HyenaDNA). Per-snapshot cost ≈ 1–3 min.
  * `analyze_real.py` gains two columns (probe MCC, fine-tune MCC) and a third table: the epoch with the best downstream MCC and the canary status there — the utility optimum by DNABERT's own metric.

Launched `tmux gue_ds` (`pilot2/queue_gue_ds.sh`): GUE rerun of DNABERT 3/4/5/6 causal, DNABERT-2 BPE causal and HyenaDNA medium with the probe at every snapshot → `outputs/dnabert_gue_ds`, `outputs/hyena_gue_ds`; ends `GUE_DS_DONE` in `outputs/queue_gue_ds.log`. The earlier GUE runs (3.14) stay as they are.

### 2.13 (8 Oct, late) Downstream panel widened: human-wide GUE tasks + yeast histone marks (323d410)

User's question "why only prom_300_all, what about the other species?" → answer: the utility task must match the fine-tuning data (human promoters → human task); GUE has no bacterium; mouse / virus / fungi-species tasks measure transfer, not utility on the fine-tuned data. User's decision: add (A) a wider human panel and (B) yeast-matched tasks, queued on the server.

`pilot2/downstream.py` generalised to any list of GUE tasks (`--downstream_tasks`, default by `--data`: gue → prom_300_all; yeast → emp_H3, emp_H3K4me3). Multi-class MCC via sklearn (splice has 3 classes). Downloaded from hf-mirror: prom_core_all (70 nt, 53k train), human_tf_0 (100 nt, 32k), splice_reconstructed (400 nt, 36k, 3 classes), emp_H3 and emp_H3K4me3 (500 nt yeast histone-mark sets, 12–33k). `analyze_real.py` prints per-task MCC columns and uses the mean over tasks for the best-downstream table.

Queued `tmux ds2` (`pilot2/queue_ds2.sh`), which starts after `gue_ds` finishes and the smoke test passes (`outputs/DS2_GO`):
  (A) GUE memorisation runs with the human-wide panel prom_core_all + human_tf_0 + splice at every snapshot → `outputs/dnabert_gue_ds2`, `outputs/hyena_gue_ds2`;
  (B) yeast memorisation runs with emp_H3 + emp_H3K4me3 at every snapshot → `outputs/dnabert_yeast_ds`, `outputs/hyena_yeast_ds`.
Six models each (DNABERT 3/4/5/6 causal, DNABERT-2 BPE causal, HyenaDNA medium), seed 0, 50 epochs. Ends `DS2_DONE` in `outputs/queue_ds2.log`. E. coli keeps the language-model utility only (no bacterial task in GUE) — to be stated in the paper.

### 2.14 (9 Oct, 05:00-06:00) The four RECOMB hardening items, queued

After the "can this win RECOMB" discussion the user asked for the first four of the five items on
the list. Item 2 was already running; items 1, 3 and 4 were built tonight.

**(1) The from-scratch BPE cell** — `pilot2/bpe_arm.py` (aef2380). DNABERT-2 shows that the BPE model
memorises most, but it also has 117M instead of 86-89M parameters, ALiBi instead of learned absolute
positions and a different pretraining corpus, so it cannot isolate the tokenizer. This trains the SAME
12.9M backbone as `run_pilot.py` with a BPE vocabulary, so char / 3mer / 6mer / BPE differ in the
tokenizer and nothing else. Forced differences, stated with the results: AR only (variable-length tokens
are right-padded and a bidirectional objective would leak through the pads, so BPE+MLM stays with
`dnabert2.py`, which has a native attention mask); scores are token sums divided by the nucleotides those
tokens cover; the embedding table is larger (the capacity controls `--emb_rank` / `--d_ff` still apply).
Four BPE vocabularies trained with `pilot2/train_bpe.py` (now also `--synthetic` and CSV corpora):
synthetic k=4.83, E. coli k=5.01, yeast k=5.05, GUE k=4.9 nt/token. Output names (`bpe4096_ar_s0`,
`bpe4096_ecoli_ar_s0`, ...) are read by `analyze_traj.py`, so the BPE rows land in the matched-overfitting
table next to the k-mer cells.

**(3) Real human canaries** — `pilot2/human_canary.py`, `pilot2/analyze_human.py` (318060f, 2421ef8).
Downloaded hg38 chr22 (51 Mb) and the 1000 Genomes phase-3 phased VCF for chr22 (2,548 samples, 186 MB).
A canary is now a REAL haplotype segment: 96 nt of chr22 centred on a variant with AC/AN <= 0.001 and at
most 5 carriers, with the carrier's alternate allele substituted at every rare variant in the window.
400 canaries, 366 distinct carriers, 2.07 rare variants each, AF mean 3.5e-4, max 9.8e-4, GC 43 %.
Non-members come from the same pool, so the control is equally real and equally rare and differs only in
having been trained on. Every extraction now records the decoded bases, so `analyze_human.py` can score
the privacy-relevant question per variant: did the model return the individual's rare allele, the
reference base (the null), or neither. `--canary_npz` works in all four model CLIs.
Two notes for the write-up: the INFO AF field of that VCF is rounded to two decimals, so every variant
rarer than 1 % reads as 0.00 and the frequency must come from AC/AN (this silently produced zero canaries
at first); and a real segment is in-distribution, so part of it is predictable from biology, which makes
this test strictly more conservative than the random-canary one.

**(4) Mechanism, per-token accounting** — `pilot2/token_info.py`. A 96-nt canary is 192 bits for every
tokenizer; what changes is the number of token slots carrying them (char 96, 3-mer 32, 6-mer 16, BPE ~20)
and the information per slot. The script re-reads the saved scores and reports memorisation at matched
held-out loss both per nucleotide (the result) and per token slot (the explanation), plus the corpus
statistic behind it: how often the tokens making up a canary occur elsewhere in the training corpus, and
what fraction never occur at all. If a model stores a roughly fixed amount per slot, the per-nucleotide
curves that separate by tokenizer should move together per slot, and the residual is what the tokenizer
explains beyond slot counting. Figure with both panels via `--plot`.

**Infrastructure note.** Mutagen had stalled for hours staging a 238 MB chr22 VCF left in `data/1000g/`
by an earlier session, which blocked all code from reaching the server. Large corpora now live outside the
synced tree in `/data/wh/yqdata/glm_data` (1000g, human, gue) and the code takes the root from
`GLMEXT_DATA` (default `data`), so a download can never block the sync again. Tonight's code also went up
with `scp` to bypass the backlog.

**Queued.** `tmux night1009` (`pilot2/queue_night1009.sh`), after the prep smoke tests passed:
  * phase A, now, 4 GPUs: BPE cell on synthetic (2 seeds), E. coli (2 seeds), yeast, GUE, 30 epochs with
    snapshots; then `analyze_traj` against core100 / ecoli_ar and `token_info` for both;
  * phase B, after `tmux seeds12` finishes so the GPUs are not oversubscribed: real human canaries on
    chr22 for DNABERT 3/4/5/6 causal, DNABERT-2 BPE, HyenaDNA medium and the from-scratch BPE cell,
    50 epochs, snapshots 1/3/8/15/30/50 plus the pre-fine-tuning baseline;
  * phase C: `analyze_real`, `analyze_human`, `analyze_dnabert` over `outputs/human_real`.
Ends `NIGHT1009_DONE` in `outputs/queue_night1009.log`. Still running alongside: `tmux ds2` (human-wide
GUE panel + yeast histone tasks) and `tmux seeds12` (yeast / GUE seeds 1 and 2), both from 2.13.

---

## 3. Results (to be filled as runs finish)

- [x] 2.3 DNABERT family (seeds 0, 1): table from `pilot2.analyze_dnabert` → `outputs/dnabert/dnabert_report.md`
- [x] 2.5 E. coli AR
- [x] 2.5 synthetic MLM core
- [x] 2.5 RoPE char 100 epochs (DNABERT seed 2 of the original setting dropped; causal seeds 1–2 running)
- [x] 2.5 E. coli MLM

### 3.1 DNABERT family — causal variant: the pre-registered ordering holds (seed 0; seeds 1, 2 running in `tmux dnabert3`)

`outputs/dnabert/dnabert_report.md`, epoch 30, lr 2e-5, random placement; cells = bits/nt / rank-1 / exact:

| k | held-out floor | r=4 training host | r=16 training host | **r=16 in a new host, new offset** |
|---|---|---|---|---|
| 3 | 2.002 | 1.99 / 0.05 / 0 | 1.99 / 0.10 / 0 | 2.00 / **0.00** / 0 |
| 4 | 2.005 | 1.99 / 0.05 / 0 | 1.96 / 0.35 / 0 | 1.97 / **0.30** / 0 |
| 5 | 2.012 | 1.96 / 0.25 / 0 | 1.86 / 1.00 / 0 | 1.86 / **0.90** / 0 |
| 6 | 2.045 | 1.83 / 0.80 / 0 | 1.23 / 1.00 / 0 | 1.29 / **1.00** / 0.10 |

- **3 < 4 < 5 < 6 on every column**, at the same learning rate, epochs and (nearly identical, 2.00–2.05) held-out floors. False positives 0–3%. Epoch 0 (pretrained weights under a causal mask) is far from fitted (2.8–4.7 bits) and reaches ~2.0 after one epoch for every k, so all four start the comparison from a common point.
- Trajectory: k=6 reaches rank-1 100% at epoch 15, k=5 at 30, k=4 35% at 30, k=3 never within 30 epochs.
- **Unlike our from-scratch absolute-position models, the pretrained DNABERT models recognise the canary in a new host at a new offset as well as in its training host** (k=6: 100% / 100%; k=5: 90% / 100%). The memory is content-based. This is the privacy-relevant case.
- **MLM with equalised hidden-nucleotide rate (5%, lr 1e-4):** r=16 training host 2.00 / 1.89 / 1.96 / 1.73 bits (k = 3/4/5/6), rank-1 0 / 15 / 15 / 75%. Same direction, weaker, with a 4/5 swap inside noise (20 probes). k=6 snapshot scoring was still running at 07:00.
- Still open: seeds 1 and 2 (running). A matched-floor comparison is not possible here because nothing overfits in 30 epochs at lr 2e-5; the comparison is at matched epochs with the floors reported.

### 3.2 Real genome (E. coli, `outputs/ecoli_ar/`, AR × 3 tokenizers × 2 seeds, 50 probes/tier, random placement)

| | char | 3mer | 6mer |
|---|---|---|---|
| r=1 bits/nt at matched floor 2.10 / 2.20 | 1.84 / — | 1.58 / 1.36 | **1.05 / 0.68** |
| r=16 at own training host, epoch 30 (bits / rank-1 / exact) | 1.77 / 0.97 / 0 | 0.02 / 1.00 / 1.00 | 0.02 / 1.00 / 1.00 |
| r=16 in a new host, new offset (rank-1) | 1% | 8% | **48%** (in-phase, n=94) |
| non-member false positives | 0% | 0% | 1% |

The tokenizer order holds on real DNA and the gap is wider than on synthetic data (at 2.10: 1.84 / 1.58 / 1.05 vs 1.89 / 1.74 / 1.21). Held-out "floors" are above 2.0 for char (2.11–2.16) because a 12.9M model trained on 5,000 windows does not learn E. coli structure; the chance line is no longer exactly 2.000, so only within-corpus comparisons are made. `outputs/ecoli_mlm/` (MLM@0.15/0.5, seed 0, 40 probes): little memorisation in 30 epochs, 6mer most (r=16 rank-1 12–28%).

### 3.3 Masked objective under random placement (`outputs/core_mlm/`, 40 probes/tier, 2 seeds) and the combined decomposition

- r=16 training host, pll: char 1.999 / 3mer 1.98–1.99 / 6mer 1.92–1.93; rank-1 0 / 3–12 / 57–72%; extraction 0 everywhere. Masked models memorise far less than the fixed-placement week-2 numbers suggested (then: 3mer@0.5 0.16, 6mer@0.5 0.11).
- **Combined two-way decomposition, random placement, seeds 0+1 (`outputs/core_all/`, AR from core100 + MLM from core_mlm): objective 57.7%, tokenizer 15.4%, interaction 26.9%, seed 0.0%.** Within masked models the tokenizer explains 97.8%; within causal models 100%.
- **This changes the headline.** Under fixed placement (week 2, `tok1`) the split was tokenizer 59.5 / objective 25.7. Under random placement the objective dominates, because causal models memorise whole training examples (k-mer bits ≈ 0.01) while masked models barely memorise at 30 epochs, and char AR also stays near 1.95. The honest statement: *the objective decides whether whole examples are memorised; within an objective, the tokenizer decides almost everything else.* Both tables go in the paper, labelled by placement.

### 3.4 RoPE char at 100 epochs (`outputs/rope_char100/`)

Own training host: r=16 fully memorised by epoch 100 (0.01 bits, 93% extraction) at a held-out floor of 10.6–10.9 bits (extreme overfitting). In a new host: still 0%. The matched-floor r=1 curve coincides with absolute-position char (1.797 vs 1.773 at 2.20). For char, relative positions change nothing; position-free recognition of a repeated sequence appears only with k-mer tokenizers.

### 3.5 Pointers

Copies in `notes/figures/`: `dnabert_dnabert_report.md`, `core_all_tok_analysis_r16_train.md`, `core_mlm_tok_analysis_r16_train.md`, `ecoli_ar_trajectory.md/.png`, `ecoli_ar_offset_report.md`, `core100_*`, `rope_char100_trajectory.md`.

### 3.6 DNABERT causal, three seeds (`tmux dnabert3` done 08:25): the ordering is stable

Epoch 30, mean of seeds 0/1/2 (`outputs/dnabert/dnabert_report.md`, rows `causal`):

| k | floor | r=16 training host (bits / rank-1 / exact) | r=16 new host | r=4 training host |
|---|---|---|---|---|
| 3 | 2.002 | 1.99 / 0.03 / 0 | 1.99 / 0.07 / 0 | 2.00 / 0.03 / 0 |
| 4 | 2.006 | 1.96 / 0.37 / 0 | 1.96 / 0.37 / 0 | 1.99 / 0.08 / 0 |
| 5 | 2.011 | 1.86 / 0.88 / 0 | 1.85 / 0.92 / 0 | 1.96 / 0.25 / 0 |
| 6 | 2.042 | 1.23 / 1.00 / 0.03 | 1.32 / 1.00 / 0.10 | 1.83 / 0.80 / 0 |

Monotone in k on every column with three seeds; false positives ≤ 1%. New-host recognition equals training-host recognition (content memory).

### 3.7 HyenaDNA (`tmux hyena1` done ~09:40): the pretrained character model memorises far MORE than the DNABERT family

`outputs/hyena/*.log` (summary lines), 30 epochs, lr 2e-5 unless noted, random placement, pool 500:

| model (params) | epoch | floor | r=1 training host | r=16 training host (bits / rank-1 / exact) | r=16 new host |
|---|---|---|---|---|---|
| medium-160k (14.24M), seed 0 | 0 | 2.094 | 2.09 / 0 / 0 | 2.07 / 0 / 0 | 2.07 / 0 / 0 |
| | 15 | 2.032 | 1.94 / 0.55 / 0 | **0.21 / 1.00 / 0.95** | 0.26 / 1.00 / 1.00 |
| | 30 | 2.445 | 1.59 / 1.00 / 0 | 0.14 / 1.00 / 0.70 | 0.31 / 1.00 / 0.65 |
| medium, seeds 1 / 2 at epoch 30 | 30 | 2.39 / 2.35 | 1.60 / 1.58 | 0.13 / 0.16 (rank-1 1.00, exact 0.95 / 0.65) | 0.33 / 0.48 |
| medium, lr 1e-4 | 30 | 2.349 | 1.43 / 1.00 / 0 | 0.12 / 1.00 / 0.65 | 0.76 / 0.95 / 0.20 |
| small-32k (3.28M) | 30 | 2.192 | 1.68 / 1.00 / 0 | 0.22 / 1.00 / 0.85 | 0.64 / 1.00 / 0.25 |

Reading.
- HyenaDNA, a **single-nucleotide** model, memorises the 16× canaries almost completely by epoch 15 (0.21 bits, 95% verbatim extraction, 100% recognition in a new host) at a held-out floor of only 2.03. DNABERT-6 (causal) reaches 1.23 bits and 3% extraction at epoch 30 with floor 2.04. So **across architectures the tokenizer ordering does not hold**: the character model memorises more than every k-mer BERT, at the same lr and epochs and at a matched floor.
- Why this is not a contradiction of §3.1 / §3.6: the within-DNABERT comparison varies only k; HyenaDNA vs DNABERT varies architecture (Hyena vs Transformer encoder), size (6.5M vs 89M), pretraining objective (causal vs masked) and, importantly, **objective match**: HyenaDNA is fine-tuned on the objective it was pretrained with, while DNABERT is pretrained masked and fine-tuned causal (its epoch-0 floor under a causal mask is 2.8–4.7 bits). This is exactly the confounded comparison the BCB paper made; our data say that in such a comparison the tokenizer is not the deciding variable.
- It also matches the BCB paper's own observation that HyenaDNA shows the strongest extraction.
- The HyenaDNA memory is content-based (new host ≈ training host), unlike our from-scratch absolute-position toy models.
- Model size note, resolved 20 Oct and **reversed 2 Nov**: the checkpoint named in the BCB config (`hyenadna-medium-160k-seqlen-hf`) has **6,554,624 learnable parameters (6.55M)**. Its safetensors file holds 14,236,768 values in 212 tensors, but 7,680,096 of those are the fixed `pos_emb.t`/`.z` positional grids sized by `max_seq_len: 160002` and duplicated across all eight layers, with 2,048 more in `filter_fn.modulation.deltas`; subtracting those 7,682,144 registered buffers returns 6,554,624 exactly. [Amended 2 Nov: this sentence first named a filter bias as the 2,048. Loading the model separates them --- the eight `filter_fn.bias` tensors are trainable and inside 6,554,624, while `modulation.deltas` is the buffer.] 6.55M was never a miscount. The BCB table cited here is the predecessor's Table 1, which does list HyenaDNA at 14.2M --- but that figure is itself the file total, so the predecessor overstates HyenaDNA's capacity by 2.17x. The HyenaDNA paper gives "7 M" at 160k in its Table 4.4 and 6.6M for an eight-layer, width-256 model in its appendix, and `config.json` confirms ours is eight layers at `d_model` 256, so 6.55M is the figure that agrees with HyenaDNA's own. Still no question for Alex. Companion file totals: tiny-1k 450,712, small-32k 4,069,168, likewise inflated by their own grids.

### 3.8 DNABERT causal at 100 epochs (`tmux dnabert4`, k = 3 and 5 finished; 4 and 6 running)

| k | epoch | floor | r=16 training host | r=16 new host |
|---|---|---|---|---|
| 3 | 50 / 75 / 100 | 2.016 / 2.089 / 2.195 | 1.93 / 1.72 / 1.36 (rank-1 0.4 / 0.8 / 1.0; exact 0) | 1.96 / 1.95 / 1.84 (rank-1 0.1 / 0.2 / 0.55) |
| 5 | 50 / 75 / 100 | 2.024 / 2.072 / 2.156 | 1.56 / 0.63 / 0.28 (rank-1 1.0; exact 0 / 0.5 / 1.0) | 1.60 / 0.85 / 0.54 (exact 0 / 0.5 / 0.9) |

At a matched floor (k=3 at epoch 100, 2.195, vs k=5 at epoch 75, 2.072) k=5 has memorised far more (0.63 vs 1.36 bits; 50% vs 0% verbatim). So at the real-model scale, too, coarser tokens memorise **more, not only sooner**. k = 4 and 6 to be added when the runs finish.

**3.8 completed (10:40, all four k):** `outputs/dnabert_e100/dnabert_report.md` (copy: `figures/dnabert_e100_report.md`).

| k | floor at epoch 30 / 50 / 75 / 100 | r=16 training host, bits at 30 / 50 / 75 / 100 | exact extraction at 100 | r=16 new host at 100 (rank-1 / exact) |
|---|---|---|---|---|
| 3 | 2.00 / 2.02 / 2.09 / 2.20 | 2.00 / 1.93 / 1.72 / 1.36 | 0% | 55% / 0% |
| 4 | 2.01 / 2.03 / 2.08 / 2.15 | 1.97 / 1.82 / 1.41 / 0.97 | 20% | 100% / 5% |
| 5 | 2.01 / 2.02 / 2.07 / 2.16 | 1.89 / 1.56 / 0.63 / 0.28 | 100% | 100% / 90% |
| 6 | 2.04 / 2.12 / 2.31 / 2.50 | 1.47 / 0.33 / 0.19 / 0.12 | 95% | 100% / 65% |

Interpolated at a matched held-out floor, r=16 canary bits/nt: @2.05: 1.84 / 1.62 / 1.06 / 1.28; @2.10: 1.68 / 1.27 / 0.52 / 0.61 (k = 3 / 4 / 5 / 6). So at the real-model scale coarser k-mers memorise more at equal generalisation cost, with k = 5 and 6 indistinguishable at matched floor (6 overfits faster, so at a fixed epoch it is ahead). For r=1 canaries the matched-floor values are flat across k (1.81–1.89 at 2.10): a single exposure is not memorised by any DNABERT within this budget. Both facts go in the paper as they are.

### 3.9 Real models fine-tuned on the real genome: memorisation vs utility (`tmux real1`, done 13:30)

Utility = held-out loss on unseen E. coli windows (bits/nt, lower = more useful; the pretrained HyenaDNA scores 2.07 on E. coli, the DNABERT models 2.9–4.8 under a causal mask). Canary numbers as before (20 per tier, random placement). Files: `outputs/dnabert_ecoli/dnabert_report.md` (copy `figures/dnabert_ecoli_report.md`), `outputs/hyena_ecoli/*.log`.

**DNABERT family (causal fine-tuning, lr 2e-5, seed 0)** — utility / r=16 canary bits (rank-1, exact):

| k | epoch 8 | epoch 15 | epoch 30 | epoch 50 |
|---|---|---|---|---|
| 3 | 1.939 / 2.05 | 1.908 / 2.02 | 1.890 / 1.94 (0.10, 0) | 1.919 / 1.60 (0.90, 0) |
| 4 | 1.935 / 2.05 | 1.925 / 2.00 | 1.919 / 1.77 (0.60, 0) | 1.932 / 0.90 (1.00, 0.40) |
| 5 | 1.931 / 2.03 | 1.917 / 1.98 | 1.910 / 1.69 (0.90, 0) | 1.934 / 0.58 (1.00, 0.50) |
| 6 | 1.928 / 1.98 | 1.919 / 1.85 (0.50) | 1.922 / 0.99 (1.00, 0.20) | 1.981 / 0.31 (1.00, 1.00) |

**HyenaDNA medium (2 seeds)** — utility / r=16 bits (rank-1, exact): epoch 8: 1.92 / 0.61–0.64 (1.00, 0.30–0.40); epoch 15: 1.96 / 0.27 (1.00, 0.70–0.80); epoch 30: 2.19–2.20 / 0.17–0.18 (1.00, 0.70–0.85); epoch 50: 2.82–2.88 / 0.11–0.12 (1.00, 0.70–0.85). r=1 canaries: 1.67–1.69 at epoch 30, 1.19–1.20 at epoch 50 (rank-1 1.00).

Reading.
1. **Order holds on the real genome with real models**: at epoch 50, r=16 bits 1.60 / 0.90 / 0.58 / 0.31 for k = 3/4/5/6, exact extraction 0 / 40 / 50 / 100%, new-host recognition 90–100% for all four.
2. **Utility peaks early (epoch 15–30 for DNABERT, epoch 8 for HyenaDNA) and memorisation is already under way at the peak.** DNABERT-6 at its best utility (1.92, epoch 30) has the 16× canary at 0.99 bits with 100% recognition and 20% verbatim extraction; HyenaDNA at its best utility (1.92, epoch 8) has it at 0.64 bits with 100% recognition and 30–40% extraction. So **stopping at the utility optimum does not prevent memorisation**, which answers Erman's question directly: the trade-off is not "a little less memorisation for a little less utility"; the canaries are captured before utility starts to degrade.
3. After the utility peak, more epochs only buy more memorisation at a utility cost (HyenaDNA: utility 1.92 → 2.88, worse than before fine-tuning, while the canary goes 0.64 → 0.12).
4. HyenaDNA again memorises more and sooner than any DNABERT at equal utility (0.64 vs 1.85–2.05 bits at utility ≈ 1.92).
5. Caveat: DNABERT seed 0 only; HyenaDNA 2 seeds agree.

### 3.10 E. coli, real models, 3 seeds + DNABERT-2 (BPE) (`ecoli_s12`, `bpe_ecoli`; 19:50)

`pilot2/analyze_real.py` (1f180b3) → `outputs/dnabert_ecoli/real_report_ecoli.md` (copy `figures/real_report_ecoli.md`). DNABERT k-mer rows are now 3-seed means; the seed-0 numbers of 3.9 move by ≤ 0.03 bits. DNABERT-2 BPE: 2 seeds done (third running).

**At each model's best-utility epoch** (lowest held-out E. coli loss) — r=16 canary bits / rank-1 / exact extraction, training host:

| model | params | best epoch | utility | r=16 at best | utility at ep 50 | r=16 at ep 50 |
|---|---|---|---|---|---|---|
| DNABERT 3-mer | 86M | 30 | 1.890 | 1.95 / 0.13 / 0 | 1.919 | 1.60 / 0.88 / 0 |
| DNABERT 4-mer | 86M | 30 | 1.915 | 1.77 / 0.60 / 0 | 1.930 | 0.88 / 1.00 / 0.33 |
| DNABERT 5-mer | 87M | 30 | 1.907 | 1.70 / 0.80 / 0 | 1.935 | 0.59 / 1.00 / 0.55 |
| DNABERT 6-mer | 89M | 15 | 1.921 | 1.85 / 0.23 / 0 | 1.988 | 0.30 / 1.00 / 0.98 |
| **DNABERT-2 BPE** | 117M | 8 | 1.955 | **1.31 / 1.00 / 0** | **2.630** | **0.05 / 1.00 / 1.00** |
| HyenaDNA medium (char) | 14.24M | 8 | 1.917 | 0.62 / 1.00 / 0.35 | 2.849 | 0.12 / 1.00 / 0.77 |

Reading.
1. **BPE extends the k-mer line**: within the DNABERT family the coarser the tokenizer, the more is memorised at matched epochs (ep 15: 3/4/5/6-mer 2.02/2.00/1.97/1.85 vs BPE 0.25 bits; ep 50: 1.60/0.88/0.59/0.30 vs 0.05). At its own best-utility epoch BPE already has 100 % recognition of the 16× canary; the k-mers 13–80 %.
2. **BPE also destroys utility fastest**: held-out loss 1.95 (ep 8) → 2.63 (ep 50), worse than the untuned model's 2.74 is approached; the k-mer models stay at 1.92–1.99. The BPE model trades utility for memorisation like HyenaDNA does, the k-mer models do not (yet) at 50 epochs.
3. Caveat for the paper: DNABERT-2 has 117M parameters vs 86–89M, a different position scheme (ALiBi vs learned absolute) and non-overlapping tokens, so "BPE" here is "the BPE model", not the tokenizer alone. The from-scratch BPE arm (same backbone) is what separates the two; it is on the list.
4. HyenaDNA remains the cross-architecture exception (char-level but memorises most per unit of utility), as in 3.7/3.9.
5. The matched-floor interpolation in `dnabert_report.md` is undefined on real data (floors < 2.0); use the best-utility table instead.

### 3.11 From-scratch backbone (AR, char / 3-mer / 6-mer) on all three real datasets (`bpe_real`, toy lines; 19:53)

Same protocol as `ecoli_ar` (3.3): 5,000 real windows + canaries, 50 per tier, 2 seeds, 30 epochs, snapshots scored. Files `outputs/{ecoli,yeast,gue}_ar/trajectory.md`.

**r=16 canary bits/nt at matched held-out loss** (mean of 2 seeds; char never overfits to 2.03 on yeast / GUE within 30 epochs):

| dataset | tok | @2.03 | @2.05 | @2.10 | @2.20 | @2.40 |
|---|---|---|---|---|---|---|
| E. coli | char | 1.88 | 1.86 | 1.80 | — | — |
| E. coli | 3-mer | 1.63 | 1.58 | 1.46 | 1.21 | 0.95 |
| E. coli | 6-mer | 1.15 | 1.05 | 0.81 | 0.48 | 0.09 |
| yeast | 3-mer | 1.67 | 1.62 | 1.50 | 1.26 | 1.03 |
| yeast | 6-mer | 1.19 | 1.08 | 0.85 | 0.49 | 0.06 |
| GUE (human promoters) | 3-mer | 1.72 | 1.67 | 1.55 | 1.32 | 1.07 |
| GUE (human promoters) | 6-mer | 1.19 | 1.08 | 0.82 | 0.46 | 0.05 |

Same-epoch view, epoch 12 r=16 bits: E. coli 1.09 / 0.57 (3-mer / 6-mer), yeast 1.26 / 0.59, GUE 1.34 / 0.59; char at epoch 30: 1.77 / 1.94 / ≈1.9.

Reading: **the tokenizer effect is the same on all three real genomes, to within a few hundredths of a bit** — 6-mer > 3-mer > char at every matched floor, with the 6-mer/3-mer gap ≈ 0.5–0.65 bits at @2.10 on each. The organism (bacterium, yeast, human promoters) does not change the ordering or its size; what the data contributes is only the level of the held-out floor (E. coli 1.91, yeast 1.93, GUE 1.92 at best). This is the dataset-generality claim for the paper: one table, three genomes, one ranking.

### 3.12 DNABERT-2 (BPE) on synthetic data, 3 seeds, next to the k-mer rows (`bpe_real` GPU3; 20:18)

`outputs/dnabert/dnabert_report.md` now has the BPE rows (30 epochs, causal, same schedule as the 3/4/5/6-mer runs). r=16 canary bits / rank-1 / exact extraction, training host:

| k | epoch 15 (floor) | epoch 30 (floor) | matched @2.03, r=16 |
|---|---|---|---|
| 3 | 2.00 / 0 / 0 (2.001) | 1.99 / 0.03 / 0 (2.002) | — |
| 4 | 2.00 / 0.07 / 0 (2.002) | 1.96 / 0.37 / 0 (2.006) | — |
| 5 | 1.97 / 0.30 / 0 (2.004) | 1.86 / 0.88 / 0 (2.011) | — |
| 6 | 1.89 / 1.00 / 0 (2.009) | 1.23 / 1.00 / 0.03 (2.042) | 1.47 |
| **BPE** | **0.28 / 1.00 / 1.00** (2.063) | 0.14 / 1.00 / 0.98 (2.281) | **1.11** |

Reading: on iid synthetic DNA, where nothing but the canaries can be learned, the BPE model memorises more than the 6-mer at the same epoch and also at the same held-out floor (1.11 vs 1.47 bits at 2.03), and it is the only DNABERT that reaches verbatim extraction (100 % at epoch 15). The ordering 3 < 4 < 5 < 6 < BPE is monotone in every column. Same caveat as 3.10 (117M params, ALiBi, non-overlapping tokens).

### 3.13 DNABERT-2 (BPE) under its NATIVE masked objective on E. coli (`bpe_real` GPU3; 20:50)

One seed, 15 % token masking (DNABERT-2's own pretraining objective), PLL scoring; utility here is PLL bits/nt, not comparable to the causal floors. r=16 canary bits / rank-1 / exact extraction:

| epoch | PLL utility | r=1 train | r=4 train | r=16 train | r=16 fresh |
|---|---|---|---|---|---|
| 0 | 1.872 | 2.01 / 0 / 0 | 1.98 / 0.10 / 0 | 2.02 / 0.10 / 0 | 2.02 / 0 / 0 |
| 8 | 1.572 | 1.96 / 0 / 0 | 1.87 / 0.10 / 0 | 1.68 / 0.80 / 0 | 1.71 / 0.80 / 0 |
| 15 | 1.568 (best) | 1.94 / 0.30 / 0 | 1.71 / 0.70 / 0 | **0.70 / 1.00 / 0** | 0.74 / 1.00 / 0 |
| 30 | 1.594 | 1.72 / 0.60 / 0 | 0.95 / 1.00 / 0 | 0.05 / 1.00 / 0.30 | 0.14 / 1.00 / 0.70 |
| 50 | 1.644 | 1.47 / 0.90 / 0 | 0.38 / 1.00 / 0 | 0.02 / 1.00 / 0.30 | 0.16 / 1.00 / 0.50 |

Reading. **With non-overlapping BPE tokens the native 15 % masked objective memorises strongly** (16× canary at 0.70 bits with 100 % recognition at the utility optimum, 0.05 bits by epoch 30, verbatim extraction 30–70 %). This is the opposite of the DNABERT k-mer result under the same nominal objective (3.1: no memorisation at 15 % token masking), and the difference is exactly the overlap: masking 15 % of overlapping k-mers hides only 15 %/k of nucleotides, masking 15 % of BPE tokens hides 15 % of nucleotides. So "masked models memorise less" in the real-model family is a property of overlapping k-mer masking, not of the masked objective as such; the from-scratch grid (non-overlapping k-mers) already showed MLM memorising at a 0.5 mask rate. Verbatim extraction under MLM is lower than under causal (30 % vs 100 % at epoch 30), matching the toy-grid pattern "masked models recognise but extract less".

### 3.14 Real models on yeast and GUE (human promoters): the three-genome picture (`bpe_real`; all done 21:17)

Seed 0 only on yeast / GUE (E. coli has 3 seeds, 3.10). Reports: `outputs/dnabert_{yeast,gue}/real_report_{yeast,gue}.md` (copies in `figures/`). Causal fine-tuning, 50 epochs.

**r=16 canary bits/nt at epoch 30 and 50, training host** (rank-1 is 1.00 for every cell at epoch 50; exact extraction in brackets at epoch 50):

| model | E. coli ep30 | ep50 | yeast ep30 | ep50 | GUE ep30 | ep50 |
|---|---|---|---|---|---|---|
| DNABERT 3-mer | 1.95 | 1.60 (0) | 1.48 | 0.75 (0.70) | 1.94 | 1.54 (0.05) |
| DNABERT 4-mer | 1.77 | 0.88 (0.33) | 1.37 | 0.53 (0.85) | 1.77 | 1.00 (0.25) |
| DNABERT 5-mer | 1.70 | 0.59 (0.55) | 0.93 | 0.37 (1.00) | 1.61 | 0.50 (0.75) |
| DNABERT 6-mer | 0.99 | 0.30 (0.98) | 0.43 | 0.20 (1.00) | 0.88 | 0.30 (0.85) |
| DNABERT-2 BPE | 0.12 | 0.05 (1.00) | 0.14 | 0.06 (1.00) | 0.14 | 0.04 (1.00) |
| HyenaDNA medium | 0.17 | 0.12 (0.77) | 0.17 | 0.13 (0.70) | 0.16 | 0.11 (0.70) |

**At each model's best-utility epoch** — utility / r=16 bits / rank-1 / exact:

| model | E. coli | yeast | GUE |
|---|---|---|---|
| DNABERT 3-mer | ep30 1.890 / 1.95 / 0.13 / 0 | ep15 1.926 / 1.96 / 0.20 / 0 | ep30 1.911 / 1.94 / 0.30 / 0 |
| DNABERT 4-mer | ep30 1.915 / 1.77 / 0.60 / 0 | ep15 1.927 / 1.97 / 0.10 / 0 | ep15 1.917 / 1.99 / 0.00 / 0 |
| DNABERT 5-mer | ep30 1.907 / 1.70 / 0.80 / 0 | ep15 1.937 / 1.89 / 0.50 / 0 | ep15 1.922 / 1.94 / 0.30 / 0 |
| DNABERT 6-mer | ep15 1.921 / 1.85 / 0.23 / 0 | ep8 1.939 / 1.94 / 0.20 / 0 | ep15 1.901 / 1.83 / 0.90 / 0 |
| DNABERT-2 BPE | ep8 1.955 / 1.30 / 1.00 / 0 | ep3 1.952 / 1.92 / 0.90 / 0 | ep3 1.933 / 1.92 / 0.80 / 0 |
| HyenaDNA medium | ep8 1.917 / 0.62 / 1.00 / 0.35 | ep8 1.929 / 0.41 / 1.00 / 0.60 | ep3 1.900 / 1.95 / 0.15 / 0 |

Reading.
1. **The ordering 3 < 4 < 5 < 6 < BPE holds on all three genomes at epoch 30 and at epoch 50**, every column monotone (one tie-level exception: GUE 4-mer vs 3-mer at ep30 is 1.77 vs 1.94, still ordered). The absolute levels are close across genomes (6-mer ep50 0.30 / 0.20 / 0.30; BPE 0.05 / 0.06 / 0.04). Together with 3.11 (from-scratch backbone) this is the dataset-generality result: organism changes the held-out floor, not the ranking.
2. **"Early stopping at best utility" is not a defence, but how much it leaks depends on the model**: at the utility optimum the k-mer DNABERTs have the 16× canary at 1.83–1.99 bits with 0–90 % recognition and no extraction; DNABERT-2 BPE already 80–100 % recognition on all three genomes (and 1.30 bits on E. coli); HyenaDNA 0.41–0.62 bits with 35–60 % verbatim extraction on E. coli and yeast. On GUE HyenaDNA's utility optimum is at epoch 3, before capture (by epoch 8 it is at 0.26 bits — not shown — while utility is only 0.005 worse). So the honest statement is: the utility optimum sits on the steep part of the memorisation curve, and the margin between "best utility" and "canary captured" is a few epochs at most.
3. **After the optimum every model trades utility for memorisation**: utility at epoch 50 is worse than at the optimum by 0.03–0.06 (k-mer), 0.6–0.7 (BPE) and 0.7–0.9 bits (HyenaDNA), while the canaries go to ≤ 0.3 bits.
4. Yeast makes the k-mer models memorise a little more than E. coli / GUE at equal epochs (ep50 3-mer 0.75 vs 1.60 / 1.54), plausibly because its windows are more predictable (entropy 1.96 vs 1.98–2.00), so the model has spare capacity sooner; a point for the discussion, not a result.
5. Caveats: single seed on yeast / GUE; DNABERT-2 has more parameters; HyenaDNA utility is measured with its native head, DNABERT with a causal mask on a bidirectional encoder (its ep0 utility is 2.7–4.8, so the fine-tuning first has to repair that).

### 3.15 Downstream utility (GUE promoter detection) vs memorisation on GUE, six real models (`gue_ds`; done 04:24, 9 Oct)

`outputs/dnabert_gue_ds/real_report_gue_ds.md` (copy `figures/real_report_gue_ds.md`). Seed 0. Columns: LM utility (held-out bits/nt), linear-probe MCC, fine-tune MCC (20k rows × 2 epochs, full 5,920-row test), r=16 canary bits / rank-1 / exact.

| model | ep | LM utility | probe MCC | **ft MCC** | r=16 train |
|---|---|---|---|---|---|
| DNABERT 3-mer | 0 / 15 / 50 | 2.92 / 1.91 / 1.94 | 0.775 / 0.816 / 0.799 | 0.836 / 0.851 / 0.856 | — / 2.03 / 1.54 (1.00, 0.05) |
| DNABERT 4-mer | 0 / 15 / 50 | 2.68 / 1.92 / 1.96 | 0.766 / 0.818 / 0.813 | 0.818 / 0.839 / 0.838 | — / 1.99 / 1.00 (1.00, 0.25) |
| DNABERT 5-mer | 0 / 15 / 50 | 3.29 / 1.92 / 1.96 | 0.782 / 0.809 / 0.802 | 0.843 / 0.857 / 0.858 | — / 1.94 / 0.50 (1.00, 0.75) |
| DNABERT 6-mer | 0 / 15 / 50 | 4.45 / 1.90 / 2.01 | 0.750 / 0.821 / 0.801 | 0.833 / 0.851 / 0.852 | — / 1.83 / 0.30 (1.00, 0.85) |
| DNABERT-2 BPE | 0 / 15 / 50 | 2.74 / 1.97 / **2.61** | 0.739 / 0.779 / 0.768 | 0.810 / 0.817 / 0.826 | — / 0.27 (1.00, 1.00) / 0.04 (1.00, 1.00) |
| HyenaDNA medium | 0 / 15 / 50 | 1.95 / 1.94 / **2.81** | 0.761 / 0.797 / 0.783 | 0.803 / 0.806 / 0.814 | — / 0.23 (1.00, 0.95) / 0.11 (1.00, 0.70) |

Reading.
1. **The downstream metric is blind to memorisation.** Fine-tune MCC moves by ≤ 0.03 over 50 epochs for every model (3-mer 0.836→0.856, BPE 0.810→0.826, HyenaDNA 0.803→0.814) while the 16× canary goes from unmemorised to fully extractable and, for BPE and HyenaDNA, the LM utility collapses (1.97→2.61, 1.94→2.81). The promoter classifier re-learns what it needs during its own fine-tuning; it does not care that the backbone has memorised the training windows.
2. **Selecting the checkpoint by downstream score picks the leakiest one** for 4 of 6 models: the best fine-tune MCC is at epoch 50 for 3-mer, 5-mer, BPE and HyenaDNA, where the 16× canary is at 1.54 / 0.50 / 0.04 / 0.11 bits with 5–100 % verbatim extraction. "Best downstream" is therefore not a defence either, and it is worse than "best LM utility" (3.14), which at least stops before verbatim extraction for the k-mer models.
3. The **linear probe** is the only downstream signal that tracks the LM utility: it peaks at epoch 8–15 (0.81–0.82) and declines slightly after, but by ≤ 0.02, far too little to detect what the canaries show.
4. Levels are sane: DNABERT-2 reports ≈ 0.87 MCC on prom_300_all with the full recipe; our scaled-down probe gives 0.81–0.86 for all models, so the probe is working, not saturated at chance.
5. Caveats: seed 0; the labelled training rows come from the same file as the (unlabelled) memorisation fine-tuning windows (as in any pretrain→fine-tune pipeline); human-wide panel and yeast histone tasks are running (`ds2`).

### 3.16 The from-scratch BPE cell and the mechanism: it is token rarity, not slot counting (`night1009` phase A; 06:33, 9 Oct)

Phase A ran the BPE cell of the tokenizer axis on our own 12.9M backbone (`pilot2/bpe_arm.py`), AR,
30 epochs with snapshots, 50 canaries per tier at random offsets: synthetic and E. coli with 2 seeds,
yeast and GUE with 1. Non-embedding parameters are 12.61M, identical to the k-mer cells, and the
non-member controls stay at the held-out floor throughout with 0 % rank-1 and 0 % extraction, so the
scoring convention (token sums divided by covered nucleotides) is calibrated.

**Matched held-out loss, 16x canary, memorised bits/nt is 2 - probe bits/nt; the table shows probe bits/nt
(lower = more memorised).** Reports `outputs/{core100,ecoli_ar}/trajectory.md` (copies
`figures/bpe_trajectory.md`).

| data | tokenizer (nt/token) | @2.05 | @2.10 | @2.20 | @2.40 |
|---|---|---|---|---|---|
| E. coli | char (1.0) | 1.858 | 1.804 | — | — |
| E. coli | 3-mer (3.0) | 1.583 | 1.458 | 1.207 | 0.947 |
| E. coli | **BPE (5.0)** | **1.344** | **1.115** | **0.608** | **0.294** |
| E. coli | 6-mer (6.0) | 1.050 | 0.811 | 0.475 | 0.085 |
| synthetic | 3-mer | 1.864 | 1.757 | 1.567 | 1.235 |
| synthetic | **BPE (4.7)** | 1.445 | 1.267 | 0.629 | 0.279 |
| synthetic | 6-mer | 1.598 | 1.124 | 0.578 | 0.160 |

**1. The headline claim has to be corrected.** On a matched backbone the BPE cell sits BETWEEN the 3-mer
and the 6-mer on E. coli, at the position its mean token length (5.0 nt) predicts, and it is never below
the 6-mer. So "BPE memorises most" (3.10, 3.12, 3.14) is a property of DNABERT-2, not of BPE: that model
also has 117M instead of 86-89M parameters, ALiBi instead of learned absolute positions, and a different
pretraining corpus. The tokenizer axis is monotone in **mean token length**, and BPE is simply a tokenizer
with a token length of about 5. This is the control the paper needed and it strengthens the claim, because
the axis now has a continuous parameter rather than a four-way categorical.

**2. One new interaction.** At r=1 the BPE cell memorises LESS than the 3-mer (E. coli @2.10: 1.787 vs
1.580) while at r=16 it memorises more (1.115 vs 1.458). BPE segmentation depends on context, and with
random placement the same canary is cut differently in each host, so a single occurrence contributes to a
different token sequence each time and the evidence does not accumulate; by 16 occurrences it does. The
k-mer cells have a fixed grid (up to phase) and do not show this. Worth one paragraph: it predicts that a
BPE model leaks rare, single-occurrence records less than its token length suggests.

**3. The mechanism is token rarity, not slot counting** (`pilot2/token_info.py`,
`figures/{synthetic,ecoli}_token_info.{md,png}`). A 96-nt canary is 192 bits for every tokenizer; what
changes is the number of slots (char 96, 3-mer 32, BPE 21, 6-mer 16) and how often those tokens occur in
the rest of the corpus (4,000 ordinary windows of E. coli):

| tokenizer | slots per canary | vocab | canary-token corpus count |
|---|---|---|---|
| char | 96.0 | 7 | 287,995 |
| 3-mer | 32.0 | 67 | 6,014 |
| BPE | 20.8 | 4,096 | 400 |
| 6-mer | 16.0 | 4,099 | 47 |

If a model stored a fixed amount per slot, the per-nucleotide curves would collapse when re-expressed per
slot. They do the opposite: at @2.10, r=16, memorised bits per slot are 0.17 (char), 1.63 (3-mer), 0.86
(BPE), 7.14 (6-mer) — a 40x spread, wider than the 7x spread per nucleotide. So fewer slots is not the
explanation; coarse tokenizers store more per slot as well. What does order the four cells, on both
datasets, is the corpus count above: the canary of a 6-mer model is written in tokens that appear 47 times
elsewhere, the canary of a char model in tokens that appear 288,000 times. Storing a rare token costs
almost no interference with ordinary data; storing a frequent one means storing it in context. That is the
sentence the mechanism section should make precise, and it also explains why the effect is monotone in
token length rather than in vocabulary size (the 6-mer and BPE vocabularies are both ~4,100 but their
canary-token counts differ by 8x).

**Limitation to state.** On synthetic data the BPE cell never reaches a held-out floor below 2.084, while
the k-mer cells reach 2.00-2.03, because a 4,096-way softmax over variable-length tokens does not calibrate
to the uniform distribution with 5,000 windows; the matched-floor comparison there is only valid at
@2.10-2.40. On real data (where the distribution is learnable) BPE reaches 2.03 and the comparison is clean
over the whole grid, so E. coli is the primary panel.

### 3.17 The wider human panel: three more GUE tasks, same verdict (`ds2`; k-mer family done 06:38, 9 Oct)

Asked of the GUE fine-tuning runs at every snapshot: core promoter detection (prom_core_all, 70 nt),
transcription-factor binding (human_tf_0, 101 nt) and splice-site reconstruction (splice_reconstructed,
400 nt, 3 classes). Report `outputs/dnabert_gue_ds2/real_report_gue_wide.md`. Fine-tune MCC (20k rows,
2 epochs) in task order TF / core-promoter / splice:

| model | ep 0 | ep 8 | ep 15 | ep 30 | ep 50 | r=16 canary at ep 50 |
|---|---|---|---|---|---|---|
| DNABERT 3-mer | .650 / .628 / .767 | .675 / .642 / .792 | .647 / .636 / .795 | .654 / .640 / .794 | .642 / .636 / .797 | 1.54 bits, 100 % rank-1, 5 % exact |
| DNABERT 6-mer | .664 / .643 / .766 | .653 / .654 / .782 | .660 / .661 / .795 | .655 / .662 / .803 | .646 / .658 / .801 | 0.30 bits, 100 % rank-1, 85 % exact |

Reading.
1. **Same verdict on all four tasks.** Over 50 epochs each task moves by at most 0.04 MCC, with no
downward trend, while the 16x canary goes from unmemorised to 85 % verbatim extraction. Adding tasks does
not rescue the downstream metric as a leakage signal; the promoter result of 3.15 was not a quirk of that
one dataset.
2. **The only downstream number that moves is the linear probe on splice** (0.26 at epoch 0 to 0.41-0.43
by epoch 8-15, then flat). It moves UP: fine-tuning on E. coli-style windows improves the representation
for a task about sequence structure. So the downstream signal that is sensitive to fine-tuning is
sensitive in the wrong direction for leakage detection.
3. One degenerate cell to mention if these numbers are shown: DNABERT-6 at epoch 1 scores MCC 0.000 on
splice, i.e. that 2-epoch 3-class fine-tune collapsed onto one class. It recovers at every later snapshot
(0.78-0.80). With 2 epochs of supervised fine-tuning an occasional collapse is expected; it is not a
property of the checkpoint.

### 3.18 Real human canaries: the carrier's rare allele comes back (`night1009` phase B; 10:00, 9 Oct)

Canaries are real 96-nt haplotype segments of chr22 carrying rare 1000 Genomes variants (AC/AN <= 0.001,
<= 5 carriers; 2.07 variants each). Non-members come from the same pool, so they are equally real and
equally rare and differ only in having been in the training data. Fine-tuning on 5,420 real chr22 windows,
50 epochs, 20 canaries per tier, random placement. Each variant inside the decoded region is one trial with
three outcomes: the carrier's ALT allele, the reference base (the null), or neither. Report
`outputs/human_real/human_report.md` (copy `figures/human_report.md`).

**Epoch 50, rare-allele recovery (trials in brackets) and verbatim extraction of the 48-nt continuation:**

| model | r=16 allele | r=1 allele | non-member allele | r=16 exact | r=1 exact | r=16 bits/nt |
|---|---|---|---|---|---|---|
| DNABERT 3-mer | 0.97 (29) | 0.37 (38) | 0.21 (67) | 0.80 | 0.00 | 0.38 |
| DNABERT 4-mer | 0.86 | 0.32 | 0.19 | 0.75 | 0.00 | 0.43 |
| DNABERT 5-mer | 0.79 | 0.42 | 0.18 | 0.65 | 0.00 | 0.49 |
| DNABERT 6-mer | 1.00 | 0.34 | 0.24 | 0.85 | 0.10 | 0.29 |
| **DNABERT-2 BPE** | **1.00** | **0.82** | 0.31 | **1.00** | **0.55** | 0.04 |
| **HyenaDNA medium** | **1.00** | **0.55** | 0.27 | 0.75 | 0.05 | 0.15 |

Reading.
1. **The privacy statement the paper needs.** Give a fine-tuned model the first 48 nt of a real human
haplotype segment it was trained on and let it continue: the carrier's rare allele comes back 79-100 % of
the time for a segment seen 16 times, against 18-31 % for matched segments the model never saw. Before
fine-tuning every gap is within noise of zero, so this is not sequence predictability; it is the training
data coming back. Whole-segment recovery is 65-100 %.
2. **One occurrence is enough for the two models that memorise most.** DNABERT-2 reproduces a segment seen
ONCE verbatim 55 % of the time and returns its carrier's rare allele 82 % of the time against a 31 %
baseline; HyenaDNA 55 % allele recovery against 27 %. The k-mer family at r=1 is near its baseline
(0.32-0.42 vs 0.18-0.24) with no verbatim extraction except 6-mer at 10 %. So the single-record threat is
real but model-dependent, and it lands on exactly the two models that the earlier arms flagged.
3. **The 16x tier is saturated**, so the tokenizer ordering is not resolvable there (0.79-1.00 across the
k-mer family, all four with ~29 trials). The r=1 tier is where the models separate. The second pass
(below) raises the trials per cell to ~75.
4. **The from-scratch toy backbone is an upper bound, not a threat model.** Trained 30 epochs from random
init on the same 5,420 windows, the 12.9M BPE cell recovers every allele and extracts every segment at
r=1 and r=16 alike (1.00/1.00, 0.009 bits) while scoring 2.78 bits/nt on unseen real sequence, i.e. worse
than chance: it has memorised the corpus instead of learning it. Useful as the ceiling, useless as a model.
5. **One column of this pass is invalid and is being redone.** The ranking pool was uniform random DNA,
which any real human sequence outranks, so non-member rank-1 is 0.45-0.55 and the rank column says nothing
about membership. Fixed (163db5b) by ranking each canary against other real rare-variant segments from the
same pool, which is the matched test: can the model pick this individual's segment out of other people's.
The allele, extraction and bits columns are unaffected. Second pass `tmux human2`
(`pilot2/queue_human2.sh`) re-runs all six models with the real pool and 50 canaries per tier, plus the
toy char / 6-mer cells for the same comparison on real canaries; then `tmux seeds12b` picks up the extra
yeast / GUE seeds that were deferred at 08:45.

### 3.19 Yeast histone marks: six downstream tasks, two organisms, same verdict (`ds2` done 10:53, 9 Oct)

The yeast arm was given the two GUE histone-mark tasks of S. cerevisiae (emp_H3, emp_H3K4me3) at every
snapshot, which is the organism-matched downstream metric for a model fine-tuned on yeast windows.
Report `outputs/dnabert_yeast_ds/real_report_yeast_ds.md`. Fine-tune MCC in task order H3 / H3K4me3:

| model | ep 0 | ep 15 | ep 50 | r=16 canary at ep 50 |
|---|---|---|---|---|
| DNABERT 3-mer | .723 / .253 | .724 / .255 | .722 / .305 | 0.76 bits, 100 % rank-1, 68 % exact |
| DNABERT 6-mer | .718 / .230 | .727 / .243 | .738 / .279 | 0.21 bits, 100 % rank-1, 100 % exact |
| DNABERT-2 BPE | .746 / .000 | .707 / .292 | .737 / .286 | 0.06 bits, 100 % rank-1, 100 % exact |
| HyenaDNA medium | .684 / .229 | .678 / .231 | .693 / .255 | 0.13 bits, 100 % rank-1, 70 % exact |

Reading.
1. **Six tasks, two organisms, one answer.** Across GUE promoter detection, core-promoter detection,
transcription-factor binding, splice-site reconstruction (3.15, 3.17) and now the two yeast histone marks,
no task moves by more than about 0.05 MCC over 50 epochs, and none moves down, while every model goes from
no memorisation to 70-100 % verbatim extraction of the 16x canary. The claim "downstream performance does
not reveal memorisation" is now supported on the task families a GLM paper would actually report.
2. **Calibration of the probe.** On emp_H3 our scaled-down fine-tune reaches 0.68-0.75 MCC against about
0.78 for the published full recipe, so the probe is sound. On emp_H3K4me3 it reaches only 0.23-0.31 against
about 0.70 published: 20k rows, 2 epochs and a mean-pooled linear head are not enough for that task. The
H3K4me3 column should therefore be read as a weak probe, not as a model comparison, and the paper should
say so.
3. Two degenerate fine-tunes to mention if the raw tables are shown: DNABERT-2 at epoch 0 on H3K4me3 and
DNABERT-6 at epoch 1 on splice both score MCC 0.000, i.e. the 2-epoch head collapsed onto one class. Both
recover at every later snapshot.

### 3.20 The tokenizer axis on real human canaries, matched backbone: the character model does not leak (`human_toy`; 11:13, 9 Oct)

Same 12.9M backbone, AR, 30 epochs with snapshots, on 5,420 real chr22 windows with 50 real rare-variant
haplotype canaries per tier at random offsets, ranked against other real rare segments. Two seeds for
char / 3-mer / 6-mer, one for BPE (plus the seed-0 BPE from phase B). Reports
`outputs/human_toy/{trajectory.md,human_report.md,human_token_info.md}`.

**Trajectory, 16x canary (seed means):**

| tokenizer | best held-out loss (epoch) | canary bits there | exact there | state at epoch 30 |
|---|---|---|---|---|
| char | **1.794 (30, still falling)** | 1.612 | **0.00** | floor 1.794, canary 1.612, **0 % exact, allele gap +0.03** |
| 3-mer | 1.775 (5) | 1.667 | 0.00 | floor 3.925, canary 0.006, 100 % exact, allele 1.00 |
| 6-mer | 1.862 (5) | 1.421 | 0.00 | floor 2.347, canary 0.009, 100 % exact, allele 1.00 |
| BPE | 1.878 (5) | 0.813 | **0.14** | floor 2.681, canary 0.008, 100 % exact, allele 1.00 |

Reading.
1. **The strongest form of the result, and it is on real human data.** After 30 epochs the character model
has not begun to memorise: zero verbatim extraction at every tier and every snapshot, and the rare-allele
recovery gap against matched non-members stays within noise of zero (+0.03 at epoch 30). Over the same 30
epochs the 3-mer, 6-mer and BPE cells all reach 100 % verbatim extraction of the canary and recover the
carrier's rare allele every time, at both r=16 and r=1.
2. **And the character model is the most useful one.** Its held-out loss is still falling at epoch 30
(1.794) and is the lowest of the four at that point, while the coarse cells turn up after epoch 5-8 and end
at 2.35-3.93. So on real human sequence the fine tokenizer costs nothing in utility and removes the
leakage; this is the concrete recommendation the paper can make, measured rather than argued.
3. **Onset order is monotone in token length.** First verbatim extraction appears at epoch 5 for BPE
(14 %), epoch 8 for 6-mer (5 %), epoch 8-12 for 3-mer (2-34 %), never for char. At each model's own utility
optimum, char and 3-mer leak nothing, 6-mer nothing yet, BPE already 14 %: the coarser the tokenizer, the
earlier leakage starts relative to the point where one would stop training.
4. **Caveat to state plainly.** 30 epochs is where the coarse cells have long passed their optimum but the
character cell has not reached its own; a longer run would eventually make it memorise too (the
100-epoch RoPE runs on synthetic data showed char memorising late). The claim is therefore about matched
epochs and about the utility optimum, not about an impossibility. The character cell is also the most
expensive per window (96 token slots against 16), so the comparison is at matched data and epochs, not
matched compute; that belongs in the limitations.
5. Corpus statistics behind it, on this human corpus: the canary's tokens occur 287,916 times elsewhere for
char, 6,026 for the 3-mer and 48 for the 6-mer, the same ordering as on E. coli and synthetic data (3.16).

### 3.21 Real human canaries, second pass: corrected ranking pool and 3x the trials (`human2`; 11:20, 9 Oct)

Supersedes the numbers of 3.18. Same six pretrained models, 50 epochs on chr22, but 50 canaries per tier
instead of 20 (97 allele trials at r=16, 81 at r=1, 105 for non-members) and each canary ranked against
other real rare-variant segments instead of uniform random DNA. Report
`outputs/human_real2/human_report.md` (copy `figures/human_report_pass2.md`).

**Epoch 50. Rare-allele recovery / verbatim 48-nt extraction / rank-1 against real segments:**

| model | r=16 allele | r=1 allele | non-member allele | r=16 exact | r=1 exact | r=16 rank-1 | r=1 rank-1 | non-member rank-1 |
|---|---|---|---|---|---|---|---|---|
| DNABERT 3-mer | 0.99 | 0.27 | 0.25 | 0.96 | 0.00 | 1.00 | 0.08 | 0.00 |
| DNABERT 4-mer | 0.98 | 0.26 | 0.27 | 0.86 | 0.00 | 0.86 | 0.04 | 0.00 |
| DNABERT 5-mer | 0.88 | 0.31 | 0.22 | 0.66 | 0.00 | 0.88 | 0.08 | 0.00 |
| DNABERT 6-mer | 0.95 | 0.36 | 0.26 | 0.84 | 0.06 | 0.96 | 0.26 | 0.00 |
| **DNABERT-2 BPE** | **1.00** | **0.84** | 0.29 | **1.00** | **0.56** | 1.00 | — | 0.00 |
| **HyenaDNA medium** | 0.93 | **0.43** | 0.14 | 0.86 | 0.00 | 1.00 | — | 0.00 |

Reading.
1. **The membership signal is now clean.** With a matched real pool the non-member rank-1 rate is 0.00 for
every model (it was 0.45-0.55 against a random-DNA pool, which measured only "is this sequence real"). At
r=16 rank-1 is 0.86-1.00, at r=1 it is 0.04-0.26: membership inference on a real rare segment works when
the record repeats and barely works from one copy, except through extraction.
2. **The single-occurrence result holds with 81 trials.** DNABERT-2 recovers the carrier's rare allele for
a segment seen ONCE 84 % of the time against a 29 % baseline and reproduces it verbatim 56 % of the time;
HyenaDNA 43 % against 14 %. The k-mer family sits on its baseline (0.26-0.36 against 0.22-0.27) with no
verbatim extraction except 6 % for the 6-mer. The split is between models that memorise heavily overall
and models that do not, and it is the same split every other arm found.
3. **Timing.** DNABERT-2's single-copy leak appears late: r=1 allele recovery is 0.19 at epoch 8, 0.33 at
epoch 30 and 0.84 at epoch 50, while its 16x tier is already saturated at epoch 15. A defence based on
early stopping would have to stop before epoch 8, where the 16x tier is already at 0.75.
4. The 16x tier is saturated for all six models (0.88-1.00), so it cannot order the tokenizers; the toy
matched-backbone runs of 3.20 are where the tokenizer effect on real canaries is visible.

### 3.22 (9 Oct, after the 1:1) Erman’s blocking question, and what it really is

Erman stopped at one column of slide 7: whole-segment extraction for the 16x tier on human chr22, which
reads 96 / 86 / 66 / 84 per cent for the 3-, 4-, 5- and 6-mer DNABERT models. He expected it to rise with
k and asked for either an explanation or more runs. Three separate things are going on, and only the last
one needs GPU time.

**1. That column is the worst statistic to order models by.** It is thresholded (all 48 letters correct or
nothing), it is at the 16x tier where every model is near saturation, and it comes from 50 canaries, so one
standard error is about 7 points. The smooth statistic on the same runs is the canary score: 0.33 / 0.40 /
0.43 / 0.28 bits per letter. Still not monotone, so this is not the whole answer.

**2. On real sequence the right statistic subtracts the matched control.** A real canary is ordinary human
DNA, so part of its score is biology the model legitimately learned. `pilot2/analyze_matched.py`
(eec0e70) reports `excess = non-member bits − member bits` at the same checkpoint. On human chr22 at
epoch 50 that gives 1.46 / 1.37 / 1.39 / 1.55 bits for k = 3/4/5/6: flat, with the 6-mer highest, and the
spread (0.18 bits) is the size of the seed-to-seed noise I have not yet measured on this arm. Matched
*utility* turns out not to be available for this family: within 50 epochs these pretrained models barely
overfit on real data, so their held-out-loss ranges are 0.03 to 0.08 bits wide and do not overlap, which
also means the fixed-epoch comparison was already nearly utility-matched.

**3. The real point: the DNABERT family is not the clean tokenizer axis.** DNABERT tokenizes with
OVERLAPPING k-mers (stride 1), so a 288-nt window is 283-286 tokens whatever k is. Changing k there does
not change how many slots carry the canary; it changes the vocabulary and how much neighbouring tokens
overlap. My controlled arm uses NON-overlapping k-mers, where k really does change the slots per canary
(96 / 32 / 16) and the rarity of those slots, and there the ordering is monotone on synthetic DNA, E. coli,
yeast, GUE and human chr22 (3.16, 3.20). So the causal claim rests on the controlled arm, and the DNABERT
family answers a different, model-level question: do the published k-mer releases differ from each other.
On E. coli they come out ordered; on human chr22 they do not, and with overlapping k-mers there is no
strong reason they must. Writing it this way removes the apparent contradiction instead of explaining it
away, and it is a point I should have made two weeks ago.

**A methodological bug found while checking this.** Non-member canaries were being scored inside a
uniform-random host window while members were scored inside their real chromosome window, so the control
differed from the member in host type as well as in membership. For the 3-mer model this is large enough
to make the single-copy excess negative (−0.3 bits). Fixed in eec0e70: when canaries are real, the fresh
host is drawn from unused real windows of the same genome. This invalidates the control column of 3.18 and
3.21 and the single-copy numbers of 3.21, so the human arm is being re-run.

**Queued.** `tmux human3` (`pilot2/queue_human3.sh`), after `seeds12b`: six published models, real fresh
hosts, 50 canaries per tier, three seeds for the k-mer family and for DNABERT-2 and HyenaDNA, then
`analyze_real`, `analyze_human` and `analyze_matched`. That is the table for the paper and the answer to
Erman’s question with error bars.

### 3.23 Three seeds settle it: the published k-mer family IS ordered, and chr22 seed 0 was the outlier (`seeds12b`; 16:59, 9 Oct)

The extra seeds finished. With three seeds per cell the DNABERT family is monotone in k on every real
dataset, in both the smooth statistic and the thresholded one. Round 50, canary planted 16 times, training
host; reports `outputs/dnabert_{gue,yeast}_ds/real_report_*.md`.

| model | E. coli bits / exact (3 seeds) | yeast bits / exact (3 seeds) | GUE human promoters bits / exact (3 seeds) |
|---|---|---|---|
| DNABERT 3-mer | 1.60 / 0 % | 0.76 / 68 % | 1.53 / 5 % |
| DNABERT 4-mer | 0.88 / 33 % | 0.56 / 78 % | 1.00 / 23 % |
| DNABERT 5-mer | 0.59 / 55 % | 0.36 / 100 % | 0.51 / 68 % |
| DNABERT 6-mer | 0.30 / 98 % | 0.21 / 100 % | 0.29 / 90 % |
| DNABERT-2 BPE | 0.05 / 100 % | 0.05 / 100 % | 0.04 / 100 % |
| HyenaDNA medium | 0.12 / 77 % | 0.12 / 82 % | 0.11 / 83 % |

Reading.
1. **Monotone in k on all three datasets, in bits and in extraction.** The column Erman stopped at
(96 / 86 / 66 / 84 per cent) came from the human chr22 arm with one seed and with the host confound of
3.22; on the three datasets that now have three seeds there is no zigzag at all. So the honest answer to
his question is first that it was a single-seed artefact, and only second that the chr22 arm is the one
place where the published family might genuinely behave differently, which the re-run will show.
2. **The ordering is the same on a bacterium, a yeast and human promoter sequence**, and the absolute
levels line up within about 0.1 bits for the coarse models, which is the dataset-generality claim in its
strongest form.
3. **Two models break the k ordering from outside**, as before: DNABERT-2 memorises most of all and
HyenaDNA, which is letter-level, memorises more than the 5-mer. Both are explained by the controlled arm:
BPE has an average piece length of about five letters, and HyenaDNA differs in architecture and
pretraining, not in tokenizer.
4. Downstream scores over these same three seeds stay flat, which closes 3.15, 3.17 and 3.19: GUE promoter
0.856 / 0.838 / 0.858 / 0.852 for k = 3/4/5/6 and yeast H3 0.714 / 0.738 / 0.716 / 0.728, against canary
extraction of 5 to 100 per cent.

### 3.24 (9 Oct, 20:15) Correction: the character tokeniser delays memorisation, it does not prevent it

3.20 reported that the character cell shows no memorisation on real human canaries after 30 rounds and
concluded that fine tokenisation removes the leakage. Running the same cell to 150 rounds shows that
conclusion was wrong (`outputs/human_long`, two seeds):

| round | held-out loss | canary excess (bits/nt) | verbatim extraction |
|---|---|---|---|
| 20 | 1.774 | 0.16 | 0 % |
| 30 | 1.757 | 0.76 | 6 % |
| 50 | 3.389 | 3.69 | 68 % |
| 80 | 7.008 | 7.83 | 92 % |
| 150 | 10.209 | 11.48 | 100 % |

The character cell memorises completely; 30 rounds simply did not reach it. The claim in the
mitigation section has to change from "removes the leakage" to "delays it", with the delay quantified
against the 6-mer on the same schedule (running).

**A second, methodological point that this exposed.** The learning rate is cosine-annealed over the
*total* number of rounds, so the 150-round run is still hot at round 30 while the 30-round run has
already annealed: at round 30 the two differ (excess 0.76 against 0.19). Epoch number is therefore not
a comparable axis between runs with different schedules, which is exactly why every comparison in this
project is made at matched held-out loss. Any table that puts two differently scheduled runs in the
same epoch column is wrong, and 3.20 did that implicitly by comparing a 30-round character run with
30-round coarse runs -- that part is fine, because all four had the same schedule, but the conclusion
drawn from it over-reached.

**What survives from 3.20.** At matched held-out loss and at each cell's own utility optimum the
ordering is unchanged: at its best floor (1.757-1.794) the character cell is at 0.16-0.76 excess with
0-6 % extraction, while the 3-mer, 6-mer and BPE cells are at full extraction well before their floors
degrade that far. The useful statement is about the budget at which leakage begins, not about
immunity.

### 3.25 (10 Oct, 01:00) The objective axis on real human data, and a measurement bias that had to be removed first

Three arms finished. The second one changes the order of the mitigation recommendations and the third
forces a correction to 3.22-3.24.

**(a) Objective axis, from-scratch backbone, real human canaries, identical 30-round schedule.**
Epoch-1 excess is 0.00-0.04 for every cell, so a same-epoch comparison is sound here (a randomly
initialised model has no preference between the two canary groups; see (c) for why that matters).

| tokeniser | objective | round-30 held-out loss | round-30 excess | verbatim extraction |
|---|---|---|---|---|
| char | next-token | 1.794 | 0.28 | 0 % |
| char | masked 15 % | 1.854 | **0.02** | 0 % |
| char | masked 50 % | 1.832 | 0.04 | 0 % |
| 3-mer | next-token | 3.925 | 4.27 | **100 %** |
| 3-mer | masked 15 % | 1.717 | **0.12** | 0 % |
| 3-mer | masked 50 % | 1.667 | 0.15 | 0 % |
| 6-mer | next-token | 2.347 | 2.45 | **100 %** |
| 6-mer | masked 15 % | 1.840 | **0.16** | 0 % |
| 6-mer | masked 50 % | 1.807 | 0.29 | 0 % |
| BPE | next-token | 2.681 | 2.82 | **100 %** |

The masked cells memorise 15 to 35 times less than the same tokeniser trained next-token, reproduce
nothing verbatim at any snapshot, and reach a BETTER held-out loss (1.67-1.85 against 2.35-3.93),
because they are still improving at round 30 while the next-token cells have long passed their
optimum. Within the masked cells the dose-response of 3.2 reappears on real human data: 50 % masking
memorises more than 15 % (0.29 against 0.16 for the 6-mer).

**This reorders the mitigation section.** The objective is both the larger lever and the cheaper one:
it removes verbatim extraction outright, whereas fine tokenisation only delays it (3.24). The cost is
that a masked model cannot be sampled from, which rules it out for generative uses but not for the
embedding and classification uses that most genomic pipelines actually need. The ordering also matches
the variance decomposition, where the objective accounts for 58 % and the tokeniser for 15 %.

**(b) The released DNABERT checkpoints under their own masked objective**, at equal hidden-nucleotide
rate (5 % of nucleotides, so the comparison across k is fair), human chromosome 22, baseline-corrected
excess at round 50: \NUM{0.58} (k=6), \NUM{0.87} (k=5), \NUM{1.05} (k=4), and verbatim extraction 0 %
for k=3,4,5 and 10 % for k=6. Against the same checkpoints fine-tuned next-token (1.43-1.54 excess,
67-97 % extraction) the objective effect holds for published models on real human sequence, not only
for our backbone. One run to flag rather than interpret: DNABERT-3 destabilised between round 30 and
50 (held-out loss 1.391 to 1.933, excess turned negative), so its round-50 cell is excluded.

**(c) A measurement bias in the real-canary arm, found while checking (b).** At round 0 the pretrained
models already read the member canaries as 0.30-0.45 bits/nt easier than the non-members, before any
fine-tuning. Decomposing it: the host contributes 0.00-0.04 (the real-fresh-host fix of 3.22 works),
and the remainder is a difference between the two canary GROUPS. The cause is structural: which
canaries are members and which are controls is fixed by `--data_seed`, identical for every model and
every model seed, so an accidental difference between two sets of 50 real haplotype segments - they
differ in GC, repeat content and number of variants - does not average out. With random canaries the
offset is negligible (-0.36 to +0.11, mostly within 0.15, measured on the E. coli, yeast and GUE arms),
which is why this only surfaced on real canaries, and it is zero for from-scratch models at round 1
because an untrained model has no preference.

`pilot2/analyze_matched.py` now subtracts each cell's own round-0 excess (`--raw` keeps the old
behaviour) and prints the offsets it removed. Consequence for the chromosome-22 result: after
correction the four released k-mer checkpoints are **1.54 / 1.46 / 1.43 / 1.52** at r=16, i.e. flat,
and the single-copy column (0.03 / 0.47 / 0.38 / 0.02) is noise. The earlier reading that the 6-mer
was highest on chr22 (3.22, 3.24) was largely its own +0.21 offset, so **no ordering is resolvable on
chromosome 22 for the released family**. The three random-canary datasets of 3.23 are unaffected and
their monotone ordering stands. The proper fix for future runs is to vary `--data_seed` across runs so
the split is re-drawn; the round-0 subtraction is the correction available for the runs we have.

### 3.26 (10 Oct, 01:15) Re-drawing the canary split, and the two paper sections that had to change

**(a) The split re-draw is running** (tmux `dseed`, `pilot2/queue_dseed.sh`, GPUs 0/2/3, about 3.5 h).
3.25(c) left the member/non-member group offset handled by subtracting each cell's round-0 value,
which is a correction rather than a measurement. This arm re-draws the split instead: the six released
models on chromosome 22, the `queue_human3.sh` configuration unchanged apart from `--data_seed`
(2345 / 3456 / 4567, one model seed each, one root per split because run directory names do not
encode the data seed). With `human_real3` (data_seed 1234) that gives four independent draws, so the
chromosome-22 reading can be stated with an across-split spread. `analyze_matched` accepts several
roots and treats same-named cells as repeats, which is the averaging wanted here.

**(b) The chromosome-22 reading, stated carefully.** Two readings exist and they disagree, so the
paper now says so explicitly rather than picking one:

| | k=3 | k=4 | k=5 | k=6 | comment |
|---|---|---|---|---|---|
| excess at equal exposure (round 50) | 1.54 | 1.46 | 1.43 | 1.52 | flat, within seed noise |
| excess at matched held-out loss | 1.54 | 1.16 | 1.15 | 1.26 | inverted: k=3 highest |
| held-out loss at round 50 | 1.664 | 1.704 | 1.726 | 1.728 | k=3 overfits slowest |
| verbatim extraction at round 50 | 97 % | 86 % | 67 % | 85 % | not monotone |

The two disagree because the 3-mer is the slowest to overfit, so its round-50 checkpoint sits at a
better held-out loss than the others'. Worse, on chromosome 22 the six models' overfitting branches
overlap in a window only 0.01 bits/nt wide (1.655-1.664), and restricting the analysis to the four
k-mer models does not widen it, because the bound comes from the 3-mer never reaching the others'
loss within 50 rounds. So any matched comparison on this dataset is fragile. **Conclusion unchanged
from 3.25: no tokeniser ordering is resolvable on chromosome 22**, and the paper rests the ordering
claim on the three datasets where the comparison is well conditioned.

**(c) Sections updated.** `08_mitigation.tex` now leads with the objective and demotes the tokeniser
to second, with the numbers filled in from 3.24-3.25 and the mitigation table's first two rows
written out: objective = extraction 100 % to 0 %, excess 15-35x lower, no utility cost but no
sampling; tokeniser = about 10x delay in rounds, 100 % to 30 % extraction at matched held-out loss,
6x the token slots. The 150-round delay is now quantified rather than left as a TODO: at matched
held-out loss of 2.4 bits/nt the 6-mer extracts 100 % and the character cell 30 %, and the character
cell only reaches 100 % at round 150 where its held-out loss has degraded to 10.2 bits/nt (seeds 0
and 1: excess 11.48 and 11.79, extraction 1.00 and 1.00). `05_published.tex` has the chromosome-22
paragraph rewritten to (b) plus a new paragraph stating the group-offset correction and pointing at
the re-draw; `07_human.tex` has the excess column corrected (1.54 / 1.46 / 1.43 / 1.52 / 2.27 / 2.33)
and a caption note that recovery and extraction are read against the control column and need no such
correction.

**(d) Objective-axis table, current seed counts.** 3-mer and 6-mer cells have both seeds; the BPE
next-token cell and the two character masked cells still have one, because the character masked runs
take about 2 h 20 each on the shared GPU and seed 1 is still going. The numbers in 3.25(a) are seed
means over what has finished and move by at most a few hundredths when the second seed lands.

**(e) The email to the co-authors** now carries the objective result and the
chromosome-22 correction, because Erman asked about exactly that column this morning and the honest
answer has three parts: wrong statistic, wrong axis, and a measurement bias.

### 3.27 (10 Oct, 02:10) Second queue: finishing the objective x tokeniser grid, and a reusable analyser

**(a) `pilot2/analyze_objaxis.py` (new, committed).** The table in 3.25(a) was produced by a throwaway
script. It is now a module: one row per (tokeniser, objective) cell at the end of a shared schedule,
with the across-seed range, the seed count and the epoch-1 excess, which must be ~0 for a from-scratch
backbone and is the group offset of 3.25(c) otherwise. It identifies the dataset from each run's
`args.json` rather than from the directory the run sits in, which is the mistake `token_info` made in
3.21. Re-running it reproduces 3.25(a) exactly and shows the seed ranges are tight: the excess range
across seeds is 0.01-0.02 for every cell that has two seeds, and the held-out loss range 0.002-0.03.

**(b) `pilot2/queue_1010a.sh` (launched, tmux `q1010a`).** Three holes in that grid, all cheap to fill
because these cells take 1-17 minutes each (79 s for the 6-mer, 155 s for the 3-mer, 1013 s for the
character cell, which pays for its 96 token slots):

1. **no 4-mer or 5-mer on human.** The tokeniser axis has five points on synthetic data and three on
   real human canaries, so the ordering claim on human data rests on three points. Adding both under
   all three objectives: 18 runs.
2. **two seeds where every other table has three.** Seed 2 for every existing cell: 6 runs.
3. **the BPE next-token cell has one seed**, because its seed-0 run was never launched. Seeds 0 and 2:
   2 runs. Masked BPE stays out by design -- with right-padding a bidirectional objective can attend
   through the pads (`pilot2/bpe_arm.py`), so that cell would not measure what it appears to, and this
   is stated as a scope limit rather than silently left blank.

Plus one symmetry fix: the 150-round delay claim of 3.24 has two seeds for the character cell and one
for the 6-mer reference, so the 6-mer seed 1 is queued (1 run). Every cell uses the `queue_human_toy`
/ `queue_1009b` argument string unchanged, so new cells are comparable with the old ones, and the
queue blocks on `Q1009B_DONE` (GPU 1) and `DSEED_DONE` (GPUs 0/2/3) so it never contends with the
running arms.

**(c) Monitoring.** Two watchers are armed: one for `DSEED_DONE` and one for `Q1010A_DONE`, both of
which also break out early on `Traceback`, `CUDA out of memory` or `Killed` in any of the arm's run
logs. The split re-draw is on pace -- all three splits finished $k{=}3$ at 01:44, so six models at
about 30 min each puts `DSEED_DONE` near 04:15 and `Q1010A_DONE` an hour or so after.

### 3.28 (10 Oct, 05:00) The split re-draw: the epoch-0 correction of 3.25(c) is wrong, and chromosome 22 stays unordered

`DSEED_DONE` at 04:17, 18 runs, no failures. Four independent draws of the member/non-member canary
split on chromosome 22: data_seed 1234 (three model seeds, the `human_real3` arm) and 2345 / 3456 /
4567 (one model seed each).

**(a) The epoch-0 subtraction does not survive its own test.** 3.25(c) found a 0.30-0.45 bits/nt
offset between the two canary groups at round 0 and prescribed subtracting it. With four draws the
prescription is refutable, and it is refuted three ways:

| | raw across-draw sd | baseline-corrected sd | r(offset, raw) | regression slope |
|---|---|---|---|---|
| DNABERT 3-mer | 0.07 | 0.24 | -0.60 | |
| DNABERT 4-mer | 0.07 | 0.15 | -0.15 | |
| DNABERT 5-mer | 0.06 | 0.17 | +0.80 | |
| DNABERT 6-mer | 0.04 | 0.39 | +0.39 | 0.055 |
| DNABERT-2 BPE | 0.06 | 0.08 | +0.62 | |
| HyenaDNA | 0.11 | 0.10 | +0.43 | |

(epoch-50 excess at r=16; the slope is cov/var of round-50 excess on round-0 offset.)

1. **The offset is gone after one epoch.** Excess at round 1 is 0.00 +- 0.05 for every model on every
   draw, although the round-0 offsets on those same runs range from -0.48 to +0.88. A real difference
   in group difficulty would persist; this does not.
2. **It barely propagates.** Regressing each draw's round-50 excess on its own round-0 offset gives a
   slope of 0.055 at r=16 and 0.19 at r=1, so subtracting the offset in full over-corrects by 5-20x.
3. **And that shows up as variance.** The raw statistic is 2-10x more stable across draws than the
   corrected one for the five models whose offsets are large; for HyenaDNA, whose offsets are ~0, the
   two agree, which is the control this argument needs.

What the round-0 reading actually measures is the instability of a pretrained model's prior over two
sets of real haplotypes. Note which models have it: +-0.9 for the four masked-pretrained DNABERTs,
+-0.09 for HyenaDNA, the only causal-pretrained model in the panel, and these are scored causally. So
`pilot2/analyze_matched.py` now reports the **raw** excess by default, keeps `--baseline` to reproduce
the subtraction, still prints the offsets as a diagnostic, and adds the across-run spread to the
trajectory table (across splits when several roots are given). Committed with the measurement in the
docstring, so the next reader does not have to rediscover it.

**(b) Chromosome 22 stays unordered, now with four draws behind it.** Raw excess at r=16:

| reading | k=3 | k=4 | k=5 | k=6 | DNABERT-2 | HyenaDNA |
|---|---|---|---|---|---|---|
| equal exposure, round 50 | 1.45 +-0.07 | 1.51 +-0.07 | 1.50 +-0.06 | 1.68 +-0.04 | 2.35 +-0.06 | 2.39 +-0.11 |
| matched held-out loss | 1.48 | 1.06 | 1.01 | 1.37 | 1.47 | 1.50 |
| verbatim extraction (r=50) | 94 % | 87 % | 78 % | 88 % | 100 % | 82 % |
| single copy, round 50 | 0.38 +-0.12 | 0.44 +-0.15 | 0.48 +-0.14 | 0.75 +-0.10 | 2.18 +-0.09 | 1.62 +-0.14 |

Equal exposure rises weakly with $k$ and separates $k=6$ from $k=3$; matched held-out loss reverses
the direction and puts $k=3$ highest. They disagree because the 3-mer overfits chromosome 22 most
slowly, so matching the loss hands it the most exposure to the planted records: its round-50 loss is
1.612 where the 6-mer is at 1.689, and the six rising branches overlap in a window 0.005 bits/nt wide
(1.624-1.629), which leaves no room to prefer one normalisation. **So no tokeniser ordering is
claimed on chromosome 22** -- unchanged from 3.25/3.26, but now with an error bar instead of a single
draw. What is robust there: DNABERT-2 and HyenaDNA sit above the whole k-mer family under both
readings and on every draw, as on the other three datasets, and the single-copy tier is the sharpest
separation of the three (0.38-0.48 for k=3,4,5 against 0.75 for k=6 and 2.18 for BPE).

Also worth recording: the recovery numbers reproduce across draws within 0.05 (3-mer at r=16: alt
1.00 on draw 1234 against 0.83-0.93 on the new draws; DNABERT-2 single copy: 0.86 against 0.84), so
Table 4 of the paper needed only its excess column and its extraction column updated to four-draw
means, which is done.

**(c) `05_published.tex` and `07_human.tex` rewritten** to this: the chromosome-22 paragraph now
states both normalisations and the refusal to order, a second paragraph states the four-draw
refutation of the epoch-0 correction, and the human table carries four-draw means with the
across-draw spread as the error bar.

### 3.29 (10 Oct, 04:35) The 5-mer does not exist on our backbone, and what GPU 2 is doing instead

Six cells of `queue_1010a` failed within a minute of starting:
`AssertionError: (288, 5)` from `pilot2/tokenizers.py`. Not a bug: non-overlapping k-mers need
`window % k == 0`, and the window is 288 nt, so our backbone admits k in {1,2,3,4,6,8,9,12} and never
5. DNABERT's 5-mer is unaffected because its k-mers overlap at stride 1, which is the same distinction
that explains Erman's non-monotone column (3.19, 3.26). **The tokeniser axis on our backbone is
therefore char / 3-mer / 4-mer / 6-mer plus BPE**, four k-mer points on human rather than the five I
wrote in 3.27, and the 150-round and seed-2 cells of that queue are unaffected. `queue_1010a.sh` is
still running, so its 5-mer lines will be replaced when it finishes rather than edited underneath a
running shell.

That freed GPU 2, which is now on `queue_1010b.sh` (tmux `q1010b`, about 3 h): the two gaps in the
E. coli arm, which is the second real genome behind the objective claim. The masked cells there have
one model seed where the next-token cells have two, so all six get a second seed (char ~60 min, 3-mer
~8, 6-mer ~3), and the 4-mer is missing on both objectives, so it is added at two seeds. Each root's
existing arguments are copied verbatim -- they differ between the two roots (the next-token arm scores
snapshots with 50 canaries per tier and a 500-sequence ranking pool, the masked arm does neither and
uses 40 and 300) -- because the point is to put an error bar on numbers already in the log, which a
re-run under different settings would not do.

### 3.30 (10 Oct, 06:20) E. coli confirms the objective axis on a second genome; yeast and GUE queued to finish the set

`Q1010B_DONE` at 06:16, 12 runs, no failures: the E. coli masked cells now have two model seeds and
the 4-mer exists on both objectives. With the analyser fixed (below), the E. coli grid at round 30,
canary planted 16x, two seeds each:

| tokeniser | next-token | | masked 15 % | | masked 50 % | |
|---|---|---|---|---|---|---|
| | excess | extraction | excess | extraction | excess | extraction |
| char | 0.49 | 0 % | **-0.01** | 0 % | **-0.01** | 0 % |
| 3-mer | 4.41 | 100 % | **-0.01** | 0 % | **0.00** | 0 % |
| 4-mer | 3.35 | 100 % | **0.02** | 0 % | **0.00** | 0 % |
| 6-mer | 2.62 | 100 % | **0.06** | 0 % | **0.12** | 0 % |

Held-out loss for the masked cells is 1.86-1.97 against 2.13-4.14 for next-token, so again the masked
model is both the less memorising and the better model at the same budget. On E. coli the masked
excess is at the noise floor -- the across-seed ranges are 0.01-0.03 wide and three of the eight cells
sit at or below zero -- which is a stronger statement than on human (0.02-0.29) and makes the claim
dataset-general rather than human-specific. The dose-response survives only for the 6-mer
(0.06 to 0.12), consistent with the mask rate being the second-order dial.

**Analyser fix that this table depended on.** `analyze_objaxis` read only `scores_ep*.json`, and the
masked arms are run without `--score_snapshots`, so they write `scores_final.json` only: every masked
row was silently missing from the first E. coli table. Each run now contributes at most one value per
epoch, so a run that has both `scores_ep30` and `scores_final` is not counted twice. The preamble now
also says how to read the table: **down a tokeniser's rows, never across tokenisers**, because at a
fixed round the tokenisers sit at held-out losses more than a bit/nt apart (E. coli next-token: 2.13
for char against 4.14 for the 3-mer), which confounds the excess. The tokeniser axis is read at
matched held-out loss, and nothing in this table should be used for it -- the apparent ordering
char < 6-mer < 4-mer < 3-mer in the next-token column is an overfitting ordering, not a tokeniser one.

**`queue_1010c.sh` launched (tmux `q1010c`, GPUs 0 and 3, about 2.5 h).** The objective claim should
hold on every dataset in the paper, and it was measured on three of five: synthetic, E. coli and human
have both objectives, yeast and GUE have next-token only. This queue adds their masked cells (two mask
rates, two seeds) and the 4-mer on both objectives, so all four real datasets share the
char / 3-mer / 4-mer / 6-mer axis. Cheap tokenisers run first, so if it has to be cut short the
unfinished cell is the character one.

Still on GPU 1: the two character masked cells at seed 2 for the human grid, then the human 4-mer.
Character cells are slow for a structural reason worth recording -- PLL scoring is one forward pass
per masked position, so it costs 288 passes per probe for the character tokeniser against 96 for the
3-mer and 48 for the 6-mer, and the snapshot schedule multiplies that by eight.

### 3.31 (10 Oct, 09:40) Five datasets agree on the objective, and the masked column gives the tokeniser axis for free

`Q1010C_DONE` at 09:33, 28 runs, no failures. Yeast and GUE now have masked cells and the 4-mer, so
every dataset in the paper carries both objectives on the same four-point tokeniser axis. Round 30,
canary planted 16x, two seeds, masked at 50 %:

| dataset | objective | char | 3-mer | 4-mer | 6-mer |
|---|---|---|---|---|---|
| E. coli | next-token | 0.49 (0 %) | 4.41 (100 %) | 3.35 (100 %) | 2.62 (100 %) |
| | masked 50 % | -0.01 (0 %) | 0.00 (0 %) | 0.00 (0 %) | 0.12 (0 %) |
| yeast | next-token | 0.15 (0 %) | 4.08 (100 %) | 3.36 (100 %) | 2.60 (100 %) |
| | masked 50 % | 0.00 (0 %) | 0.02 (0 %) | 0.03 (0 %) | 0.20 (0 %) |
| GUE promoters | next-token | 0.13 (0 %) | 4.05 (100 %) | 3.25 (100 %) | 2.53 (100 %) |
| | masked 50 % | 0.00 (0 %) | -0.00 (0 %) | 0.02 (0 %) | 0.23 (0 %) |
| human chr22 | next-token | 0.31 (0 %) | 4.24 (100 %) | — | 2.45 (100 %) |
| | masked 50 % | 0.03 (0 %) | 0.15 (0 %) | 0.23 (0 %) | 0.29 (0 %) |

**The objective result is now the most dataset-general claim in the paper**: across five datasets,
every masked cell reproduces 0 % of the planted records at every checkpoint and sits at excess <= 0.3,
while every coarse-tokeniser next-token cell reproduces 100 % at excess 2.5-4.4 -- and the masked
cells reach the better held-out loss (1.90-1.97 against 2.0-4.4) on the same budget.

**A second result that fell out of it.** Under next-token training at a fixed round the four
tokenisers sit at held-out losses 2.0-4.4, so their excess values are not comparable without the
matched-utility interpolation, which is the trap flagged in 3.30. Under masked training they all
converge to 1.90-1.97 on the same budget -- a spread of 0.05-0.09 within a dataset -- so **the masked
column is already matched**, and in it memorisation is monotone in token length on all four real
datasets: the 6-mer is the leakiest masked cell everywhere (0.12-0.29), the character cell the
tightest (-0.01 to 0.03). The mask-rate dose-response appears only where there is something to dose
(6-mer 0.12 to 0.23 between 15 % and 50 %; nothing resolvable for char). So the two levers compose
the way the variance decomposition says: the objective decides whether records are reproduced at all,
the tokeniser decides how much is memorised either way.

Paper: `04_controlled.tex` gains Table~\ref{tab:objaxis} (the table above) and a paragraph on the
masked column as a matched comparison; `08_mitigation.tex` states the five-dataset claim; `main.tex`
loads `multirow` for the table. Three cells of that table are still TODO -- the human 4-mer
next-token cell is on GPU 1 and the synthetic row is `queue_1010d` (tmux `q1010d`, six runs, the
cheapest cells in the project: the synthetic arm was the only one still missing the 4-mer, and the
mechanism section leans on it most).

Grid status after this: 5 datasets x {next-token, masked 15 %, masked 50 %} x {char, 3-mer, 4-mer,
6-mer} x 2-3 seeds, plus BPE under next-token on human and synthetic, plus the released-model panel
on four datasets with four canary splits on chr22. The grid is complete; what remains is writing.

### 3.32 (10 Oct, 10:50) Grid complete: both remaining queues done, two scripts corrected, Table 2 filled

`Q1010D_DONE` 09:48 (6 runs), `Q1010A_DONE` 10:45 (the GPU-1 branch: the two slow character masked
cells at seed 2, then the human 4-mer at three seeds). No failures beyond the 5-mer cells of 3.29.

**The grid as it now stands.** 5 datasets x {next-token, masked 15 %, masked 50 %} x
{char, 3-mer, 4-mer, 6-mer} x 2-3 seeds, plus BPE under next-token on human and synthetic, plus the
released-model panel (4 k-mer checkpoints + DNABERT-2 + HyenaDNA) on 4 datasets with 4 canary splits
on chromosome 22, plus the 150-round character and 6-mer runs for the delay claim, plus the GUE and
yeast-histone downstream panels. Nothing in the claim-to-evidence map (18) is now unsupported.

Human cells completed overnight: 4-mer next-token 3.23 (100 % extraction) at held-out loss 3.051,
4-mer masked 0.16 / 0.23 at 1.729 / 1.688, and seed 2 for all three character cells, which moved
nothing (char next-token 0.31 across three seeds, range 0.27-0.36). Synthetic 4-mer: next-token 3.34
(100 %), masked 0.03 / 0.11. Both rows of Table~\ref{tab:objaxis} are filled, and with them the
statement that the ordering by token length holds in the masked column on **all five** datasets.

**Two corrections to the scripts, made only after the queues exited** -- editing a file that a running
`bash` is still reading is how a run gets corrupted, which is why these waited:

1. `queue_1010a.sh` asked for 5-mer cells that cannot exist (3.29). The dead lines are replaced by the
   explanation, so the script is a correct record of what was run.
2. `queue_1010d.sh` sent the synthetic masked cells to `outputs/core_mlm`, and `core_mlm` turns out to
   be a duplicate of `core_all`'s masked cells -- identical files, identical md5s -- so passing both
   roots to `analyze_objaxis` counted every synthetic masked cell twice (the first synthetic table
   printed "4 seeds" for cells that have two). The new cells were copied into `core_all`, the script
   and the analysis now use that root alone, and the table was regenerated. Worth remembering as a
   pattern: `analyze_matched` and `analyze_objaxis` treat same-named cells in different roots as
   repeats, which is what the chromosome-22 split re-draw needs and exactly wrong for a duplicated
   root.

**Our backbone at matched held-out loss on human** (`human_obj_matched.md`, the AR cells; the masked
cells and the character cell do not overfit into the common range, which is itself the point): at
held-out loss 2.19, verbatim extraction is 39 % (3-mer), 37 % (4-mer), 75 % (BPE) and 88 % (6-mer),
so the thresholded statistic orders by token length on real human sequence. The smooth statistic at
the same point is 1.91 / 2.03 / 2.14 / 2.17, monotone but tight. This is the human counterpart of
Table~\ref{tab:controlled-matched} and should go in the appendix if the page budget bites.

### 3.33 (10 Oct, afternoon) The body is drafted end to end, and it is twice the page budget

With the grid complete the paper is the work, so every section now has prose instead of a plan. What
changed, what it cost, and what has to happen next.

**Sections written from measured numbers.**

| section | state | notes |
|---|---|---|
| 00 abstract | written, 229 words | the claim ladder: objective, tokeniser, utility blindness, real haplotypes |
| 01 introduction | written, 939 words | contributions renumbered to six; the stale "character tokeniser removes the leakage" claim is gone |
| 02 related | written | one TODO left, the two unverified 2026 infilling references |
| 03 setup | unchanged | one TODO, the schematic figure |
| 04 controlled | two paragraphs added | variance decomposition, placement flip, parametrisation sensitivity, above-capacity regime |
| 05 published | done earlier today | four-split chr22 reading |
| 06 utility | rewritten | the early-stopping claim is now correct (below) |
| 07 human | rewritten | four-split pooled recovery numbers |
| 08 mitigation | completed | the mitigation table has no empty cells left |
| 09 discussion | written | limitations now include the parametrisation sensitivity and the chr22 non-ordering |

**A claim that had to be corrected while writing 06.** The draft said "stopping at the best held-out
loss does not help". The data say something more precise and more useful: at its own loss optimum
every released model except the 3-mer extracts **0%** of the planted records, so stopping exactly
there does work --- and the optimum is a knife edge. Moving one snapshot costs HyenaDNA 0.004 bits of
held-out loss and takes it from 0% to 69% extraction; the corresponding gaps are 0.032 to 100% for
DNABERT-2, 0.039 to 51% for the 4-mer, 0.046 to 84% for the 5-mer and 0.111 to 95% for the 6-mer. A
validation loss five hundredths of a bit from optimal is what anyone would call converged. And the
optimum is not clean on the other rulers: recognition there is already 4% (4-mer), 28% (5-mer), 52%
(3-mer), 80% (DNABERT-2) and 88% (6-mer). **Stopping at the optimum suppresses what the model writes,
not what it knows.**

**The downstream claim also needed fixing.** "No task moves by more than 0.05 MCC and none moves
down" is false. Four of six tasks move by at most 0.037 in either direction; splice sites move up by
0.02-0.15 and H3K4me3 by 0.03-0.11 --- upward as leakage grows, so they actively mislead --- and TF
binding drifts down for three models by up to 0.036. Best-downstream selection picks 44-100%
extraction for five of six models, not four. Four of the 252 (model, round, task) fine-tuning runs
collapsed to a degenerate head and are excluded and listed; that is the only exclusion in the paper.

**New analyser:** `pilot2/analyze_downstream.py` (committed) pulls every score file's downstream
block into one table per model --- each task's fine-tuned and frozen-probe MCC beside the canary of
the same checkpoint --- plus the summary of what each stopping rule would select. The variance
decomposition was also recomputed on the finished grid: with the 4-mer added it is objective 67.1%,
tokeniser 12.0%, interaction 21.0%, seed 0.0% (24 runs); restricted to the three tokenisers the
fixed-placement arm also has, it reproduces the recorded 57.7 / 15.4 / 26.9 / 0.0 exactly, against
59.5 / 25.7 / 14.0 / 0.8 for fixed placement. Within the masked cells alone the tokeniser explains
97.8% of what is left, and within the next-token cells 100%.

**The problem: length.** The body is 8103 words excluding comments, which is about 12.5 pages of
10 pt text before any float, and there are seven tables and four planned figures on top of that. The
limit is 10 pages including everything. So the draft is roughly twice the budget.

The lever is the call's own rule: the appendix is a **separate PDF with no page limit**, and
reviewers may skip it. Nothing has to be deleted, only moved. Planned cut, section by section:
introduction 939 -> 600, related 510 -> 320, setup 531 -> 420, controlled 1505 -> 850 (the
parametrisation and capacity paragraphs go to the appendix as three sentences plus a pointer),
published 738 -> 480 (the group-offset argument moves), utility 1045 -> 600 (the per-model downstream
panels move; keep the stopping table), human 978 -> 700 (the headline novelty, cut least), mitigation
983 -> 700, discussion 645 -> 400. That lands near 5300 words, about 8 pages with floats, which
leaves room for two figures rather than four.

**Open question for the collaborators, not for the data:** the Overleaf project is now shared with
Erman and Alex, so the editing surface is there while these files are local. Either the files get
uploaded to Overleaf as a batch, or Overleaf's Git/GitHub sync is pointed at a repository, before
anyone else starts editing; otherwise the two copies diverge within a day.

### 3.34 (11 Oct) Verifying two references turned into a new control, four figures, and the cut to length

**(a) The references were wrong, two of three.** Checked against the local PDFs rather than from
memory:

| as filed | actually |
|---|---|
| "Memorization in Diffusion Language Models", Luo and others | **Characterizing Memorization in Diffusion Language Models: Generalized Extraction and Sampling Effects**, Luo, Yu, Li, Bjerva (Aalborg), arXiv:2603.02333 |
| "...by Infilling", Wang and Asokan | **...via Infilling**, Yihan Wang, N. Asokan (Waterloo/KTH), arXiv:2605.24173 |
| "Memorization Dynamics and the Fisher Information Metric", **Simon** von Arx | **Memorization Dynamics of Fill-in-the-Middle Pretraining**, **Tobias** von Arx and Tanguy Dieudonne (ETH), ICML 2026 workshop, arXiv:2605.22981 |

Morris (full eight-author list, arXiv:2505.24832) and Jagielski (an arXiv note, not a conference
paper) were corrected the same way. VERIFY flags: 5 -> 2 (the BCB proceedings version of Nemecek,
and the Nucleotide Transformer volume/pages).

von Arx and Dieudonne is the text analogue of our objective axis -- matched Llama 3.2 models,
fill-in-the-middle against left-to-right, with infilling recovering short or partial spans and
left-to-right the long exact ones -- so it is independent support, now cited in Sec. 2.

**(b) Wang and Asokan found a hole in our strongest claim, and the control closes it.** Their
result: prefix-only probing understates extraction from models that denoise arbitrary positions, by
up to 3x on LLaDA-8B and Dream-7B. Our extraction ruler is prefix-conditioned -- for a masked cell
`extract_prefix` masks everything after the revealed prefix -- so "masked training reproduces
nothing" had been shown only in the geometry that suits an autoregressive model. That is the first
question a reviewer who knows this literature would ask.

So `score.py` gained `extract_infill` (the host after the record stays visible; the 48 masked
nucleotides are decoded in confidence order, which is the stronger attack) and `infill_audit.py`
re-runs both protocols from the saved `final.pt`, writing to new files so nothing is overwritten.
**Result: the claim holds.** 120 cells -- five datasets, four tokenisers, two mask rates, two to
three seeds, three tiers, 20 canaries each -- give 0 % under both protocols, with 34.9 wrong
nucleotides out of 48 under the prefix protocol and 35.2 under infilling, against 35.0-35.6 for
non-members. The leakiest masked cell in the paper (human 6-mer at 50 % masking, excess 0.29) is at
the non-member level under the protocol designed to break it.

**(c) Four figures, built from the score files** (`pilot2/figures_paper.py`, PDF + PNG):
F1 the objective x tokeniser grid on all five datasets, with a second row replotting the masked
cells on their own scale so the surviving tokeniser ordering is visible -- **this replaced the wide
five-dataset table**; F2 the mechanism in three panels (per nucleotide, per slot, and memorisation
against canary-token corpus count, which orders every cell including BPE); F3 the variance
decomposition with the placement flip; F4 the 150-round delay and what it costs in held-out loss.

**(d) The cut.** Main text went from 8701 words to 6805 (5565 prose + 1240 inside floats), which is
about 10.6 pages against the 10-page limit including everything -- close enough that the Overleaf
compile decides it. Two passes: whole blocks moved into the appendix (parametrisation and capacity,
the placement decomposition, the per-model downstream panels, the infilling audit detail, the
four-draw argument), then a concision rewrite of every section. The appendix now has nine sections
built from the moved text rather than placeholders, and every `Appendix~A*` reference in the main
text resolves. Zero TODOs left in the main sections.

One judgement to record: the rule I used for what may move is the call's own -- reviewers may skip
the appendix, so it holds how things were done and the per-seed numbers, never the only evidence
for a claim. What stayed: the five-dataset objective result (now Fig. 1), the chromosome-22 four-draw
reading, the early-stopping margins, the human recovery table.

### 3.35 (11 Oct, 02:30) The 150-round arm closes the audit gap: the tokeniser ordering is now matched-utility on all five datasets

`Q1010E_DONE` at 02:27, 30 runs, no failures. The gap 3.32 found was that the tokeniser claim could
only be made at matched held-out loss on E. coli and human, because on synthetic, yeast and GUE the
30-round cells had no common overfitting band. At 150 rounds they do, and the band is 0.13-0.15
bits/nt wide instead of 0.005. Verbatim extraction of the 16x canary at the most-overfit shared
point:

| tokeniser | nt/token | synthetic | E. coli | yeast | GUE | human chr22 |
|---|---|---|---|---|---|---|
| character | 1.0 | 8 % | 0 % | 6 % | 5 % | — |
| 3-mer | 3.0 | 27 % | 0 % | 40 % | 33 % | 47 % |
| 4-mer | 4.0 | 88 % | 1 % | 93 % | 86 % | 53 % |
| BPE-4096 | 5.0 | 99 % | 28 % | 100 % | 99 % | 86 % |
| 6-mer | 6.0 | 100 % | 53 % | 100 % | 100 % | 100 % |

Monotone in nucleotides per token in every column, and BPE lands with the 6-mer rather than above
it, which is the control that separates the tokeniser from the model (DNABERT-2 memorises more than
any released k-mer checkpoint, and that is the model, not the tokeniser). The character cell never
reaches the common range on chromosome 22, which is itself the delay result of 3.24 seen from
another angle. This replaces the E. coli-only matched table in the paper.

**Two repairs to the draft, both found by auditing rather than by reading.** The concision pass of
3.34 extracted floats by searching for a label, and the fig:objaxis caption happens to contain the
string `tab:controlled-matched`; the extractor therefore returned the figure for the table, so
Sec. 4 ended up with the figure twice and no table at all, while four references to it still
pointed nowhere. Fixed, and the replacement table is the five-dataset one above. A reference audit
then showed `tab:human` and `tab:mitigation` had lost their in-text references in the same pass;
both are back. Every float now has exactly one label and at least one reference, and the main text
has no TODO left.

Final state of the main text: 6946 words, of which 5599 are prose and the rest inside the three
figures and five tables; estimated 10.6 pages against a 10-page limit, which is close enough that
the Overleaf compile decides it rather than my estimate.

### 3.36 (11 Oct, 02:50) The four robustness arms a reviewer will ask for, all launched

A asks whether a planted record is needed at all, B adds a second chromosome, C answers the
matched-compute objection, D tests whether the ordering is a small-model artefact. Three queues,
chained so nothing contends: `q1011a` (C and D) runs now, `q1011b` (B) has already fetched its data
and waits for the GPUs, `q1011c` (A) waits for B.

**C -- matched compute (`outputs/ecoli_mc`).** Every comparison so far is at matched data and
matched rounds, and a character model processes 288 token slots per window where the 6-mer processes
48. Here the round count is set so each cell processes the same number of token slots as the 6-mer at
30 rounds (30 x 5000 x 48 = 7.2M): char 5 rounds, 3-mer 15, 4-mer 20, 6-mer 30. Each cell's wall
clock is in its `train_summary`, so the same runs also answer the harsher version of the question --
attention is quadratic in the slot count, so equal slots is not equal seconds.

**D -- scale (`outputs/ecoli_big`).** The grid repeated at $d{=}768$, 8 layers, 12 heads: 59.9M
parameters, 56.7M non-embedding, 4.5x the backbone the paper uses and within a factor of two of
DNABERT. `run_pilot` gained `--d_model/--n_layers/--n_heads` for it (defaults unchanged). Next-token
at two seeds, masked at one, because PLL scoring is one forward pass per masked position.

**B -- a second chromosome (`outputs/human_chr21`).** hg38 chr21 (46 MB) and the 1000 Genomes
phase-3 GRCh38 phased VCF for chr21 (180 MB) are downloaded, from the same release as the chr22
files. Canaries are built by the same filter, then the released-model panel runs with two seeds for
the four $k$-mer checkpoints and one for DNABERT-2 and HyenaDNA.

**A -- natural duplicates, and what the smoke test changed about it.** The plan was to hash the
training corpus for 96-nt blocks it repeats by itself, score them with the paper's rulers and
compare against single-occurrence blocks: memorisation without anything planted. Two measurements
reshaped the design before any GPU time was spent.

1. **E. coli has no exact 96-nt repeats at all.** 85,000 distinct blocks across 5,000 windows,
   every one of them unique. The bacterium is simply not repetitive at this length, so the
   experiment cannot be run there.
2. **At 5,000 windows the control is already fully memorised.** Single-occurrence blocks come back
   at 100 % verbatim extraction and 0.002-0.03 bits/nt for the $k$-mer cells. With 5,000 windows and
   30 rounds the model has stored its training set wholesale, so "duplicated against not duplicated"
   has no contrast to measure. This is worth recording on its own: the planted-canary design is not
   a convenience, it is what makes the question answerable at a corpus size where everything fits.

Both are fixed by the corpus. Chromosome 22 at 60,000 windows (17 Mb) holds 2,235 blocks that occur
twice, 1,245 three or four times, 717 five to eight and 68 nine or more, and at that size the model
is far enough above capacity that it cannot store everything. So `q1011c` trains the four tokenisers
on 60,000 chr22 windows and then scores the natural duplicates. The planted canaries stay in the
training set, so the two populations can be read against each other directly: a block the corpus
repeats nine times against a record we inserted sixteen times.

New code, committed: `pilot2/natural_dups.py` (duplicate census + scoring from `final.pt`),
`--d_model/--n_layers/--n_heads` in `run_pilot`, and the three queue scripts.

### 3.37 (11 Oct, 07:30) All four robustness arms landed, and A needed a second control before it meant anything

275 minutes for the three queues, no failures.

**A -- memorisation with nothing planted.** On 60,000 chromosome-22 windows, scoring the 96-nt
blocks the corpus repeats by itself. The first pass looked like a clean win and was not yet an
argument: natural duplicates came back at 85-98 % verbatim against 15-38 % for single-occurrence
blocks, but a block chr22 repeats nine times is usually a transposable element, so a model may
complete it because the family is predictable rather than because it saw those copies. The control
is the same logic the planted canaries use: hash 60,000 windows of the same genome the run never
trained on, keep the blocks that repeat there and occur zero times in training, score them
identically.

| tokeniser | x1 trained / held out | x2 trained / held out | x3-4 trained / held out | x5-8 trained / held out |
|---|---|---|---|---|
| char | 3 % / 0 % | 63 % / 23 % | 83 % / 50 % | 97 % / 73 % |
| 3-mer | 23 % / 0 % | 87 % / 10 % | 97 % / 27 % | 100 % / 60 % |
| 4-mer | 23 % / 3 % | 87 % / 10 % | 100 % / 27 % | 97 % / 57 % |
| 6-mer | 30 % / 0 % | 93 % / 23 % | 100 % / 23 % | 100 % / 43 % |

(verbatim extraction, 30 blocks per cell.) Three readings. **Repetition in training is what the
rulers capture**: a block present twice is reproduced 63-93 % when trained on and 10-23 % when an
equally repetitive block of the same families was not. **Two copies of real sequence are enough** --
the planted 16x tier is not where this starts. And the **held-out column inverts the ordering**: on
repeats it has never seen, the character model completes more than the coarse ones (73 % against
43 % at multiplicity 5-8), so coarse tokenisers memorise more without generalising better. Worth
keeping: the predictability confound is real and large (held-out x5-8 reaches 43-73 %), so the first
pass would have overstated the effect by that much.

**D -- scale.** The E. coli grid on a 59.9M backbone (56.7M non-embedding, 4.5x ours, within a
factor of two of DNABERT) reproduces both findings. Matched held-out loss, r=16: excess 1.06
(char, 0 % extraction), 2.01 (3-mer, 5 %), 2.04 (4-mer, 51 %), 2.51 (6-mer, 100 %). Objective axis:
next-token excess 2.36-5.17 with 100 % extraction (char 0 %), masked -0.01 to 0.04 with **0 %
extraction in every cell**. The ordering is not a small-model artefact.

**C -- matched compute.** Round counts set so every cell consumes the same 8.71M supervised tokens
(char 5 rounds, 3-mer 15, 4-mer 20, 6-mer 30 -- the budget matched to three decimal places). At
matched held-out loss the order is unchanged: 1.32 (3-mer, 0 %), 1.45 (4-mer, 5 %), 1.96 (6-mer,
76 %), with the character cell never overfitting into the shared range. The wall clock is the
surprise: under that budget char is the **cheapest** (14 s against 35 s) because it takes six times
fewer optimiser steps. At this scale the GPU is step-bound, not FLOP-bound, so this would reverse at
longer windows where attention dominates -- stated that way in the paper rather than claimed as a
free lunch.

**B -- chromosome 21.** 400 canaries, 365 carriers, 2.23 variants each, two seeds for the k-mer
family. Rare-allele recovery at r=16 is 0.84-1.00 against a 0.23-0.29 control; DNABERT-2 again leaks
a record seen **once** (77 % of its rare alleles against 27 % control, 44 % of segments verbatim)
while no k-mer checkpoint extracts a single-copy record. And the anomaly reproduces: extraction at
r=16 is 79, 68, 48, 91 % for k=3,4,5,6 -- the same non-monotone shape with the same 5-mer dip as
chromosome 22. An artefact of one chromosome would not survive the change of chromosome.

**Into the paper.** Section 4 gains the natural-duplicate paragraph with Table 3 (two multiplicities
in the main text, the full table in Appendix A10) and a compact scale-and-compute paragraph; Section
5 gains the chromosome-21 paragraph; the limitations list loses three bullets that are now answered
rather than conceded. The variance figure moved to Appendix A4 and the mechanism figure stayed, which
is the right split: the mechanism panel is evidence, the variance bars are four numbers already in
the text.

**One repair.** The float-moving script matched `\begin{figure}...fig:variance...\end{figure}`
non-greedily from the FIRST figure in the file, so it swallowed the objective figure, the variance
decomposition paragraph and the placement paragraph along with the figure it was supposed to move.
Caught by the label/reference audit (fig:objaxis had a reference and no label), repaired, and the
audit is now part of the routine after any structural edit: every float must have exactly one label
and at least one reference.

Main text after all of it: 7505 words, 6068 of them prose, three figures and six tables, which
estimates to 10.6-11.5 pages depending on the words-per-page assumption. That has to be settled by a
compile rather than by arithmetic.

### 3.38 (11 Oct, 20:40) Reading the predecessor properly: it has four models, not nine, and its Evo result is a question we can answer

Adding the Nucleotide Transformer meant reading Nemecek et al. closely, which turned up two things.

**(a) A factual error in our draft.** We wrote "nine published genomic models". The paper evaluates
**four**: SimpleDNALM (12.9M, full fine-tune, character-level), DNABERT-2 (117M, full, BPE),
HyenaDNA (14.2M, full, single-nucleotide) and **Evo (7B, StripedHyena, LoRA, byte-level)**, on four
datasets. Corrected in the introduction and in related work. Worth recording separately: **our
controlled backbone is their SimpleDNALM**, which is why the two sets of numbers are comparable at
all, and we now say so.

**(b) Their headline result looks like a contradiction of ours.** Evo is the leakiest model in that
panel by a distance -- 100 % canary extraction on all three real genomes even at a *single*
insertion, where DNABERT-2 resists extraction entirely. Evo is byte-level, which is the finest
tokenisation there is, and our grid says fine tokenisation memorises least. Their own reading is
that the pretrained parameters already hold the distribution so a low-rank update has nothing to
learn except the examples. But Evo differs from the rest of their panel in scale, architecture,
tokenisation, objective AND fine-tuning strategy at once, so that reading is a hypothesis.

**The experiment that separates one of those five (`queue_1011d`).** Same backbone throughout:
pretrain on 60,000 chromosome-21 windows (giving our backbone what every released model has and ours
never had), then fine-tune on chromosome 22 with the planted canaries, once with all parameters and
once with a LoRA adapter of rank 8 on qkv/proj/ff1/ff2 -- the analogue of the
["Wqkv", "dense", "gated_layers", "wo"] set used for Evo -- everything else identical. RoPE
throughout, because the default blocks' fused in-projection is a Parameter and cannot be adapted.

First cell (character tokeniser, seed 0), both trajectories, canary planted 16x:

| | full ft | | LoRA r=8 | |
|---|---|---|---|---|
| round | held-out loss | excess (exact) | held-out loss | excess (exact) |
| 1 | 1.608 | 0.41 (0 %) | 1.605 | 0.11 (0 %) |
| 3 | 1.624 | 1.38 (82 %) | 1.601 | 0.24 (0 %) |
| 8 | 1.994 | 2.19 (98 %) | 1.608 | 0.55 (10 %) |
| 12 | 3.141 | 3.65 (92 %) | 1.617 | 0.82 (16 %) |
| 30 | 7.843 | 8.76 (100 %) | 1.652 | 1.22 (48 %) |

The two ranges overlap at 1.60-1.65, so the matched comparison is available. **At matched held-out
loss the full fine-tune memorises MORE, not less**: at 1.617 it is at about 1.16 excess and ~52 %
extraction against LoRA's 0.82 and 16 %; at 1.638, about 1.45 and ~87 % against 1.13 and 36 %. LoRA
also never extracts a single-copy canary at any round (r=1 exact 0 % throughout) where the full
fine-tune reaches 96 % by round 30 -- at a held-out loss of 7.84, which is useless.

So on a matched backbone **LoRA reduces memorisation at matched utility but does not prevent it**
(48 % of 16x canaries by round 30, at a perfectly good held-out loss of 1.65). Two consequences. The
predecessor's conclusion survives in its weaker form -- parameter-efficient fine-tuning is not a
defence -- and we can say why with a measurement rather than a hypothesis. But LoRA cannot be the
explanation for Evo being the leakiest model in that panel, because here it is the *protective*
direction. That leaves scale, architecture and pretraining corpus, and our own above-capacity result
(3.x) points at scale: a 7B model fine-tuned on a small corpus has capacity to spare.

A second thing this arm gives us for free: our backbone now has a pretrain-then-fine-tune setup, so
its numbers sit on the same footing as the released checkpoints rather than being from-scratch runs.

### 3.39 (12 Oct, 02:30) NT and Evo both land, and NT finds the hole in our headline claim

**(a) NT 250M runs, and it is the released model that sits on our axis.** Its vocabulary is the 4096
NON-overlapping 6-mers -- our 6-mer cell with 250M pretrained parameters behind it, 48 tokens per
288-nt window for both. Masked objective only: the released code multiplies its embeddings by the
attention mask, so the causal mask we give DNABERT is rejected, and that is the checkpoint's limit
rather than our choice.

**(b) And it breaks "a masked objective reproduces nothing".** The trajectory, canary planted 16x:

| | E. coli | | human chr22 | |
|---|---|---|---|---|
| round | held-out loss | excess (extraction) | held-out loss | excess (extraction) |
| 3 (optimum) | 1.823 | 0.01 (0 %) | 1.376 | 0.29 (0 %) |
| 8 | 1.826 | 0.31 (0 %) | 1.382 | 0.51 (**8 %**) |
| 15 | 1.851 | 1.62 (4 %) | 1.411 | 0.80 (6 %) |
| 30 | 2.004 | 2.11 (20 %) | 1.501 | 1.39 (12 %) |
| 50 | 2.263 | 2.37 (**28 %**) | 1.632 | 1.77 (**18 %**) |

At its utility optimum NT extracts 0 %, which is our claim and survives. Past it the claim does not:
a masked 250M model reaches 18-28 % verbatim extraction, and on human the knife edge is as thin as
it is for next-token training -- **0.006 bits/nt past the optimum is already 8 % extraction**.

Our own masked cells report 0 % at every checkpoint, but they were stopped at 30 rounds with their
held-out loss still improving: **they never entered the overfitting regime at all**, so "0 % at
every snapshot" was a statement about the budget, not about the objective. `queue_1011h` pushes the
3-mer and 6-mer masked cells to 150 rounds on human to settle which it is.

This is the kill shot a reviewer would have had, and it is better found now. It also makes the
paper's two recommendations the same shape, which is a better story than the one we had: **both
levers delay rather than prevent**, the objective by far the more, and neither is immunity. The
early-stopping finding of Sec. 6 now covers masked models too, which previously it did not.

**(c) Evo 1 (7B) runs under our rulers, and memorises nothing in 10 rounds.** E. coli, LoRA r=8 in
the predecessor's configuration, 4.4 h on one 4090:

| round | held-out loss | r=16 canary bits/nt | rank-1 | extraction |
|---|---|---|---|---|
| 0 | 1.704 | 2.13 | 5 % | 0 % |
| 1 | 1.517 | 2.10 | 5 % | 0 % |
| 10 | 1.425 | 2.10 | 5 % | 0 % |

The model learns the corpus -- held-out loss falls 1.70 to 1.43, and 1.70 before any fine-tuning is
already far better than our 12.9M backbone ever reaches -- while the planted canaries sit at chance
(2.0 for random DNA) at every tier and every round, with rank-1 at the 1 % chance level of a
100-candidate pool.

That is the opposite of the predecessor, which reports 100 % extraction on E. coli at a single
insertion. The difference is protocol, and the candidates are testable: 10 rounds against their 25;
our strict all-48-nucleotides greedy criterion against their beam search over 1000 candidates; and
our canaries sitting at an independently drawn offset inside a longer host window against theirs
being the training example. `queue_1011g` runs two cells at their corpus size and round count
(1000 windows, 25 rounds) differing only in canary placement -- the variable our own grid already
shows is worth 59.5 % against 15.4 % of the attributed variance.

Also recorded: Evo's held-out loss on human chromosome 22 before fine-tuning is **2.096, worse than
chance**. Evo 1 was trained on prokaryotic genomes, so human sequence is out of domain for it, and
any human-chromosome number from it has to be read that way.

**(d) Three walls cleared to get Evo running**, all without touching the shared environment:
transformers 4.29 is too old for the remote code (4.44 side-loaded with `--no-deps`, leaving the
env's torch 2.1.1 and numpy 1.24 alone); flash-attn is required and the wheel pinned in
`requirements_evo.txt` is cu11, which will not load against cu121 torch (2.5.8+cu122torch2.1 does,
and its kernel runs on a 4090); and StripedHyena compiles Triton kernels, which want `libcuda.so`
beside the `libcuda.so.1` that ldconfig reports -- Ubuntu 18.04 ships only the latter, so `evo.py`
points Triton at CUDA's own stub rather than adding a symlink to a system directory other people
share. Two more for the rulers: peft's `CAUSAL_LM` task type calls forward with `inputs_embeds`,
which StripedHyena does not accept, and `rank_probe` scores a whole candidate pool in one forward --
2.8 GiB of FFT workspace at 4096 channels -- so the wrapper chunks the batch.

**(e) Docker, checked rather than assumed.** `docker` 24.0.2 is installed, we are in the docker
group, nvidia-container-toolkit is present, `--gpus all` shows both cards, and glibc inside a
container is 2.35 against the host's 2.27. So the glibc wall that blocks Evo 2's
`transformer_engine >= 2.0` does come down in a container. The driver does not: 530.30.02 caps CUDA
at 12.1, and an RTX 4090 is a GeForce card, which CUDA forward compatibility does not cover. Evo 2
therefore needs a driver upgrade as well as a container, and that is a decision for whoever owns a
shared machine, not for us.

**(f) One near-miss worth recording.** The two new Evo cells were about to write into the finished
run's directory, because the run name carried only model, dataset and seed. Caught by reading the
directory listing before the first snapshot landed; the finished scores were preserved, the name now
carries epochs, corpus size and offset mode, and the adapter is saved at the end so a finished run
can be re-examined.

### 3.40 (12 Oct, 18:40) The budget explanation is dead, the three rulers come apart, and 3.39(b) was half wrong

**This entry corrects 3.39(b).** Last night I wrote that both levers "delay rather than prevent" and
that our masked cells' 0 % was "a statement about the budget, not about the objective". The first
half of that is now refuted for our own backbone, by the very run I queued to test it.

**(a) `queue_1011h`: five times the budget, total recognition, still nothing emitted.** The 3-mer and
6-mer masked cells on human chromosome 22, pushed from 30 rounds to 150:

| | 3-mer | | | | 6-mer | | | |
|---|---|---|---|---|---|---|---|---|
| round | floor | r=16 bits | r=16 rank-1 | exact | floor | r=16 bits | r=16 rank-1 | exact |
| 30 | 1.675 | 1.641 | 0.04 | 0 % | 1.828 | 1.655 | 0.10 | 0 % |
| 50 | 1.645 | 1.233 | 0.22 | 0 % | 1.845 | 1.301 | 0.28 | 0 % |
| 80 | 1.718 | 0.509 | 0.70 | 0 % | 1.947 | 0.688 | 0.90 | 0 % |
| 110 | 1.897 | 0.216 | 0.90 | 0 % | 2.074 | 0.313 | **1.00** | 0 % |
| 150 | 2.074 | 0.116 | 0.98 | 0 % | 2.176 | 0.140 | **1.00** | 0 % |

Both cells end well past their utility optimum and past the 2.000 chance level, so they are deep in
the overfitting regime the 30-round runs never reached. By the surprise ruler they have the canaries
almost exactly (0.12-0.14 bits/nt against a 2.000 chance level). By the recognition ruler the 6-mer
cell is at **rank-1 = 1.00 at every tier from round 110, including r=1** -- it picks a record it saw
**once** out of a hundred candidates, every time. **Verbatim extraction is 0.00 in all 30 cells**,
and the greedy reconstruction stays 30-34 of 48 nucleotides wrong, which is barely better than the
chance level of 36 and barely better than the same decode on a window the model never trained on.

So the budget explanation is dead, and what replaces it is better: **the three rulers dissociate**. A
masked model can store a record well enough to recognise a single copy of it with certainty and
still never emit it. That is not "memorises less"; it is memorisation of a different kind, and it is
exactly the distinction the paper's three rulers were built to make. This is the strongest result we
have for the objective axis.

**(b) But NT still extracts, and that is the real open question.** The Nucleotide Transformer at 250M
runs the same masked objective through **our own extraction code** and reaches 28 % on E. coli and
18 % on human. Two things follow. First, **the scorer is not broken** -- the same code path does
produce exact matches, which is the internal control the 0 % above needs, and the objection a
reviewer would have raised. Second, a masked model *can* be made to emit records, so the dissociation
in (a) is not a property of the objective alone.

It is also not a threshold in surprise: NT extracts 12 % at 0.285 bits/nt on human where our 3-mer
extracts 0 % at 0.116, i.e. **our cell is the more memorised of the two by the surprise ruler and
still emits nothing**. NT differs from our backbone in exactly two ways -- 250M parameters against
12.6M, and a pretrained prior -- and it cannot separate them.

**(c) `queue_1012a` separates them**, and it is the run that decides how the paper's headline is
phrased: 150 rounds at 59.9M and 201M from scratch, a causal cell beside every masked one (without
it a reviewer answers "everything extracts at 201M" and we could not contradict them), then masked
chromosome-21 pretraining feeding the same chromosome-22 fine-tune. Launched 18:41, all four cards,
about 6 s/round at 201M.

**(d) `queue_1011g`: Evo at the predecessor's configuration, both canary placements, still nothing.**
1000 windows and 25 rounds, the two cells differing only in where the canary sits in its host window:

| | floor ep1 -> ep25 | r=16 bits ep1 -> ep25 | r=16 rank-1 | exact |
|---|---|---|---|---|
| random offset | 1.590 -> 1.468 | 2.102 -> 2.075 | 0.00 | 0 % |
| fixed offset | 1.590 -> 1.473 | 2.112 -> **2.015** | 0.00 -> 0.15 | 0 % |

Placement moves the signal in the expected direction and nowhere near far enough. What matters more
is that **Evo's canary surprise never leaves the 2.0 chance level and its held-out loss plateaus by
round 10**, which rules out the explanation I thought most likely: if there is no signal at all, then
no extraction criterion, however lax, can recover anything, so "their beam search over 1000
candidates against our strict all-48 greedy" cannot be the difference. That leaves one untested
protocol difference -- in the predecessor the canary **is** the training example, where ours is
embedded inside a longer host window and is a fraction of that example's supervised tokens.

**(e) A caveat Evo's human numbers need.** On chromosome 22 its held-out loss starts at 2.096, worse
than chance, and reaches 1.855 by round 10, and at r=16 the canary surprise does fall to 1.780 with
rank-1 0.20. But its greedy decode **degenerates**: the mean longest single-nucleotide run in the
48-nt reconstruction is 35-43 of 48 at rounds 5-10, i.e. it emits homopolymer. Evo 1 is prokaryotic
and human is out of domain for it, and any human extraction number from it has to carry that.

**(f) Two cells that said "done" and had not run.** `queue_1011e`'s GUE cell died after round 1 (I
killed it to free a card for Evo) and both its 500M cells died immediately: the guard tested for
`config.json`, which the interrupted download had already written, while the weights had not arrived.
Both queues logged "done" regardless of exit status. `queue_1012b` re-runs the GUE cell, resumes the
500M download from the partial file still in the hub cache, and guards on the weights; both new
scripts record the exit status, which is how the two false lines got in.

### 3.41 (12 Oct, 19:40) The masked 0 % was partly our decoder, the mechanism is now measured, and scale alone does not turn extraction on

**This entry corrects 3.40 twice and is the most consequential thing found today.** An adversarial
audit of the draft asked whether the 0 % could be an artefact of how we decode, and named one
decode that had never been run. It was right to ask.

**(a) The conditional each ruler uses, which we had never separated.** `rank_probe` normalises
bits/nt over all 96 nucleotides of a canary and `extract_prefix` hands the attacker the first 48 of
them, so a low canary surprise can sit beside a hopeless reconstruction purely because half the
scored span was given away. `pilot2/recon_audit.py` measures the quantity extraction has to invert
instead: the teacher-forced surprise of the 48 TARGET nucleotides given the revealed 48, and the
fraction of decoding steps whose argmax is the true token.

**(b) And a decode neither shipped protocol performs.** Both mask the whole 8-16-token target block
at once, which is far outside the 15 % iid masking of training, while surprise and recognition read
a conditional with ONE token masked. Iterated conditional modes re-masks one target token at a time
and sweeps to a fixed point: in distribution, and the strongest attack available to someone holding
only the flanking sequence. On the 150-round chromosome-22 cells, 25 probes per tier:

| cell | tier | target bits/nt | per-step top-1 | prefix | edge-infill | **ICM** |
|---|---|---|---|---|---|---|
| 6-mer masked, 150 r | r=16 | 0.851 | 0.41 | 0 % | 0 % | **12 %** |
| 6-mer masked, 150 r | r=1 | 1.219 | 0.23 | 0 % | 0 % | 0 % |
| 6-mer masked, 150 r | r=0 control | 2.454 | 0.02 | 0 % | 0 % | 0 % |
| 3-mer masked, 150 r | r=16 | 1.296 | 0.31 | 0 % | 0 % | 0 % |
| next-token, 150 r, same data | r=16 | **0.000** | **1.00** | **100 %** | n/a | n/a |
| next-token, 150 r | r=0 control | 3.55 | 0.03 | 0 % | n/a | n/a |

**So "a masked objective reproduces nothing" is false, and it is our own backbone that falsifies it,
not only NT.** Three of 25 canaries come back verbatim from a cell that the two published protocols
call clean, with the non-member control at 0 % under the same decoder and its Hamming distance
moving the wrong way (34.8 against 33.9), so the gain is not decoder luck.

**(c) The mechanism, which is the part that makes this a better paper.** A next-token model at 150
rounds has the target half at **0.000 bits/nt with the true token top-1 at every single step** --- no
decoder cleverness is needed, which is why every causal cell reads 100 %. A masked model holds the
record too (0.85 against 2.45 for the matched control) but its per-step accuracy is 0.41, and
all-48-exact needs every step at once. That is where the tokeniser enters: **the 6-mer target is 8
decoding steps and the 3-mer target is 16**, at 0.41 against 0.31 per step, which is an exponential
difference in the joint and explains why the finer tokeniser never emits even when it stores as
much. The tokeniser axis and the extraction ruler are now connected by a measured quantity rather
than by the token-rarity hypothesis alone (3.16).

**(d) Scale alone does not turn masked extraction on.** `queue_1012a` stage 1, 150 rounds on
chromosome 22, from scratch:

| backbone | 3-mer r=16 target / top-1 / ICM | 6-mer r=16 target / top-1 / ICM |
|---|---|---|
| 12.6M | 1.296 / 0.31 / 0 % | 0.851 / 0.41 / **12 %** |
| 59.9M | 1.044 / 0.44 / 0 % | 1.237 / 0.19 / 0 % |
| 201M | 1.365 / 0.32 / 0 % | 1.862 / 0.03 / 0 % |

Sixteen times the parameters changes nothing, and the 201M cell holds the target half *less* than
the 12.6M one. So the Nucleotide Transformer's 18-28 % is unlikely to be a parameter count, which
leaves the pretrained prior --- stage 2 of the same queue, masked chromosome-21 pretraining feeding
the same fine-tune, now the decisive half. Caveat to settle with the floors: a 201M model at 150
rounds may simply sit at a different point on its own trajectory, so this is read at matched rounds
and not yet at matched overfitting.

**(e) Two corrections to 3.40, both mine.** (1) I wrote "0.12 bits/nt against a 2.000-bit chance
level" for the chromosome-22 cells. **Wrong**: those canaries are real haplotype segments from
`canaries_chr22.npz`, so 2.000 is the loss of a uniform predictor and not chance, and part of a real
canary's score is biology the model legitimately learned. The paper's own rule is excess against a
matched non-member control, and on that footing (`pilot2/prefix_vs_pll.py`) our 150-round cells
carry excess 1.57 (3-mer) and 1.89 (6-mer) at r=16 against NT's 1.19 --- the direction of the claim
survives, the arithmetic behind it did not. Raw bits are also not comparable between models whose
held-out floors differ (NT 1.632, ours 2.176). (2) I wrote that our Evo canary "is a fraction of
that example's supervised tokens" where the predecessor's is the whole example. **Also wrong, and
backwards**: their 64-nt canary is 12.5 % of a 512-token left-padded row and ours is 96 of 288 nt,
i.e. 33 %. The real differences are that the rest of their row is zero-entropy padding rather than
real genome competing for capacity, that every repetition is byte-identical and position-locked to
the window end, and that their loss ignores the padding (`ignore_index=pad_token_id`) so all of the
gradient is on the canary. The experiment must be written about identical position-locked
repetitions, not about token fractions, and it must ignore PAD in the loss or a drop in memorisation
would have a second explanation.

**(f) Three latent faults found before they cost anything.** `pilot2/infill_audit.py` rebuilt the
backbone with the default 512/4/8 geometry and its run-name pattern could not match the `_ft` names
`--init_from` produces, so the audit of `queue_1012a` --- both its 59.9M/201M arm and its
pretrained-prior arm, the arm that decides the paper's wording --- would have died or silently
skipped every cell. Its r=0 control also used a hardcoded offset 96 rather than `score_run`'s own
fresh draw, so it was not phase-matched. All three are fixed in `recon_audit.py`; `infill_audit.py`
itself is left alone until `queue_1012a` finishes, because that queue is mid-flight and every one of
its cells has to be scored by the same code.

**(g) Running now.** `queue_1012c` re-asks the whole masked grid (92 cells, five datasets, four
tokenisers, two mask rates, saved checkpoints, no training) with all three decoders, on card 0.
`queue_1012a` is in its causal wave, then the prior arm. `queue_1012b` holds for cards. Deferred
until nothing is in flight, because they touch files those queues import: the `--canary_alone`
flag for the Evo replication, and ICM on NT itself, which needs an NT fine-tune that saves its
weights since the released-checkpoint runs did not.

### 3.42 (12 Oct, 23:00) The masked 0 % is an attack-strength artefact: the record is there, and extraction rises monotonically with search budget

**(a) First, the grid survives.** `queue_1012c` re-asked every masked cell with a saved checkpoint
under all three decoders: **544 cells, 408 member rows, and exactly ONE extracts anything** --- the
150-round 6-mer cell at r=16. Five datasets, four tokenisers, two mask rates, two or three seeds,
and the 59.9M and 201M scale cells are all 0 % under prefix, edge-conditioned infilling and ICM
alike. So the paper's table is not wrong; it is incomplete in one place.

**(b) But my mechanism was wrong, and the right one changes the claim.** I reported the
prefix-conditional per-step top-1 rate as a ceiling. ICM beat it by two orders of magnitude (0.010
against 0.12), because ICM conditions on the suffix and on the other target tokens while a
prefix bound assumes left-to-right. The predictor that matches the decoder is **leave-one-out**:
every other target token held at its true value, one masked --- exactly the conditional the PLL
scorer reads and the one ICM converges to. At 150 rounds on chromosome 22:

| cell | tier | LOO bits/nt | LOO per-token top-1 | ceiling | prefix | ICM (1 restart) |
|---|---|---|---|---|---|---|
| 6-mer | r=16 | 0.134 | **0.97** | 0.84 | 0 % | 12 % |
| 6-mer | r=1 | 0.271 | 0.89 | 0.50 | 0 % | 0 % |
| 3-mer | r=16 | 0.116 | **0.96** | 0.72 | 0 % | 0 % |
| 6-mer | r=0 control | 2.490 | 0.02 | 0.000 | 0 % | 0 % |

**Given seven of its eight target tokens, the model names the eighth correctly 97 times in a
hundred.** The record is not partially retained, it is essentially present. So the 0 % was never an
information limit --- it is a **search** limit: one descent from one initialisation lands on the
wrong fixed point.

**(c) And the search gap closes as you spend on it.** `extract_icm --restarts` adds random
admissible starts beside the published joint-argmax one, sweeps each to a fixed point, and outputs
the one with the best **pseudo-log-likelihood** --- a quantity an attacker computes without the
answer, so this stays an attack and not an oracle. 6-mer, 150 rounds, 25 probes per tier:

| restarts | r=16 exact | r=1 exact | mean wrong nt (r=16) | oracle = attack? |
|---|---|---|---|---|
| 1 | 12 % | 0 % | 26.4 | yes |
| 2 | 16 % | 0 % | 24.0 | yes |
| 4 | 20 % | 0 % | 20.8 | yes |
| 8 | 20 % | **4 %** | 21.0 | yes |
| 16 | 24 % | 4 % | 18.8 | yes |
| 32 | **40 %** | 4 % | **12.9** | yes |

Monotone, steepening rather than flattening, and at 32 restarts it is halfway to the 0.84 ceiling
with the mean reconstruction down to 12.9 wrong nucleotides of 48 from the prefix protocol's 30.0. The non-member control stays at 0 % at
every budget, so this is not decoder noise. The truth-free selection picks the correct fixed point
whenever one exists, so the attacker needs no oracle. And at eight restarts **a canary inserted
exactly ONCE comes back verbatim from a masked model** that both published protocols call clean.

**The consequence for the paper is unavoidable: our 0 % measured the strength of our attack, and any
extraction number we publish for a masked model is a lower bound set by the compute we spent on it.**
The claim has to become quantitative --- how much work recovery takes --- rather than categorical.

**(d) The tokeniser now enters as search difficulty rather than as storage.** The 3-mer cell holds
just as much (LOO 0.96 per token, 0.116 bits/nt, ceiling 0.72) and yet eight restarts recover
nothing, and so does the oracle over those eight. Its target is **16 joint slots against the
6-mer's 8**. Under a masked objective the two tokenisers store the same record and differ only in
how hard it is to assemble --- which is a sharper statement than "finer tokenisation memorises
less", and a different one.

**(e) The objective contrast at 59.9M and 201M, for the record.** `queue_1012a` stage 1, 150 rounds,
same data and canaries:

| | 3-mer causal | 6-mer causal | 3-mer masked | 6-mer masked |
|---|---|---|---|---|
| floor at round 30 | 3.771 | 2.514 | 1.724 | 1.862 |
| r=1 extraction at round 30 | 68 % | **96 %** | 0 % | 0 % |
| r=1 extraction at round 150 | 100 % | 100 % | 0 % | 0 % |
| r=16 canary bits at 150 | 0.003 | 0.005 | 0.058 | 0.693 |

(59.9M shown; 201M is the same picture.) A causal model reproduces a single-insertion canary
**96 % of the time by round 30**, at a held-out loss it can still be argued for. Also worth
recording: **larger masked models memorise less at a fixed round count** --- r=16 canary surprise at
150 rounds is 0.140 / 0.693 / 1.691 bits/nt at 12.6M / 59.9M / 201M, because the bigger models are
simply less overfit after the same number of passes.

**(f) The prior arm, corrected.** I first read these cells off the aggregate scorer, which
normalises over all 96 nucleotides of a canary and mixed the two sizes together under one run name.
The reconstruction audit separates them, and it says something different:

| prior cell | tier | LOO bits/nt | LOO top-1 | ceiling | prefix | ICM (1 restart) |
|---|---|---|---|---|---|---|
| 12.6M, 6-mer | r=16 | 0.012 | **1.00** | 1.000 | **5 %** | **25 %** |
| 12.6M, 6-mer | r=1 | 0.043 | 0.99 | 0.967 | 0 % | 0 % |
| 12.6M, 3-mer | r=16 | 0.032 | 0.99 | 0.920 | 0 % | 0 % |
| 201M, 3-mer | r=16 | 0.084 | 0.97 | 0.790 | 0 % | 0 % |
| 201M, 6-mer | r=16 | 1.831 | 0.03 | 0.000 | 0 % | 0 % |

So a chromosome-21 prior does change whether the record comes out: the 12.6M 6-mer cell extracts
**5 % under the published prefix protocol** at a held-out loss that is not degraded, which no
from-scratch cell at any scale did. My earlier sentence that the prior "changes how much is stored,
not whether it comes out" was wrong and is withdrawn. What survives is that the prior does not do it
for the 3-mer at either size, and that the 201M 6-mer cell with a prior barely memorises at all
because it is nowhere near overfitting after 150 rounds. Honest limitation: ten rounds on 60,000
chromosome-21 windows is not a foundation-model prior, so this bounds "a little pretraining" and not
NT's actual pretraining.

**(h) The one discriminator that holds across everything measured tonight.** Storage is close to
universal once a masked cell passes its utility optimum: leave-one-out top-1 reaches 0.96 to 1.00 in
every such cell, at every multiplicity, single insertions included. What differs is reachability,
and the variable that tracks it is the number of joint slots the target occupies --- 8 for the
6-mer, 16 for the 3-mer. Eight slots yielded 5 % to 48 % depending on search budget, prior, and
round count. Sixteen slots yielded 0 % in every cell, at every budget up to 128 restarts, including
cells whose per-token knowledge is perfect. Whether that is a barrier or only a delay is what
`queue_1012g` is running now.

**(g) Running.** `queue_1012d`: seeds 1 and 2 at 150 rounds (the 12 % rested on one seed) and seed 0
pushed to 300 rounds. `queue_1012e`: the eight-restart attack on the scale cells, the prior arm and
the 30-round contrast. `queue_1012a` is on its last fine-tune; `queue_1012b`'s 500M cells follow it.

### 3.43 (13 Oct, 01:00) At 300 rounds the published protocol extracts from a masked model, and the slot count turns out to be a delay

**(a) Both tokenisers end up storing the record perfectly.** 300 rounds on chromosome 22, seed 0,
20 probes per tier, leave-one-out conditioning:

| cell | tier | LOO bits/nt | LOO top-1 | prefix protocol | ICM (1 restart) |
|---|---|---|---|---|---|
| 6-mer | r=16 | 0.001 | **1.00** | **10 %** | 40 % |
| 6-mer | r=4 | 0.001 | **1.00** | 0 % | 20 % |
| 6-mer | r=1 | 0.001 | **1.00** | 0 % | **20 %** |
| 3-mer | r=16 | 0.001 | **1.00** | 0 % | 0 % |
| 3-mer | r=1 | 0.008 | **1.00** | 0 % | 0 % |
| control | r=0 | 3.37 | 0.02 | 0 % | 0 % |

A leave-one-out top-1 of 1.00 at 0.001 bits/nt means that given the other target tokens the model
names the remaining one correctly **every time**, at every multiplicity, for a canary inserted
**once**. Storage is not partial and it is not a function of the tokeniser.

**Two firsts here.** The protocol the paper reports --- reveal 48 nucleotides, greedy-decode 48 ---
**extracts 10 % from a masked model with no help from us**, so the published 0 % was a statement
about the training budget as well as about the attack. And ICM recovers 20 % of canaries that were
inserted exactly once, which is the number that matters for a privacy claim.

**(b) The 16-slot barrier is a delay, not a wall.** The 3-mer target occupies 16 joint slots against
the 6-mer's 8, and through every cell so far that difference looked absolute: 0 % at 1, 8, 32 and
128 restarts even where per-token knowledge was perfect. At 300 rounds with 32 restarts it breaks
--- 5 % at r=4 --- so the slot count buys search time rather than immunity. That is the same shape
as every other lever in this paper (3.20, 3.24): **delay, not prevention**, and it is now measured
for the one lever we had been tempted to call a barrier.

**(c) The 150-round restart curve, complete.** 6-mer, 25 probes per tier:

| restarts | 1 | 2 | 4 | 8 | 16 | 32 | 64 | 128 |
|---|---|---|---|---|---|---|---|---|
| r=16 exact | 12 % | 16 % | 20 % | 20 % | 24 % | 40 % | 44 % | **48 %** |
| r=1 exact | 0 % | 0 % | 0 % | 4 % | 4 % | 4 % | 4 % | 4 % |
| wrong nt (r=16) | 26.4 | 24.0 | 20.8 | 21.0 | 18.8 | 12.9 | 11.3 | 11.8 |

It flattens near 48 % against a ceiling of 0.84, so our attack is leaving something on the table but
is no longer cheap to improve. The non-member control is 0 % at every budget and the truth-free
pseudo-log-likelihood selection equals the oracle at every budget, so the attacker needs no answer
key.

**(d) Seeds replicate.** At one restart the 150-round 6-mer cell gives 12 %, 15 % and 5 % at seeds 0,
1 and 2, with leave-one-out top-1 0.97, 0.98 and 0.97 --- so the storage is identical across seeds
and only the search outcome varies, which is what a search-limited quantity should look like. The
3-mer cells are 0 % at all three seeds with leave-one-out top-1 0.96 to 0.98.

**(e) The last Evo variable, implemented without touching anything shared.** `--canary_alone` in
`pilot2/evo.py` fills the host row with PAD and writes the canary at `PROBE_OFFSET`, and masks PAD
out of the loss to match the predecessor's `ignore_index=pad_token_id`. It reproduces the four things
their planting has and ours does not: byte-identical repetitions, a locked position, zero-entropy
context, and all of the gradient on the canary. Confined to `evo.py` --- no shared builder, scorer or
tokeniser is touched, so nothing else in the paper can move under it --- and because the canary stays
at `PROBE_OFFSET` the geometry is exactly what `score_run` probes under `--probe_offset fixed`, with
the non-member control padded to match so it measures membership rather than padding. Smoke test
rewrote 34 rows correctly; the real cell is training. The baseline it is read against already exists:
`queue_1011g`'s fixed-offset cell is the same configuration with real hosts.

**Correction to my own earlier summary**, which the audit caught: their canary is 64 of 512 tokens
(12.5 % of its row) and ours is 96 of 288 (33 %), so the canary is a *smaller* fraction of its
example there. The variable is identical position-locked repetitions against varied hosts, not token
share.

**(f) Where the paper stands after tonight.** Storage is close to universal once a masked cell passes
its utility optimum, at every multiplicity, for both tokenisers. What varies is the work needed to
read it back, and three things set that work: the objective (a causal model needs none --- 0.000
bits/nt on the target half, the true token top-1 at every step, 100 % extraction), the number of
joint slots (8 against 16, worth everything at 150 rounds and a delay by 300), and the attacker's
search budget (12 % to 48 % on one cell). None of them is a defence, and the paper has to be written
in those terms.

### 3.44 (13 Oct, 05:00) A record inserted once comes back 95 % of the time, and the protocol this field uses calls it 0 %

**(a) The number.** 6-mer masked, human chromosome 22, 300 rounds, 128 restarts of the
iterated-conditional-modes decoder, 20 probes per tier:

| tier | prefix protocol | **ICM** | mean wrong nt of 48 |
|---|---|---|---|
| r=16 | 10 % | **95 %** | 0.2 |
| r=4 | 0 % | **80 %** | 5.9 |
| r=1 (**one** insertion) | 0 % | **95 %** | 1.6 |
| r=0 non-member | 0 % | **0 %** | 35.6 |

The reconstruction is not approximate: at r=16 it is wrong by two tenths of a nucleotide out of 48 on
average. The non-member control is 0 % under the same decoder with 35.6 wrong, and the attack chooses
its own output by pseudo-log-likelihood, so none of this needs an answer key. The 3-mer cell at the
same budget gives 10 % at r=4 and 0 % elsewhere: **16 joint slots against 8 is a cost, not a
barrier.**

**(b) What this does to the paper.** Our headline claim --- the objective decides whether whole
records come back --- is dead, and we killed it with our own stronger attack rather than having a
reviewer do it. What replaces it is worth more than what it replaces, and it is methodological:

- **Measured memorisation is attack-relative.** The same checkpoint reads 0 % or 95 % depending only
  on the decoder, and the decoder that works is the one matching the conditional the model was
  trained on.
- **The prefix protocol under-reports a masked model by up to 95 percentage points.** That protocol
  --- reveal a prefix, greedy-decode the rest --- is what this field uses, including the predecessor
  and including every table we have published so far. For a bidirectional model it is the wrong
  question, and the gap is not a correction factor, it is the whole measurement.
- **The objective and the tokeniser change the cost of extraction, not its possibility.** A causal
  model needs no search at all (0.000 bits/nt on the target half, the true token top-1 at every
  step, 100 %). A masked model needs a search whose difficulty scales with the number of joint slots
  --- 8 for the 6-mer, 16 for the 3-mer --- and with how far past its utility optimum it was trained.
  Every lever we have is a cost multiplier. None is a defence.

**(c) Where the number comes from, in one line each.** Storage: leave-one-out top-1 is 1.00 at
0.001 bits/nt, so given the other target tokens the model names the remaining one correctly every
time, at every multiplicity. Search: one descent gets 20 %, 128 restarts get 95 %, and the selection
rule needs no truth. Budget: 150 rounds gave 48 % at r=16 and 0 % at r=1; 300 rounds gives 95 % at
both.

**(d) NT v2 at 500M, for the scale point on a released checkpoint.** Under the prefix protocol
alone, r=16 extraction reaches **38 % on E. coli** (round 50, floor 2.210) and **32 % on chromosome
22** (round 50, floor 1.662), against 250M's 28 % and 18 %. At a single insertion it is 0 % at every
round on both. So scale raises extraction on the released family too, and the single-insertion tier
is where the search decoder would have to be pointed next.

**(e) Three things this immediately demands, now running as `queue_1013b`.**
1. **Early stopping.** Sec. 6 recommends stopping at the held-out optimum and the whole grid reports
   0 % at 30 rounds --- but that was one restart. 128 restarts on the 30-round cells decides whether
   the paper's one surviving recommendation survives.
2. **Generalisation.** 300 rounds is measured only on human. The same cells on E. coli, yeast, GUE
   and synthetic say whether 95 % is a chromosome-22 fact.
3. **Seeds.** 95 % rests on seed 0, exactly as 12 % did before seeds 1 and 2 gave 15 % and 5 %.

**(f) Still running.** The Evo `--canary_alone` cell (card 3, about five hours for 25 rounds) and the
last of the prior-arm audits.

### 3.45 (13 Oct, 17:30) All four questions answered: the protocol is wrong, early stopping is real, the tokeniser sets the price, and the Evo disagreement is resolved

**(a) The under-reporting is universal, not a chromosome-22 fact.** 6-mer masked, 300 rounds, 128
restarts, 20 probes per tier, five datasets:

| dataset | r=16 standard -> ours | r=1 (**one** insertion) standard -> ours | wrong nt of 48, ours |
|---|---|---|---|
| E. coli | 15 % -> **100 %** | 15 % -> **100 %** | 0.0 |
| yeast | 15 % -> **95 %** | 5 % -> **100 %** | 0.0-0.8 |
| GUE | 10 % -> **100 %** | 0 % -> **95 %** | 0.0-1.4 |
| synthetic | 0 % -> **100 %** | 5 % -> **100 %** | 0.0 |
| human chr22 | 10 % -> **95 %** | 0 % -> **95 %** | 0.2-1.6 |

Non-member controls stay at 0 % under the same decoder with 33-36 of 48 wrong. Seeds 1 and 2 on
human give 95 %/100 % and 90 %/95 % at r=16/r=1, so the number is not a seed artefact. **A masked
model trained past its optimum returns essentially every planted record, including records inserted
exactly once, and the protocol this field uses reports 0 to 15 %.**

**(b) Early stopping survives the strongest attack we have, and that is the paper's one real
recommendation.** At 30 rounds -- at or near the held-out optimum -- 128 restarts recover **0 % at
every tier, both tokenisers, both seeds**. And the reason is visible in the right statistic:
leave-one-out top-1 is **0.03 to 0.21**, against 1.00 at 300 rounds. The record is not hidden at the
optimum, it is **not yet stored**. So early stopping is not a decoding accident; it is the one lever
we have tested that removes the thing an attacker would search for.

**(c) The tokeniser sets the price, and the price is the whole outcome.** At 300 rounds the 3-mer
cells store the record just as completely on human (leave-one-out top-1 1.00 at 0.001 bits/nt, all
three seeds) and return **0 %**, where the 6-mer returns 90-100 %. The target is 16 joint slots
against 8. On E. coli, yeast, GUE and synthetic the 3-mer is 0 % as well. The only exceptions found
anywhere are 5-10 % on synthetic and at r=4, so it is a cost rather than a barrier -- but at every
budget we can afford, a 16-slot target is the difference between recovering everything and
recovering nothing.

**(d) The Evo disagreement is resolved, with one variable.** Same model, same LoRA configuration,
same corpus size, same 25 rounds, same held-out loss (1.473 against 1.478). The only difference is
whether a canary is its own training example or embedded in a varied host window:

| ruler at round 25 | real hosts | **canary alone** |
|---|---|---|
| r=16 canary surprise | 2.015 (chance) | **0.098** |
| r=16 rank-1 | 0.15 | **1.00** |
| r=16 verbatim extraction | **0 %** | **70 %** |
| r=16 wrong nt of 48 | 35 | **6** |
| r=4 rank-1 | 0.00 | **1.00** |
| r=1 rank-1 | 0.00 | **0.75** |

So the predecessor's 100 % is real and reproducible, and it is a property of **planting whole,
byte-identical, position-locked examples** rather than of Evo, of scale, or of byte-level
tokenisation. Our 0 % is equally correct for canaries embedded in varied hosts. Both numbers belong
in the paper with the mechanism between them, and this is the kind of disagreement that is worth
more resolved than either number alone. Note the single-insertion tier: recognised at 0.75 and
reproduced at 0 %, so even whole-example planting does not give verbatim recovery of a once-seen
record at 25 rounds.

**(e) The paper, as it now stands.**

*Thesis.* Whether a genomic language model gives a training record back is not a property of the
model. It is a property of the model together with how well the question is asked, and the standard
way of asking is wrong for half of all models.

*Method.* Three rulers on planted records -- surprise, recognition, reproduction -- plus the one
statistic that predicts reproduction, which is the model's accuracy on one target position given the
others, and a decoder matched to the conditional the model was actually trained on.

*Results.* (1) The standard prefix protocol under-reports masked models by up to 100 percentage
points, on five datasets, at single insertion. (2) Stopping at the held-out optimum removes the
stored record, and is the only lever tested that does. (3) Tokenisation and training budget set the
price of recovery, over three orders of magnitude of search, and neither makes recovery impossible.
(4) A 7B released model reproduces nothing when records sit in varied hosts and 70 % when each
record is its own example, which reconciles our result with the predecessor's.

*Contribution.* A corrected measurement protocol for bidirectional genomic models; a price list
across five datasets, four tokenisations, two objectives, three scales and two released
checkpoints; and the demonstration that every published claim of the form "our encoder-style
genomic model does not leak", ours included, rests on the wrong test.

### 3.46 (13 Oct, 19:00) The released-model evidence we already had, and the two bugs that would have thrown away the run meant to get more

The user's objection is that conclusions measured only on our own 12.9M backbone cannot be written
as claims about models in the world. It is correct, and acting on it turned up three things.

**(a) We already had the result, from 8 October, and never put it in the paper.** DNABERT-2, the
released 117M checkpoint, under ITS OWN native masked objective, on E. coli, re-read today from the
raw scores rather than from the old note:

| round | PLL held-out floor | r=16 bits / rank-1 / **verbatim** | r=1 rank-1 / verbatim |
|---|---|---|---|
| 15 (its best utility) | **1.568** | 0.698 / 1.00 / 0 % | 0.30 / 0 % |
| 30 | **1.594** (+0.026) | 0.048 / 1.00 / **30 %** | 0.60 / 0 % |
| 50 | 1.644 (+0.076) | 0.021 / 1.00 / 30 % | 0.90 / 0 % |

**At 0.026 bits past its own optimum — a model anyone would ship — a released masked checkpoint
reproduces 30 % of 16x-planted records verbatim, with recognition at 1.00, under the STANDARD
protocol and with no new decoder.** The mean reconstruction is 17.2 of 48 nucleotides wrong against
38-43 before memorisation sets in. This is a materially better privacy data point than our own
300-round cell, because that cell's held-out loss is 2.866 against a 1.675 optimum, i.e. worse than
uniform, while this one costs 0.026 bits.

It also means the paper's current claim that a masked objective prevents reproduction was already
contradicted by our own released-model data from five days ago, which the draft does not report.
That contradiction is in our files and a reviewer can find it.

**(b) So the released-model account is now three-quarters built, not empty.**

| claim | released-model evidence | status |
|---|---|---|
| masked released models store records completely | DNABERT-2 r=16 at 0.048 bits with rank-1 1.00; NT 250M and 500M | validated |
| and reproduce them verbatim at usable utility | DNABERT-2 30 % at +0.026 bits from its optimum | validated |
| including records present as a single copy | recognition 0.60-0.90, verbatim 0 % under the standard protocol | NOT yet |
| the standard protocol under-reports masked models | needs the search decoder on a released checkpoint | running |

The single-copy row is exactly where the new decoder has to be pointed, and it is the row that
matters for a privacy claim, because a rare haplotype is unique to one person.

**(c) Two bugs that would have silently wasted the runs meant to settle (c).** Both found by audit,
both verified. `recon_audit.rebuild` called our backbone's objective parser before deciding whether
the cell is a released one; that parser demands `mlm@<rate>` and raises on the bare `mlm` that
`nt.py` writes and the `causal` that `dnabert.py` writes, so every released cell died before the
decoder ran. Worse, it read `n_val` and `n_test` unguarded, and `dnabert.py`, `dnabert2.py` and
`hyena.py` all pass 200 without recording it — and probe HOSTS are drawn from the windows after
`n_train + n_val + n_test`, so a wrong value silently relocates every canary into a window the model
never trained on and the decoder returns a confident number for the wrong sequence. Fixed, and
verified by running the decoder on the ep15 checkpoint of the NT fine-tune still in flight:
leave-one-out per-position accuracy 0.77 for members against 0.00 for the matched control.

**(d) Keeping checkpoints is now the default, at the user's instruction, and it was never a real
saving.** `/data` has 5.3 TiB free against the 59 GiB all our outputs occupy; a snapshot of our
backbone is 56 MiB and of NT 250M about 0.9 GiB. The cost of deleting them was not disk, it was that
the decoder could only ever be pointed at a run's last round — which is why the
extraction-against-held-out-loss curve had to be faked by retraining at 150 and 300 rounds, and why
every released masked checkpoint had to be retrained from scratch today rather than merely
re-scored.

**(e) The decoder for overlapping k-mers, which can only live in nucleotide space.** One token at a
time is undefined on DNABERT: with stride 1 a valid token string satisfies
`token_t[1:] == token_{t+1}[:k-1]`, so changing one token contradicts the 2(k-1) overlapping it and
decodes to no DNA string; and five of a 6-mer's six letters are visible in its neighbours anyway, so
the conditional is answerable from context with no memorisation. `pilot2/recon_overlap.py` re-masks
one NUCLEOTIDE at a time by masking the k tokens covering it and marginalising onto that letter,
which is the conditional DNABERT was pretrained on. This also makes the mechanism falsifiable on
released models: hiding 48 nucleotides takes 48+(k-1) tokens, i.e. about 48 slots for EVERY k, so the
joint-slot claim predicts a FLAT profile across DNABERT k=3,4,5,6 beside the 0-to-95 split on the
non-overlapping axis. A large spread would refute it.

**(f) And the caveat the headline is still missing.** The 300-round cells sit at a held-out loss of
2.866 (chromosome 22) and 3.164 (E. coli), both worse than the 2.000 of a uniform predictor.
`queue_1013e` retrains one cell per tokeniser with twelve snapshots kept and runs the decoder at
every one, so the paper can publish the curve of recovery against utility instead of an endpoint at
a utility nobody would accept. The interesting region is between round 30 (floor 1.675, 0 %) and
round 150 (floor 2.176, 48 %), and it has never been measured with this decoder.

### 3.47 (13 Oct, 19:30) "150 rounds" and "300 rounds" are not two points on one trajectory

Noticed while the curve run was scoring its snapshots, and it corrects something I have written
several times. The 3-mer cell of `queue_1013e` reports a held-out floor of **2.353 at epoch 150**,
where the 3-mer cell of `queue_1011h` reported **2.074 at epoch 150**. Same tokeniser, same seed,
same data, same probe block. The difference is the learning-rate schedule: `pilot2/train.py:143`
computes the decay as `(step - warmup) / (total - warmup)`, and `total` is the whole run's step
count. So epoch 150 of a 300-epoch run is **mid-decay at a much higher learning rate** than epoch
150 of a 150-epoch run, and it is a different model.

Three consequences.

**(a) A sentence I have repeated is wrong as stated.** "150 rounds gives 48 % and 300 rounds gives
95 %" reads as two points on one trajectory. They are two separate runs with different schedules,
and the only honest way to put them side by side is by their own held-out losses: 48 % at a floor of
2.176, and 95 % at a floor of 2.866.

**(b) The curve must be plotted against held-out loss, not against round number.** That is already
what `queue_1013e` does -- twelve snapshots of ONE run, each carrying its own floor -- which turns
out to be necessary rather than merely tidy. Round number is not comparable across budgets and the
paper should not use it as an axis anywhere that two budgets are compared.

**(c) It also explains why the early-stopping result is cleaner than it looked.** The 30-round cells
that recover 0 % under 128 restarts were trained with a 30-epoch schedule, so they are fully decayed
and genuinely converged at their optimum, not merely stopped early in a longer schedule. Those are
two different claims and we have the stronger one: a model trained to convergence at its optimum
holds nothing the decoder can find. What we do NOT yet have is the other one -- stopping a long run
early -- and the twelve-snapshot curve supplies exactly that, because every snapshot comes from a
single 300-epoch schedule.

### 3.48 (13 Oct, 20:30) A released DNABERT stores the record perfectly at no utility cost, and the standard protocol says zero

**(a) The cleanest setting we have for the under-reporting claim, and it is on released weights.**
DNABERT k=3 and k=4, 150 rounds on E. coli, `--mask_nt_rate 0.05`, the configuration the family was
already measured with:

| | ep15 | ep50 | ep150 |
|---|---|---|---|
| held-out floor, k=3 | 1.774 | **1.724** (best) | 1.739, i.e. **+0.015** |
| r=16 canary bits | 1.846 | 0.070 | **0.003** |
| r=16 recognition | 0.40 | 1.00 | **1.00** |
| r=16 verbatim, STANDARD protocol | 0 % | 0 % | **0 %** |
| r=4 recognition | 0.00 | 0.50 | **1.00** |
| r=1 recognition | 0.00 | 0.00 | **0.58** |

k=4 is the same picture (0.004 bits/nt and recognition 1.00 at ep150, floor 1.739 against a best of
1.725). **A released checkpoint, at fifteen thousandths of a bit above its own best held-out loss,
holds a 16x-planted record at 0.003 bits/nt and names it first out of a hundred candidates every
time, and the protocol this field uses reproduces none of it.** The record is demonstrably present
and the model is demonstrably useful, so whether it comes out is a question about the decoder and
nothing else. That is a far better setting for the argument than our own 300-round cell, whose
held-out loss is 2.866 against a 1.675 optimum.

Note also that these models do NOT degrade the way our from-scratch cells do: the floor is flat from
ep50 to ep150. A pretrained 86M checkpoint fine-tuned on 5,000 windows memorises the planted records
without paying for it in held-out loss at all, which is the regime an actual practitioner is in.

`queue_overlap` is now running the nucleotide-level decoder on those weights, at their final round
and at their own optimum (ep50). Every snapshot was kept, so the DNABERT utility curve is available
too.

**(b) The utility curve, first two points, and they are the reassuring end.** One 300-round run of
the 6-mer cell, twelve snapshots, each read with 128 restarts:

| snapshot | floor | from best | LOO per-token top-1 (r=16) | verbatim, both protocols |
|---|---|---|---|---|
| ep15 | 1.866 | +0.040 (still improving) | 0.03 | 0 % |
| ep30 | **1.825** | **the optimum** | 0.07 | 0 % |
| non-member control | | | 0.02 | 0 % |

At and before the optimum the record is **not stored**: the leave-one-out accuracy is 0.03-0.07
against 0.02 for a sequence the model never saw. So the 0 % there is not a decoder failing to find
something, it is nothing being there. The decisive points are ep45 (+0.003), ep60 (+0.054), ep80
(+0.171) and ep100 (+0.351), all running.

**(c) NT 250M at round 50, for the record.** Floor 2.263 on E. coli (its optimum is 1.823) and 1.632
on chromosome 22 (optimum 1.376). Leave-one-out top-1 is **0.98** at r=16 on both, against 0.01 and
0.07 for the matched controls, with ceilings of 0.87 and 0.90 -- so a released 250M checkpoint also
stores the record almost completely. The standard prefix protocol already gets **35 %** (E. coli)
and **25 %** (chromosome 22), and 5 % at a single insertion on chromosome 22.

One thing to be careful about: at ONE restart the search decoder is WORSE than the prefix protocol
here (5 % against 35 %), the opposite of our backbone. NT is pretrained and 250M, so its
prefix-conditional is already strong (target top-1 0.78), and a single descent lands on the wrong
fixed point. The 128-restart pass is what the claim rests on and it is still running.

### 3.49 (13 Oct, 21:00) DNABERT holds the record perfectly and nothing can get it out, which is the mechanism confirming itself and the scope narrowing

**(a) The result.** DNABERT k=3, released weights, E. coli, round 150 at a held-out loss of 1.739
against its own best of 1.724, read with the nucleotide-level re-masking decoder at 32 restarts,
20 probes per tier:

| tier | LOO per-nucleotide top-1 | LOO bits/nt | implied ceiling | ICM-nt | oracle over 32 restarts | wrong nt of 48 |
|---|---|---|---|---|---|---|
| r=16 | **1.00** | 0.004 | **0.968** | **0 %** | **0 %** | 35.7 |
| r=4 | 0.91 | 0.361 | 0.233 | 0 % | 0 % | 36.4 |
| r=1 | 0.35 | 2.050 | 0.000 | 0 % | 0 % | 36.0 |
| r=0 control | 0.28 | 2.277 | — | 0 % | 0 % | 36.5 |

Given the other target nucleotides the model names the remaining one correctly **every single time**,
at 0.004 bits/nt, and the ceiling says 97 % of records should be reconstructible. The search recovers
**nothing** -- not once in 32 restarts across 20 probes -- and its reconstruction sits at the chance
Hamming distance, indistinguishable from the non-member control.

**(b) This is the mechanism confirming itself, on released weights.** Overlapping k-mers pin the
joint-slot count to the nucleotide count: hiding 48 nucleotides needs 48+(k-1) tokens, so the target
is **48 joint slots for every k**. Our own non-overlapping cells already showed 8 slots giving
90-100 % and 16 slots giving 0 %. Forty-eight slots giving 0 % is the same law continued, and it is
now measured on a released checkpoint rather than on a backbone we trained. The claim that the
joint-slot count sets the price of recovery has survived the test that could have refuted it.

**(c) And it narrows the scope of the headline, usefully.** "The standard protocol under-reports
masked models" is NOT true of DNABERT. There the standard protocol's 0 % is operationally correct:
the record is in the weights, but no decoder we can build gets it out, so the number a practitioner
cares about really is zero. The honest claim is narrower and sharper:

> The standard protocol under-reports masked models **whose target occupies few joint slots** --
> coarse non-overlapping tokenisation. It is accurate for fine or overlapping tokenisation, where the
> record is stored but unreachable.

That makes tokenisation the lever, not the objective, and it makes the recommendation concrete:
a fine or overlapping vocabulary keeps a fully memorised record out of reach, and that is a much
stronger thing to be able to say than "masked objectives are safer".

**(d) What this does to the released-model account.** The under-reporting claim now rests entirely on
the two released checkpoints with few-slot targets: NT v2 250M, whose 4096 non-overlapping 6-mers are
literally our own axis and whose 128-restart pass is still running, and DNABERT-2, whose BPE is also
non-overlapping and which is queued. DNABERT's four k variants become the negative control they were
predicted to be, and HyenaDNA and Evo stay on the causal side where the prefix protocol is already
the matched idiom. If NT and DNABERT-2 both come back at or near their ceilings, the claim is
established on released models with a mechanism and a control. If they come back at 0 % like
DNABERT, then the 95 % on our own 6-mer backbone is bounded to from-scratch models and the abstract
must say so.

**(e) The utility curve, third and fourth points.** The 6-mer cell, one 300-round run:

| snapshot | floor | from best | LOO top-1 (r=16) | verbatim |
|---|---|---|---|---|
| ep30 | 1.825 | the optimum | 0.07 | 0 % |
| ep45 | 1.829 | +0.003 | 0.17 | 0 % |
| ep60 | 1.879 | +0.054 | 0.37 | 0 % |

Storage is climbing steadily (0.07, 0.17, 0.37) while recovery stays at zero, so the turn has not
happened yet and the remaining points -- +0.171, +0.351 and beyond -- are where it must be.

### 3.50 (13 Oct, 21:40) Early stopping does not protect a released checkpoint, and the pretrained model leaks at a utility you would ship

**This reverses the recommendation in 3.45(b).** The early-stopping result was measured on our own
from-scratch backbone, where at the optimum there is nothing stored to find. On a released,
pretrained checkpoint that is false.

**(a) NT v2 250M, round 15, held-out loss 1.851 against its own optimum of 1.823 — plus 0.028 bits,
which is a model anyone would ship:**

| tier | standard protocol | **128 restarts** | oracle | LOO per-token top-1 |
|---|---|---|---|---|
| r=16 | **0 %** | **10 %** | 15 % | 0.70 |
| r=4 | 0 % | 0 % | 0 % | 0.04 |
| r=1 | 0 % | 0 % | 0 % | 0.01 |
| r=0 control | 0 % | 0 % | 0 % | 0.01 |

Two things at once. The search decoder recovers records from a released masked checkpoint **at
0.028 bits past its optimum**, where the protocol this field uses reports zero — so the
under-reporting claim now has released-model evidence. And early stopping is **not** a defence
there: a pretrained 250M model has already stored the 16x record by round 15 (leave-one-out 0.70),
whereas our 12.9M from-scratch backbone had stored nothing at all at its optimum (0.07 against a
control of 0.02).

The honest reading of the difference is that a pretrained model does not have to spend its capacity
learning the distribution, so it memorises planted records within a handful of rounds, long before
its held-out loss degrades. Our from-scratch cells had to be ruined first. **The from-scratch
backbone was giving us a falsely reassuring picture, and only a released checkpoint could show it.**

Caveat to close: NT's optimum is round 3 and our earliest kept snapshot is round 15, so this is
measured 0.028 bits past the optimum rather than at it. `queue_ntopt` is running rounds 1, 3 and 5
with the decoder at each, which is where a practitioner would actually stop.

**(b) The utility curve on our backbone, and where it turns.** One 300-round run of the 6-mer cell,
twelve snapshots, 128 restarts at each:

| snapshot | floor | from best | LOO top-1 (r=16) | verbatim | oracle |
|---|---|---|---|---|---|
| ep30 | 1.825 | the optimum | 0.07 | 0 % | 0 % |
| ep45 | 1.829 | +0.003 | 0.17 | 0 % | 0 % |
| ep60 | 1.879 | +0.054 | 0.37 | 0 % | 0 % |
| ep80 | 1.997 | +0.171 | 0.68 | 0 % | 0 % |
| ep100 | 2.176 | +0.351 | 0.88 | **20 %** | 25 % |

So for a from-scratch model recovery begins between +0.171 and +0.351 bits, which is past the point
where the model is worse than a uniform predictor (2.000). On its own that reads as reassuring. Put
beside NT's 10 % at +0.028, it is the opposite: **pretraining moves the leak from a broken model to a
usable one**, and that is the number that matters in practice.

**(c) DNABERT at its own optimum, for completeness.** k=3, round 50, held-out loss 1.724, its best:
leave-one-out per-nucleotide top-1 **0.96** at r=16 with a ceiling of 0.360, and the nucleotide-level
decoder recovers **0 %**, oracle 0 %. So DNABERT stores the record almost perfectly even at its
optimum and still nothing comes out, because the target is 48 joint slots.

**(d) The picture, now with released-model evidence in three of four rows.**

| model | tokenisation | joint slots | utility cost where it leaks | leak |
|---|---|---|---|---|
| our 6-mer, from scratch | non-overlapping 6-mer | 8 | +0.351 (broken model) | 20 % |
| **NT 250M, released** | non-overlapping 6-mer | 8 | **+0.028 (usable model)** | **10 %** |
| our 3-mer, from scratch | non-overlapping 3-mer | 16 | never, to 128 restarts | 0 % |
| **DNABERT k=3/4, released** | overlapping | 48 | never, stores at 1.00 | 0 % |

Three claims follow, and the recommendations change.

1. **The joint-slot count decides whether recovery is possible at all.** 8 slots leak, 16 and 48 do
   not, at every budget we can afford. This is the lever, and it is a tokenisation choice.
2. **Pretraining decides whether the leak happens at a utility anyone would accept.** This is why a
   controlled from-scratch backbone cannot be the only evidence, and the user was right to insist.
3. **Early stopping is not a defence for a pretrained model**, and Sec. 6 and Sec. 8 have to be
   rewritten. What survives is the narrower statement that a from-scratch model at its optimum has
   not yet stored the record.

### 3.51 (13 Oct, 23:10) The under-reporting claim now has released-model evidence: 35 % becomes 70 % on a published checkpoint

**(a) The pillar.** Nucleotide Transformer v2 250M, the released checkpoint, E. coli, round 50
(held-out loss 2.263 against its optimum of 1.823), 128 restarts, 20 probes per tier:

| tier | standard protocol | **search decoder** | oracle | ceiling | wrong nt of 48 |
|---|---|---|---|---|---|
| r=16 | **35 %** | **70 %** | 80 % | 0.869 | 12.2 -> **7.4** |
| r=4 | 0 % | 0 % | 0 % | 0.245 | 35.4 -> 35.0 |
| r=1 | 0 % | 0 % | 0 % | 0.010 | 34.5 -> 36.1 |
| r=0 control | 0 % | **0 %** | 0 % | 0.000 | 36.7 -> 36.2 |

On a published checkpoint the protocol this field uses reports **half** of what is actually
recoverable, and the decoder gets within 0.17 of the information-theoretic ceiling its own
leave-one-out accuracy implies. The non-member control stays at 0 % and its reconstruction stays at
the chance Hamming distance, so this is recall and not decoding luck.

**(b) Together with 3.50(a) the claim is now two-sided on released weights.**

| NT 250M, E. coli | held-out loss | from its optimum | standard | ours |
|---|---|---|---|---|
| round 15 | 1.851 | **+0.028 (a model you would ship)** | **0 %** | **10 %** |
| round 50 | 2.263 | +0.440 | 35 % | **70 %** |

At a utility anyone would accept the protocol reports **zero** where records do come back. Past the
optimum it reports **half**. Both measured on weights we did not train.

**(c) An honest limit that has to be stated.** On NT the single-copy and 4-copy tiers stay at 0 %
under every decoder, and the reason is visible in the right column: their ceilings are 0.010 and
0.245, so the record is not stored well enough for any search to find it. Our own backbone reached
95 % at a single copy, but only at a held-out loss of 2.866, i.e. on a model worse than a uniform
predictor. **So "a record present once comes back" is NOT established on released weights** and must
stay a controlled-backbone statement, scoped to a ruined model. What released weights establish is
the 16-copy case, which is still the right case for duplicated reference material and for anything
that appears in a corpus more than once.

**(d) The released-model account, as it stands tonight.**

| model | tokenisation | joint slots | utility | standard | ours |
|---|---|---|---|---|---|
| NT 250M | non-overlapping 6-mer | 8 | +0.028 | 0 % | **10 %** |
| NT 250M | non-overlapping 6-mer | 8 | +0.440 | 35 % | **70 %** |
| DNABERT k=3 | overlapping | 48 | +0.015 | 0 % | **0 %** (stores at 1.00) |
| DNABERT k=4 | overlapping | 48 | +0.014 | 0 % | **0 %** (stores at 1.00) |
| DNABERT-2 | non-overlapping BPE | few | +0.026 | 30 % | queued |

k=4 reproduces k=3 exactly (leave-one-out 1.00 at 0.006 bits/nt, ceiling 0.968, recovery 0 %,
oracle 0 %), and both store the record almost perfectly **at their own optimum** too (0.94-0.96).
So the flatness the joint-slot mechanism predicted holds for the two variants measured, and k=5 and
k=6 are running.

**(e) What the paper can now say, with the evidence attached to each clause.**

1. *Measured memorisation is attack-relative.* Released checkpoint, two utility points, 0 % -> 10 %
   and 35 % -> 70 %. **Released-model evidence.**
2. *The joint-slot count decides whether recovery is possible at all.* 8 slots recover, 16 and 48 do
   not, at every budget tried; two of the four rows are released weights. **Released-model evidence
   for the negative half, controlled for the positive half.**
3. *Pretraining decides the utility at which the leak appears.* NT leaks at +0.028, our from-scratch
   cells need +0.351. **Released against controlled, which is the comparison that makes the point.**
4. *Early stopping is not a defence for a pretrained model.* NT at +0.028. **Released-model
   evidence**, and it reverses what 3.45 recommended.
5. *A single-copy record coming back* stays controlled-backbone and ruined-utility only.

### 3.52 (13 Oct, 23:40) Two complete figures: the released DNABERT family is flat, and the utility curve has a knee

**(a) Figure A, the mechanism's negative control, on four released checkpoints.** DNABERT k=3, 4, 5
and 6, E. coli, round 150, nucleotide-level re-masking at 32 restarts, r=16:

| k | LOO per-nucleotide top-1 | LOO bits/nt | ceiling | recovery | oracle over 32 restarts |
|---|---|---|---|---|---|
| 3 | 1.00 | 0.004 | 0.968 | **0 %** | 0 % |
| 4 | 1.00 | 0.006 | 0.968 | **0 %** | 0 % |
| 5 | 1.00 | 0.003 | 1.000 | **0 %** | 0 % |
| 6 | 0.99 | 0.018 | 0.841 | **0 %** | 0 % |

**Perfectly flat across the entire released family.** Every variant stores the 16x record essentially
exactly and none of them gives any of it back. That is what the joint-slot account predicts and
nothing else does: overlapping k-mers pin the target at 48 slots whatever k is, so changing k from 3
to 6 cannot change recovery. Had the spread been large the mechanism would have been refuted. It is
a stronger test than a positive result because the prediction was made first and the four
checkpoints are not ours.

One clarification the paper has to make. Our earlier DNABERT result (3.10, 3.14) found the ordering
3 < 4 < 5 < 6 monotone, and that is not contradicted: it was an ordering of **how much is stored**,
measured with the surprise ruler on causal fine-tunes in the transient. Here at round 150 all four
have saturated at 0.003-0.018 bits/nt, so the ordering has washed out, and what is being compared is
**whether what is stored can be read back**. Two different rulers, and the paper must not let them
be read as one.

**(b) Figure B, the utility curve, all twelve snapshots of one 300-round run.** 6-mer masked, human
chromosome 22, r=16, 128 restarts, each point carrying its own held-out loss:

| round | held-out loss | vs best | LOO top-1 | recovery | oracle |
|---|---|---|---|---|---|
| 15 | 1.866 | +0.040 | 0.03 | 0 % | 0 % |
| 30 | **1.825** | **optimum** | 0.07 | 0 % | 0 % |
| 45 | 1.829 | +0.003 | 0.17 | 0 % | 0 % |
| 60 | 1.879 | +0.054 | 0.37 | 0 % | 0 % |
| 80 | 1.997 | +0.171 | 0.68 | **0 %** | 0 % |
| 100 | 2.176 | +0.351 | 0.88 | **20 %** | 25 % |
| 120 | 2.368 | +0.542 | 0.95 | 50 % | 50 % |
| 150 | 2.590 | +0.765 | 0.98 | 30 % | 30 % |
| 190 | 2.750 | +0.925 | 0.99 | 75 % | 75 % |
| 230 | 2.823 | +0.998 | 1.00 | 85 % | 85 % |
| 265 | 2.847 | +1.022 | 1.00 | 95 % | 95 % |
| 300 | 2.866 | +1.041 | 1.00 | 95 % | 95 % |

Three things to read off it. **Storage saturates long before recovery starts**: leave-one-out is
already 0.68 at +0.171 where recovery is still exactly zero, which is the storage-reachability
dissociation measured along a single trajectory rather than inferred across runs. **The knee is at
about +0.35 bits**, and the model is already worse than a uniform predictor there (2.176 against
2.000). And recovery saturates at 95 %, not 100 %, with the attack matching the oracle at every
point past the knee, so the truth-free selection costs nothing.

The dip at round 150 (30 % against 50 % before and 75 % after) is sampling noise: 20 probes give a
standard error near 11 points. If this curve goes in the paper it needs 50 probes per point, which
is a cheap re-run now that the checkpoints are kept.

**(c) The comparison that matters, and it needs both figures.** For a from-scratch model the leak
begins only after the model is ruined (+0.35 bits, past uniform). For the released pretrained NT the
leak begins at **+0.028 bits**, on a model anyone would ship. Reporting either alone misleads: the
first reads as reassuring, the second as alarming. **The honest statement is that pretraining moves
the knee from a broken model to a usable one**, and that is only visible because we have both.

### 3.53 (14 Oct, 17:00) Overnight: early stopping does work on a released model, a single-copy record does come back, and the slot law is airtight

All seven queues finished. Two of last night's conclusions change, both in the direction of being
more precise rather than less useful.

**(a) CORRECTION to 3.50. Early stopping IS a defence on a released checkpoint, with a 0.028-bit
margin.** I tested NT at round 15 and found 10 % recovery, and concluded early stopping fails. But
NT's optimum is round 3, and round 15 is twelve rounds past it. Measured AT the optimum:

| NT 250M, E. coli | held-out loss | vs optimum | LOO top-1 (r=16) | recovery |
|---|---|---|---|---|
| round 1 | 1.834 | +0.011 | 0.02 | 0 % |
| round 3 | **1.823** | **the optimum** | 0.01 | 0 % |
| round 5 | 1.826 | +0.003 | 0.03 | 0 % |
| round 15 | 1.851 | +0.028 | **0.70** | **10 %** |
| round 50 | 2.263 | +0.440 | 0.98 | 70 % |

At the optimum the record is **not stored at all** -- leave-one-out 0.01 against a non-member control
of 0.01 -- and nothing is recoverable under any decoder. So the recommendation survives on released
weights. What it costs is the margin: between round 5 and round 15 the model goes from storing
nothing to storing 0.70 and leaking 10 %, and the whole transition is worth **0.028 bits** of
held-out loss. That is inside the noise with which anyone picks a checkpoint, which is the
knife-edge Sec. 6 already describes, now measured on a released model and on the extraction ruler
rather than the surprise ruler.

So the honest claim is neither 3.45's "early stopping removes the stored record" nor 3.50's "early
stopping is not a defence". It is: **stopping at the optimum works, and the margin is three
hundredths of a bit.**

**(b) CORRECTION to 3.51(c). A single-copy record does come back from released weights, on human.**
NT 250M, chromosome 22, round 50, where the canaries are real rare haplotype segments:

| tier | standard protocol | **ours** | oracle | LOO top-1 |
|---|---|---|---|---|
| r=16 | 25 % | **65 %** | 75 % | 0.98 |
| r=4 | 0 % | **10 %** | 15 % | 0.70 |
| **r=1 (one copy)** | 5 % | **10 %** | 15 % | 0.62 |
| r=0 control | 0 % | **0 %** | 0 % | 0.07 |

I wrote last night that single-copy recovery was not established on released weights, on the basis of
the E. coli cell where r=1 is 0 %. On chromosome 22 it is 10 %, with the control at 0 %. The
difference is that E. coli's canaries are synthetic and chromosome 22's are real haplotypes, which
the pretrained model finds easier to hold. **So the strongest privacy statement now has
released-model evidence: a real rare-variant haplotype present once in the fine-tuning corpus is
reproduced verbatim from a published checkpoint.** It is 10 %, not 95 %, and the model is 0.44 bits
past its optimum, and both of those belong in the sentence.

**(c) The slot law, now with twelve points per tokeniser and 50 probes at the knee.** The 20-probe
dip at round 150 was sampling noise and is gone; the curve is monotone.

| vs optimum | 6-mer (8 slots) r=16 | 6-mer r=1 | 3-mer (16 slots) r=16 | DNABERT (48 slots) r=16 |
|---|---|---|---|---|
| +0.17 | 0 % | 0 % | 0 % | -- |
| +0.35 | **16 %** | 0 % | 0 % | -- |
| +0.54 | 46 % | 6 % | 0 % | -- |
| +0.77 | 48 % | **40 %** | 0 % | -- |
| +0.93 | 74 % | 58 % | 0 % | -- |
| +1.00 | 88 % | 74 % | 0 % | -- |
| +1.76 | -- | -- | **0 %** | -- |
| +0.015 (released) | -- | -- | -- | **0 %** at LOO 1.00 |

The 3-mer cell reaches leave-one-out 1.00 by round 190 and stays at **0 %** through a held-out loss
of 3.400, which is 1.76 bits past its optimum and far worse than a uniform predictor. One point
reads 5 % and the rest read 0, so that is noise. **Sixteen slots is a wall even when the record is
stored perfectly and the model is destroyed.** Forty-eight slots likewise, on four released
checkpoints. Eight slots leak from +0.35 and saturate near 90 %.

**(d) What is left.** DNABERT-2 trained but has not been decoded: its BPE is non-overlapping so the
token-level decoder is the right one, but BPE tokens are variable length and `recon_audit`'s
boundary-constraint helper assumes a fixed k, so it needs a span-aware version first. That is the
one remaining piece of the released-model account, and it matters because DNABERT-2 is the second
tokeniser family and already reads 30 % under the standard protocol. The DNABERT chromosome-22 pair
is decoding now, to check the flatness result where the records are real rather than synthetic.

### 3.54 (14 Oct, 17:30) No decoder is right for every vocabulary, and that reframes the paper for the last time

The BPE decoder is written and run, the overlapping decoder has been run on real haplotypes, and
together they refute the framing I have been using all day. **Our search decoder is not universally
stronger than the published one.** It wins on fixed-width non-overlapping k-mers and loses on BPE
and on overlapping k-mers.

**(a) The decoder comparison, every released cell we have.**

| released model | vocabulary | utility cost | standard protocol | our decoder | which wins |
|---|---|---|---|---|---|
| NT 250M, E. coli, ep15 | non-overlapping 6-mer | +0.028 | 0 % | **10 %** | **ours** |
| NT 250M, E. coli, ep50 | non-overlapping 6-mer | +0.440 | 35 % | **70 %** | **ours** |
| NT 250M, chr22, ep50 | non-overlapping 6-mer | +0.256 | 25 % | **65 %** | **ours** |
| DNABERT-2, E. coli, ep30 | BPE | **+0.008** | **30 %** | 0 % | standard |
| DNABERT-2, E. coli, ep150 | BPE | +0.482 | **74 %** | 0 % | standard |
| DNABERT k=6, chr22, ep150 | overlapping 6-mer | +0.180 | **56 %** | 0 % | standard |
| DNABERT k=3, chr22, ep150 | overlapping 3-mer | +0.110 | 2 % | **10 %** | ours |

Why ours loses where it loses is mechanical, not mysterious. Our decoder starts from a random
nucleotide assignment and climbs. On BPE a random string **re-segments** into different tokens, so
the conditional it climbs is evaluated on a window whose segmentation is itself garbage, and there is
no local structure to follow. On overlapping k-mers the same thing happens through a different route:
a random target makes every one of the 48 covering positions mutually inconsistent. The published
prefix decode, by contrast, builds left to right from real context and never leaves the manifold of
plausible strings. **It is the better attack precisely where the vocabulary couples neighbouring
positions.**

**(b) So the methodological claim narrows, and becomes more useful.** Not "the standard protocol
under-reports masked models". Rather:

> No single decoder measures memorisation correctly across vocabularies. The published prefix decode
> is the right question for BPE and for overlapping k-mers. For fixed-width non-overlapping k-mers it
> under-reports by up to 35 points, and a re-masking decode matched to the training conditional is
> required. A paper that reports one decoder for all models has measured the decoder, not the models.

That is a claim about measurement practice with four released checkpoints behind it, and it survives
the fact that our decoder is sometimes the weaker one -- indeed that fact is the evidence for it.

**(c) And the privacy result is now much stronger than the methodological one.** Reading each model
with whichever decoder is better for it:

| released checkpoint | utility cost | verbatim recovery |
|---|---|---|
| DNABERT-2, E. coli | **+0.008** | **30 %** |
| NT 250M, E. coli | +0.028 | 10 % |
| DNABERT k=3, chr22 | +0.110 | 10 % |
| DNABERT k=6, chr22 | +0.180 | **56 %** |
| NT 250M, chr22 | +0.256 | 65 %, and **10 % at a single copy** |
| NT 250M, E. coli | +0.440 | 70 % |
| DNABERT-2, E. coli | +0.482 | **74 %** |

**Every released masked checkpoint we tested reproduces planted records verbatim at a utility cost a
practitioner would accept**, the cheapest at eight thousandths of a bit. Four checkpoints, three
vocabulary families, synthetic and real records. The claim that a masked objective prevents
reproduction is dead on released weights, comprehensively, and that is the paper's result.

**(d) Two details that belong in the write-up.** Single-copy *recognition* is universal: DNABERT-2
reaches rank-1 1.00 at r=1 by round 80 while verbatim stays 0 %, so membership inference would flag
these records everywhere that reproduction does not. And on chromosome 22 the overlapping k=3 cell
gives **10 %** where E. coli gave 0 %, so the 48-slot barrier is a near-wall rather than a wall: real
sequence is predictable enough to give the search something to climb. The slot law is about
difficulty, not impossibility, and real records are easier than synthetic ones everywhere we look.

**(e) Queued on the four free cards** (`queue_1014a`): the single-copy chromosome-22 number at 60
probes instead of 20, because 10 % currently means two hits and it is the number that carries the
privacy claim; NT 500M with weights kept, for a scale point on released weights; NT seeds 1 and 2,
because every NT number is seed 0; and DNABERT-2 trained on chromosome 22, where its records are
real haplotypes rather than synthetic DNA.

### 3.55 (14 Oct, 19:00) DNABERT-2 on real haplotypes: 20 % verbatim at +0.033 bits, and 94 % membership on single copies

The second released tokeniser family, now on chromosome 22 where the planted records are real
rare-variant haplotype segments rather than synthetic DNA. Standard protocol, 150 rounds:

| round | held-out loss | from best | r=16 recognition / verbatim | r=1 recognition / verbatim |
|---|---|---|---|---|
| 15 | **1.266** | best | 0.60 / 0 % | 0.00 / 0 % |
| 30 | 1.299 | **+0.033** | **1.00 / 20 %** | 0.00 / 0 % |
| 50 | 1.357 | +0.090 | 1.00 / 10 % | 0.00 / 0 % |
| 80 | 1.454 | +0.187 | 1.00 / 20 % | **0.20** / 0 % |
| 120 | 1.599 | +0.333 | 1.00 / 50 % | **0.80** / 0 % |
| 150 | 1.726 | +0.459 | 1.00 / 40 % | **0.94** / 0 % |

**(a) The verbatim line.** At 0.033 bits past its own best held-out loss -- a model anyone would ship
-- a released 117M checkpoint reproduces **20 % of real rare-variant haplotypes** that were planted
16 times, and 50 % by +0.333. This is the second vocabulary family to do it and the first on real
human records, so the privacy result is no longer an NT property.

**(b) The membership line, which is the stronger one.** Single-copy *recognition* climbs 0.00 -> 0.20
-> 0.80 -> **0.94** while verbatim reproduction stays at exactly 0 % throughout. So a released
checkpoint will tell an attacker, correctly 94 times in a hundred, **whether one specific rare
haplotype was in its fine-tuning set**, while never reproducing it. Reproduction and membership come
apart completely here, and the direction matters: the ruler the field reports (verbatim) says zero
where the ruler that matters for a person's privacy (was my sequence in there) says almost
certainly yes.

That is the cleanest statement of the paper's Sec. 7 argument we have, and it is now on released
weights with real haplotypes rather than on our backbone with synthetic canaries.

**(c) What it costs to avoid.** Its optimum is round 15 at 1.266, where recognition is 0.60 at r=16
and 0.00 at a single copy and verbatim is 0 %. So stopping at the optimum again removes the thing
an attacker would use -- and again the margin is small, 0.033 bits to reach 20 % verbatim and 1.00
recognition.

The search decoder is running on these weights now. On E. coli it recovered nothing from this family
(3.54), so the expectation is that the standard protocol stays the better attack here and these
numbers are the ones that go in the paper.

### 3.56 (15 Oct, 03:10) Overnight: the privacy numbers get their intervals, the seeds replicate, and 500M leaks LESS

**(a) The headline privacy number, at 50 probes instead of 20.** NT 250M, chromosome 22, round 50,
128 restarts, real rare-variant haplotypes:

| tier | n | standard protocol | **search decoder** | oracle | LOO top-1 |
|---|---|---|---|---|---|
| r=16 | 50 | 18 % | **52 %** | 66 % | 0.96 |
| **r=1 (one copy)** | 50 | 2 % | **8 %** | 10 % | 0.57 |
| r=0 control | 50 | 0 % | **0 %** | 0 % | 0.08 |

The 20-probe estimates (25 % -> 65 % and 5 % -> 10 %) were in the right place but optimistic. At 50
probes the single-copy number is **4 of 50**, i.e. 8 % with a Wilson interval of roughly 3-19 %, and
the 16-copy number is 52 % against the standard protocol's 18 %. **So the under-reporting factor on
a released checkpoint is about three, and a real rare-variant haplotype present once is recovered
verbatim in roughly one case in twelve.** Both numbers go in with their intervals.

**(b) Three seeds, and the result replicates with spread.** NT 250M, E. coli, at round 15, which is
0.028-0.031 bits past each run's own optimum:

| seed | its optimum | round-15 floor | standard | **ours** | oracle | LOO |
|---|---|---|---|---|---|---|
| 0 | 1.823 | 1.851 | 0 % | **10 %** | 15 % | 0.70 |
| 1 | 1.824 | 1.855 | 5 % | **15 %** | 20 % | 0.71 |
| 2 | -- | -- | 0 % | **25 %** | 30 % | 0.77 |

Mean 17 % against the standard protocol's 2 %. The leave-one-out column is nearly constant across
seeds (0.70, 0.71, 0.77) while the recovered fraction varies 10-25 %, which is the signature of a
search-limited quantity and matches what the controlled backbone showed. At round 50 the two
measured seeds give 35 % -> 70 % and 25 % -> 80 %.

**(c) The 500M checkpoint leaks LESS under the matched decoder, not more.** NT 500M, E. coli:

| | held-out loss | from its optimum | standard | ours | LOO |
|---|---|---|---|---|---|
| round 3 (its optimum) | 1.798 | -- | 0 % | **0 %** | 0.01 |
| round 15 | 1.828 | +0.030 | 0 % | **0 %** | 0.48 |
| round 50 (standard protocol only so far) | 2.253 | +0.455 | **36 %** | running | -- |

At the same round and a comparable utility cost the 500M model has stored less (leave-one-out 0.48
against the 250M's 0.70) and the search decoder recovers nothing where it recovered 10-25 % at 250M.
That is the same direction our own backbone showed -- a larger masked model is less overfit after the
same number of passes -- and it cuts against the simple reading that scale makes leakage worse. Under
the STANDARD protocol at round 50 the 500M is the leakier of the two (36 % against 28 %), so the two
protocols disagree about the scale trend and the paper has to report both.

**(d) The membership result replicates in all three seeds, and its control is clean.** DNABERT-2 on
chromosome 22, single-copy real haplotypes, standard protocol at round 120:

| seed | held-out loss | single-copy recognition | single-copy verbatim | 16-copy verbatim |
|---|---|---|---|---|
| 0 | 1.599 | **0.80** | **0.00** | 0.50 |
| 1 | 1.593 | **0.70** | **0.00** | 0.40 |
| 2 | 1.607 | **0.80** | **0.00** | 0.30 |
| non-member control, all seeds | | **0.000** | 0.00 | -- |

Single-copy verbatim is 0.00 at **every** checkpoint in **every** seed, while recognition of the same
single-copy records reaches 0.70-0.80 and the never-trained control sits at 0.000 against a chance
level of 0.01. **A released checkpoint identifies which specific rare haplotype was in its
fine-tuning corpus, seven or eight times in ten, without ever reproducing it.** The dissociation is
not a one-seed artefact.

One caveat to close before this is written up: the non-member tier carries only 10 scored probes per
seed, so 0/10 is a clean separation from 0.70 but a weak bound on the false-positive rate itself.
More non-members is cheap and should be run.

**(e) Still running** (`queue_1014a`, `queue_finish`): NT 500M at round 50 under the search decoder,
NT seed 2 at round 50, DNABERT k=4 and k=5 on chromosome 22 to complete the flatness table on real
records, and the 3-mer utility curve at 50 probes, which was only ever done for the 6-mer.

### 3.57 (16 Oct, 09:00) The 16 Oct deck, rebuilt through the ppt-agent pipeline

Built the group-meeting section (slides 42-52 of the cumulative deck) with the `ppt-agent` skill
rather than by hand with python-pptx. The pipeline is HTML design drafts -> dom-to-svg -> native
PowerPoint shapes, so the slides stay editable in PowerPoint rather than arriving as pictures.

**Section**: a divider page plus ten content pages -- what changed since 9 Oct, the released-model
rule and its audit table, the test surface, the five findings, the mechanism with its negative
control, and where the paper stands. Eleven pages, each with the usual Chinese one-line summary and
the English speaking script in the notes.

**Three pipeline faults worth recording, because they will recur on the next deck.**

*(a) No mixed styling inside a line.* dom-to-svg emits one tspan per style run within a line, and
`svg2pptx` turns each tspan into its own non-wrapping textbox at a recomputed x. A bold phrase in
the middle of a sentence therefore lands the rest of the sentence on top of the phrase. Every
emphasis is now a whole line -- a bold lead-in above its paragraph -- which also reads better.

*(b) `<polyline>` is silently dropped.* `svg2pptx` has handlers for rect, text, circle, ellipse,
line, path and image, and none for polyline; the chart's two series vanished while the stats still
reported 0 skipped and 0 errors. Drawn as consecutive `<line>` segments they render correctly.

*(c) PowerPoint renders ~10.3 % wider than headless Chrome measures.* Measured, not estimated: a
line Chrome gives `textLength="538.109375"` comes out 593.6 px in the exported slide. Headless
Chrome does not get the real Calibri and falls back to narrower metrics, while PowerPoint
substitutes the deck's declared fonts (Source Serif 4, IBM Plex Sans -- neither installed on this
machine) with genuine Calibri. Since the line breaks are baked in by Chrome and each line is a
non-wrapping textbox, a line that merely fits in Chrome spills out of its card in PowerPoint. Text
is now laid out at 90 % of the available width, which absorbs it; verified by measuring glyph
extents in the exported PNG (text ends at 675-677 px against a card inner edge of 680).

**One content change made for honesty rather than for layout.** The Finding 5 chart first plotted
the downstream task score on an expanded 0.665-0.695 band, which made a series that moves by fifteen
thousandths look like a mountain -- the opposite of what the slide claims, and the exact chart crime
the section argues against. Both series now share one 0-1 axis: the task score is visibly flat while
single-copy identification climbs from 0 to 0.94.

Artefacts under `ppt-output/`: `style.json` (a `mocha_editorial` derivative retuned to this deck's
own measured tokens), `planning.json` (11 pages, passes `planning_validator.py` with 0 errors and 0
warnings), `slides/*.html`, `svg/*.svg`, `preview.html`. The deck itself is
`GLM Memorization - Spinoff Proposal (Group Meeting 1016).pptx`, 52 slides, built on the 41-slide
9 Oct deck. Automated `visual_qa.py` leaves two blank-space flags: the section divider, where the
whitespace is the design, and slide 45, which the 90 % text column pushes just over a 40 % heuristic.

Nothing here touches an experiment. `queue_util` and `queue_tighten` are still running and can only
tighten intervals.

### 3.58 (19-20 Oct) The decoder gets 41x faster, one claim is retired, and the tokenizer curve becomes a curve

Nothing between 16 and 20 Oct was written down, so this entry covers all of it. Four things
happened: a bug that had silenced every Nucleotide Transformer utility cell was fixed, a claim
already printed on slide 50 of two decks turned out to rest on a smoke-test probe and does not
survive the full one, the ICM decoder was rewritten and verified bit for bit, and the tokenizer
axis was finally measured at five cut sizes instead of three.

**(a) The NT branch of the downstream probe (`01d9ce5`).** `utility_at_leak` dispatches
Nucleotide Transformer runs as kind `"nt"`, but `_Backbone.forward` only knew `kmer` / `bpe` /
`hyena` and ended in `raise ValueError(self.kind)`. Every NT utility cell had been dying there
before producing a number, which is why the chr22 utility curve had three DNABERT-2 seeds and no
NT at all. The branch feeds `<cls>` followed by non-overlapping 6-mers, matching how `nt.py`
builds its training batches and how the scorers call the model, and trims the row to a whole
number of 6-mers because the vocabulary has no partial-k-mer token.

NT 250M on chr22, linear probe on frozen features, `n_train=20000`, GUE `prom_300_all`:

| checkpoint | held-out bits | r=16 verbatim | r=16 recognition | r=1 recognition | MCC |
|---|---|---|---|---|---|
| ckpt_ep15 (best saved) | 1.411 | 0.06 | 0.33 | 0.04 | **0.802** |
| ckpt_ep30 | 1.501 | 0.12 | 0.56 | 0.17 | 0.798 |
| ckpt_ep50 | 1.632 | 0.18 | 0.73 | 0.35 | 0.780 |
| final | 1.632 | 0.18 | 0.73 | 0.35 | 0.780 |

**(b) A claim retired.** The slide-50 statement -- "the task score's maximum is a checkpoint that
already leaks 20 %" -- came from `smoke_util.json`, the `n_train=2000` smoke probe, which put MCC
at 0.678-0.692 with its maximum at round 80. The full probe (`n_train=20000`, three seeds) puts
MCC at 0.787-0.802 and it **declines monotonically**; its maximum is round 15 for seeds 0 and 1
and round 50 for seed 2, and single-copy identification is 0.00 at all three of those points. So
on DNABERT-2 the metric does **not** point at a leaking checkpoint over a clean one.

What survives, and is still worth a slide: across the whole range the task score moves 1.1-1.5 %
while single-copy identification goes from 0 to 0.92-0.96. The metric carries essentially no
signal. The stronger form of the claim is available on NT instead, from table (a): there the
metric's own maximum, round 15, already reproduces 6 % of records and identifies 4 % of single
copies, because on real haplotypes NT has no clean checkpoint for the metric to point at.

**Slides 1016 and 1019 still carry the retired wording on slide 50 and have not been rebuilt.**

**(c) The ICM decoder, 141 s -> 3.4 s per probe (`d1a47b5`).** A cell was taking four hours at 31 %
GPU utilisation and 90 W of 450 W, which is what a 235M model looks like when it is called about
600,000 times at batch 1: 128 restarts x up to 6 sweeps x 8 target tokens per probe, each its own
forward, with roughly four host syncs per position-step -- argmax to int, two `.item()`
comparisons, and a 4096-wide `nonzero` to find the current token's row in the content table --
which is about two million syncs per cell. The restarts are independent and follow the same
schedule, so they now run as one batch; `changed` accumulates as a tensor and syncs once per
sweep; an index table replaces the `nonzero`; and a sweep that changes nothing leaves the state
its logits were computed from, so the pseudo-likelihood reuses them instead of recomputing eight
forwards per restart. Factor of 41.

Verified rather than asserted. Against the pre-batching code run on the same machine the same
day, `--chunk 1` reproduces every cell bit for bit -- the 128-restart Hamming vector, the chosen
prediction, the sweep counts, the leave-one-out numbers and the pseudo-likelihood score, 8 of 8
whole cells. That last column needed a fix: the old code summed the per-position terms as Python
floats and the new one summed them in float32, which moved the total by 1e-7 relative, enough to
reorder two restarts whose pseudo-likelihoods are nearly tied. The accumulator is float64 now.

`--chunk > 1` is a different arithmetic, not a different algorithm. bf16 picks kernels by batch
shape and ICM amplifies a last-bit logit difference into a different trajectory: across 16 cells
not one restart vector survived batching, yet 15 of 16 agreed on whether the attack succeeded and
the reported extraction rate was identical (8.0 % either way). The any-restart oracle moved from
18 % to 22 %. `--chunk 1` is kept as the setting that reproduces the old arithmetic exactly.

**(d) The machine's arithmetic changed across the reboot, and this is a methodological finding.**
`target_surprise` is code we did not touch and it runs at batch 1 in every case. It is bitwise
identical between two runs made today and 0 of 16 identical with the run made on 16 Oct. So the
16 Oct numbers are not reproducible on this machine regardless of any change of ours, and a
reported extraction percentage carries a run-to-run uncertainty of a few points that comes from
numerical sensitivity rather than from the probe count. **The binomial interval on the number of
probes understates the real uncertainty**, and the any-restart oracle -- a maximum over 128
stochastic restarts -- is the quantity most exposed to it. Either report that caveat or demote
the oracle to the appendix.

**(e) Seven cells re-run on one basis.** Because of (d), every n=50 cell was re-run with one code
path and one setting (`--tiers 16,1 --max_probes 50 --restarts 128 --chunk 64`). The 16 Oct
versions are archived unmodified in `outputs/pre_reboot_basis_1016/` (5 cells, 10 files). All
seven finished between 13:02 and 13:19 -- seventeen minutes for what the old decoder would have
spent about 28 GPU-hours on.

E. coli, 16 planted copies, 50 probes, `prefix` = the field's standard test, `icm` = ours:

| cell | target b/nt | standard | ours | oracle | LOO top-1 |
|---|---|---|---|---|---|
| 250M s0, ep15 (+0.03) | 0.971 | 4.0 % | **8.0 %** | 14 % | 0.72 |
| 250M s1, ep15 | 0.892 | 8.0 % | **8.0 %** | 22 % | 0.73 |
| 250M s2, ep15 | 0.888 | 4.0 % | **14.0 %** | 26 % | 0.75 |
| 250M s0, ep50 | 0.298 | 26.0 % | **66.0 %** | 84 % | 0.98 |
| 250M s1, ep50 | 0.275 | 26.0 % | **68.0 %** | 82 % | 0.97 |
| 250M s2, ep50 | 0.280 | 30.0 % | **76.0 %** | 88 % | 0.99 |
| 500M s0, ep50 | 0.307 | 36.0 % | **78.0 %** | 90 % | 0.99 |

Non-member controls read 0.0 % in every cell; the single-copy tier on E. coli reads 0 % throughout.

**This corrects the Finding-1 table in the 16 Oct deck.** The near-optimum row was written as
"standard 0 % vs ours 10-25 %". On one basis at n=50 it is **standard 4-8 % vs ours 8-14 %** --
the standard test under-reports by about a factor of two there, not infinitely. The far-past-optimum
row holds and is stronger than before: 26-30 % against 66-76 % across three seeds, and 36 % against
78 % on the 500M.

**(f) The tokenizer curve, read at matched held-out loss.** `core100` was re-run with five cut
sizes (`char 2mer 3mer 4mer 6mer`, AR, three seeds, uniform DNA) as `outputs/kcurve`, and
reproduces the original char/3mer/6mer cells exactly. Read at the final epoch it says nothing:
every k >= 3 saturates at 100 % extraction, including records planted once, so the table reads
0/0/1/1/1 and separates nothing. Read at matched held-out loss, which is what 3.11 did, it is a
curve. `pilot2/kcurve_report.py` produces it.

| tokenizer | slots for 48 nt | @2.05 | @2.10 | @2.20 | @2.40 | loss at 100 % |
|---|---|---|---|---|---|---|
| char | 48 | - | - | - | - | never |
| 2-mer | 24 | 0 % | 0 % | 0 % | 0 % | never |
| 3-mer | 16 | 0 % | 0 % | 0 % | 3 % | 4.15 |
| 4-mer | 12 | 0 % | 0 % | 2 % | 11 % | 3.01 |
| 6-mer | 8 | 1 % | **18 %** | **65 %** | **91 %** | **2.47** |

Controls 0.00 for every tokenizer at every snapshot. `char` has no entries because its held-out
loss never leaves 2.00-2.04 in thirty epochs -- it does not overfit far enough to reach the
comparison points, and extracts 0 % throughout.

Two readings. The ordering is monotone in the number of token slots the hidden 48 nucleotides
occupy, with no exception, and the right x axis is therefore the slot count rather than k -- which
is also why the released DNABERT family, whose tokens overlap so the slot count barely moves with
k, shows no trend. And the second column of the claim is cost: reaching full extraction costs 2.47
bits at 6-mer, 3.01 at 4-mer, 4.15 at 3-mer, and never happens at 2-mer or char. **Coarser
tokenisation does not only leak more, it leaks more cheaply**, which puts this result in the same
currency as the released-model numbers.

**(g) The window is configurable now (`83c7bee`).** `KmerTokenizer` asserts `window_nt % k == 0`
and 288 is not divisible by 5, so a 5-mer run could not be built at all. `WINDOW` now comes from
`PILOT2_WINDOW`, default 288 so every existing result and every unchanged command behaves as
before; 300 divides every k from 1 to 6. It is an environment variable rather than a flag because
several modules do `from .data import WINDOW`, which binds at import time -- setting it afterwards
would leave each module with a different window, which produces wrong numbers rather than errors.

The same commit fixes three analysis entry points -- `recon_audit`, `infill_audit`,
`natural_dups` -- that rebuilt a run's tokenizer with a literal 288. Left alone they would have
analysed a 300-nt run as if it were 288: wrong slot count, every probe offset resolving somewhere
else, and no error raised. They read the run's own `data_meta.json` through `data.window_of()` now,
falling back to 288, which is the window older runs were in fact built at.

**(h) Running, state unknown.** `kcurve300` was launched at 18:03 on 20 Oct: six tokenizers
(k = 1..6) x three seeds at window 300, with the matched-floor analysis chained after it so the
result lands in `outputs/kcurve300/MATCHED_FLOOR.txt` without supervision. `STATUS.txt` had
reached `START` when contact was lost. The server has been refusing connections on port 6004 since
some time on 21 Oct -- the second outage in four days, host pingable, so sshd or the port forward
rather than the machine. Whether the sweep finished before the outage is not known. It adds k=2
and k=5 to the curve above; it does not change any conclusion.

**(i) Also resolved --- and then resolved the other way; see the 2 Nov correction below.**
The HyenaDNA parameter count: the checkpoint `config/hyenadna_config.yaml` names has
**14,236,768 parameters**, counted from its own state_dict, which agrees with the BCB
paper's Table 1. The 6.55M recorded earlier in 3.6 was our miscount, and 3.6 now says so. Worth
keeping in mind for the paper: HyenaDNA at 14.24M and our controlled backbone at 12.9M are the
same size, so the 1-mer counterexample cannot be waved away as a scale effect.

**[Corrected 2 Nov.]** Every claim in the paragraph above is wrong except the file total.
`hyenadna-medium-160k-seqlen-hf` has **6,554,624 learnable parameters**. The 14,236,768 is the
count of values in its safetensors file, and 7,680,096 of those are `mixer.filter_fn.pos_emb.t`
and `.z` --- a uniform ramp from 0.0 to 1.0 of length 160,002 and five positional features of
it, byte-identical across all eight layers while the learned `implicit_filter` weights are not,
and sized by `max_seq_len: 160002` rather than by capacity. Take those and the 2,048 of
`filter_fn.modulation.deltas` out --- 7,682,144 registered buffers in all, the eight
trainable `filter_fn.bias` tensors not among them --- and 6,554,624 is recovered exactly, which is what every run's `train_summary.json`
recorded all along. The Table 1 meant above is the predecessor's, and it does
list HyenaDNA at 14.2M --- but that figure is the same file total, so the predecessor overstates
HyenaDNA's capacity by 2.17x, just as its 12.9M row is the number our own paper inherited.
The HyenaDNA paper itself gives "7 M" at 160k in Table 4.4 and 6.6M for an eight-layer,
width-256 model in the appendix, and `config.json` confirms ours is eight layers at `d_model` 256.

So the two models are **not** the same size, and the conclusion drawn above was too weak rather
than too strong: HyenaDNA at 6.55M is about half the controlled character model's 12,768,256 and
still recovers 65--100% of sixteen-copy records where ours recovers none. `p08_discussion.tex`
prints 6.55M and is correct as it stands. The figure to pair it with is 12.77M, the character
model's own recorded total, not 12.9M, which is the predecessor's number for a different
model (see the 2 Nov entry at the end of this log).

### 3.59 (21-23 Oct) Every chromosome-22 cell re-measured on one basis, the tokenizer sweep completed, and the paper written

**(a) `kcurve300` did finish, which closes 3.58(h).** All eighteen runs (k = 1..6, three seeds,
window 300) completed before the outage and the matched-floor analysis ran with them. The curve now
has every cut size:

| tokenizer | slots for 48 nt | @2.05 | @2.10 | @2.20 | @2.40 | loss at 100 % |
|---|---|---|---|---|---|---|
| char | 48 | - | - | - | - | never |
| 2-mer | 24 | 0 % | 0 % | 0 % | 0 % | never |
| 3-mer | 16 | 0 % | 0 % | 0 % | 2 % | 4.07 |
| 4-mer | 12 | 0 % | 0 % | 2 % | 12 % | 2.99 |
| 5-mer | 9.6 | 0 % | 2 % | 24 % | 61 % | 2.63 |
| 6-mer | 8 | 1 % | 17 % | 67 % | **92 %** | **2.47** |

Monotone in the slot count with no exception across six cut sizes, and monotone in what full
extraction costs. The window-288 sweep of 3.58(f) agrees where the two share a tokenizer: 2 % against
3 %, 12 % against 11 %, 92 % against 91 % at matched loss 2.40, and 4.07/2.99/2.47 against
4.15/3.01/2.47 for the cost of saturation. Two sets of runs at different geometries, one curve.

**(b) The nineteen chromosome-22 cells were re-run on one numerical basis (23 Oct, 20:51-23:34).**
`outputs/chr22_rerun/STATUS.txt` records `rc=0` on all nineteen and `ALL_FINISHED`. Every cell is 50
probes per tier, every cell on the same host after the reboot, so nothing in the table below is
comparing a pre-reboot number with a post-reboot one. The reports are now published as
`results/*/*/rb_*.{md,json}`, which they were not before: the newest reports in `results/` dated from
14-15 Oct, had 20 probes and 32 restarts, and disagree with these (the overlapping family read
10/0/10/0 % there against 2/0/4/0 % here). The 14-15 Oct cells are superseded, not averaged in.

| checkpoint | held-out bits/nt | 16 copies, standard | 16 copies, ours | 1 copy, standard | 1 copy, ours |
|---|---|---|---|---|---|
| NT 250M round 15 | 1.145 | 6 % | 6 % | 0 % | 0 % |
| NT 250M round 30 | 0.739 | 10 % | 28 % | 0 % | 0 % |
| NT 250M round 50 | 0.465 | 18 % | **52 %** | 2 % | **8 %** |
| NT 500M round 15 | 1.045 | 16 % | 14 % | 0 % | 0 % |
| NT 500M round 50 | 0.396 | 24 % | **58 %** | 0 % | **12 %** |
| never-trained control | - | 0 % | 0 % | 0 % | 0 % |

The first launch of this batch died instantly in nineteen cells on `data/human/chr22.fa`:
`GLMEXT_DATA` lives in `.bashrc`, which a non-interactive SSH does not read. That is the third time
the same `.bashrc` guard has cost a batch (conda, the proxy, now the data root), and the fix is the
same each time -- export it inside the script. Before relaunching I also checked that all four runs
name `canary_npz=/data/wh/yqdata/glm_data/human/canaries_chr22.npz`; without it they would have
fallen back to iid canaries silently and the whole human arm would have measured nothing.

**(c) Where our decoder reads zero, the leave-one-out probe says the record is there.** Asked for one
nucleotide of a planted record with the other 47 supplied, DNABERT-2 answers correctly 0.94/0.93/0.95
across three seeds for records planted **once**, which bounds whole-record recovery at 0.27/0.21/0.39.
Our BPE search returns 0 % from all three. The standard prefix-conditioned protocol, which is matched
to that vocabulary, returns 30 %. The released overlapping family behaves the same way and more
strongly: per-position accuracy 0.99-1.00 at 16 copies, implied ceiling 0.70-0.87, and our
nucleotide-level decoder recovers 2 %, 0 %, 4 %, 0 % for k = 3,4,5,6. Both zeros are limits of the
attack, not properties of the model, and the paper has to say so in both places -- it is the same
inference the field currently makes in the opposite direction.

**(d) `pilot2/rescore.py` (`29d6d12`) separates the measurement from the machine.** Scoring a saved
checkpoint again from its own `args.json` was not possible before, so every recognition number dated
from the day its run finished -- a problem once the host's floating-point behaviour changed across the
18 Oct reboot. Re-scoring a checkpoint whose old scores still exist answers the question the paper
has to answer anyway: identification reproduces **to the digit** (rank-1 0.800 before and after,
held-out loss identical to four decimals), while extraction on the same checkpoint moves by **six
points**, which is the same order as the binomial standard error on 50 probes. So: identification
quoted without an interval, extraction quoted with one.

**(e) Code, measurements and logs are public.** `pilot2/export_figure_data.py` flattens 3,844 score
files (725 MB) into `results/figure_data.csv` -- 27,106 rows, 2.3 MB, keyed on (group, run) because
`3mer_ar_s0` exists in both `kcurve` and `kcurve300`. That file, 201 MB of score output and these
notes are on `origin/glmex`. It was checked rather than assumed: the matched-loss cells recomputed
from the CSV reproduce the table in (a) cell for cell, including the window-288 column.

**(f) The paper is written end to end.** Eight sections, about 5,800 words, privacy first, in
`paper/sections/p0*.tex`, with Overleaf connected over its git bridge (`git.overleaf.com`, branch
`main`) rather than GitHub Sync, because the LaTeX is a subdirectory of a large repository. Three
things worth recording from the writing:

- The citations never compiled. `main.tex` loaded no `natbib`, so every `\citep` was an undefined
  control sequence, the key was printed into the running text and the bibliography came out empty:
  28 errors, all of them this. With `natbib` and `plainnat` the log is clean -- 0 errors, 0 warnings.
- Drawing the figures caught two wrong numbers and one broken cross-reference. The round-120 MCC
  range was quoted as 0.788-0.792 when seed 1 reads 0.7845; the downstream decline was called
  monotone when seed 2 rises at round 50 before falling again; and the paragraph on DNABERT's flat
  row cited `\S\ref{sec:slots}`, which is its own section, so the printed paper pointed the reader
  at the page they were on. Plotting a claim is a cheaper audit than re-reading it.
- Three figures are drawn, not five: `F5_slots`, `F6_ident`, `F7_blind`, by
  `pilot2/figures_privacy.py` from `figure_data.csv`. The planned probe-geometry figure was dropped
  because the text carries it, and the released-cost figure because Table 1 already does.

The compiled PDF is 12 pages: the extra title page the call allows, ten content pages, and the
references, which the call excludes. It fits, with three figures and five tables in it.

### 3.60 (23 Oct) The title was wrong for the venue, and the related work was missing this field's own literature

**(a) Three years of RECOMB titles, read rather than assumed.** The accepted lists for 2024 (57
papers), 2025 (55) and 2026 (65) contain **no paper with a manifesto subtitle**, so
``Reproduction Is the Wrong Alarm, and Tokenisation Explains Why'' had to go. The venue's own
privacy papers are named for the artefact that leaks: *Private Information Leakage from Polygenic
Risk Scores* (RECOMB 2026, Nikitin and Gursoy, Genome Research special issue), *TX-Phase: Secure
Phasing of Private Genomes in a Trusted Execution Environment* (2025), *Privacy Preserving
Epigenetic PaceMaker* and *Secure Discovery of Genetic Relatives* (2024). Declarative findings are
accepted too (*Synthetic control removes spurious discoveries from double dipping...*, 2025), so the
register is sober, not dull. New title, chosen by the user from four candidates:

> **Identification without Reproduction: Privacy Leakage from Fine-Tuned Genomic Language Models**

It states the paper's own claim, it reads in the venue's syntax, and it separates us from the
predecessor, which quantifies how much is memorised where we argue the usual ruler points the wrong
way. The slot mechanism is deliberately not in the title: it is the explanation, and putting it
there moves the reader's attention off the people being identified.

**(b) Attack papers do belong here.** Worth recording because it was an open worry: RECOMB has
published attacks on released genomic artefacts before. *Reconstructing Genotypes in Private Genomic
Databases from Genetic Risk Scores* (RECOMB 2020, extended abstract pp. 266-268; full version in
J. Comput. Biol. 28(5):435-451) and the 2026 polygenic-score paper above are both leakage results,
not protective methods. Our threat model is in scope.

**(c) Nine references added, all checked on 23 Oct.** The related-work section cited two CCS papers
on privacy definitions and nothing a RECOMB reader would recognise as genomic privacy. Added: Homer
et al. 2008 (allele-frequency membership), Shringarpure and Bustamante 2015 and von Thenen et al.
2019 (beacons), Paige et al. 2021 and Nikitin and Gursoy 2026 (polygenic scores), Erlich and
Narayanan 2014 (the survey for ``identification is the harm''), Oprisanu et al. 2022 (NDSS) and
Belfiore et al. 2025 (membership inference against generative models of genomes --- the nearest
neighbours by subject, though both audit model *output* rather than released weights), and Che et
al. 2026, **the one that matters most**: it proves the general form of our section 5 result, that
counterfactual memorisation and adaptive extraction do not bound one another in either direction,
with a construction that is fully extractable while loss-based audits certify it clean. Our result
is the measured instance of their theorem on released genomic weights, with a mechanism attached;
the paper now says so rather than letting a reviewer discover it.

The predecessor's entry is also fixed: accepted at ACM BCB 2026, DOI 10.1145/3807503.3819470, which
its own VERIFY note had been waiting for.

**(d) The audit notes are no longer printed (done 24 Oct).** `plainnat` renders `note`, so the
references carried lines like ``checked 10 Oct 2026 against the PDF'' and ``VERIFY volume/pages''.
`paper/strip_notes.py` now writes `refs_submit.bib` --- `refs.bib` with the `note` fields removed and
every other field copied byte for byte, so the submitted bibliography cannot drift from the audited
one --- and `main.tex` cites that. It cost a page: 13 pages became 12, references now 10-11.

The script also prints which entries still say VERIFY, because stripping them should not hide an
unfinished check from us. It listed five; three were resolved the same day against Europe PMC,
Crossref and arXiv:

- `vonthenen2019reidentification` is Bioinformatics **35(3):365--371**, 2019, and the DOI we had
  guessed is right (Europe PMC, PMID 30052749). Volume, number and pages were simply missing.
- `dalla2024nucleotide` is Nature Methods **22(2):287--297**, 2025 (PMID 39609566); only the issue
  number was missing.
- The predecessor is published, not merely accepted: **BCB '26, Rende, Italy, pp. 1--10**, ACM
  (Crossref record for 10.1145/3807503.3819470).
- `nikitin2026prs` is advance online publication, 17 Aug 2026, with **no volume or issue assigned**,
  so it cites as Genome Research 2026 with its DOI and no pages field --- the article id
  `gr.282202.126` would otherwise print as a page number.
- `belfiore2025bihmia`: the arXiv listing claims **no venue and no journal reference**. The AAAI
  2026 attribution came from a third-party lecture page whose date is inconsistent, so we cite the
  preprint. dblp sits behind a bot check and was not worked around.

Two VERIFY notes remain, both waiting on a publisher rather than on us.

### 3.61 (24 Oct) Reading the whole draft against the measurements: nine corrections, one of them a claim our own table contradicts

Checking every number in the draft against the files it came from, rather than against the previous
draft. Nine things, in the order they matter.

**(a) The downstream claim was wrong, and the true version is stronger.** Sections 4 and 7 said the
six downstream tasks never move more than one or two per cent while extraction goes to saturation.
`results/dnabert_gue_ds/utility_downstream.md` does not say that. Measured from each model's own
held-out optimum --- the checkpoint a practitioner stops at --- to the end of its run, over which
extraction goes from 0\% to 37--100\%, the frozen-probe MCC moves:

| model | largest move over six tasks | fine-tuned head |
|---|---|---|
| DNABERT 3/4/5/6-mer | 0.024 / 0.020 / 0.021 / 0.022 | ≤ 0.050 |
| DNABERT-2 | **0.083** (yeast H3) | 0.109 (H3K4me3, **upward**) |
| HyenaDNA | **0.066** (splice) | 0.032 |

Measured from round 0 instead, the splice task moves 0.12--0.17 on the k-mer models. The claim as
written was indefensible. What replaced it is the claim the objective-first draft made and this one
had lost: the score has **no consistent direction** with respect to the leak --- down 1.1--1.6 points
on chromosome~22, up on four of six tasks for DNABERT-2, so a practitioner watching the fine-tuned
head is told to keep training. Not flat. Uninformative, which is worse.

**(b) One cell in Table 4 was still on the old numerical basis.** NT 250M at round 30 read 12\%
there and 10\% in Table 2 --- the same checkpoint, the pre-rerun number against the 23 Oct one.
Fixed, and \S3's blanket sentence ``every cell was measured on one machine state'' is now the true
narrower statement: every cell read with our decoders and every NT cell were re-measured in the
nineteen-run batch; the identification rates and DNABERT-2's standard-protocol rates on
chromosome~22 are from the runs' own scoring passes. Identification is reproduced to the digit, so
only the latter needs the caveat.

**(c) HyenaDNA's 95\% was cited to the HyenaDNA paper**, which runs no extraction experiment. The
number is **ours** (`results/hyena*`, four corpora, 20 probes per cell): 65--100\% for records
planted sixteen times, 95\% at its best cell. And at a single copy it extracts **nothing**, like
every character-level model we ran --- which narrows the counterexample and is now said out loud.
Our character backbone still differs from it at sixteen copies, so the scope argument survives.

**(d) The never-trained control is 300 probes over 18 cells, not 350 over 19.** Three seeds, six
checkpoints, 10 probes at each of the first five and 50 at the last. The direction of the claim was
never in doubt --- not one was ranked first --- but the number was not reproducible from the files.
Four places said 350.

**(e) Which window is primary was contradictory in three places.** \S3 declared 288\,nt; \S6's prose
called the 300\,nt sweep a repeat of the 288 one; Table 3 and the figure are the 300\,nt sweep. The
fact is that 300 is the one length divisible by every $k$ from 1 to 6, and a 5-mer run cannot be
built at 288 at all, which is why the sweep moved. Said once, in \S3, and \S6 now matches.

**(f) ``Six released checkpoints'' was followed by a list of seven**, and with HyenaDNA, which we
measure, it is eight. Abstract and \S3 corrected.

**(g) ``Three decoders'' was followed by four**: the standard protocol and our three.

**(h) Round-80 identification is 0.20 / 0.20 / 0.40**, which is one in five or better, not better
than one in five.

**(i) The objective-first draft was still in the Overleaf project.** Ten files beside the current
ones, which is why Overleaf opened `09_discussion.tex` by default --- anyone browsing the project
read a draft that says different things about the same measurements. Moved to `paper/old/` in the
repository and removed from Overleaf, where its own history keeps it.

**Where that leaves the page budget.** The body now ends on printed page~10 rather than page~9: the
corrections cost about a page, mostly (a) and the \S3 caveat. Ten content pages is exactly the
limit, so the next addition has to be paid for by a cut. The candidates are Table~1's cost column,
which \S4's prose repeats, and the second half of \S2's scoring paragraph.

### 3.62 (24 Oct) Everything that should be in the paper is now in it, and it is one page over

User's call: write the content first, cut later. Three things were missing.

**(a) The objective axis, which is the largest effect in the project, was not in the privacy draft
at all.** It is in \S\ref{sec:blind} now, and it earns its place through how it \emph{fails}. On our
own backbone, same corpus and budget, replacing next-token with masked training takes extraction
from 100\% to zero in every cell --- four corpora, two mask rates, three cut sizes --- and
\emph{improves} held-out loss, 2.3--4.2 down to 1.66--1.98\,bits/nt. Verified from
`figure_data.csv`, not quoted from the old draft. And every released checkpoint in Table~1 was
pretrained with a masked objective and leaks anyway. So the lever is real from scratch and worthless
on released weights, which is the paper's own theme turned on a mitigation: a defence validated on a
backbone one trains oneself should be assumed not to transfer until checked.

**(b) There was no ethics section**, in a paper that demonstrates an attack, at a venue whose
privacy papers are mostly protective methods. \S9 now states that no real cohort was put at risk ---
every checkpoint we audit we fine-tuned ourselves on public corpora, we did not attack anyone's
released model trained on a private cohort --- what we do not publish (no reconstructed haplotypes,
no carrier identifiers, no fine-tuned weights), why the attack is described in full, and where the
code and measurements live.

**(c) The leave-one-out evidence was three numbers scattered across three sections**, while being
load-bearing in all of them. Collected into Table~\ref{tab:loo}: what is stored against what is
read, every released checkpoint on chromosome~22, from the 23 Oct batch. It also shows the one place
where a zero is \emph{not} a decoder limit: on the overlapping family the single-copy ceiling falls
to 0.01--0.02, so there the probe and the attack agree.

Section 8 also now says what we do not do about differential privacy, with the two things this paper
contributes to that question: audit identification rather than reproduction, and expect the slot
count to change what a given noise level buys.

**Page count.** The body is now printed pages 1--11, i.e. **one page over the ten-page limit**, with
references on 12--13 (excluded from the limit). Deliberate. The cut list, in the order I would spend
it: Table~1's \emph{cost} column, which \S4's prose repeats in full; the second half of \S2's
scoring paragraph; Figure~F7's second panel, which Table~4 already gives; and the first two
paragraphs of \S6, which restate \S3's setup.

### 3.63 (24 Oct) The appendix is this paper's appendix now, and its data tables generate themselves

`appendix.tex` was still the objective-first one, down to its title. Rewritten: what was measured
when and on which numerical basis (A1), probe geometry and real-canary construction (A2), the four
decoders and the leave-one-out ceiling in full (A3), per-seed cells behind every range in the main
text (A4--A6), the nineteen single-basis cells as measured (A7), numerical reproducibility (A8),
and the exact commands (A12). The controls from the earlier campaign --- placement, capacity and
parametrisation, the edge-conditioned audit, the split re-draws --- are kept, printed in blue, and
labelled in A1 as not re-measured, so nobody has to guess which era a number comes from.

**The data tables are generated.** `pilot2/appendix_tables.py` writes four `.tex` files into
`paper/tables/` from `results/figure_data.csv` and the reports beside it, and `appendix.tex` inputs
them. Transcribing 57 cells by hand is how a paper acquires a number no file supports; this way an
appendix cell that disagrees with the main text is a real disagreement. Two bugs found while
writing it, both the kind that fails silently: a bare `%` read out of a report starts a LaTeX
comment and eats the rest of the row, and the dispatch that picks a report's column layout was
keyed on the path, so every DNABERT $k$-mer run --- whose directory name contains `nt0.05`, the
mask rate --- went down the Nucleotide Transformer branch and twelve cells were dropped without a
word.

Compiles in Overleaf as its own document: 8 pages, no errors, one cosmetic float warning. The
project's main document was switched to `appendix.tex` to check that and switched back.

### 3.64 (24 Oct) The appendix has no open items left, and filling them corrected three more numbers

Five tables, all generated from the measurements rather than transcribed, plus the position-encoding
one that was the last TODO. The appendix now has zero \TODO markers.

**The best of them is the placement table.** The paper claims every canary offset is drawn rather
than fixed, because fixed placement manufactures a tokeniser effect. The explanation on record was
that a model with learned absolute positions can score a record from its position. That explanation
is wrong, and the table says so: with \emph{RoPE}, which has no learned absolute positions, fixed
offsets still take the 3-mer from 0--2\% extraction to 31--74\% at matched held-out loss, and the
6-mer from a cost of 2.40 to 2.05. The effect is about a record occupying one place in the corpus,
not about how position is encoded, which is why drawing the offset is the fix and changing the
encoding is not.

**The canary census.** 400 segments, 366 distinct carriers, no carrier contributing more than four,
2.07 rare variants per segment and 827 in total. The row worth reading twice: **248 of the 400 are
anchored on a variant carried by exactly one** of the 2,548 individuals. ``At most five carriers''
is the filter; most of these windows are built around something unique to one person.

**Three inherited numbers were wrong.**

- The edge-conditioned audit is **88 cells, 264 rows** with the tiers separated, not the 120 cells
  the old draft claimed. The conclusion is unchanged: no record comes back under either protocol.
- The across-draw spread of the canary split is **0.06--0.27\,bits at one copy and 0.07--0.64 at
  sixteen**, not the 0.04--0.11 on record, with the 5-mer least stable. And the fourth draw has no
  matched comparison at all: its models' overfitting branches do not overlap, so there is no common
  held-out loss to read them at. Both facts are now in the table.
- The published GUE comparison, which was a TODO rather than a number, is now real: against the
  DNABERT-2 row of Table 6 of the DNABERT-2 paper, our scaled-down recipe sits 0.039 (H3), 0.049
  (promoter), 0.057 (TF), 0.069 (H3K4me3), 0.086 (core promoter) and 0.095 (splice) below. The
  published H3K4me3 figure is itself only 0.363, so that task is a weak probe for everyone.

**On the two silent bugs from yesterday: fixed before anything was published**, and two more of the
same kind turned up today. The escaper was being applied to our own table labels as well as to data,
so `\quad` became `/quad`; and the draws header joined its two column groups without a separator.
Both were visible only by reading the generated file, which is the argument for generating it and
then reading it rather than trusting either step alone.

Appendix compiles on its own: 14 pages, no errors, no overfull boxes. The project's main document
was switched to it to check and switched back.

### 3.65 (25 Oct) Which host the identification is read in, a second architecture, the cohort sweep, and 50 probes

Four things, two of them from reading the data rather than from new runs.

**(a) The identification numbers never said which host window the record is read in, and two tables
used different definitions.** A canary is scored inside a host window. In the record's own genomic
context --- the real chromosome-22 sequence it was planted in --- DNABERT-2 reaches 0.92--0.96 at a
single copy. In a window the model never saw, the same records at the same checkpoint read
0.18--0.26. Both are far above the 0.0099 chance level and they answer different questions. Worse,
Table 4 was quoting a third thing, `utility_at_leak`'s `r1_recognition`, which averages the two
hosts: its NT rows read 0.04/0.17/0.35 where those cells are 0.08/0.30/0.64 in the record's own
context. Both columns are in Table 3 now, \S3 defines them, and Table 4 uses the same definition as
Table 3.

The own-context reading is the realistic one and the paper now says why: the host window is the
variant's real neighbouring sequence, so an adversary holding the candidate haplotype knows its
locus and can take that context from the reference. It is not privileged knowledge.

**(b) Nucleotide Transformer repeats the whole result and was not in \S5 at all.** Single-copy
identification rises to **0.64** (250M) and **0.74** (500M) by round 50, while verbatim recovery of
those records is 0.02 and **zero**. The 500M checkpoint is the cleanest instance in the paper: it
names three single-copy haplotypes in four and reproduces none of them at any checkpoint we saved.
The overlapping DNABERT family is the exception that fits: 0.00--0.06 at a single copy --- what it
cannot be made to write, it cannot be made to rank either.

**(c) The cohort-size sweep is run** (`pilot2/queue_scale.sh`, 10 runs, 9 minutes): n_train in
{1000, 2500, 5000, 10000, 20000}, two seeds, 6-mer next-token on real chr22 windows with real
haplotype canaries, 50 probes per tier, five snapshots scored. At matched held-out loss, single
copy:

| windows | best loss | id @2.05 | id @2.20 | verbatim @2.05 | verbatim @2.20 |
|---|---|---|---|---|---|
| 1,000 | 1.954 | 1.00 | - | 97 % | - |
| 2,500 | 1.910 | 1.00 | - | 96 % | - |
| 5,000 | 1.883 | 0.95 | 1.00 | 56 % | 94 % |
| 10,000 | 1.789 | 0.74 | 1.00 | 50 % | 82 % |
| 20,000 | 1.708 | **0.64** | 0.91 | **23 %** | 37 % |

**Dilution delays the leak and does not prevent it.** Twenty times the corpus divides single-copy
recovery by about four at 2.05 and takes identification from 1.00 to 0.64 --- and 0.15 bits further
into overfitting every size is identified at 0.91 or better. At each corpus's own optimum,
single-copy verbatim is 0 % at every size and 16-copy is 78--100 % at every size: the stopping rule
does the work, not the number of people. The confound is stated rather than hidden --- a fixed epoch
count at a larger corpus is more updates, which is why the table is read at matched loss and why a
matched-updates sweep is named as not run. \S8's first limitation is now \S7's fourth result.

**(d) The 50-probe re-scoring landed, and it moved several numbers.** Rounds 15--120 had been scored
during training with 10 probes per tier. With 50, on one basis:

- single-copy identification is **0.22--0.26 at round 50**, where 10 probes read 0.00, and
  **0.42--0.50 at round 80**, where they read 0.20--0.40. The trajectory starts two checkpoints
  earlier than the paper said.
- 16-copy identification at the best held-out checkpoint falls from 0.60 to **0.34--0.40**: the old
  value was a 10-probe overestimate.
- the control becomes the stronger statement: **3 of 900** never-trained segments ranked first,
  $0.0033$ against chance $0.0099$. ``None of 300'' could be read as a probe too blunt to produce a
  false positive; below chance on 900 cannot.
- the same batch re-measured that arm's standard-protocol extraction, so **\S3's caveat about older
  cells is deleted**: every cell behind a claim is on one machine state.

**One more silent bug.** `export_figure_data` anchored its regex on `scores_<ep>.json`, so every
re-scored file was invisible to the derived table, the figures and the appendix --- the better
measurement of the same weights, ignored. It now prefers `_rb` files where they exist.

### 3.66 (26 Oct) Three seeds for NT, the pool sweep, a column that held the wrong quantity, and four silent failures

**(a) The NT arm has three seeds.** Four runs, one per GPU (250M about 1h15, 500M about 2h50), with
only `--seed` changed from the s0 runs' own `args.json` --- same `data_seed`, so the
member/non-member split is identical and the spread is seed and not split. Single-copy
identification at round 50: **0.60 / 0.66 / 0.64** on the 250M with verbatim recovery at most 2\%,
and **0.74 / 0.90 / 0.86** on the 500M with verbatim recovery **zero in every seed**. The 500M claim
got stronger rather than weaker. Its spread tracks held-out loss --- the two new seeds sit
0.12\,bits further into overfitting at the same round --- which is the axis \S4 prices leaks in, so
the text says that rather than leaving it as seed noise.

A second pass ran the search decoder on the new checkpoints so Table 2's *ours* column has an
interval too: 250M returns **8\% of single-copy haplotypes in every one of three seeds**, 500M
12--18\%.

**(b) Table 2's second column held the wrong quantity.** It was labelled held-out \bits{} and
contained 1.145 / 0.739 / 0.465, which are the 16-copy canary's *target surprise*. The held-out
losses at those checkpoints are 1.411 / 1.501 / 1.632. A held-out loss of 0.465\,\bits{} on DNA is
not a thing a reader in this field would let past.

**(c) The pool-size sweep says the headline is not an artefact of a 100-segment pool.** Re-scoring
the same checkpoints against 50 and 200 candidates moves chance by a factor of four
(0.0196 to 0.0050) and the single-copy rate by at most 0.08:

| | pool 50 | pool 100 | pool 200 |
|---|---|---|---|
| DNABERT-2, three seeds | 0.96 / 0.92 / 0.98 | 0.94 / 0.92 / 0.96 | 0.94 / 0.92 / 0.96 |
| NT 250M | 0.64 | 0.64 | 0.56 |
| NT 500M | 0.78 | 0.74 | 0.72 |

200 is a ceiling, not a choice: the canary file holds 400 real segments and the members and their
matched controls are drawn from it first. Worth stating in the paper, because it explains why 100.

**(d) And it turned up a scorer result we had not looked for.** Identification needs a sequence
score, and the two available ones disagree as sharply as the decoders do: on NT 250M at round 50,
pseudo-log-likelihood ranks the single-copy record first **0.64** of the time where a
prefix-conditioned scorer manages **0.06** --- same records, same checkpoint. The same argument
\S3 makes about decoders applies one ruler up, and \S3 now says so and says which scorer we use.

**(e) Four silent failures in one afternoon, all of the same family.**

1. `echo "$(date) rc=$? ..."` reports the exit status of `date`: bash runs the command substitution
   before expanding `$?`. **Every rc=0 these queue scripts had ever written was the status of a date
   call.** Five scripts fixed to capture the status into a variable first.
2. NT names its snapshots `ckpt_ep<N>.pt` where the controlled backbone uses `ep<N>.pt`. With the
   wrong name `recon_audit` finds no run, prints one line and returns --- three seconds of nothing
   per cell --- and `rescore` raises FileNotFoundError. Four decoder cells and four pool cells failed
   this way, under a reported rc=0.
3. The appendix quoted the wrong checkpoint name in the command a reader would copy.
4. `rescore.py`'s NT branch, written 23 Oct, had never been executed: `nt.load` returns
   (model, parameter count), not (model, kind), so the first real call raised
   `KeyError: 235120780`.

The project's failures have a shape: **they are silent**. The `.bashrc` that a non-interactive SSH
does not read, a bare `%` eating a table row, a column-layout dispatch keyed on a path, an exporter
blind to re-scored files, and now a status line reporting the exit code of `date`. The practice that
catches them is the same every time: **count the output files, do not read the status line**.

### 3.67 (26 Oct) The compile that verified 3.66, and a fifth silent failure

The edits of 3.66 compile: **0 errors, 0 undefined references or citations, one underfull hbox,
15 pages.** Reading the PDF rather than the log turned up a fifth failure of the same family.

Two `\ref{tab:loo}` had lost their backslash --- a Git Bash heredoc ate it and left the `\r`
itself, so the file held a carriage return followed by `ef{tab:loo}`. The PDF printed
**"(Table eftab:loo)"** twice, in \S6 and in \S8's limitations. LaTeX raised nothing: `ef{tab:loo}`
is ordinary text, the label is still defined elsewhere, and so no undefined-reference warning
fires either. A clean log is compatible with a sentence that points a reader at nothing.

The two had drifted apart, which is why a single search did not find both. p06's still held the
carriage return; p08's had been normalised to a newline, so grepping for `\r` found one and
grepping for `ef{` on a line start found the other. The sweep afterwards --- every stray control
character, every macro head that survives losing a backslash (`ef`, `ewline`, `extbf`, `egin`,
`imes`, `ho`, `ight`) --- is clean across all twelve source files.

The project's note against heredocs was already written (3.47, backslashes) and this is what it
costs when it is not followed: the damage is invisible to the tool that is supposed to catch it.
**The compile log is a check on LaTeX's syntax, not on ours.** Read the PDF.

### 3.68 (27 Oct) The own-window rate survives its control, 235 of the 400 planted windows belong to nobody, and the BPE decoder's 0% is its own objective

Three things the pre-submission panel broke were followed to the measurement rather than to an
argument. Two of them held up; one did not, and the one that did not was ours.

**(a) The own-window identification rate had no control at all, and it survives the one it now
has.** Every scoring pass built `hosts["train"]` only for probes with `repetitions > 0`
(`score.py`, `dnabert.py`, `dnabert2.py`, same three lines in each), because a never-trained record
has no training row to be scored in. So the own-window rate was read against the *fresh-window*
control, and those two conditions differ in two things at once: membership, and whether the window
is one the model was fine-tuned on. A rate of 0.94 against a control of 0.00 does not separate the
record from its flanks.

`data.borrowed_hosts` lends each control a member's training row and that member's own offset. The
probe region is overwritten by every candidate exactly as it is for a member, so the conditioning
is identical --- same memorised flanks, same offset, same hundred real rare segments in the pool
--- and the only difference left is whether the model has seen the 96 nucleotides now sitting
between those flanks. If anything the control is harder, because the record the model *did*
memorise at that offset is competing.

All eighteen cells of Table 3 were re-scored (`queue_1027_bh.sh`, three GPUs, 23 minutes, nothing
retrained, nothing overwritten). **Every member number reproduced to the digit --- 108 of 108
comparisons at +0.000, and all 18 held-out losses at +0.0000** --- which is also the check that the
patch disturbed nothing. The borrowed-host control reads **0.00 to 0.04 across all 18 cells**
against members at 0.74 to 0.96 in the same condition, and **0.02 / 0.00 / 0.00 at the final
checkpoint against 0.94 / 0.92 / 0.96**. The own-window rate is a property of the record, not of
the host window.

What did *not* survive is §3's reason for reporting it. The section said the own-window context is
not privileged knowledge, "because anyone holding the candidate haplotype knows the variant's
position and can take the surrounding sequence from the reference". That is false about this
experiment: `real_data.build_real_dataset` assigns each copy `remainder[ridx % len(remainder)]`, an
unrelated 288 nt reference window from the part of the genome the splits leave unused, at an offset
the fine-tuner's generator drew. **A canary's flanks are not its genomic neighbourhood**, so an
adversary holding only the weights has neither the window nor the offset. The condition is now
described as what it is, and the rate as what an adversary holding the corpus too could reach ---
which is what the abstract already said, for a weaker reason than the real one.

And a lesson about counting controls. Each row of 900 is 50 records re-scored in 18 cells, not 900
trials. `count_control_hits.py` now names the distinct records behind any total: the 13 own-window
rank-1 scorings are **3 distinct records** (probes 159, 175, 197, each ranking first at several
consecutive checkpoints), and the 3 fresh-window ones are **one record** (probe 175, the same one).
The interpretable figure is the per-cell count, 0 to 2 of 50. This is the same error, found a
second time, that produced "3 of 900, below chance" in the submitted draft.

**(b) 164 of the 400 planted human windows are a sequence a real chromosome carries. 235 are
carried by nobody.** The paper called them "haplotypes, each carried by at most five of the 2,548
individuals". The bound was established for the *anchor* variant only. `build_canaries` then
substitutes every rare ALT inside the 96 nt window from a position-keyed table shared across all
anchors, and never asks whether the anchor's carrier carries those neighbours or which of that
person's two chromosomes any allele sits on. With 619,639 rare biallelic SNVs on chromosome 22 the
density is about 1.2 per 96 nt, so most windows pick one up: 237 of 400 carry more than one.

`canary_haplotype_audit.py` settles it from the phased genotypes, recording for each rare variant
the exact set of (sample, chromosome copy) pairs carrying the ALT and intersecting those sets across
the alleles actually substituted. **164 windows are real haplotypes** --- 163 of them the
single-variant ones, which are haplotypes trivially, plus one composite --- with the number of
carrying chromosomes 1 for 98 windows, 2 for 27, 3 for 20, 4 for 10 and 5 for 9, **never more than
five**, so "at most five" is exact for that subset. One window is a real genotype split across both
of one person's chromosomes. **235 are carried by no chromosome in the cohort**: realistic rare
human sequence, and nobody's.

Nothing about the leakage measurement depends on whose sequence was planted, so no rate changes.
What changes is which sentences the paper may write, and the ethics statement in particular, which
said every window was "written with a real carrier's alleles". `analyze_canary_status.py` splits
every rate by subset, matching probes to canaries by sequence (exact: 150 of 150 matched, no
collisions). **One rate separates**: single-copy identification in a fresh window is
**0.30 / 0.30 / 0.48** on the real haplotypes against **0.04 / 0.13 / 0.00** on the rest, n=27 and
n=23 per seed. The own-window rate differs by at most 0.07 per seed with no consistent sign,
verbatim recovery is zero in both, and **the never-trained controls read zero in both subsets** ---
which is what rules out a generic preference for one kind of sequence and shows the gap appears only
among records the model trained on. So the paper's new headline is *stronger* on the subset the
privacy claim describes, and it was being averaged down by 235 windows that the claim never
described.

`human_canary.py --phased` rebuilds the set properly: choose a carrier chromosome first, then write
the window as that chromosome reads it. Doing it correctly needs a **second pass over the VCF**,
because a window also holds variants too common to pass the rare filter and leaving those at the
reference base is by itself enough to make the sequence nobody's --- on the 38,400 positions inside
the chosen windows the full carrier sets fit in memory. The rebuilt set is 400 windows each one real
chromosome's own sequence, **252 of them unique to a single chromosome** among the cohort's 5,096
and none shared by more than five; 37 common alleles are written in across the 400, which is the
part the original construction could not have got right. `verify_phased_canaries.py` checks it
against the reference and the genotypes independently of the builder --- sequence equals reference
plus exactly the recorded substitutions, the named carrier chromosome carries every substituted
allele, the carrier count recounts, no window is left identical to the reference --- and **all six
checks pass on all 400**. The default path is untouched, so the reported measurements stay
reproducible; the rebuilt set is what any extension should plant.

**(c) The BPE re-masking decoder's 0% is a property of its own objective.** `recon_bpe.nt_dist_bpe`
scored candidate letter *a* at nucleotide *j* by writing *a* in, re-tokenising, masking every token
whose span covers *j*, and dividing the summed log-probability of those tokens by the nucleotides
they cover. The division was there to make candidates comparable, since different candidates
re-segment the window. But **the divisor depends on the candidate, and a log-probability is
negative, so whichever letter happens to segment into a longer span is pulled towards zero, which
is towards winning.**

Measured on the released vocabulary with no model involved at all
(`diag_bpe_denominator.py`, 1,920 positions in real planted windows): the covering span averages
5.3 nt and the spread across the four candidates averages 1.79 nt, up to 11. At the 1,435 positions
where the divisors differ, **the largest divisor falls on A 707 times against 359 expected**, with
C 312, T 229, G 187 --- and "continues the run to the left" is only 0.291, barely above chance. So
this is a **vocabulary-level letter prior created by the division**, not the homopolymer-merge story
I first assumed; per-letter mean covered span is A 5.51, T 5.47, G 5.17, C 5.12.

Iterated over 48 positions that prior is enough to decide the output. In `rb_epfinal.json` for seed
0, probe 102 is reported as **48 A's** at Hamming 32, and the truth-free selection step chose it
over restart 7 at Hamming 26 --- while the leave-one-out ceiling for that same record reads
**top-1 1.00 at 0.001 bits**. The content is entirely present and the search reports nothing. Note
also that restart 0 is initialised to all-A, so the decoder was handed that basin and never left it.

`nt_dist_bpe_fixed` picks a nucleotide interval around *j* that is token-boundary aligned under all
four candidates (`union_span`, grown to a fixed point), scores exactly those nucleotides for each
candidate, and **divides by nothing**: the masked event is "this interval reads thus", the
conditioning is the identical remainder of the window, and the four events differ only at *j*. The
update becomes a block conditional on the interval, which is a stronger ICM proposal rather than a
weaker one. One residual remains and is documented rather than hidden: candidates still decompose
the interval into different numbers of masked tokens, and a product of masked-token marginals is not
the joint, so a segmentation with fewer factors is still mildly favoured --- same direction as the
old bias, but no longer multiplied by the span. `score="pernt"` keeps the old path so the submitted
numbers stay reproducible.

Re-decoded on the same 60 cells (`compare_bpe_scorers.py`, which intersects on probe id because the
two runs used different `--max_probes`), the difference is not subtle:

| | divided score | fixed interval |
|---|---|---|
| one letter covers >= 3/4 of the output, 16 copies | **0.95** | **0.00** |
| ditto, 1 copy | 0.85 | 0.05 |
| ditto, never-trained control | 0.75 | 0.00 |
| Hamming of 48, 16 copies | 34.9 | **30.1** |
| Hamming, 1 copy | 32.1 | **30.6** |
| Hamming, control | 34.6 | **35.8** |
| exact recovery | 0.00 | 0.00 |

Chance Hamming is 36.0. Under the divided score the control at 34.6 sits *between* the two member
tiers, so the decoder separated nothing; under the fixed interval the members are at 30.1 and 30.6
and the control at 35.8, which is chance. **The decoder now tracks the record, and exact recovery is
still zero.**

So the paper's 0% for this family stands as a number but changes meaning. It was measuring a letter
prior; with the prior removed it measures our search's limit, which is what §3 claims the
leave-one-out ceiling is there to establish, and the ceiling under the new objective is 0.78 at
sixteen copies and 0.17 at one. Two things were true at once and only one of them was ours. The
general point is now in §3: **a decoder reading zero is worth inspecting and not only tabulating**,
and what found this was reading the decoded strings and seeing runs of a single base. Any BPE
decoder that normalises by the span its own candidate happens to cover has the same defect.

One unit to watch: `loo_bits_per_nt` is not comparable between the two scorers, because one scores a
nucleotide's covering tokens and the other a whole interval. It now carries a `loo_bits_unit`
beside it; only `loo_top1` and the Hamming distances compare.

**(d) Two more silent failures, both mine.** The rescore queue died in 50 seconds on all 18 cells
because `GLMEXT_DATA` was unset --- **the fourth time the `.bashrc` guard has cost a run** (conda,
proxy, data root, now this). And the fixed decoder ran a full 40-probe decode and then threw
`TypeError: Object of type ndarray is not JSON serializable`, because the new `score` parameter I
added to `icm_bpe` is shadowed by the function's own `score = np.zeros(restarts)` selection array:
the returned `"scorer"` field was that array. Dispatch was unaffected, `dist` being bound before the
shadowing, so the decode itself was correct and only the write failed. **A new parameter needs a
name the body does not already use; `git grep` the name in the function before adding it.**

Also the heredoc rule (3.47, 3.67) cost me a third time today: `"\\S\\ref{app:haplo}"` in a Git Bash
heredoc arrives at Python as `\S` + carriage return + `ef{...}`, so the pattern matched nothing and
the script reported 0 replacements instead of failing. **Any script whose text contains a backslash
goes in a file, not a heredoc.**

**(e) The paper is now about 14.5 pages of body against a 10-page limit.** The three items above
added roughly two pages: §3's host-window definition, §5's subset split, and two new appendix
sections (A3, A4). The appendix also numbers its own tables and figures A1, A2, ... now --- it was
calling its own second table "Table 2" while the main text has a different Table 2 and the two PDFs
are submitted side by side. The cut list from 3.62 is unchanged and now has more to do.

## 4. Open items

- F4, the probe-geometry figure, is drawn and committed (`paper/figures/F4_probe.pdf`,
  `figures_privacy.py --only probe`) but deliberately **not placed in the paper** (user, 26 Oct).
  Placing it costs about 0.4 of a page; the intended payment is compressing the first two
  paragraphs of the slot-count section, which restate the setup.

- HyenaDNA (pretrained 1-mer, causal) as the second real-model anchor — not started; needs its HF code to load under transformers 4.29.
- Utility metric next to memorization (Erman) — needs real data; plan: held-out loss on E. coli + a small downstream probe.
- Explanation for "smaller tokens overfit less at equal memorization" (Erman) — hypothesis: context collision; test pending.
- Figures + one-paragraph explanations for Alex's proposal update (mid-October).

---

## 28 Oct 2026 — the pre-submission experiment audit, all 14 (A) items verified

An agent sweep classified the paper's unbacked claims into (A) must measure (14), (B) stronger if
measured (12), (C) reword (25). The classification was not reliable: of the nine (A) items checked
first, one was simply wrong, one had its direction reversed, and the remaining seven were real but
differed in detail from the report. The six left over were checked today, and the (A) list is much
shorter than 14.

### A2 — the k-sweep has no per-nucleotide measurement (queued, running)

The worst of the fourteen, because it sits in the **abstract**: "models differing only in
tokenisation answer any single hidden nucleotide identically", with S6 closing on "both ends of
tab:slots learn a planted record to the same per-nucleotide accuracy". `outputs/kcurve300` held no
recon files at all. The 0.99--1.00 figures S6 cites are the DNABERT family's, not this one's.

Two things had to be settled before it could run.

The family is **autoregressive**, and `extract_icm` opens with `if kind == "ar": return None`. The
leave-one-out conditional tab:loo reports — every other target position at its true value, one
masked — is a masked-model quantity and does not exist for a causal model. So A2 cannot produce a
leave-one-out number here at all, and the paper must not imply it did. The AR analogue is
`target_bits_per_nt`, which is per nucleotide and therefore comparable across tokenizers;
`top1_rate` is per **token** (a 6-mer step covers six nucleotides, a char step one) and must be
reported as such if at all.

`PILOT2_WINDOW=300` is load-bearing. `data.py` reads `WINDOW` from that env var at import,
defaulting to 288, and `recon_audit.py` passes `window_of(run_dir)` to the tokenizer but the module
constant to the hosts and offsets. These runs are window 300, so without the export
`6mer_ar_s0/ep30` reads target 2.267 b/nt, top1 0.00, prefix 0.0% at a checkpoint whose published
`exact_rate` is 1.00 — silently, no error. With it the same cell reads 0.005 b/nt, top1 1.00,
prefix 100.0%. Verified both ways before queueing. Seventh member of the silent-environment family.

`pilot2/queue_1028c.sh`: 6 tokenizers x 3 seeds x {ep5,8,12,20,30}, 90 cells, 100 probes per tier.
ep1--3 are omitted: all six tokenizers sit at held-out 2.00--2.02 there with 0% extraction.

Also recorded: tab:slots is read at matched held-out loss 2.05/2.10/2.20/2.40 and **no checkpoint
sits on any of them** — the table interpolates between saved epochs, so anything compared against
it must interpolate the same way. And the character model never exceeds 2.044 bits/nt in thirty
epochs, so the two ends of the sweep never meet above that: "both ends at matched loss" has no
matched point above 2.04, where both extract ~0%.

### A10 — four tokenizer claims asserted from published descriptions. All four true.

`pilot2/tokenizer_audit.py` -> `results/tokenizer_audit.json`.

| claim | measured |
|---|---|
| NT "six nucleotides per token without overlap" | 288 nt -> 48 tokens, every observed width 6, overlap False |
| DNABERT "k-mers overlap, advancing one nucleotide" | stride 1 and overlap confirmed, 286/285/284/283 tokens = W-k+1 exactly |
| DNABERT-2 "token length varies with content" | observed widths 2--8; vocabulary 1--32 |
| "between 1 and 32 for byte-pair encoding" | vocabulary width min 1, max 32 — exact |

Bonus: it makes S6's pre-registered prediction quantitative. The hidden 48 nucleotides occupy
48+k-1 slots under stride 1, so **50/51/52/53** at k=3/4/5/6. "Stays near 48 whatever k is" is a
measured 50 to 53, against 48 down to 8 in the non-overlapping sweep.

Two traps: DNABERT's released tokenizer wants space-separated k-mers, so a raw 288-nt string
returns one `[UNK]` — an earlier version of the script read that as 288 nt per token for all four
checkpoints. And it must run as a module, because `pilot2/tokenizers.py` shadows the Hugging Face
`tokenizers` package when `pilot2/` leads `sys.path`.

### A11 — per-person TPR. Reclassified (A) -> (C): a mapping, not a measurement.

The discussion's "has shipped a model that will tell an adversary which of their participants it
was trained on" is per-individual where every rate is per record. The audit asked for per-person
aggregation and TPR at a controlled FPR. It is not needed, and would not help:
`pilot2/carrier_audit.py` -> `results/carrier_audit.json`.

- 400 canaries, **366 distinct carriers**: 335 people contribute one canary, 29 two, two of them
  three or four. Pooling across a person helps 31 people and changes nothing for 335, so a
  per-person rate is the per-record rate under another name.
- The anchor variant of **248 of the 400** is carried by exactly one of the 2,548 individuals, and
  **312 of the 400** contain at least one such variant.

So for 62% of canaries the anchor alone names a unique person, and S5's metric (rank first against
100 real rare segments, chance 1/101) is already a low-FPR operating point. The claim is supported
without new measurement, and is understated rather than overreaching. What the paper lacks is the
sentence stating the mapping.

### A13 — capacity controls at fixed placement. True, and already disclosed. (A) -> (B).

`tab:capacity` is referenced only inside the appendix. S6 lines 88--90 scope the spaced-tokenizer
numbers explicitly: "Both are from the 28 September batch and sit at fixed canary placement, which
inflates every rate in them, so they are read against each other and not against Table tab:slots".
The appendix repeats it at lines 84--85. Re-running at drawn placement would strengthen the
spaced-tokenizer comparison; nothing currently printed is misleading.

### A14 — variance decompositions with nothing behind them. Confirmed, and one number was wrong.

The three sets of shares were **hard-coded literals** in `figures_paper.py`'s `fig_variance()`,
whose docstring records the command they came from but not its output: the figure could be redrawn
and not regenerated. `pilot2/variance_audit.py` recomputes all three from the stored score files
into `results/variance_decomposition.json`, and all three reproduce exactly:

| arm | tokenizer | objective | interaction | seed |
|---|---|---|---|---|
| drawn, full grid (24 runs) | 12.0 | 67.1 | 21.0 | 0.0 |
| fixed, full grid (18 runs) | 59.5 | 25.7 | 14.0 | 0.8 |
| drawn, 3 shared tokenizers (18) | 15.4 | 57.7 | 26.9 | 0.0 |

The last matches the F3 caption's "57.7, 15.4, 26.9 and 0.0" to the digit.

**The placement paragraph was wrong.** It read "59.5% to the tokenizer under fixed placement and
25.7% under drawn placement". Tokenizer-under-drawn is 12.0 on the full grid and 15.4 on the
shared-tokenizer subset; 25.7 is the **objective** share under **fixed** placement — the wrong
cell of the same table. The two arms carry different tokenizer sets, so the like-for-like pair is
the shared-tokenizer one, which is why the caption restricts to it. Fixed to 59.5% against 15.4%,
with the objective going 25.7% to 57.7% the other way. Pushed to Overleaf, compiles clean.

### A3 — the BPE ranking divisor. Scoped; no retraining needed.

`dnabert2.py:163--178` is the chain:

    bits = tot / cov        # cov is CANDIDATE-dependent: BPE re-segments each candidate
    s = -bits * PROBE_LEN   # a constant
    rank = 1 + (cands > true).sum()

Multiplying by a constant does not change an ordering, so this ranks by `-tot/cov`: bits per
nucleotide with a **candidate-dependent divisor**. A candidate whose segmentation happens to cover
more nucleotides has its total surprise divided by a larger number, which lowers its bits/nt and
raises its score regardless of how probable the sequence is. The measured divisor spread is
96--107 nt, about 11%, far wider than the gaps between candidates in a tight pool.

By contrast `score.py`'s `rank_probe` has no divisor in the ordering at all: one shared span is
computed once from the offset and raw summed log-probs are compared, so the fixed-width family is
clean. For BPE identical token spans are impossible, so the ablation is a three-way re-rank of the
existing scorings — current `-(tot/cov)`, raw `-tot`, and a span-matched total that attributes each
token's log-prob across the nucleotides it covers and sums over exactly the 96 probe nucleotides.
One forward pass per candidate per probe; no retraining. It bears on DNABERT-2's identification
numbers in tab:ident and S5.

### Where the (A) list stands

Must still measure: **A6** (NT ICM is seed 0 only), **A3** (the ablation above), and the n=50
re-scorings for **A7** / **A5** if those rows are to be kept as printed rather than narrowed.
Reword only: A4 (the agent misread; `icm-confidence-r128` has 86 files, 128 is real), A8, A9, A11,
A12, A13. Done today: A10, A14.

### Queues

- `queue_1028.sh` phase A (36 donor-tier cells) + phase B (DNABERT k=3--6 human retrain with the
  borrowed-host control, 12 runs): **ALL DONE 07:33 UTC**, every cell rc=0.
- `queue_1028b.sh` overlapping family at n=50: running. Two rc=1 are cosmetic —
  `scores_ep150_n50.json` was written for k=4 and k=5; only `--compare` failed, because no n=10
  ep150 scoring exists to compare against.
- `queue_1028c.sh` A2: running, 39/90 cells.

---

## 28 Oct, 10:15 UTC — A3, A6 and the n=50 re-scoring: the (A) list is empty bar two E. coli cells

Three queues finished within an hour of each other. All three results defend the paper rather
than change it, which is worth saying plainly after A2 went the other way this morning.

### A3 — the ranking divisor does not carry the identification numbers

`dnabert2.py:163-178` ranks a candidate by `-(tot/cov)`, and `cov` depends on the candidate, so
the ranking compares quantities of unequal length. `pilot2/bpe_divisor_ablation.py` recomputes
three rules from one forward pass: that one, the undivided total, and a span-matched score that
attributes each token's surprise across the nucleotides it covers and sums over `[o, o+2L)` alone.
Five checkpoints — three human seeds at the end of training, E. coli seed 0 at round 30 and at the
end — four tiers, both host conditions, fifty records: 2,000 cells.

| | current | raw_total | span_matched |
|---|---|---|---|
| single-copy, fresh host (the headline) | 0.18–0.26 | 0.18–0.26 | **0.22–0.28** |
| never-trained controls, pooled | 0.014 | 0.016 | 0.014 |
| rank-1 verdict differs from `current` | — | 20/2000 = 1.0% | 33/2000 = 1.65% |

Where the rules disagree the span-matched one reads **more** leakage, so the divisor is
conservative. S3 now carries the measurement in place of the argument from mean covered span
(100.2 against 99.7), which was true but not the point.

Validated before being trusted: the `current` rule reproduces the ranks the runs themselves
published on every comparable cell, including the tier-0 controls at rank 92 and rank 44.

### A6 — tab:loo's NT rows, and a provenance defect found on the way

The audit said "NT's ICM exists only for seed 0". Half right, and the correction mattered for what
had to run: NT 250M on E. coli already had seeds 1 and 2; the **human** arm — the arm tab:loo
reports — had none. Weights were on disk for all four, so this was a probe and not a retrain.
128 restarts, 50 records per tier, all six runs through one identical invocation:

| checkpoint | copies | LOO top-1 | ceiling | standard | ours |
|---|---|---|---|---|---|
| NT 250M, round 50 | 16 | 0.96–0.97 | 0.81–0.85 | 16–18% | 48–54% |
| | 1 | 0.57–0.66 | 0.14–0.23 | 0–2% | 8% |
| NT 500M, round 50 | 16 | 0.96–0.99 | 0.84–0.92 | 24–50% | 58–72% |
| | 1 | 0.67–0.80 | 0.24–0.41 | 0% | 12–18% |

The extraction columns reproduce the ranges the S4 table already printed, which is the check worth
having: those columns were three seeds all along, and it was the leave-one-out probe that was one.
The single-copy ceiling range in the S4 prose moves 0.14–0.39 → 0.14–0.41 and the attack range
0–12% → 0–18%, both only because the table now carries three seeds.

**The defect.** tab:loo's "NT 500M, 16 copies, ours 58%" did not exist in that run's
`recon_r128_ep50.json`, which reads 0.54. It existed only in `rb_ep50.json` from a later batch, so
one row was spliced from two files. The decoder is deterministic given its config — seed 0 of the
250M reproduced its own 23 Oct file to the cell at every tier — so this was a code-version
difference, not noise. Re-running seed 0 under the same command as the other five
(`pilot2/queue_1028f.sh`) returns **0.580** and reproduces every other cell exactly: 58% is right
and the 16 Oct file is the stale one, two records of fifty. The re-run is kept as
`recon_r128_ep50_rerun` so the 16 Oct file stays on disk and the splice stays checkable.

### S6's \TODO — the overlapping family's trend is not four records

The prefix-protocol trend was 0/0/10/40% at the ten records per cell the run had scored, so the
four recovered records at k=6 were the whole of it. All fifty records of every human cell are now
scored at rounds 120 and 150:

- training window: **0 / 2 / 6 / 50%**
- fresh window: **0 / 2 / 2 / 36%**

The trend survives and strengthens at k=6; single copy stays at 0% for every k under both hosts.
tab:loo's standard column for that family moves 0–40% → 0–50%, and its caption no longer says the
column is read at ten records. On E. coli, at the same round, the same trend reads 0/0/10/58%, so it replicates on a
second corpus at the full probe set; that clause is now in S6.

### Also corrected

S8 said our searches "return nothing" for both of the families whose ceiling it quotes, where its
own table says 0% and 0–4%. Found by reading tab:loo against the prose that cites it.

### Where the (A) list stands

**Empty**, bar the two E. coli cells above. A2, A3, A6, A10 and A14 are measured; A11 and A13
became (C) and (B) on inspection; A4 was the agent's misreading. A7 / A5 n=50 re-scorings remain
optional — they narrow rows that are already correct as printed.

### State

GitHub `0b68859`, Overleaf `bab8571` (three topic commits), compiled from a clean checkout of what
was pushed: **errors=0, undefined=0, 21 pages**. The page budget is still the open item and the
cuts are the author's call.

### Two things to settle before submission, neither of them mine to decide

1. `\NUM{}` is defined in `main.tex` as "number still pending a run; must be black at submission",
   but `appendix.tex:39` tells the reader blue means "from the earlier measurement campaign".
   Two conventions for one macro, 18 blue numbers in the appendix.
2. 21 pages against a 10-page body limit.


## 28 Oct, 12:40 UTC — the NUM convention goes black, and the appendix gets compiled for the first time

The conflict is settled the way `main.tex` wrote it: **blue is a drafting colour, and nothing in the
submission is coloured.** Three coupled changes, because the appendix had two sentences promising
the reader that colour.

- `\NUM{}` is the identity in both preambles, with a comment saying how to flip it back to blue
  while drafting. The call sites stay in the source, so which numbers sit on the earlier
  measurement basis is still recoverable from the `.tex`.
- The convention sentence at the head of the appendix no longer names a colour. It points at the
  enumeration in §B.1, which already lists the five analyses of the 8--16 October campaign one by
  one, and keeps both halves of the disclosure: those were not re-measured on the current numerical
  basis, and every number in the main text was.
- The campaign item drops "and their numbers are printed in blue throughout this appendix".

**Correction to my own count.** I said 18 blue numbers twice; that was `grep -c`, which counts
lines. There are **35** `\NUM{}` call sites on 16 lines, two of them the literal word "blue" in the
sentences now gone, so **33 numbers** change from blue to black. No value moved.

**Checked before the colour went.** Yesterday's A14 audit re-derived the placement decomposition
(59.5 / 15.4 / 25.7 / 57.7), which could have meant those numbers had left the earlier basis.
`results/variance_decomposition.json` records its roots as `outputs/core_all` and `outputs/tok1`,
that campaign's own runs, so the audit confirmed the arithmetic and not the basis. The disclosure
is unchanged in substance.

**Found while verifying the change.** `paper/sync_overleaf.sh` compiles `main.tex` only, so
`appendix.tex` had never been compiled by a push check. On its own it reports four undefined
references, one of which is a label that does not exist: the `tab:a4` caption cites
`\S\ref{app:borrowed}` where the section is labelled `app:bh`, and it rendered as `??`. `app:bh` is
*The matched control for the own-window identification rate*, whose text says that until 27 October
only the member side of that condition existed — exactly what the caption says about it. Fixed.

**Left alone, and reported instead.** The appendix cites main-text sections and tables by hard-coded
number, and the main text has been renumbered (it gained `tab:loo` as Table 3; its result sections
became subsections of §3). Against `main.aux` — `sec:ident` 3.2, `sec:slots` 3.3, `tab:human` 2,
`tab:loo` 3, `tab:ident` 4, `tab:slots` 5 — the suspect sites are appendix lines 88
(`\ref{sec:slots}`, a main-text label that cannot resolve in a separate document), 148 and 151
(`\S5` → 3.2), 206 and 339 (`Table 3` → Table 4), 289 (`\S3` → §2), 523 (`\S7`, which does not
exist), 564 (`Tables 2 and 5`; 2 is right, 5 unclear) and 578 (`Table 4` → Table 5). Each is a
judgement about what a sentence now means in a document that ships with the paper, so none was
guessed at.

**State.** GitHub `affd4bc`, Overleaf `2705d9f`. From a clean clone of what was pushed, both
documents: `main.tex` 0 errors, 0 undefined, 21 pages; `appendix.tex` 0 errors, 17 pages, one
undefined (`sec:slots`, above).


### 3.72 (28 Oct) Yesterday's two queues, written in at last: both control gaps closed, and the overlapping family's fresh window is a clean null

`queue_1028.sh` finished at **07:33 UTC**, every cell `rc=0`, and neither phase had been written
into the paper. Read now from the files on disk.

**Phase A --- the four- and sixteen-copy own-window controls.** The 27 October control draws its
donor from the single-copy members, because that is the cell the main text quotes, so those two
tiers had no control of their own; the paper said so in two places. `--donor_tier` gives them one:
36 further scoring passes over the same 18 cells, 50 records each.

| tier | own-window control (3 seeds × 6 rounds) | members, same condition |
|---|---|---|
| 1× (27 Oct) | 0.00--0.04 | 0.04--0.96 |
| 4× | 0.00--0.04 | 0.06--1.00 |
| 16× | **0.00 in all 18 cells** | 0.34--1.00 |

At the final checkpoint the members are at 1.00 in all three seeds under both new tiers. The point
is the direction: **the control does not weaken where the record was planted more often**, which is
what it has to do to be a control at all --- more copies make the host *window* more familiar to
the model, and a never-trained record dropped into that window still ranks at chance.

Validated before being trusted: the same aggregation **reproduces the tier-1 numbers the appendix
already prints** (0.00--0.04 against 0.04--0.96 over 18 cells; 0.04/0.00/0.02 against
0.94/0.92/0.96 at the final checkpoint). Both statements of the limitation are now replaced by the
measurement --- the `tab:ident` caption in the main text and the `app:bh` paragraph.

**Phase B --- the overlapping $k$-mer family, the one architecture with no own-window control at
all.** Its human runs predate `--drop_ckpt` and kept no weights, so like HyenaDNA they had to be
retrained rather than re-scored: twelve runs, $k=3$ to $6$ over three seeds, control in place,
checkpoints kept this time.

*The retrain reproduces the 9 October originals exactly* --- every member own-window and
fresh-window rate to the digit, every held-out loss to three decimals, in all twelve. That is the
second lost-weight family to reproduce cell for cell after HyenaDNA, and it is worth keeping,
because it is what licenses treating these retrains as the original runs rather than as new ones.

| $k$ | member own | control own | member fresh | control fresh | verbatim own |
|---|---|---|---|---|---|
| 3 | 0.08--0.10 | 0.00--0.02 | 0.02 | 0.00 | 0.00 |
| 4 | 0.04--0.06 | 0.00 | 0.02 | 0.00 | 0.00 |
| 5 | 0.08 | 0.00 | 0.02 | 0.00--0.04 | 0.00 |
| 6 | 0.24--0.26 | 0.02--0.04 | 0.02--0.04 | 0.00--0.02 | 0.06 |

Two readings, and the second one is a limit on the paper rather than a result for it.

1. **Own window:** only $k=6$ separates from its control by a margin fifty records can carry.
   Four of fifty against one of fifty is not a separation; twelve of fifty against one is. And
   $k=6$ is the coarsest cut of the family, which is the direction §3.3 predicts.
2. **Fresh window: a clean null at every $k$.** Members 0.02--0.04, controls 0.00--0.04. So at the
   sizes we train, **this family gives up nothing about membership from the weights alone.** The
   appendix now says, where the control is reported, that the identification result of §3.2 is a
   property of the two released masked families we can price and not of released genomic models in
   general. That bound is stated, not softened.

**Not added to the main text.** The fresh-window null is a candidate for one sentence in §3.2 or
§4, but the body is 21 pages against a limit of 10, so adding prose there is yours to decide. The
appendix has no page limit and carries it in full.

**State.** GitHub `b44327b`, Overleaf `0036c06`. From a clean clone of what was pushed:
`main.tex` **0 errors, 0 undefined, 21 pages** (unchanged --- the caption edit is length-neutral);
`appendix.tex` **0 errors, 18 pages**, up one page, one undefined reference which is still
`sec:slots` from §3.71's hard-coded family.

## 28 Oct, 14:28 UTC — the appendix's nine references to the main text, resolved against main.aux

Two questions, and the second one turned out to have a clean answer.

**Is the appendix missing from Overleaf?** No, and nothing is broken. `appendix.tex` carries its own
`\documentclass` and is submitted as a separate PDF, which the 2027 call allows ("optional appendix,
EITHER appended to the main paper OR uploaded separately; no page limit"). `main.tex` never
`\input`s it, so compiling the main document correctly produces 21 pages with no appendix. To see it
on Overleaf you set `appendix.tex` as the main document in the file menu. Checked while there:
`p02_related.tex` and `p09_ethics.tex` are also not `\input` anywhere, and both are deliberate
tombstones --- two and three lines each, saying where their content went (prior work into the
introduction, per the five RECOMB papers we followed, none of which has a Related Work section; the
ethics and availability statements into `sec:ethics` 2.6 and `sec:availability` 5). Nothing was
dropped by accident.

**The nine stale references.** `main.aux` of this tree gives the authority: `sec:measure` 2,
`sec:ident` 3.2, `sec:slots` 3.3, `sec:blind` 3.4, `sec:discussion` 4, `sec:availability` 5;
`tab:cost` 1, `tab:human` 2, `tab:loo` 3, `tab:ident` 4, `tab:slots` 5, `tab:blind` 6, `tab:scale` 7.

| appendix said | now | how it was established |
|---|---|---|
| `\S\ref{sec:slots}` | `\S3.3` | the one that printed `??` --- a main-text label cannot resolve in a separate document |
| `\S5` (twice) | `\S3.2` | `p05_identify.tex:91-104` carries the $0.29$/$0.06$ haplotype split and both warnings |
| `Table 3` (twice) | `Table 4` | `tab:a4` is `tab:ident` per seed (id / own / fresh / verbatim, two controls), not `tab:loo`, which is LOO and ceiling over four families |
| `\S3` | `\S2` | the decoders are defined in Methods |
| `\S7` | `\S3.4` | `p07_practice.tex:136`, "Do not read a masked objective as a defence, although from scratch it is one" |
| `Tables 2 and 5` | `2 and 3` | the nineteen chr22 cells are quoted in `tab:human` and `tab:loo` |
| `Table 4` | `Table 5` | the $k=1..6$ window-300 sweep is `tab:slots` |

**Where the off-by-one came from.** `git log -S` dates the appendix rewrite to 24 Oct 18:33 and
`tab:loo` entering the main text at 18:21 --- twelve minutes earlier. The appendix was drafted
against the numbering of a main text that had just renumbered under it, and every number from
Table 3 down was one short. Two sites needed more than that. `\S7` was resolved by recovering the
nine-section structure at `ff9aaf9` (§7 = `p07_practice`) and then confirming by content that
`p07_practice` is where the objective result lives. `Tables 2 and 5` had no recoverable intent ---
it was edited from "Tables 2, 5 and A7" on 27 Oct without re-deriving the numbers --- so it was
settled by content instead: Table 5 is the from-scratch uniform-DNA tokenizer sweep, which these
three chromosome-22 commands cannot produce, so "5" was wrong whatever it meant.

The appendix's own numbers in those two verbatim comments were already right. Compiling
`appendix.tex` shows its labels no longer match the numbers they were named after --- `tab:a4`
prints as **A2**, `tab:a7` as **A5**, `tab:a5` as **A3**, `tab:a10` as **A8** --- which is harmless
while every internal reference goes through `\ref`, and means the "and A5" and "and A3" in those
comments were correct.

**Two gaps closed, because the body still has to come down from 21 pages to 10 and that will
renumber it again.**

- `paper/check_xrefs.py` reads each hard-coded reference against `main.aux` and names what the
  appendix says instead. It passes on this tree and reports **10 of 11 stale** on the previous
  commit. The eleventh is the one written on 27 Oct, which was right.
- `sync_overleaf.sh` now compiles **`appendix.tex` as well as `main.tex`** and runs the check. It
  built `main.tex` only, which is why a caption citing a label that does not exist survived four
  days of push checks all reporting `errors=0 undefined=0`. `build.sh` runs the check too.
- Found while testing that: the push check's **page count had been blank on every push**. pdflatex
  writes `Output written on main.pdf (21 pages, ...)` and the pattern looked for `on <n> pages`, so
  it matched nothing and nobody noticed, because the two counts beside it were the ones being read.
  It is the field that says whether the body is inside the limit. Fixed, and it now says
  `pages: NOT REPORTED` rather than nothing when there is no count.

**State.** GitHub `baa1e5d`, Overleaf `ba4ec01`. Three-way parity verified by **sha256 on all 33
Overleaf files**, not by commit id: the two repositories apply different CRLF filters, so
`git hash-object` reports `main.tex` as differing when the bytes are identical. From a clean clone
of what was pushed, both documents: `main.tex` **0 errors, 0 undefined, 21 pages**; `appendix.tex`
**0 errors, 18 pages, 0 undefined for the first time**.

## 28 Oct, 14:55 UTC — the page-cut plan, measured rather than estimated (a proposal; nothing applied)

Full plan in `notes/22_page_cut_plan.md`; the measurement in `pilot2/tmp/measure_heights.py`,
`measure_cuts.py` and `verify_combo.py`.

**The baseline, pinned.** `main.pdf` is 21 pages = 1 title page (the call permits one
*additional* title page, so it sits outside the limit) + **18 body pages** + 2 bibliography
pages, which the call excludes. Against a limit of 10, **8.00 pages have to come out, 44% of the
body.**

**How it was measured.** Integer page counts are useless for ranking: removing any one of the
eleven floats reports "saves 1 page". So each float is boxed with `main.tex`'s own preamble and
TeX is asked for `\ht+\dp` over `\textheight` (650.4pt), and prose is calibrated in characters
against the pages the floats do not occupy (5,049 chars/page). **The per-section column sums to
18.00**, the measured body, and removals are **additive**: three combinations predicted
14.44 / 15.85 / 12.77 and measured 14 / 16 / 13.

(Same trap twice: the measurement tree's `figures/` had been emptied by a crashed `rmtree`, so
`\includegraphics` fell back to draft boxes and **every figure read about 50% too tall**, moving
the baseline from 18 pages to 20. The scripts now assert that no log line says
`not found: using draft`.)

| section | prose | floats | total | its floats |
|---|---|---|---|---|
| §1 Introduction | 1.63 | 0.67 | **2.30** | fig:overview 0.67 |
| §2 Methods | 4.58 | 0 | **4.58** | — |
| §3.1 Leak | 1.04 | 0.99 | **2.03** | tab:cost 0.24, tab:human 0.30, tab:loo 0.45 |
| §3.2 Identification | 2.26 | 0.80 | **3.06** | tab:ident 0.42, fig:ident 0.38 |
| §3.3 Slots | 1.57 | 0.63 | **2.20** | fig:slots 0.38, tab:slots 0.25 |
| §3.4 Practice | 1.41 | 0.86 | **2.27** | tab:blind 0.27, fig:blind 0.36, tab:scale 0.23 |
| §4 Discussion | 1.22 | 0 | **1.22** | — |
| §5 Availability | 0.34 | 0 | **0.34** | — |
| total | 14.05 | 3.95 | **18.00** | |

**Three things only the measurement showed.**

1. **Methods is 4.58 pages, a quarter of the body, with no floats** — the largest block anywhere.
2. **All eleven floats together are 3.95 pages.** Deleting every figure and table in the paper
   would still leave 14 pages. Figures and tables are not where the problem is.
3. **The decoders are described twice in the main text.** Lines 184--250 of `p03_setup.tex`
   define all four formally with equations 7--10; then "Extraction is where the measurement
   becomes delicate…" restates the same four in prose with nothing new. The letter-prior error is
   told three times. The introduction gives the canary construction, the matched control and the
   leave-one-out bound that §2 then defines properly, and `fig:overview`'s caption (0.24) states
   the results a third time with their numbers.

**The least cuttable thing is the biggest.** The largest single block is
`\paragraph{The decoders.}` at 1.69 pages, and the scope clause returns papers whose contribution
is "the application of existing methods to new data" without full review. Those four equations
are the reason this paper is not returned. `fig:slots` is already marked unmovable in `main.tex`.

**Three tiers.**

- **Tier 1 --- duplication and compression, nothing leaves the record: ≈ 4.4 pages.** Eighteen
  items. The cleanest is the duplicate prose above (0.23; it removes a copy, not a claim). The
  ones that hurt are §3.2's and §3.3's reviewer-anticipation paragraphs (1.5 pages down to 0.8):
  cutting them changes no number, only how much work a hostile reviewer has to do to find the
  boundary we would have told them about. → 13.6
- **Tier 2 --- floats, 3.95 in total.** `fig:ident` (0.38) and `fig:blind` (0.36) carry no number
  that `tab:ident` and `tab:blind` do not; `tab:cost` to the appendix with one sentence left
  (0.24); `tab:scale` to the appendix (0.23, and §4 already scopes it to one backbone and one cut
  size). But `fig:slots`, `tab:slots`, `tab:human` and `tab:ident` are the claim ladder, so the
  realistic take is **1.2--1.6**, not 2.2. → ≈ 12.2
- **Tier 3 --- one whole result has to leave the body, and that decision is not mine.**
  Compression and floats reach 12.2 and stop. §3.1 (2.03) is the foundation, §3.3 (2.20) is one
  of the three claimed contributions with an unmovable figure, §3.2 (3.06) is the title result.
  **Recommended: §3.4 (2.27) to the appendix**, with about 0.3 of a page of recommendation
  surviving at the end of §4 as the paper's practical conclusion. It is the only candidate whose
  removal does not break a claim the rest of the paper depends on, and §4 already hedges half of
  it.

That budget lands at **9.80 pages**, 0.2 of slack; the first thing to spend it on is item 11.

**What not to do:** not the font or the margins (10pt / 1in is the floor, and a violation "may be
rejected without review"); not an equation into the appendix (a reviewer who skips the appendix
must still see that the decoders are new work); not the matched controls; and not the ethics
statement down to nothing.

**State.** `c20b31a`. `paper/` is byte-for-byte untouched --- re-checked by sha256 against all 33
Overleaf files, 0 differing --- so no Overleaf sync and no recompile is due.

## 28 Oct, 15:40 UTC — duplication cleared: the decoders written twice, the canary classification three times

**Duplication only.** No claim, number, hedge or boundary is compressed and no section moved; the
rest of `notes/22_page_cut_plan.md` is untouched.

**Four removals.**

1. **Methods: the decoders re-described in prose.** The paragraph beginning "Extraction is where
   the measurement becomes delicate…" restated all four decoders forty lines after equations 7--10
   define them, and repeated the letter-prior sentence almost verbatim. **Two things lived only
   inside it and had to be carried up before it could go:**
   - **The value of $R$.** The formal block says only "from $R$ restarts" and **never gives $R$
     anywhere in the paper**; the deleted sentence carried the 128. Now "from $R=128$ restarts",
     at the definition of that decoder. (128 belongs to the re-masking decoder alone --- the
     appendix's own commands run `--restarts 32` for the overlapping-$k$-mer and BPE decoders ---
     so it could not be written as a blanket value.)
   - **The `mireshghallah2022mlm` citation.** Without the carry that reference would have dropped
     out of the bibliography entirely.
   The paragraph after it opened "The same is true one ruler up", whose antecedent was the deleted
   text, so it is now self-contained. Its numbers (NT 250M at round 50, $0.64$ against $0.06$) are
   unchanged.
2. **Methods/Ethics:** the 145 / 20 / 235 classification, restated seventy lines below the
   Canaries subsection that gives it in full, inside the same section.
3. **§3.1:** the canary construction re-defined in full in the section immediately after §2
   defines it. Replaced by a pointer that keeps 145 of 400 and the appendix reference. The replaced
   sentence spelled out the 20 and the 235 separately; "rare human sequence that no single
   chromosome carries" covers both, so nothing is lost.
4. **§3.2:** the same classification a third time. **The one-line gloss is kept** --- the reader
   needs it to read the $0.29$ against $0.06$ split that follows --- and only the re-definition goes.

**Net −1,586 characters**, about **0.31 of a page** at the measured 5,049 chars/page, and it
crossed a page boundary:

| | before | after |
|---|---|---|
| `main.pdf` physical pages | 21 | **20** |
| **body pages (limit 10)** | 18 | **17** |
| `appendix.pdf` | 18 | 18 |

Both documents 0 errors, 0 undefined, 0 figures falling back to draft boxes. `R = 128` is present
in the typeset text and the Mireshghallah entry is still in the bibliography.

**A bug of my own from this morning, caught by its own fallback.** The page-count field added to
the push check this morning printed **"pages: NOT REPORTED"** on the very next push: that fix was
still wrong. pdflatex wraps every log line at **79 columns**, so with `-output-directory` the
output path pushes "(20 pages" onto a continuation line where no single-line pattern can see it.
It now reads the count from the PDF with `pdfinfo`, with the flattened log as a fallback; both
paths verified against a real build (main 20, appendix 18). The "NOT REPORTED" default is worth
recording: it did exactly what it was put there to do, which was to make its own upstream failure
visible instead of leaving the field blank.

**State.** GitHub `f88a4b1`, Overleaf `4f40795`, all 33 files sha256-identical. Compiled from a
clean clone of Overleaf: `main.tex` **0 errors, 0 undefined, 20 pages (body 17)**; `appendix.tex`
**0 errors, 0 undefined, 18 pages**; `check_xrefs` reports all 11 references to the main text
agreeing with `main.aux`.

**Seven pages still to find.** Next in the plan is the remainder of Tier 1 (≈4.1 pages, nothing
leaving the record), on the author's word.

## 28 Oct, 16:35 UTC — Tier-1 compression applied, and why Tier 1 was never worth 4.4 pages

**The result first.** The compression is applied, with every number, hedge and evidence boundary
intact --- verified on the **typeset body**, not the source. The body is still **17 pages**: this
pass took out **169 words, 1.3%**. The 4.4 pages Tier 1 claimed in the plan was my estimate, and it
was wrong.

**What changed**

- **Introduction:** the précis restated the method that the three contribution bullets state
  immediately below it. The bullets keep the method; the précis keeps the setup, the results and
  "compared at matched held-out loss rather than at matched epoch", which the bullets do not carry.
- **Methods:** threat model, models and canaries tightened. "Advancing one nucleotide at a time"
  becomes "at stride~1", the term the Notation paragraph and appendix A6 already use.
- **Methods:** the divisor-defect audit in `\paragraph{Identification.}` tightened, with **all 19
  of its numbers and all four of its hedges intact**.
- **Discussion:** the last two paragraphs *each* required "a decoder matched to the model's own
  tokenizer" and "a never-trained control scored in the same run", and *each* gave the
  shipping-team scenario. Merged into one; the scenario now points at §3.2, where it has its
  numbers.
- **§3.4 said "Three things follow" above four recommendations.** Fixed to four. Not compression; a
  defect.

**Why only 1.3% --- two measurements**

| | measured | status |
|---|---|---|
| duplication (items 1, 2, 9, plus three more found by a 10-gram scan) | **0.31** | applied, body 18 → 17 |
| genuine wordiness (items 3–8, 16–18) | **≈ 0.20** | applied, −169 words, page count unmoved |
| the defensive prose of §3.2 and §3.3 (items 11–14) | **≈ 1.15** | **not applied, see below** |
| the rest of the 4.4 | **does not exist** | |

The body is **12,982 words** carrying **266 distinct numbers in 17 pages**: the volume is content,
not verbosity. And reaching 10 pages from 17 by prose alone would mean removing **41% of the body
text, about 5,415 words**, which is not compression.

Methods is the clearest case: 4.58 pages, the largest block in the paper, and it gave up **under
0.1 of a page**. `Identification`'s divisor audit packs 19 numbers and four hedges into 0.59 of a
page; the plan asked it for 0.21 and there is no such slack in it.

**Items 11–14's 1.15 pages are real and they are not free.** They are the paragraphs in §3.2 and
§3.3 that pre-empt a reviewer's objections and state the scope of each claim. Cutting them changes
no number; it changes how much work a hostile reviewer has to do to find the boundary we would have
told them about. That is a judgement about how the paper defends itself, not a compression, so it
is left for the author rather than applied.

**Consequence, written back into `notes/22_page_cut_plan.md` directly above the table it replaces.**
Tier 1 is worth about 0.5 of a page rather than 4.4, so the eight pages have to come almost
entirely from structure. Tier 2 is 1.2–1.6. **Moving one result section to the appendix is no
longer enough:** 17 − 1.4 − 2.3 ≈ 13.3, still three pages over. Either two of the four result
sections go, or items 11–14 are spent as well, or both.

**New tool: `pilot2/tmp/numguard.py`** (`snapshot`, then `check`). It guards what a compression pass
must not lose: the multiset of numbers in the **typeset** body, the hedge and scope words, the
citation keys reaching the bibliography, and the section and float numbering the appendix cites by
hard-coded number. It counts the typeset text rather than the source, so a change of wrapping or of
macro cannot hide a loss. Two things about its first run are worth recording: it reported "lost the
number 26", which was natbib's **citation label** `[26]` after I deleted one of salazar2020pll's
three in-text citations; and "lower bound 5 → 4", which was pdftotext wrapping the phrase across a
line. Neither was a loss. Rather than wave them off I diffed the two typeset bodies directly to
establish it, then made the guard strip citation labels and normalise whitespace first. Without
those two fixes it would stay silent when it should fire and fire when it should not.

**State.** GitHub `fd08155`, Overleaf `0a4f476`, all 33 files sha256-identical. Compiled from a
clean clone of Overleaf: `main.tex` **0 errors, 0 undefined, 20 pages (body 17)**; `appendix.tex`
**0 errors, 0 undefined, 18 pages**; `check_xrefs` all 11 agreeing. The push check's page-count
field printed correctly this time, the fix from the previous step.

**Seven pages still to find, and we now know compression cannot supply them.** What follows is a
structural decision, and it is the author's.

## 28 Oct, 17:30 UTC — 3.1 and 3.4 into the appendix: body 17 pages to 13

The author's decision. Results keeps the identification result and the slot-count result, which
renumber to **§3.1 and §3.2**. The appendix is now 22 pages and holds the two moved sections as
**A16 and A17**.

**How, and the part that mattered: no second copy.** The two section files remain the single copy
of their text. They are transformed in place and `appendix.tex` inputs them, so nothing is
duplicated between the documents --- which is exactly what the rest of the day was spent removing,
and would have been a poor thing to recreate. They go in immediately before
`\section{Exact commands}`, the only appendix section that then renumbers and the one thing
nothing in the paper cites by number. Their tables become **A10--A14** and `fig:blind` becomes
figure **A2**, all after the existing appendix floats, so every "appendix A1--A9" reference in the
paper stays valid.

**Self-containment, which I flagged first and then repaired.** The call requires the main paper to
be self-contained and says reviewers need not read the appendix, and the old §3.2 opened by
leaning on §3.1's result. It now **states that premise itself, with its numbers** --- seven
thousandths of a bit on *E.~coli*, 8 to 18\% letter-for-letter on chromosome~22 --- and cites A16
for the detail rather than depending on it.

**References broke in both directions, so the guard now runs both ways.**

- **11** references in the staying text pointed into the moved sections, and became hard-coded
  appendix numbers.
- **15** references inside the moved sections pointed at the main text, and became hard-coded
  numbers there (`sec:ident` 3.2 → **3.1**, `sec:slots` 3.3 → **3.2**, `tab:ident` Table 4 → **1**,
  `tab:slots` Table 5 → **2**).
- `check_xrefs.py` now guards **32** rows: appendix → main, main → appendix, and the appendix's
  references to itself from inside a `verbatim` block, where `\ref` cannot be used. `build.sh` and
  `sync_overleaf.sh` both pass it the two `.aux` files, and `build.sh` now builds the appendix too.

**Four defects surfaced, three of them older than this move.**

1. **Two references to "Table~A9" pointed at the wrong table.** They mean the 28 September
   fixed-placement table, which appendix A1 discusses by name: that is `tab:capacity` = **A7**. A9
   is `tab:draws`, about member/non-member re-draws. Wrong for weeks.
2. **"We return to this in \S2 of the main text" points forward at a section that precedes it**,
   and has done since the 27 October restructure put Methods ahead of Results.
3. §3.4's recommendation block said "Three things follow" above four recommendations (fixed in the
   previous step).
4. **One I introduced, which the guard caught:** `\ref{fig:overview}` carried a panel letter, so
   `Figure~\ref{fig:overview}b` became **"Figure 1 of the main textb"** in the typeset PDF. Now
   "Figure~1b of the main text".

**Checked.** Both documents **0 errors, 0 undefined, 0 figures falling back to draft boxes**;
`main` 16 physical pages with a **13-page body**, `appendix` 22. **No number is lost across the two
documents:** the only decimals that moved are figure axis labels that pdftotext glues differently,
and `0.74` and `0.72` occur 10 and 5 times both before and after.

**State.** GitHub `bd8ae2f`, Overleaf `c7f4825`, all 33 files sha256-identical, and Overleaf
confirmed to have the structural change (its `main.tex` inputs neither file, its `appendix.tex`
inputs both).

**Three pages still to find.** Most of Tier 2's floats now sit in the appendix, where there is no
page limit, so the body's own figures and tables are worth less than the 1.2--1.6 the plan's table
claims. The only remaining block of that size is items 11--14, the ~1.15 pages of paragraphs in
§3.1 and §3.2 that pre-empt reviewer objections. Spending them is a decision about how the paper
defends itself, and it is not mine.

## 28 Oct, 18:20 UTC — abstract restructured: motivation, then method, then results

**A co-author's reading:** it read as a highlight of the results only. The previous version was two
sentences of setup and then the whole claim ladder. The shape is now **motivation → what we did and
briefly why → one high-level sentence per claim with a couple of preview numbers under it.**

**The motivation is not invented**; it is the argument of the introduction's first two paragraphs. A
shared checkpoint is not a summary of the cohort but **a function fitted to its individuals**,
queryable without limit by whoever downloads it. The field's check on that artefact is **verbatim
reproduction**, and two assumptions under it do not survive a released genomic model: a
prefix-conditioned decoder probes, on a masked model, **a conditional the model was never trained
on**, and a zero is **a property of the search** rather than of the weights. Meanwhile in genomics
**the harm of record is identification** --- a short window of rare alleles is an identifier --- so a
reproduction test is silent in exactly the case worth worrying about, where a model emits nothing of
a member's sequence and discloses their membership all the same.

**Because §3.1 and §3.4 moved to the appendix in the previous step**, the two results the ten-page
body carries are **identification-without-reproduction and the slot count**, so those lead. The
released-checkpoint leak now reads as the setup for "reproduction is the wrong alarm", which is what
it is, and the utility-metric result is one clause rather than a sentence.

**One near-miss worth recording.** A compressed draft of the two-further-architectures sentence read
"show the same dissociation". **That is false:** on the larger of the two, *our own decoder recovers
12 to 18%* of the same records, and the paper says in terms that the fresh-window headline "is
established on DNABERT-2 and on no other family here". Checked against the paper's own paragraph and
restored to a form carrying both that rate and the fifty-record limit --- which is what the sentence
it replaced was careful to say. This is the precise way a compression pass erases a boundary.

**Nothing is strengthened.** 23 of the 25 numbers are unchanged to the digit. The two that left the
abstract are the **30%** of records returned at the cheapest price and the **8--18%** human
single-copy verbatim rate; **both are still in the paper**, the first in `tab:cost` and the second in
the introduction and §3.1.

**Length: 354 → 466 words** (488 words and 2,919 characters in the typeset text, counting the URL).
Adding motivation and method necessarily lengthens it. The **title page is still one page** (checked)
and the body is still 13. If the EasyChair abstract box or the registered text will not take it, the
two cheapest cuts are the motivation's two-assumptions clause (**−45 words**) and the
two-further-architectures sentence (**−48**, though it carries a limitation, so it should be the
second choice).

**Time-sensitive.** The call puts abstract registration at **28 Oct 23:59 AoE** and requires the
registration to "closely align" with the final paper. If the older text is already registered, this
version needs to go in before that deadline: no claim has changed, so alignment holds, but the text
should be the same one.

**State.** GitHub `ec0cdf2`, Overleaf `ff3d86f`, all 33 files sha256-identical; both documents 0
errors and 0 undefined, `main` 16 pages with a 13-page body, `appendix` 22, `check_xrefs` 32 of 32.

## 28 Oct, 18:55 UTC — the appendix moves into main.tex: one PDF

At the author's request, so reviewers get one document and the two halves stay aligned.

**How, and the part that mattered.** The appendix body is now `sections/p11_appendix.tex`, the only
copy of its text, and `main.tex` inputs it after `\bibliography`. `appendix.tex` is retired (git
recorded it as a rename, which is the continuity check). Everything its preamble changed is set in
the appendix block in `main.tex` rather than in main's preamble, so it applies from the references
onward and **cannot reach back into the body**: `\excess`, which is the WORD "excess" in the
appendix and `\Delta` in the body (which never uses it); the A-prefixed section, table and figure
counters with the counters reset; and `tabcolsep` 4pt for the nine- and eleven-column tables.
`longtable` is now loaded by `main.tex`.

**What it buys.** All **36** hard-coded cross-references become live `\ref`. They were hard-coded
only because a separate document cannot `\ref` into another, and they went stale three times in
five days: `tab:loo` entering the main text pushed nine out by one; moving §3.1 and §3.4 into the
appendix renumbered the main text under all of them; and two "Table A9" references meant a table
that is A7. **That class of bug is now gone**, and `check_xrefs.py` drops from 32 rows to 5 --- the
numbers a `verbatim` block has to spell out, which no `\ref` can reach.

**The appendix's numbering is unchanged by the merge**: `sec:leak` still A16, `tab:loo` still A12,
`fig:blind` still A2, every section A1--A18 and table A1--A14 as before. So nothing already
written, including those five verbatim numbers, went stale.

**Checked.** 0 errors, 0 undefined, 0 figures in draft. 38 pages = 1 title + **13 body** + 2
bibliography + 22 appendix; the ten-page limit applies to the body, still 13. The appendix body
diffs line for line against the old `appendix.tex` --- **522 lines both sides**, every difference
one of the relinks --- and the typeset text is unchanged except for the dropped "of the main
text", which is redundant inside one document.

**Two build-script fixes.** `build.sh` builds one document again, and it now filters and counts the
five `ignored error: Infinity` notices pdftex emits at every `\end{longtable}`: the standalone
appendix logged them identically, so they **pre-date the merge**, and an error section that always
shows five harmless lines is one nobody reads. It matches on `ignored error` rather than on the
word Infinity, because pdftex wraps log lines at 79 columns and splits it --- the same wrapping
that hid the page count from the sibling script earlier today.

**State.** GitHub `034cf6a`, Overleaf `344f903`, 33 files sha256-identical; `appendix.tex` removed
from the Overleaf project and `sections/p11_appendix.tex` added there by hand, because the sync
script deliberately never adds or removes files.

## 28 Oct, 19:40 UTC — the repo refresh, prepared and not pushed

The author asked for the public submission repo to be refreshed. **It is not refreshed.** The
refresh is prepared in a local clone and the live repo is untouched, by the author's decision.

**What the check found, and it is already public.**

| | |
|---|---|
| files | `results/scale22/n{1000,2500,5000,10000,20000}/6mer_ar_s{0,1}/data_meta.json`, **ten** |
| each | 200 probes, each with a full **96-nt** `seq` |
| total | **2,000 records** |
| also carried | `repetitions` (0 = never-trained control, 1/4/16 = member), `host_rows`, `offsets` |
| what they are | `pilot2/queue_scale.sh` line 13: "real chromosome-22 windows with real rare-haplotype canaries" |

So what is public is the sequences **and** the membership labels **and** the exact planting
positions: the answer key to this paper's own attack. Public since the repo's first and only
commit, **2026-10-26 23:46 -0400**. Repo page shows 0 stars, 0 forks, 0 watchers; clone counts are
visible only to the owner, under Insights -> Traffic, for 14 days.

**The paper says otherwise in two places**, and both are false as written while this stands: §5,
"The planted canary set is not redistributed ... publishing it would publish four hundred rare
human windows in one place with their anchor coordinates attached"; and §2.6, "publish neither
reconstructed sequences nor any identifier that would link a recovered sequence to a sample".

**For calibration, not to minimise it:** 1000 Genomes phase 3 genotypes are themselves openly
distributed, which the paper itself states, so the incremental disclosure is bounded. What is not
bounded is that the paper promises this did not happen.

**How the publish rule was established, and why it was not enough.** There was no builder script,
no local clone and no note recording how the repo was made, so the transform was read off the
artefact: `verify_strip_rule.py` diffs the published repo against our tree at the commit it was
built from (`664f2cb`) and finds that the **only** edit anywhere was removing the keys `truth_nt`
and `pred_nt`, at six paths, in 396 files --- no key added, no value changed. (Most of the apparent
1,520 differences were CRLF; ignoring line endings it is 401, of which 3 are a `claude_notes/` ->
`notes/` path rewrite in the logs.) `refresh_subrepo.py` reproduces that transform exactly.

**Applied alone it would have republished all 2,000 sequences in silence**, because `seq` is not on
that key list. What found them is `scan_sequences.py`, which ignores key names and looks for any
string that is a nucleotide run --- the promise the ethics section actually makes. **That is the
whole argument for checking the property rather than the rule.**

Worth recording: the scanner's first run reported zero, because a shell-escaped `$` turned its
anchor into a literal dollar sign. The finding was re-established by reading the committed file
directly and parsing it, and the scanner now lives in a file so no shell can edit its regex.

**Prepared, in a local clone at `C:/glmsub`** (a short path: both `git` and Python hit Windows
MAX_PATH from the scratchpad, which is why the first clone silently checked out nothing):
`strip_seq.py` removes `seq` from the ten files, keeping `probe_id`, `repetitions`, `host_rows`,
`offsets` and adding a note on rebuilding the set from the public inputs via
`pilot2/human_canary.py` and the recorded `data_seed`. The tree then scans clean, 0 sequences.
The refresh itself adds 63 files and updates 23, and introduces no sequence.

**A plain commit would not be enough**: git history keeps the old blobs, so clearing this needs the
single-commit history rebuilt and force-pushed, or the repo deleted and recreated. Both are
irreversible and public, which is why they were put to the author rather than done.

**Decided by the author:** leave the live repo alone for now, and leave the paper's wording alone
until the repo's disposition is settled. The 2,000 remain public meanwhile, and the abstract about
to be registered carries a link to that repo.

**State.** Tools landed in `pilot2/tmp/` at GitHub `ee740f1` --- `scan_sequences.py`,
`strip_seq.py`, `refresh_subrepo.py`, `verify_strip_rule.py`. No sequence appears in any of them;
checked with the scanner. Nothing was pushed to the submission repo.

## 28 Oct, 23:15 UTC — second-review items 1 to 5, and the third time the predecessor was described wrongly

The second review arrived as a ten-item work order. Items 1 to 5 are applied; 6 was applied
earlier today; 7, 8, 9 and 10 are not. Item 10 is cutting, which is the author's call.

**Item 2 first, because it decided the shape of the rest.** I had written three times that the
predecessor, `nemecek2026quantifying`, "reports the largest of three scores, so it cannot show the
two signals come apart", and that "what was missing is the comparison, not the attack". Reading
the PDF instead of my own notes settled it:

* §4.3.5: "We report both the maximum vulnerability scores and their constituent components to
  support fine-grained interpretation of where memorization risk is concentrated and which attack
  vector drives it." Table 3 carries s_ppl, s_ext and s_mia per model per dataset.
* §3.3: "the converse relationships do not hold, and because each vector can succeed where the
  others fail, together they provide a multi-dimensional characterization."
* §5.1: DNABERT-2 highest perplexity gap (0.34–0.38) with lowest extraction (0.09–0.14); HyenaDNA
  with "membership inference as its only measurable vulnerability".

So the dissociation is its headline finding, not ours, and its membership vector is a
likelihood-ratio attack fitting parametric distributions to the two loss populations — my
"loss-threshold AUC" undersold it. That is three wrong descriptions of the same paper: first that
it judges a model by what it emits, then the maximum argument, then the loss threshold. The
lesson is narrow and expensive: when a claim about a paper has been written more than once without
reading it, the claim is about my notes.

What is ours is the measurement condition, and the predecessor's own limitations name it: its
canaries "remain random nucleotide strings carrying no biological structure" and "it remains an
open question whether memorization of real sequences would manifest at comparable rates or through
the same vectors". Add that they are standalone training examples rather than windows planted at
drawn offsets, read at one early-stopped checkpoint, extracted by one prefix-conditioned beam
search, and scored for membership over populations rather than against a candidate set. The
abstract, the introduction and contribution 1 now say that, and contribution 1 states a design
instead of a gap that is not there.

**Item 1, three levels kept apart.** Membership disclosure (is a candidate record the adversary
holds in the training set), sequence reproduction (can a tested decoder write it back), participant
identification (which person contributed — needs a sequence-to-person link and a contribution
assumption this paper does not evaluate). Methods names all three; Figure 1's caption and the
Discussion follow it.

And an argument I had backwards. I wrote that the rank statistic "carries no false-positive rate"
and that it "is not the one the membership-inference literature asks for". Ranking first *is* a
positive rule, and the matched control *is* its empirical false-positive frequency under this
experiment — across the 18 cells of Table 1, at most 2 of 50 never-trained records rank first in a
borrowed training window and at most 1 of 50 in a fresh one. The real limit is resolution and
extrapolation, and that is what both passages say now.

**Item 4, the leave-one-out bound narrowed to its condition.** The bound holds for a decoder that
applies the probe's own update rule, constraints and tie-breaking and returns a fixed point of it;
under that condition every position of a recovered record must be stable, so p_i^{s_i} is a
necessary condition and a loose upper bound. It is not a success probability, and a positive value
is not evidence that any decoder attains it. The span-aware decoder exhausts its pass budget in
every one of its cells, so there it is a diagnostic and no bound is claimed. Two inference
patterns are gone from the text: "the information is demonstrably present" and "two of our zeros
are demonstrably decoder limits rather than model properties". Both become statements about
conditional predictive power, which is named as the third quantity it is. Touched: Methods ×3,
contribution 2, Figure 1's caption, Discussion, appendix A6, the Table A12 caption, A16 ×2.

**Item 5, the tokenizer result kept and the sole-mechanism claim withdrawn.** "What varies is not
how much is stored", "The same knowledge, 92% or 0% out", "holding the same content" and "the same
mechanism is at work here" each said a one-factor sweep had excluded the alternatives. It had not.
Section 6 now opens by naming the slot count as the hypothesis under test and a sufficient account
of this sweep, and says nothing here shows it is the only way a tokenizer changes what can be
reached.

The overlapping-family paragraph is renamed from "A prediction that could have falsified this, and
did not" to "Testing the slot-count hypothesis on overlapping tokenizers", and its closing
argument is withdrawn: s is constant across that family *by definition*, so its constancy cannot
confirm anything. What the family supplies is the failed empirical prediction already reported
there — no extraction trend, contradicted under the prefix protocol — and the account surviving
only in its weaker form.

Figure 5 was checked rather than changed. The character model's four matched-loss cells are
`None`, so `fig_slots` plots no point for it and annotates "never reaches these losses" at its
tick. It already shows as unavailable, not as a zero under a condition it never met.

**Item 3, the abstract at 295 words**, in the five-part shape asked for: an extraction failure
cannot settle membership; the design this paper adds; the dissociation at DNABERT-2's final
checkpoint (0.18–0.26 fresh-window rank-1, chance 0.0099, matched control 0.00 there and
0.00–0.02 across the checkpoint sequence, no whole record from either decoder); the separate
tokenizer result (0% against 92% at matched held-out loss 2.40 bits/nt); and the implication.

Four things left the abstract, and the file's header comment records why each one did, because all
four are still in the body: the own-window 0.92–0.96 (a privileged-context diagnostic — an
adversary holding the training window and the drawn offset could search the corpus instead); the
leave-one-out ceiling (without its fixed-point condition it is exactly the universal-ceiling claim
the review objected to, and the condition does not fit at this length); 2.44 against 2.79 bits/nt
beside the 0%/92% (end-of-training surprise gaps beside a matched-loss recovery rate, which in one
sentence reads as "the same amount is stored"); and "Downstream task score carries no signal about
any of it" (what was measured is that the GUE correlation moves by hundredths in both directions
across the interval where membership becomes disclosable — a failure to warn, not an absence of
information).

**State.** GitHub `0c7b537`, Overleaf `0dbfcaa`, 33 files byte-identical across local, GitHub and
Overleaf. 40 pages, body 14, errors 0, undefined 0, suspicious lines 0, check_xrefs 5/5. The one
underfull box is in `main.bbl` and predates this. Both the local build and a clean checkout of the
Overleaf remote compile.

**Open.** Items 7 (biological description of the human records), 8 (subgroup intervals and the
repeated-measures structure), 9 (practice recommendations limited to the measured endpoints) and
10 (body 14 pages to 10, plus a configuration table and the over-tall appendix float). Item 10 is
cutting. Also still open: the 2,000 sequences in the public submission repo, left there by the
author's decision; and the author list and keywords, which need written agreement from all five
authors before 4 Nov.

## 29 Oct, 00:00 UTC — the acceptance review of 0dbfcaa: 9pt captions, and the subgroup intervals recomputed

The verification pass on `0dbfcaa` scored the 23 frozen criteria at 4 fully addressed, 9 partly, 10
not, and found one thing nobody had looked for.

**The formatting violation.** `main.tex` set `caption[font=small]`, and in a 10pt article `\small`
is 9pt, so every figure and table caption in the body was below the stated minimum; the title page
set the abstract in `\small` too. Re-read the call before touching anything:

> "The maximum length is 10 pages (Letter format), **including all figures/tables and their
> captions**, using a minimum font size of 10pt and 1-inch margins. Submissions that violate the
> formatting requirement (e.g., by decreasing margins or font sizes) or exceed the page limit may
> be rejected without review."

"Including all figures/tables and their captions" settles it. Both are 10pt now. **The cost is one
body page: 14 to 15**, so the compression target is five pages rather than four. No table body in
the main text uses a reduced size; the two `\footnotesize` notes are in appendix tables, where the
limit does not apply.

**The subgroup intervals, recomputed rather than removed.** REV-16 was the only item that needed
data, and the data was on disk. The three `results/canary_status_rates_s*.json` on the server are
on the superseded 164/1/235 audit and could not be used, so the split was recomputed on the current
classification by running `pilot2.analyze_canary_status` once per run directory:

| fresh window, 1 copy | seed 0 | seed 1 | seed 2 |
|---|---|---|---|
| audited haplotypes (n=21) | 5/21 | 5/21 | 8/21 |
| carried by nobody (n=23) | 1/23 | 3/23 | 0/23 |
| genotypes (n=6) | 3/6 | 3/6 | 5/6 |

| own window, 1 copy | seed 0 | seed 1 | seed 2 |
|---|---|---|---|
| audited haplotypes | 20/21 | 19/21 | 19/21 |
| carried by nobody | 21/23 | 21/23 | 23/23 |

Pooled those are 0.286, 0.058, 0.611, 0.921 and 0.942 — **the point estimates already in the paper,
to the digit**. Only the intervals were wrong: a mean over three seeds that re-score the same
records, with a Wilson interval taken on the record count. Each seed is now reported on its own,
where a record contributes one scoring and the binomial applies, and no pooled interval is quoted,
because three seeds sharing one member/control split are not three independent draws and this
design gives no estimate of the across-seed component.

**Thirteen claims narrowed.** REV-01 the field-wide "a zero means nothing was retained", which
cited nobody. REV-02 "a short window of rare alleles is an identifier", now conditional on a panel
to link it against. REV-03 the regime defined by what was measured. REV-04 "haplotype" reserved for
the audited subset; the pooled 400 and the 50-record trajectory are human-variant-derived records,
and the 145/20/235 classification is stated in the body as conditional with 124/20/194 beside it.
REV-05 the slot count consistent with the sweep rather than a sufficient account. REV-08 DNABERT-2
is byte-pair, so its 0.21–0.39 is a diagnostic and not a bound — the overlapping family's 0.70–0.87
remains a bound and is now named as the one. REV-10 "stopping does prevent capture" and "at the
optimum there is nothing to extract", both contradicted two paragraphs later by 78–100% sixteen-copy
recovery at those same optima. REV-11 "carries no information" and "utility and nothing else". REV-12
the factor-of-two multiplier inferred from one rerun. REV-13 the appendix still calling itself a
separate document. REV-15 three success-law readings of \(p^s\). REV-18 a control row printing 0.000
where the cells behind it run to 0.003. REV-19 "more participants", where the sweep varied
chromosome-22 windows. REV-20 the DP inequality "weakened" by correlation. REV-22 "did not leak",
where the endpoint measured was exact extraction.

**The oversized float, and why the obvious fix was the cause.** Table A5 overflowed its page by
26.6pt. `\resizebox{\textwidth}{!}` — the fix applied to its two neighbours, which really are too
wide — scales a box *proportionally*, and A5 is nine narrow columns over forty rows, so its natural
width is well under `\textwidth` and the box was magnifying it off the bottom. Removing the
resizebox fixes it. No longtable needed.

**Added.** A configuration section in the appendix (REV-17, REV-23): every arm's settings read from
the recorded `args.json` rather than from this paper's prose, the fields all arms share, the decoder
budgets, and the matched-loss rule read out of the code — linear interpolation between the two saved
checkpoints bracketing the target loss, on the overfitting branch, blank outside a run's own range,
which is what every dash in a matched-loss table means and had never been written down. It closes
with the check as a releasing group would run it, and the three things it does not certify.

**State.** GitHub `758677b`, Overleaf `f6286c9`, 33 files byte-identical. 42 pages, body 15, errors
0, undefined 0, no Overfull, no float warnings, check_xrefs 5/5. Overleaf's git endpoint returned
503 for about twenty minutes in the middle of this and the commit sat in the local clone until it
came back; worth remembering that a failed sync leaves a real commit waiting rather than nothing.

**Open, and both the author's.** The body is 15 pages against a limit of 10. And Figure 1's artwork
still carries labels the text no longer supports: "leave-one-out ceiling" on two DNABERT-2 numbers
that are diagnostics, "Leave-one-out probe" and "Comparable conditional knowledge" over panel (c),
whose measurement is teacher-forced target surprise at the end of training while the 0%/92% beside
it is read at matched loss 2.40, "Target candidate haplotype", and a title that predates the
current one. The PDF is exported artwork, so the strings are listed for the author rather than
edited here.

## 29 Oct, 00:30 UTC — the masking argument, defended and then withdrawn

Yesterday's abstract said a prefix-conditioned decoder "asks the model to fill the whole target at
once, a context that training at 15% masking effectively never presents", and I defended it against
a reviewer with an expected-count table computed as 0.15^s. A second review read the code. I had
not. All three inputs were wrong.

**The rates.** `dnabert_long`'s human arm is not all at 0.15: `args.json` gives `mask_rate` 0.15,
0.20, 0.25 and 0.30 for k = 3, 4, 5, 6. I read `dnabert3_nt0.05_lr0.0001_human_s0` and generalised
to the family. The configuration table added hours earlier printed "masked, 0.15" for that whole
row for the same reason.

**The masking model.** `pilot2/dnabert.py`'s `span_mask` masks *spans of k consecutive tokens*,
starts drawn at `rate/k`, so the events are correlated by construction and an i.i.d. power is not
the probability of anything there. DNABERT-2 and NT *are* independent per token
(`dnabert2.py`, `nt.py`), so the model held for two arms out of four and the rate for one out of
four.

**The event.** `pilot2/dnabert2.py` masks everything right of the revealed prefix — host suffix
beyond the target included — and then fills left to right one slot at a time:

```
for t in range(n_rev, len(spans)): cur[t + 1] = voc.mask
for t in range(n_rev, last + 1):   cur[t + 1] = int(lg.argmax())
```

So "at once" misdescribes the algorithm, and the 8, 21 or 48 target slots are not the masked
region.

What survives is the protocol difference, which is what the code shows, and that is all the paper
now claims — in the abstract, and in the two places in the body where the same over-claim was
sitting as "probes a conditional the model was never trained on":

> For masked models, prefix-conditioned decoding masks the unrevealed suffix and fills it
> sequentially, unlike the random or span masking used during fine-tuning.

**The general lesson, and it is the second time this week.** Both of my worst claims in this
project came from generalising one file to a family: "the predecessor judges a model by what it
emits" came from reading its abstract rather than its Table 3, and "15% masking" came from reading
one of four `args.json`. Reading one member of a set is not reading the set, and the cost is the
same each time — a confident sentence that a reader who checks can disprove in one grep.

Also recorded in the abstract's header comment, because the next person to want this argument back
will be me: do not restore a probability claim here without recomputing it against `span_mask`, the
per-k rates and the whole masked suffix. And the leave-one-out probe does not settle the question
on its own either — it measures prediction with every *other* target position supplied, so a high
top-1 does not show the whole target is recoverable.

**State.** GitHub `0e15521`, Overleaf `9340c13`, 33 files byte-identical, verified by fetch and
per-file sha256. 42 pages, body 15, errors 0, undefined 0, no Overfull, no float warnings,
check_xrefs 5/5. Abstract 291 words. Overleaf's git endpoint returned 503 through both of today's
syncs and came back on the 4th and 5th retry; a failed sync leaves a real commit waiting in the
clone, not nothing.

## 31 Oct, 18:00 UTC --- the citation audit, verified at the sources and then acted on

A `citation-audit` run against Overleaf `301f1e35` produced `paper/CITATION_AUDIT.md`: 34 entries,
63 use sites, 7 marked WRONG and 21 WEAK, no file touched. I re-checked every substantive claim at
the source before changing anything, and acted on all of it except three items I argue against
below.

**One wrong number, and it was a regression we had already caught once.** The appendix compares our
DNABERT-2 fine-tuned head against the published DNABERT-2 row. For TF binding it was reading
$0.7010$, which is Table 4's *mean over five human-TF datasets*. `pilot2/downstream.py:11` and the
`TASK` map in `analyze_downstream.py` both name our task `human_tf_0`, whose Table 6 value is
$0.7199$. Our best over rounds is $0.663$
(`results/dnabert_gue_ds/utility_downstream.md`), so the like-for-like gap is $0.0569 \to 0.057$.
The paragraph *recorded its own regression*: "The TF binding gap read 0.057 in a draft of
24 October and is 0.038." 24 October was right. Somebody --- me --- re-checked the published value
on 27 October, found the number that appears in the bigger, more prominent table, and swapped the
comparator without noticing it was an average over five datasets of which we train on one. The
other five gaps all check out unchanged.

**And in the same paragraph, the fourth one-file-to-a-family generalisation this week.** "The
published recipe uses three [epochs] over the full split" is one of Table 7's five numbers: 3 for
EMP and human TF, 4 for promoter and core-promoter all, 5 for splice. The docstring in
`pilot2/downstream.py` said it too and is fixed. I now have four instances of the same error ---
the predecessor from its abstract, the mask rate from one of four `args.json`, the config table's
row, and this --- and the pattern is always that the one file I read was *representative enough to
believe*. The fix is procedural, not attentional: when a claim is about a set, the grep has to
enumerate the set.

**Three misattributions, all genuine.**

* The predecessor's HyenaDNA row does *not* show "measurable leakage only through membership
  inference". arXiv `2603.08913v3` Table 3 gives it extraction $.15$--$.23$, which is *higher* than
  DNABERT-2's $.09$--$.17$. What it lacks is a perplexity gap: Table 4's ratio is $0.53$--$0.96$,
  below 1, while DNABERT-2 is $1.51$--$1.61$. Table 5's MIA AUC is $0.73$--$0.74$. The correct
  contrast --- no perplexity gap at all, membership signal intact --- is *sharper* than what we
  wrote, so this cost nothing and gained something. This is the fourth time this paper has
  described the predecessor wrongly, and it is the second time the right description turned out to
  be better for us.
* `li2013membership` and `tramer2015bounded` were called "reconstruction attacks on released
  summary statistics" in Methods. They are a membership-privacy framework and a bounded-prior DP
  relaxation for GWAS. The threat-model contrast we wanted survives; the description of the prior
  work does not.
* `carlini2023quantifying` and `jagielski2023canary` were "one instrument, verbatim extraction from
  a prefix scored against planted canaries". Carlini extracts *real training examples* and plants
  nothing; Jagielski's note is about *loss-ranked exposure*. Wrong on both halves, and the "one
  instrument" rhetoric was what made it wrong --- compressing two measurements into one phrase to
  make the gap in the literature look tidier.

**2,548 was the right number against the wrong citation.** The 2015 phase-3 paper reports 2,504.
2,548 is the count of the GRCh38 de novo recall: Lowy-Gallego et al., *Wellcome Open Research*
4:50, PMID 32175479 --- "a set of biallelic SNVs and INDELs, from 2,548 samples spanning 26
populations from the 1000 Genomes Project, called de novo on GRCh38". Availability already named
the exact VCF and said the count came from its header, so the data was never wrong; the citation
behind the number in the abstract-facing text was. New bib entry, and all six mentions now read
"the GRCh38 call set" rather than "1000 Genomes phase 3".

**The masking over-claim had one more hiding place.** Single-slot PLL was twice described as "the
conditional the model was trained on" (Methods, equation 2's gloss and the scorer-choice
paragraph). It is not: DNABERT-2 and NT mask tokens i.i.d. at 0.15, the overlapping family masks
spans of $k$ tokens at 0.15--0.30. This is the same claim I withdrew from the abstract on
29 October, and I withdrew it there without grepping for it elsewhere. Both sites now say
*bidirectional context*, which is the defensible reason to prefer PLL and is also why the decoder
uses it.

**Eight narrowings, all because the cited paper says less than we did.** `morris2025capacity`
*does* vary vocabulary --- Appendix A.1, 128 to 4096, predictions accurate to 1.8% --- so
"capacity does not separate releases that differ in vocabulary" is contradicted by the paper on its
face; the claim is now about matched parameters and matched loss, which is what we actually
measure. `kharitonov2021bpe` writes "We conjecture this effect is caused by reduction in the
sequences' length", so "is attributed to" reported a conjecture as a finding. `che2026memorization`
separates its own local-score memorization from its own extraction game. The exclusive
"identification rather than reproduction is the harm of record in genomics" is gone, and
`lin2004privacy`'s independent-SNP argument no longer silently transfers to a *contiguous* window
whose loci need not be independent. The DP paragraph now says audit both quantities, which is also
what the cited result supports in both directions. Bounded priors interpret a guarantee rather
than being needed to obtain one. The 45M-bit figure is 3.6 bits/parameter extrapolated from
GPT-style models, so the heading no longer reads "Above capacity". `belfiore2025bihmia` is a hybrid
attack over model responses *and* generated-profile features; `paige2021reconstructing` attacks
risk-score *models* where `nikitin2026prs` attacks individual scores.

**Three things in the report I did not do, and why.** The ethics sentence "No cohort was put at
risk to write this paper" stands: the audit is right that `thousandgenomes2015` cannot establish
it, but the citation is attached to "consented for open distribution", which that paper does
support, and the claim rests on the rest of the paragraph. NT's "six nucleotides per token without
overlap" needs no single-nucleotide-fallback caveat when every sequence we feed it is ACGT, and the
audit itself marked that site SUPPORTS. And the optional pages/DOI completions are left alone: this
bibliography omits pages on conference entries throughout, so filling in four would make it
inconsistent, and `plainnat` ignores `doi` anyway.

**Bib.** NT author 5 was `Henryk Grzywaczewski, Adam`, which BibTeX parses as family "Henryk
Grzywaczewski" --- PubMed 39609566 prints Adam Henryk Grzywaczewski. Blattner's second author
carries the suffix III (Crossref). `kharitonov2021bpe` was `@inproceedings` with
`booktitle = {arXiv preprint ...}`, so the references printed "In arXiv preprint arXiv:2110.02782";
it is `@article` now. `refs_submit.bib` regenerated by `strip_notes.py`, 37 entries.

**State.** GitHub `f55c662`, Overleaf `247d6e3`. Recompiled from a fresh clone of the Overleaf
project: 0 errors, 0 undefined, 0 Overfull, 44 pages, References still on page 18, so the **body is
unchanged at 16** --- every replacement was written to the same length or shorter, and the one extra
page landed in the appendix, which is supplementary. Two Underfull hboxes appeared, both cosmetic
and both outside the body: the bibliography line that now carries "Adam Henryk Grzywaczewski" and
a Table A1 caption. `pdftotext` hyphenates that name across a line break, so the first grep for it
reported it missing when it was there --- the same false negative as the `synthetic-canary` check
on 28 October.

## 31 Oct, 19:30 UTC --- second round on the same fixes: the attribution I fixed and then left in

A review of `f55c662` came back with four items. Three stood up and one was not a disagreement at
all.

**The one I fixed and then left in.** Splitting extraction from exposure repaired the instruments
and left the sentence reading "Audits ... inherit two instruments ... and two assumptions", so the
*assumptions* were still attributed to the cited work. That is unfair to precisely the papers the
sentence leans on: the audit's own note on `carlini2023quantifying` says that paper "explicitly
treats extraction as a lower bound rather than assuming failed extraction proves no memorization",
and `mireshghallah2022mlm` is the paper that *designs around* prefix-only probing instead of
trusting it. So I corrected half a sentence and left the half that did the damage. The assumptions
now belong to the reading --- "Reading either as a verdict on a released genomic model takes two
assumptions that do not hold" --- which is where they live, in the transfer rather than in the
sources.

I did not take the replacement offered ("These instruments leave two questions for our evaluation:
how decoding protocols affect measured recovery, and whether failed recovery can coexist with
membership disclosure"). It fixes the attribution by deleting the reasons, and the reasons are the
load-bearing part: the protocol mismatch is what makes the first question worth asking, the
two-way separation is what makes the second more than a hunch, and both carry citations that would
then support nothing.

**Che's scope, this time read at the source instead of from a report.** Definition 3.4 is the local
score class, $h \in \mathcal{H}_{loc}$ iff $h$ depends on $\theta$ only through the conditionals at
$x$'s own prefixes; Section 6 is headed "Separations on the Local Score Class"; Theorem 6.1(iii)
concludes "Hence on $\mathcal{H}_{loc}$ neither measure controls the other"; Definition 3.3 is an
extraction game with list budget $m$ under arbitrarily many adaptive prompts. "In the constructions
of" was an improvement over nothing and still left out the restriction that does the work. The text
now says *local-score counterfactual memorization and adaptive extraction*.

**The ratio's sign, and this one is sharper than what I wrote.** The predecessor's Table 4 is test
perplexity *over* canary perplexity, so HyenaDNA's $0.53$--$0.96$ means its canaries are *harder*
than held-out data, not that the two are equal. "No perplexity gap at all" flattened a
wrong-direction gap into no gap. It reads "no canary perplexity advantage over held-out data" now,
which is what the metric says.

**The ethics sentence, conceded.** My reason for keeping "No cohort was put at risk to write this
paper" was about where the citation sits, which answers the audit's complaint and not the
objection: public inputs, open consent and aggregate reporting do not add up to a claim about
outcomes that nobody can check. I defended the citation and not the sentence. The replacement
offered duplicated the two sentences that follow it, so the lead now states the two facts the
paragraph already expands --- every input public, no model trained on a private cohort attacked ---
and the expansion is unchanged.

**Two non-items.** The NT single-nucleotide fallback was never a disagreement: the original report
says the shorthand is appropriate for ACGT windows divisible by six and needs a qualifier only when
describing arbitrary input. And the optional pages/DOI completions are agreed to be a different
class of thing from a wrong author or a misattributed paper.

**Bib.** Crossref's record for the GRCh38 recall carries a seventh author entry, "The 1000 Genomes
Project Consortium", after Flicek. Added.

**State.** GitHub `9d244d9`, Overleaf `21c6a81`, 33/33 files identical ignoring line endings.
Recompiled from a fresh clone of the Overleaf project: 0 errors, 0 undefined, 0 Overfull, 44 pages,
References still on page 18, **body still 16**.

## 31 Oct, 20:30 UTC --- third round: the fix introduced a defect one layer down

One item, and it was mine. Moving the two assumptions off the authors and onto the reading left
"Reading *either* as a verdict on a released genomic model takes two assumptions that do not hold",
which distributes both assumptions over both instruments. Neither of them belongs to exposure.
Assumption one is about what a prefix-conditioned decoder reads, and a loss-ranked exposure measure
never runs a decoder. Assumption two reads a failure to reproduce as an absence of retention, and
exposure reports a loss ranking and claims nothing about reproduction. Worse, the source I had
attached it to is the one paper whose entire subject is how to interpret exposure properly.

**This is the second round running in which I fixed an attribution one layer up and created a new
one underneath it.** Round one attributed the assumptions to the cited authors. Round two moved
them to "the reading" and quantified over both instruments. The shape is the same each time: I
treat the sentence as an object to be patched rather than re-deriving what each citation is
actually being asked to support. The check that would have caught both is mechanical --- for every
citation in the sentence, name the proposition it supports and confirm the source states it --- and
it is the same check that caught the mask rates and the TF comparator.

**What I took.** The distinction offered is right and I had it collapsed: a protocol difference is a
reason to *compare* decoders on the same checkpoints, not a proof that any decoder fails. That is
now what the text says. Each consideration attaches to the instrument it bears on: the protocol
point to extraction alone, and the other as "neither instrument licenses reading a failure to
reproduce as an absence of retention", which is true of both and puts it in no author's mouth.

**What I did not take.** The proposed four-sentence paragraph drops
`\citep{mireshghallah2022mlm,wang2026infilling}`, which carry "prefix-only probing under-reports on
bidirectionally trained models" --- the clause that makes the protocol difference worth reporting
rather than merely true. Having argued the round before for keeping the reasons, dropping two of the
four citations that carry them would be inconsistent, and four sentences is not what a body six
pages over wants. The substance of all four sentences is in the text; the compression is mine.

**State.** GitHub `cbb7c22`, Overleaf `f2fcd0b`, 33/33 files identical ignoring line endings.
Recompiled from a fresh clone: 0 errors, 0 undefined, 0 Overfull, 44 pages, References on page 18,
**body still 16**.

## 31 Oct, 21:30 UTC --- fourth round: I defended a citation twice without reading it

One item, and it is the worst of the four rounds. In round three I wrote that
`mireshghallah2022mlm` and `wang2026infilling` are "the citations for *prefix-only probing
under-reports on bidirectionally trained models*", and refused to drop them on the ground that
dropping them would delete the reason. **I had not read either paper for that claim.** I was
defending the citations' *position in the argument*, which is not the same thing as checking that
they say what the argument needs.

**Mireshghallah et al. 2022, read from the published PDF.** The abstract: "We devise a stronger
membership inference attack based on likelihood ratio hypothesis testing that involves an
additional reference MLM ... our attack improves the AUC of prior membership inference attacks from
0.66 to an alarmingly high 0.90 level." It is a membership-inference *scoring* paper --- single-model
loss against a reference-model likelihood ratio. It runs no prefix decoder and measures no verbatim
extraction. And its Limitations say so in as many words: "for a thorough analysis of data privacy,
it is not enough to rely only on membership inference attacks. We thus would need to extend our
analysis to reconstruction attacks and property inference attacks." So the source I spent two
rounds defending *states that it did not study the thing I was citing it for*. That is a different
category of error from the rest of this audit: not a weak citation, one the paper contradicts.

**Wang and Asokan 2026** does support the claim, for what it measured. Models are LLaDA-8B-Base and
Dream-7B-Base with LLaMA-2-7B as the autoregressive baseline; every result table is LLaDA and
Dream. The abstract says prefix-only probing "significantly underestimates the risk of
training-data extraction" and that "edge-conditioned masks extract up to three times more verbatim
sequences than prefix-conditioned ones". Nothing about BERT-style masked LMs. "Bidirectionally
trained models" was my generalisation sitting on top of a diffusion-LM result --- the same shape as
the mask rates and the TF comparator, one more time.

The clause now names the models the result is about and drops the source that denies it.
`mireshghallah2022mlm` stays at `p03_setup.tex:227` and `:312` on PLL scoring, which is what that
paper is about and where the audit verified it, so nothing is orphaned.

**The thing worth keeping from this round.** *The appendix already had it right.*
`p11_appendix.tex:531` reads "on diffusion language models, edge-conditioned masks recover up to
three times more verbatim sequences than prefix-conditioned ones" --- correctly scoped, same
citation. The introduction generalised what the appendix stated carefully, and nothing in the
pipeline compares the two. When one claim appears in two places at two levels of care, the loose
one is where to look, and the careful one is the ready-made check.

**Four rounds, four shapes of the same failure.** Round one: assumptions attributed to the authors.
Round two: moved to "the reading" and quantified over both instruments. Round three: fixed. Round
four: a citation defended on its role rather than its content. Each round I patched the sentence
instead of asking, of every citation in it, *what proposition is this being asked to support, and
does the source state it.* That question is now the procedure, and I have run it over all four
citations in that sentence.

**State.** GitHub `3cdc03b`, Overleaf `5302d63`, 33/33 files identical ignoring line endings.
Recompiled from a fresh clone: 0 errors, 0 undefined, 0 Overfull, 44 pages, References on page 18,
**body still 16**.


## 31 Oct — author-approved ten-page manuscript revision (v4)

The main text is now nine compiled pages, with F1/F2/F3 retained, at the unchanged
10pt Letter/one-inch layout. The registered abstract and all measured numbers are
unchanged. Detailed definitions and summary tables were moved/consolidated in the
appendix. Decoder restart counts and corrected-BPE audit coverage were checked
against metadata and made explicit rather than generalized across runs.
See [the full revision and evidence record](23_ten_page_revision_20261031.md) and
[the validation report](23_ten_page_validation_20261031.json) for the scope, checks
and synchronization record. No new experiment was added to the paper.

## 31 Oct, 23:00 UTC --- independent review of the v4 compression

The author asked whether the GPT-executed ten-page compression is sound. Reviewed
against the pre-compression tree at `ae9836c`, not against the revision note.

**The page claim holds, checked independently.** A fresh clone of the Overleaf project
compiles to 40 pages: title page, **nine main-text pages**, References from physical
page 11, appendix after. Zero errors, zero undefined references or citations, zero
overfull boxes, the two known underfull ones. Letter, 10pt, one-inch margins unchanged.
F1, F2 and F3 are all in the main text, on pages 3, 6 and 8.

**No number was invented or silently changed.** Mechanical check: every numeral in the
old body was matched against the new body plus everything the appendix reaches
(`p11`, `p04_leak`, `p07_practice`, `tables/*`). Of the numerals that leave the body,
all but two are decimal-to-percent re-expressions of a surviving value or material that
moved to the appendix. The two genuinely absent from the prose, the $k=6$ cells at
2.10 and 2.20 bits/nt, are plotted in Figure 3 and tabulated per seed in Table A3, so no
evidence is lost. In the other direction, every numeral new to the body resolves to an
existing value: `1.96` and `0.50` are `0.0196` and `0.0050`; `94/98` and the rest are
`0.94/0.98`; `2015` is new prose, and correct --- 2,504 is the 2015 phase-3 paper,
2,548 the GRCh38 recall. Abstract, `refs.bib`, `refs_submit.bib`, `p04`, `p07`,
`tables/*` and `results/figure_data.csv` are byte-identical to baseline.

**The four rounds of citation work survive intact.** Wang still scoped to diffusion
language models; `mireshghallah2022mlm` still absent from the extraction clause and
still present on PLL scoring; Che's separation stated in both directions and no longer
equated with our rank; Kharitonov still conjectural; the predecessor's multi-vector
credit kept; `lin2004privacy` still fenced off from short contiguous windows;
Lowy-Gallego and the 2,548 count still correct.

**The caption defect Astra and I argued about is fixed.** `fig:ident` now reads "at most
1/50 (2\%) in fresh windows and 2/50 (4\%) in borrowed training windows; final fresh
controls are zero in every seed", and the body carries the same split. The pooled
"0 to 2 of 50" that could be misread as the abstract's 0--2\% is gone.

**Figures check out against the prose.** Around fifteen plotted points were read off the
rendered pages and compared with the text: F2's single-copy final own 0.94 and fresh
0.22, round-15 0.04/0.04, round-80 0.46/0.10, the sixteen-copy 0.37 then 0.96 with
recovery 0.10 peaking below 0.46; F3's 2.40-bits curve at 2/12/61/92\% for $k=3$--6 and
full-recovery losses 4.07/2.99/2.63/2.47. All match. `figures_main10.py` imports
`figures_privacy` and reads `results/figure_data.csv`; it holds no data literals.
F1 is exactly 6.5 inches wide so it is not scaled; F5 and F6 are slightly narrower and
are scaled **up** by 1--4\%, so nothing shrinks below its designed size.

**The decoder-budget correction is right, and I verified it from the data rather than
the note.** `rb_*.json` records `restarts: 16` for the overlapping and BPE searches on
chromosome 22 across all three seeds, `restarts: 128` for NT re-masking, and the earlier
`recon_bpe_ep30.json` records 32; `recon_overlap.py:183` and `recon_bpe.py:270` both
default to 16. The old prose's single "$R=128$ restarts" did carry an NT budget onto
decoders that ran at 16, and the revision was right to split them.

**One defect found and fixed (`7aa8d6b`).** The correction reached the prose but not the
Exact-commands block, which is introduced as "One cell of the 23 Oct batch" and still
passed `--restarts 32` to `recon_overlap` and `recon_bpe` with `--name rb_ep120` --- the
same file `app:measurement` now says has 16. Two statements about one file, and a
reviewer running the commands would not reproduce the reported cells. Both now read 16,
and the lead-in no longer calls them "the 32-restart examples", which described none of
the three. The preserved full manuscript in `paper_full/` already had 16, so the two
versions had diverged on exactly this line. Appendix only; the body is unchanged.
Rebuild from a fresh Overleaf clone of `d72dd3b`: 40 pages, References on 11, body nine,
0 errors, 0 undefined, 0 overfull.

**Two things left for the author, not acted on.**

1. *Overleaf has drifted from GitHub.* Overleaf `2b14937`, "Update on Overleaf" by
   yzhang4109@gatech.edu at 2026-11-01 01:17 UTC, deletes `\author[1]{Wenbiao Li}`.
   That is the only content difference between the two trees. Six authors on GitHub,
   five on Overleaf. An author-list change needs the written agreement the author list
   has been waiting on; the direction of the sync is not mine to pick.
2. *The registered abstract is now slightly stronger than the body.* It says "Neither
   tested decoder exactly recovers the hidden 48-nucleotide target of any of these
   single-copy records", while the body correctly records that the BPE search's
   checkpoint coverage is narrower than the prefix protocol's. Nothing is false --- the
   BPE search recovered none wherever it ran --- but "of any of these" reads as the full
   grid. Changing a registered abstract is the author's call.

Also worth knowing: the headline negative result now rests on a BPE search at 16
restarts while NT re-masking got 128. That is disclosed, and it is the honest direction,
but a referee may ask why the weaker budget sat on the headline model.

## 31 Oct, 23:40 UTC --- Wenbiao Li is not an author, and one sentence moved with him

The author confirmed the Overleaf deletion was deliberate. Applied to the two places
that still carried it, local/GitHub and `paper_full/`, so all three trees agree again.

**The removal has a second consequence, and the author block is not it.** The
introduction read "The last study, by five of the present authors, already evaluates
multiple vectors". `nemecek2026quantifying` is Nemecek, Li, Jiang, Vaidya and Ayday.
With Li off this paper the people who author both are Nemecek, Jiang, Vaidya and
Ayday --- **four**. RECOMB is single-blind, so a reviewer can line the two author lists
up and count. Changed to four in both manuscripts. The predecessor's bibliography entry
keeps all five of its own authors; Li is an author of that paper, and `refs.bib`,
`refs_submit.bib` and the citation-audit artifacts are untouched.

The generalisable part: an author-list edit is a content edit, because the manuscript
makes claims about its own authorship. Nothing in the build catches this --- it compiles
either way --- and the only reason it surfaced was grepping for every mention of the
name before touching the file rather than editing the line I was pointed at.

Affiliation [1] is still carried by Zhang, Nemecek and Ayday, both footnote marks still
resolve, and the rendered title page was checked. "five" and "four" are the same length,
so nothing rewrapped.

**State.** GitHub `df279df`. Nine-page Overleaf `765d0f6`: fresh clone compiles to 40
pages, References on 11, body nine, 0 errors, 0 undefined, 0 overfull. Full-manuscript
Overleaf `7e7a7ef`: 44 pages, same clean result. Five authors on both title pages.

One hygiene note found on the way: `paper/main.tex` has mixed line endings, 259 CRLF and
5 bare LF. It compiles and diffs fine either way, so nothing was normalized.

**[Corrected 1 Nov.]** The rest of this paragraph originally said that every file on the
Overleaf side is CRLF while most of the local `sections/` are LF, and that the revision
note's "only main.tex differs in line endings" understated it. That was an artifact of my
own clone, which inherited `core.autocrlf=true` from the Windows system config while this
repo sets `core.autocrlf=false`. Re-cloning with conversion disabled gives one line-ending
difference, `main.tex`, and it runs the other way: the local file is CRLF, Overleaf's is
pure LF. The revision note was right.

## 1 Nov, 00:20 UTC --- review of the revised Figure 1

The author rejected the compact flowchart and asked for the original slide to be edited
and re-exported. Reviewed the result at Overleaf `3674aa2` / GitHub `446e5f9`.

**It is a genuine revision of the original, not a third rebuild.** Measured against the
pre-revision deck preserved at `paper_full/figures/F1_overview.pptx`: 430 shapes before,
400 shapes plus 15 native connectors after, and 25 of the original's 69 distinct text
runs survive verbatim, 44\% of the new deck's strings. The model cards, cohort icons,
DNA curves, mask cells, ranked-candidate list and the 24 and 8 token rectangles are all
there in the render. `pdfimages -list` returns nothing: the PDF is vector and text only,
no raster, fonts embedded. The compact flowchart had 14 text runs; this has 63.

**Why the slide had to get taller.** The original canvas is 960 by 540 points, so at
6.5 inches wide it prints 3.66 inches tall --- and its smallest text is 5.34 points on
the slide, which is **2.6 points on the page**. That figure could never have been used
at paper size. The revision re-proportions the canvas to 960 by 900 and collapses 47
ad-hoc font sizes into seven, 20.6 to 30 points. At the same 0.4875 scale the smallest
text now prints at **10.04 points**. That is the right operation, and it is the reason
the figure is 6.09 inches tall rather than 3.66.

**Every number on the figure checks out against `results/figure_data.csv`**, read
directly rather than from the note. `dnabert2bpe_human_s{0,1,2}`, tier 16, own window,
final: exact 0.40 / 0.44 / 0.40, so the figure's 40--44\% is exact. Tier 1 final: exact
0.00 in all three seeds in both host conditions, rank-1 0.18 / 0.22 / 0.26 fresh and
0.94 / 0.92 / 0.96 own --- the figure's 0\%, 18--26\% and 92--96\%. The run also peaks at
0.46, which is the body's "never exceeds 46\%". The 16-copy **fresh** value is 40--46\%,
within a couple of points of the own-window figure shown, so the panel's own-window
scoping costs the reader nothing even if the asterisk is read as attaching to the BPE
column alone. The caption states the scope anyway.

**One substantive thing left the figure.** The endpoint surprise comparison --- "Teacher-
forced target surprise, end of training", "Surprise gaps within a seventh of each other",
"Stored information is not reachable sequence" --- is gone from panel (c), which now
shows only slot counts and 0\% against 92\%. The body still carries it in full
(\S3.2, "Recovery and target surprise are distinct"), and dropping it makes the figure
*less* committal about the slot-count account, which is the safe direction. But it was
panel (c)'s interpretive punchline, and without it (c) reads as the slot-count story
alone. Worth a deliberate decision rather than an accident. The LOO numbers also left,
which note 25 states and which follows v4's demotion of LOO to a diagnostic.

The control line improved: "0--2 of 50 own, 0 of 50 unseen" became "final fresh 0/50",
which is exactly the pooled-versus-split distinction that cost two rounds of argument.

**One record was wrong and is now fixed.** Note 23 says the author-designated source
`Ppaper_Figure/F1_OVERVIEW.pptx` "is preserved" at SHA `1704418269...`. It is not: the
file was edited **in place** at 22:05 and now hashes `c6529be3...`, byte-identical to
the new `paper/figures/F1_overview.pptx`. Note 25 states the in-place edit plainly, so
this is a stale cross-reference rather than a concealed one, but a reader going to that
path on 4 November would get the new diagram. Note 25 also names a pre-edit backup,
`F1_source_backup.pptx`, which is in its own task directory and is **not** in the project
tree --- so the durable copies of the pre-revision figure are
`paper_full/figures/F1_overview.pptx` and the `paper-full-before-v4-20261031` tag.
Note 23 is a dated record, so the sentence stands and a superseded-by pointer was
appended after it.

**Build.** Fresh Overleaf clone of `3674aa2`: 40 pages, body nine (pages 2--10),
References on 11, F1/F2/F3 on 3/7/8, 0 errors, 0 undefined, 0 overfull, the two known
underfull. Page 9 of the body is about 55\% full, so roughly **0.45 page of slack**
survives the taller figure. Abstract, both bibliographies, generated tables and
`results/figure_data.csv` untouched; local `paper/` has content parity with Overleaf.

**The one thing to decide.** 10.04 points clears the CFP's 10-point minimum by
0.04 point. It complies, but there is no margin: raising the smallest source labels from
20.6 to about 21.5 points would print at 10.5 and remove the question entirely. That is
a figure edit, so it is the author's call.

## 1 Nov, 03:40 UTC --- review of the DIME-styled Figure 1

The author supplied a DIME figure as a visual reference and asked for F1 to be
restyled against it. Reviewed GitHub `9312eb8` / Overleaf `1e5d2f8`.

**Still the same slide, restyled.** Against the previous revision: 400 shapes to
398 plus six more native connectors (15 to 21), and 52 of the previous deck's 57
distinct text runs survive verbatim, 84\% of the new deck's strings. No raster
images; four embedded, subsetted Arial faces. The DIME borrowings are the shallow
gray panel-header strips, bold lowercase panel letters set outside those strips,
thin black arrows and restrained blue/orange accents. Five runs left and ten
arrived, and every one of them is accounted for below.

**Two of my three open points are closed.** The smallest source font went from
20.6 to 21.6 points; reading the `Tf` operators straight out of the exported PDF
gives printed sizes of 10.53 to 14.62 points, so the CFP's 10-point floor now has
half a point of margin instead of four hundredths. And the pre-revision author
source is tracked inside the submission tree at
`paper/figures/archive/F1_author_source_before_20261031.pptx`. Its SHA-256 is
`1704418269...`, the hash note 23 recorded, and it checks out against
`paper_full/figures/F1_overview.pptx`: same 960 by 540 canvas, same 430 shapes,
all 69 text runs identical. My own superseded-by note in note 23 said that hash
no longer described any file in the tree; that is no longer true, and the note was
amended rather than appended to, so a reader is not sent past the nearest copy.

**The endpoint surprise evidence is back, and it is exact.** Recomputed from
`results/kcurve_per_nt.json`, tier 16, epoch 30, three seeds each: control minus
planted teacher-forced target surprise is 2.350 / 2.438 / 2.524 for the 2-mer,
mean 2.4371, and 2.765 / 2.816 / 2.783 for the 6-mer, mean 2.7877. The figure's
2.44 and 2.79 are exact, and `prefix_exact` is 0.0 in all three 2-mer seeds and
1.0 in all three 6-mer seeds, matching the 0\% and 100\%. The body already carried
these two numbers at `p06_slots.tex:42`; that file was not touched, so the figure
is mirroring an existing claim, not making a new one.

**The scientific exposure this creates, which is the one thing worth a decision.**
The abstract's own comment block records why these numbers were kept out of the
abstract: "In one sentence they read as 'the same amount is stored', which two
measurements at different points do not establish." A three-line figure panel is
that compressed context. The figure does scope it --- the header says "End of
training", the footer defines the gap as control minus planted, the caption says
these endpoints are not the matched-loss checkpoints --- but the quantity that
actually decides exact decoding is not the gap, and the asymmetry there is severe.
Mean planted target surprise is 0.824 bits/nt for the 2-mer against 0.0052 for the
6-mer, a factor of about 160; over a 48\nt{} target that is roughly 40 bits of
residual uncertainty against a quarter of a bit. The gaps look similar only because
the control baselines differ too, 3.261 against 2.793, and held-out loss at these
endpoints is not matched either, 3.126 against 2.625. A reviewer with the released
JSON can compute all of this. The claim the body actually makes --- that low
recovery need not imply little target-specific signal --- survives it, but
"similar surprise gaps, different recovery" invites the objection, and neither the
figure nor the body states the absolute planted surprise anywhere. Pre-empting it
is one clause in `p06_slots.tex`. It is the author's call, and it is a content
change, so it was not made.

**Two smaller observations, both figure edits and therefore not made.** In panel
(a) the 48\nt{} target strand is orange and the prefix blue; in panel (c) the same
48\nt{} target strand is blue, because blue and orange there carry 2-mer and 6-mer
instead. The same object is two colours in one figure. And the figure now consumes
a whole physical page: at 6.365 inches plus a ten-line caption it cannot share a
page with text, so page 3 is a float page with roughly an inch and a half of
unused height. Nothing is recoverable without taking the figure under about 4.5
inches, which would undo the font-size fix.

The overall title and subtitle --- "Fine-tuned genomic language models" /
"Membership disclosure without sequence reproduction" --- were removed. Correct
for a figure that sits under a caption, but the figure no longer states its own
thesis anywhere, and the caption's first sentence does not either.

**Build.** Fresh clone of the real Overleaf remote at `1e5d2f8`, compiled locally:
40 pages, main text on 2--10, References on 11, F1/F2/F3 on 3/7/8, 0 errors,
0 undefined, 0 overfull, the same two underfull. Page 10 still ends about 55\% down,
so the 0.45 page of slack survives. All 39 tracked files match the local `paper/`
in content and 0 differ in content. **[Corrected 1 Nov: this sentence originally
claimed 28 line-ending differences against note 26's one. The 28 came from my clone's
inherited `core.autocrlf=true`; with conversion disabled the count is one, `main.tex`,
exactly as note 26 reports.]** Only five
pre-existing files changed against the baseline: the F1 PDF/PNG/PPTX, `F1_source.md`
and the caption in `p01_intro.tex`. Abstract, both bibliographies, generated tables
and `results/` are byte-identical. `Ppaper_Figure/F1_OVERVIEW.pptx` matches the
submission source byte for byte, and `paper_full/` was not touched.

## 1 Nov, 05:00 UTC --- audit of the five-seat review response

The five-seat panel (notes/review_20261101) returned one Major, SC-06, and twelve Minors.
The manuscript response is GitHub `385501a`, Overleaf `d5898d2`. Checked each REV item at
the source rather than against the editorial decision.

**Everything claimed closed is closed, and the code checks out.** REV-06, the Major, splits
the overlapping-DNABERT family into two campaigns. `results/human_real3/*` holds twelve
causal runs, k=3--6 times three seeds, `objective: causal`, 50 epochs, lr 2e-5, snapshots
1/3/8/15/30/50; `results/dnabert_long/*` holds the masked runs, 150 epochs, lr 1e-4,
snapshots 15/30/50/80/120/150. The server's `outputs/human_bh/dnabert6_causal_human_s0`
is causal at 50 epochs, so "their `human_bh` control retraining uses the same objective"
holds. The two new configuration-table rows match these exactly.

The scorer definitions now in A21 match `pilot2/dnabert.py` line for line: `heldout_floor`
has `stride=7` over `range(voc.k, WINDOW - voc.k, 7)`; `rank_probe` takes `--stride`, whose
default is 3, over `range(offset, offset + PROBE_LEN, stride)` with `PROBE_LEN = 96`, so
positions $o, o+3, \ldots < o+96$ is exact; `nt_logprobs` masks tokens $j-k+1\ldots j$ and
reads `min(j, T-1)`, and $T-1 = W-k$, so the paper's $\min(j, W-k)$ is the same token;
`nt_logprobs_causal` reads token $j-k+1$, skips $j<k-1$ and normalises over the four
consistent k-mers.

REV-05: `args.json` gives `epochs: 150`, so "final denotes round 150" is right. Held-out
loss at round 15 reads 1.2662 / 1.2614 / 1.2635 and at final 1.72552 / 1.72807 / 1.73449,
so "1.261--1.266" and "1.726--1.734" are both exact, the last to the digit.

REV-09: `recon_audit.py:367` takes `best["sweeps"]` --- the selected restart's count, not
every restart's --- and `used` is initialised to the cap, so a restart converging on the
final pass is indistinguishable from one that exhausted the budget. The new text states
both facts; the old "the decoder settles before its last pass in 95.8\% of cells" implied
something the data cannot show. $950/22{,}714 = 4.18\%$, so $95.8\%$ is right.

REV-12: `pilot2/sweep.sh` reads `OUT OBJS SEEDS EXTRA TOKS`, so the old command's
`--toks char,2mer,...` inside `EXTRA` was never a flag the launcher accepts. Every value in
the new `EXTRA` matches the recorded `outputs/kcurve300/.../args.json`: epochs 30, tiers
1,4,16, probe\_offset random, probes\_per\_tier 100, n\_nonmember 100, save\_epochs
1,2,3,5,8,12,20,30, score\_snapshots true. REV-13: `--score` exists in `recon_bpe.py` with
`choices=("fixed","pernt")` and default `fixed`, so the historical command did need the
explicit `--score pernt`.

REV-01/REV-10: `pilot2/human_canary.py:128` is `seg[off] = w["alt"]`, a positional
substitution, and the file's own docstring already said "A sequence written from rare
alleles alone is therefore not that person's haplotype even when every rare allele is
theirs." The old manuscript wording was wrong and the correction is not an over-reading.

The ceiling rederivation is also an improvement rather than a hedge: recovery under the
fixed-point condition forces $p_i=1$, and $\mathbf 1[p_i=1]\le p_i^{s_i}$ holds termwise,
so averaging gives $\widehat b$. That is a real proof where the old text asserted
"necessary condition and therefore an upper bound".

**Three things the response got wrong or gave away, none of them asked for by the panel.**

First, `paper_full/` was not touched. The panel's anchors are full-manuscript page numbers
--- p.14 §A2, p.30 §A17, p.34 §A21 --- and that document still reads "On real human
sequence a single copy is enough", "145 of the 400 are a real chromosome's own sequence",
"written with that carrier's own alleles", "145 are real haplotypes", "Do not read a masked
objective as a defense" and "Prefer a tokenizer with more slots". Earlier rounds did
propagate factual corrections there (`f82edb1`, `df279df`), so this is a gap rather than a
policy. Its Overleaf project is unchanged.

Second, the root `README.md` now understates the paper. "The tested decoders recover none
of the hidden 48-nucleotide targets in the reported single-copy evaluations" carries no
scope, while §3 reports NT 250M recovering single-copy records in 8\% of cases in every
seed and 500M in 12--18\%, and calls that the central result of the section. Read on its
own the sentence contradicts the manuscript it ships with.

Third, two defensible claims left the main text. The random-string versus in-distribution
contrast is gone from §3: only "The \emph{E.~coli} canaries above are uniform random
sequences" survives, with no statement of why that matters, and the point now lives only in
A2. And both effect-size statements went --- "That is the largest single effect we have
measured" for masking, "On exact extraction it is still the largest effect we found" for
tokenization. SC-03 and SC-04 objected to reading those as defenses, not to the magnitudes.

**Tone.** Across §§1--6 the "does not establish" class of construction goes from 24 to 34,
concentrated in §3 (4 to 10) and §4 (3 to 7). Every one is defensible; together they end
most paragraphs on a disclaimer.

**Build.** Clean clone of the Overleaf remote at `d5898d2`, compiled locally: 40 pages, main
text on 2--10, References on 11, F1/F2/F3 on 3/7/8, 0 errors, 0 undefined, 0 overfull, the
same two underfull. All 39 tracked files match local `paper/` in content; `main.tex` differs
in line endings only. The registered abstract, both bibliographies, the generated tables and
`results/` were not touched. Page 10 now ends about 63\% down rather than 55\%, so the slack
is roughly 0.35 page instead of 0.45. OPT-04, the 0.99 against 1.00 threshold in the
tokenizer reporting helper, is deliberately left open and does not move any of the 33
trajectories checked.

## 2 November, 08:00 UTC --- the controlled backbone is not a 12.9M model

A two-seat read-only review of the nine-page text raised one actual error and two
presentation items. I checked all three at the source. The error is real and it is larger
than the review states.

**The parameter claim.** `paper/sections/p06_slots.tex:3` says recovery is tested "even when
model size, training objective and corpus are fixed". Only the non-embedding body is fixed.
`pilot2/model.py` gives the backbone a token table `nn.Embedding(vocab_size, d_model)` tied
to the output head and a learned position table `nn.Embedding(max_len, d_model)`;
`pilot2/tokenizers.py` sets the vocabulary to `4**k + 3` and the token count to
`window_nt // k`; `pilot2/train.py:112` builds the model with `max_len = tok.n_tokens + 1`.
Both tables therefore move with $k$ in opposite directions.

The review derived the counts from that source. There is a second and stronger route it did
not use: `pilot2/train.py:197` writes `n_params` and `n_params_non_embedding` into each run's
`train_summary.json` at training time, so the numbers are recorded measurements of the models
that produced the results, not arithmetic over the code. Read from all 18 cells of
`outputs/kcurve300`:

| tokenizer | vocabulary | total parameters | non-embedding |
|---|---|---|---|
| char  |    7 | 12,768,256 | 12,610,560 |
| 2-mer |   19 | 12,697,600 | 12,610,560 |
| 3-mer |   67 | 12,696,576 | 12,610,560 |
| 4-mer |  259 | 12,782,080 | 12,610,560 |
| 5-mer | 1027 | 13,167,616 | 12,610,560 |
| 6-mer | 4099 | 14,735,360 | 12,610,560 |

The non-embedding count is one distinct value across all 18 cells, so the appendix's "Non-
embedding parameters are identical (12.61M) in every controlled cell" is exact, and the
review's derived endpoints (12,697,600 and 14,735,360, 16.0% apart) are exact as well.

**Where 12.9M comes from.** It is not a count of any model of ours. The predecessor
describes `SimpleDNALM` as having "approximately 12.9M parameters and a vocabulary of eight
tokens", and its own table lists 12.9M against character-level tokenization. Our setup
section says we use that architecture, and the figure travelled with the sentence. Our
closest cell in kind, the character model with a seven-token vocabulary, is 12.77M; the
headline 2-mer and 6-mer are 12.70M and 14.74M. So 12.9M is not merely non-uniform across
instances --- it describes none of them. It appears at
`p00_abstract.tex:85`, `p01_intro.tex:46`, `p03_setup.tex:13`, `p06_slots.tex:9`,
`p06_slots.tex:22` (figure caption), `p08_discussion.tex:13` and `p11_appendix.tex:661`.

**What this does and does not cost.** The confound runs in the unhelpful direction at the
headline pair: the 6-mer has 16% more parameters and more recovery. Two things already in the
appendix answer it. Factorizing the embedding to rank 512 is a pure reparameterization and
still moves the 6-mer from 0.61 to 1.44 bits, with no dose-response from rank 27 to 256; and
the character-to-3-mer step, which survives every variant, is matched to 0.56% (12,768,256
against 12,696,576) with the sign reversed --- the character model has slightly more
parameters and recovers less. Neither converts the random-offset sweep into exact
equal-capacity evidence, which is why the claim should be scoped rather than defended.

**The two presentation items.** Both are accurate descriptions of the current text.
`p11_appendix.tex:765--771` names the historical BPE search files as `rb_ep30.json`,
`rb_ep120.json` and `rb_epfinal.json` for each of three seeds at 16 restarts and 50 records
per tier, and the corrected scorer audit as seed 0's `rbfix_epfinal.json`, 60 cells, zero
exact recovery. `p05_identify.tex:6--8` sends both to the appendix without naming the rounds
or stating the corrected outcome, and `p03_setup.tex:135` gives the corrected audit's size
without its result. A main-text reader cannot tell which three of the six checkpoints carry
BPE measurements.

**The four protocol reversals** the contribution seat wants foregrounded are all in the main
text and all check out: NT 250M at round 50, 6% prefix against 64% PLL on the same records
and checkpoint (`p03_setup.tex:80--83`); NT 500M zero prefix against 12--18% re-masking
(`p05_identify.tex:100`); overlapping DNABERT 2/0/4/0% against 0/2/6/50%
(`p06_slots.tex:74--75`); and 0% against 92% at matched held-out loss 2.40 bits, which
`results/kcurve300/MATCHED_FLOOR.txt` records directly with never-trained controls at 0.00.
One qualifier has to travel with the first of these: the 64% is an own-window rate, the
privileged condition the paper is careful elsewhere not to present as a weights-only attack.

**Build.** `930e6a6` reached Overleaf as `95751b1`. Clean clone with conversion disabled,
compiled locally: 40 pages, main text on 2--10, References on 11, 0 errors, 0 undefined,
0 overfull, the same two underfull. All 39 tracked files match local `paper/` in content;
`main.tex` differs in line endings only. The last body page now carries 40 text lines against
47--51 on a full page, so the slack is roughly 8 to 10 lines --- the bounded-effect restoration
in `930e6a6` spent part of what was there. Any remedy adopted from this review has to be
close to length-neutral.


### 2 November follow-up: exact HyenaDNA buffer classification

The 6,554,624 trainable count is confirmed by loading the actual medium-160k model on CPU.
A remaining detail in the preceding correction is wrong: the additional 2,048 buffer values are
`filter_fn.modulation.deltas`, not filter biases. All eight `filter_fn.bias` tensors (256 each)
are trainable and already included in 6,554,624. Registered buffers total 7,682,144:
6,400,080 positional z + 1,280,016 positional t + 2,048 modulation deltas.
See note 30 for the 18-cell parameter audit, manuscript and figure corrections, and release receipt.

## 2 November, 11:00 UTC --- reviewed the parameter-accounting revision at the source

Submission Overleaf `021f9f5`, full-version Overleaf `71e652a`, GitHub `bc74ced`. Both clones
taken with conversion disabled. Submission: 39 tracked files, 0 content differences against
local `paper/`, `main.tex` differing in line endings only. Full version: 39 tracked files,
0 content and 0 line-ending differences.

**Every site is right.** `12.9` no longer occurs anywhere in `paper/`. The abstract reads "a
controlled transformer trained from scratch"; `p01_intro` "a controlled from-scratch backbone";
`p03_setup` "A transformer with a fixed 12.61M non-embedding backbone"; `p06_slots` opens on
"the non-embedding backbone, training objective and corpus fixed" and states 12.61M
non-embedding against totals of 12.70--14.74M; the Figure 3 caption reads "Fixed non-embedding
backbone"; `p08_discussion` keeps HyenaDNA's 6.55M and pairs it with "the controlled 12.77M
character model". The new appendix `app:capacity` prints all six totals and the 0.56%
character-to-3-mer gap with the character model named as the slightly larger one.

**My own correction was wrong about which tensor, and the revision caught it.** Loading
`hyenadna-medium-160k-seqlen-hf` with `AutoModelForCausalLM` gives parameters 6,554,624 and
buffers 7,682,144, summing to 14,236,768. `named_buffers` holds `pos_emb.z` 6,400,080,
`pos_emb.t` 1,280,016 and `modulation.deltas` 2,048; the eight `filter_fn.bias` tensors appear
in `named_parameters`, so they are trainable and already inside 6,554,624. I had subtracted the
filter bias instead of the modulation deltas. The appendix paragraph now states this exactly.
The end-of-log follow-up recorded it but left the three dated entries naming the wrong tensor;
those are amended in place, as is the Chinese log's inserted block.

**Both decoder-scope items are closed in the main text**, so neither now depends on the
appendix: `p05_identify` names "Historical BPE search at rounds 30, 120 and 150 across three
seeds", and `p03_setup` gives the corrected audit as "60 seed-0 final-checkpoint cells at 16
restarts, with zero exact recovery".

**Figure 1 is a genuine source edit, not a rebuild.** Old and new decks both hold 408 shapes,
22 connectors, 78 text runs, no raster media, and the same seven source font sizes with a
minimum of 21.6 pt, which at the 0.4875 include scale prints at 10.53 pt. Exactly one run
differs: "Same backbone, objective and corpus; synthetic canaries planted 16 times" became
"Fixed non-embedding body, objective and corpus; 16-copy synthetic canaries". Layout and data
are untouched.

**Builds.** Submission: 40 pages, body on PDF 2--10 (printed 1--9, so 9 of the 10 allowed),
References from printed 10, F1/F2/F3 on 3/7/8, 0 errors, 0 undefined, 0 overfull, the same two
underfull. The last body page carries 40 text lines against 47--51 on a full page, unchanged
from before the revision, so the edits were length-neutral. Full version: 44 pages, body
printed 1--16, References from printed 17, same zero counts.

**One hygiene item, raised not acted on.** Saving the deck from PowerPoint added
`ppt/changesInfos/changesInfo1.xml` to both `F1_overview.pptx` and `F1_overview_compact.pptx`.
It carries an Azure AD `userId` GUID and edit timestamps. The author name was already published
in `docProps/core.xml` and the venue is single-blind, so this is not an anonymity question, but
the account GUID is a persistent identifier now in a public repository. Deleting
`ppt/changesInfos/` is lossless for rendering and does not touch the PDF.

## 2 November, 16:00 UTC --- verified the LOO ceiling defect at the source

Reviewed the supplemental boundary audit against `pilot2/recon_audit.py`, `pilot2/score.py` and
the stored NT result files. **The defect is real and every number in the audit reproduces.**

**The scope mismatch, confirmed in source.** `score.py:98` `_cover` widens the hidden interval to
token boundaries. `recon_audit.py:162` builds the admissibility mask from
`nt0 + i < start_nt` only --- there is no `end_nt` argument and no constraint on the host bases
*after* the hidden interval, so the trailing fragment of the last covering token is free.
`recon_audit.py:359` decodes all covering tokens and then slices `start_nt - lo : end_nt - lo`,
and `exact` is Hamming zero on that crop, so a flipped trailing host base is not an error. The
leave-one-out probe at `recon_audit.py:376-385` restores the *full* original covering tokens and
compares argmax token identity against `xt[pos]`. Recovery and the probe therefore score different
objects, and `p11_appendix.tex:858`'s "recovery requires $p_i=1$" does not follow for this endpoint.

**The three cited records, read from the JSON myself.** All have `exact=true`, Hamming 0,
`sweeps_used < 6`, `loo_top1 < 1`, `restarts=128`:

| file | tier | probe | offset | offset%6 | ntok | sweeps | loo p | bound |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| nt500/nt500m_mlm_human_s0/rb_ep50.json | 1 | 33 | 27 | 3 | 9 | 4 | 0.888889 | 0.346439 |
| nt_ckpt/nt250m_mlm_human_s0/rb_ep15.json | 16 | 104 | 46 | 4 | 9 | 3 | 0.888889 | 0.346439 |
| nt_seeds/nt250m_mlm_ecoli_s1/recon_n50_ep50.json | 16 | 143 | 42 | 0 | 8 | 5 | 0.875000 | 0.343609 |

The first is a single-copy human record, so the falsified necessary condition lands on the tier the
paper's central claim rests on.

**My own scan: 43 such rows across 36 NT files with `cells`, exactly one of them aligned.** The six
human seed-0 `rb` files give 12 rows and 131 off-grid evaluations each, matching the audit. The
audit's "23 rows in 16 files" is a narrower net, not a conflict.

**Zero aggregate exceedance, checked independently.** Across all 18 tier groups of those six files,
and across each group's sub-cap subset, no mean recovery rate exceeds its mean `loo_bound`. The
worst margin is NT500M human s0 ep50 single-copy: 0.12 against 0.2431, and 0.2727 against 0.4303 on
the 22 sub-cap outputs. The empirical ordering holds; the per-record certificate does not.

**Where I go further than the audit: the aligned case excludes the boundary explanation
outright.** For `offset % 6 == 0`, `start_nt = offset + 48` is divisible by 6, so `_cover` is the
identity, `lo == start_nt`, and `recon_audit.py:255` sets `letters = None` --- **no admissibility
mask is ever built and the eight covering tokens exactly tile the 48 hidden nucleotides.** Cropped
exactness then forces the selected token state to equal the true token state, so the fixed-point
condition and the LOO probe evaluate the same conditional at the same state and must agree. They
disagree (0.875). The only remaining difference in that code path is batch width: the search calls
`masked_logits_batch` on chunks of 64 out of 128 restarts, the probe calls `masked_logits` on a
single row, both under `torch.autocast(bfloat16)`. The audit called this "a plausible additional
explanation"; for that record it is the *only* surviving one. **Consequence: constraining both
boundary fragments would not by itself restore the certificate** --- matched arithmetic is also
required, which makes the minimum repair (retract the bound reading, keep the measurements) the
only cheap route.

**Table A12's probe-granularity sentence is wrong, and the paper's own arithmetic says so.**
`p04_leak.tex:143` reads "per token for the first three models and per nucleotide for the
overlapping family". But `recon_bpe.py:246` is `loo ** len(target)` where `target` is the
*nucleotide* positions, and `recon_bpe.py:61-64` masks every token whose span covers nucleotide
`j`. I checked every stored BPE record: the exponent equals `n_generated_nt = 48` in all of them.
The appendix already relies on this --- A21 prints $\widehat p = 0.945$, $\widehat b = 0.268$ and
$\widehat p^{48} = 0.065$ for the single-copy DNABERT-2 cell, which is `rb_epfinal.json` seed 0 at
0.9446 / 0.2683 / 0.0648 exactly. So **DNABERT-2 is nucleotide-level like the overlapping family**,
and the caption contradicts A21. This also scopes the boundary defect: because the BPE and
overlapping probes run over exactly the 48 hidden nucleotides, they have no covering-token
overhang, so **the scope mismatch is confined to the two NT rows.** [Superseded --- see the 19:00 UTC entry: the mismatch is in `recon_audit.py`, so it also covers the k-mer backbone rows, and the BPE absence is vacuous.]

**The 164/145 item is already handled in the manuscript.** `p11_appendix.tex:111` narrates the
correction in the text: the earlier audit "reported 164 real haplotypes" and requiring the second
half of the condition gives 145. The stale `results/canary_status_rates_s{0,1,2}.json` still carry
164/1/235 against the current aggregate's 145/20/235, and no current generator reads them, so this
is a repo hygiene item, not a paper error.

**Verified the other local corrections.** The 8/8/14% and 66--76% at `p07_practice.tex:27-28` are
sixteen-copy rates: the E. coli seeds read tier-16 0.08/0.08/0.14 at ep15 and 0.66/0.68/0.76 at
ep50, with tier 0 and tier 1 at zero in all six files. The arm is correctly E. coli (the section
header names `nt250m_mlm_ecoli_s*`), so the only gap is the copy tier, and the preceding sentences
dwell on the single copy at 0%, which is what makes "This changes" misread. `p11_appendix.tex:75`
does call AC/AN "carrier frequency"; the construction itself uses genotype-derived `n_carriers`
(`canary_census.py:57-60`, `carrier_audit.py:55-57`), so the filter is sound and this is wording
only. `p11_appendix.tex:721` "supports no threshold" is too strong for a rank-1 statistic, which
does define a decision rule but no transferable low-FPR calibration. `p11_appendix.tex:489` draws
"rather than about how the model encodes position" from one alternative encoding; RoPE still encodes
position relatively, so the supported claim is that the effect is not specific to learned absolute
embeddings.

Nothing changed in the paper, the figures, Overleaf or `pilot2/` this round. The bound retraction is
a claim-scope decision across A6/A10/A16/A21 and the ceiling column names, and it is the author's
call.

## 2 November, 19:00 UTC --- corrected my own scope claim; the defect reaches the k-mer backbone

Two sentences from the previous entry came back narrowed. One narrowing is about wording. The other
pointed at a claim of mine that is simply wrong, and checking it widened the repair.

**The convergence premise holds, so one candidate explanation is eliminated rather than merely
unlisted.** `recon_audit.py:331-341` computes `changed` per restart row before each assignment, sets
`used` to the first pass at which that row stopped moving, and leaves `used` at the cap for rows that
never settled. So `sweeps_used < 6` is equivalent to the selected restart having reached a genuine
fixed point of the batched conditional, and non-convergence cannot explain any violation row. The
module's own `--chunk` help at `recon_audit.py:431-434` says results are "algorithmically independent
of this, but bf16 picks different kernels per batch shape", which is prior evidence for the remaining
difference. But identifying a difference is not demonstrating causation. The accurate sentence is: the
aligned record cannot be explained by boundary mismatch, and the batched-versus-singleton arithmetic
is the one candidate the code still offers, pending a replay. That replay is one probe at `--chunk 1`.

**My "confined to the two NT rows" was wrong.** The mismatch lives in `recon_audit.py`, so it reaches
every row that function produced, and that includes the controlled k-mer backbone, not only NT.
Scanning every stored decoder row by family:

| family | rows | exact | exact + settled | violations | aligned | off-grid |
|---|---:|---:|---:|---:|---:|---:|
| `recon_audit`, NT | 4480 | 432 | 352 | 43 | 1 | 42 |
| `recon_audit`, k-mer backbone | 10870 | 994 | 994 | 14 | 1 | 13 |
| `recon_bpe`, DNABERT-2 | 1750 | 0 | 0 | 0 | 0 | 0 |

So 57 violation rows, not 43, and **two** aligned ones:
`results/nt_seeds/nt250m_mlm_ecoli_s1/recon_n50_ep50.json` tier=16 probe=143 offset=42, and
`results/curve/6mer_mlm0.15_s0/recon_n50_ep190.json` tier=1 probe=39 offset=144 --- a single-copy
k-mer record at 128 restarts. The relabelling therefore has to cover the k-mer tables, Table A3 and
the tokenizer comparison among them, not only the two NT rows of `tab:loo`.

**The BPE absence is vacuous, which is a stronger reason than the wording one for keeping it a
diagnostic.** `recon_bpe.py` scores Hamming over exactly the nucleotide positions its LOO probe
iterates, so its endpoint matches by construction and no boundary fragment can exist. But it also has
zero exact recoveries in 1750 stored rows, so no row there *can* show the signature: the absence
tests nothing. Its sweep calls `dist()` on a `(restarts, L)` batch while its LOO probe calls it on a
single row (`recon_bpe.py:209` against `:229`), so it carries the same arithmetic split as
`recon_audit`. Nothing has validated its power values; they are unexercised. Keeping every power
summary as a conditional-prediction diagnostic, BPE included, is what the evidence supports.

What stands unchanged from the previous entry: the source chain, the three reproduced records, the
absence of any aggregate exceedance, Table A12's wrong granularity sentence, and the seven local
corrections.

**Repaired the Chinese log.** `log_loo.py` serialised its Chinese block with ASCII-only escapes, so
lines 3510-3581 of `claude_notes/17b_实验记录_第3周_中文.md` read as literal escape text instead of
characters. Rewrote only those lines, only the escape sequences, with a line-count and leftover-escape
check before writing.

Nothing changed in the paper, the figures, Overleaf or `pilot2/` this round.

## 2 November — LOO interpretation corrected in both manuscripts; submission appendix condensed

Implemented the author-approved repair documented in note 31. Per-record power values are
conditional-prediction diagnostics in every arm, not recovery certificates; full-token
versus cropped-target endpoints and search/probe numerical paths are distinguished.
The two manuscript versions retain all measured outcomes. A17 additionally separates
the round-3 single-copy and sixteen-copy surprise values, which the old paragraph mixed.
The submission appendix is 23 pages (previously 27), with all 264 infilling audit rows
retained as CSV and a generated grouped table. Main body remains 9 pages; full manuscript
remains 44 total pages and was not compressed. Active figures need no bound-label edits.
Both local builds have 0 errors, undefined references and overfull boxes; raw result files,
bibliographies, abstract body text and existing table data rows are unchanged. See
`notes/31_loo_correction_appendix_revision_20261102.md` and its validation receipt for
final remote commits, clean builds, data preservation and the archive tag.

Final release receipt: GitHub manuscript `a5de548` (factual repair `c914ab9`), public
code/data `b0af7a4`, submission Overleaf `cf54fae`, full Overleaf `13ce514`.
Actual remotes were freshly cloned and compiled: short 36 total / 9 main / 23 appendix;
full 44 total / 16 main / 24 appendix. Both have 0 errors, undefined and overfull,
and 2 underfull notices. All 41 short / 39 full tracked files match local content;
only short `main.tex` differs in line endings. Every rendered remote page matches
the corresponding local build. Final validation JSON accompanies this note.

## 2 November, 22:00 UTC --- verified the post-revision review against a clean Overleaf checkout

Cloned the submission project `6ac94420e9ee0b0898c127f7` fresh with `core.autocrlf=false`,
`core.eol=lf`, at `cf54fae`, 41 tracked files. Every tracked file is byte-identical to local except
`paper/main.tex`, which is identical after stripping CR. Built it from that clean checkout:
pdflatex, bibtex, pdflatex, pdflatex, all exit 0, **36 pages**, zero undefined references or
citations, zero overfull boxes above 20pt. The bound retraction did land: `p04_leak.tex:106-108`
now reads "This is a conditional-prediction diagnostic, as in every arm, not a bound or an
attainable whole-record recovery rate".

**All eight reported items are real at the source.** Checked each against the generated tables and
the stored results rather than against the review:

1. `recon_audit.py:19`, `:521-522` and `:527-528` still generate the retracted reading --- "`bound`
   = top1^steps is the implied ceiling on all-48-exact extraction, so a cell whose bound is ~0
   cannot be rescued by any decoder", and "`LOO bound` ... is the rate at which a fixed point can be
   the true string, and it is the column to read against `ICM exact`". The user-visible headers in
   `recon_bpe.py:342` and `recon_overlap.py:255` still print `LOO bound`. `bound` and `loo_bound`
   are also JSON field names in every stored result, so only the prose and headers can move; the
   fields need a compatibility note, not a rename.
2. A16, `p04_leak.tex:101-113`. The 30% is `tab:cost`, whose caption is "Released masked
   checkpoints on *E. coli*, records planted $16\times$", and whose DNABERT-2 row is standard 30% /
   ours 0%. The chromosome-22 single-copy LOO (93--95%, power 0.21--0.39) sits between the opening
   and that 30%, with no corpus or tier named at either switch. This is the highest-stakes of the
   eight: a reader can leave with "single-copy human records are 30% recoverable", which inverts
   the paper's own boundary.
3. A13, `p11_appendix.tex:486-496`. Confirmed wrong pointer --- `tables/t_capacity.tex` (Table A7)
   has no 20x row at all. Its generated header is "capacity and parametrisation controls at matched
   held-out loss"; its rows are embedding rank, feed-forward width, embedding LR and spaced
   variants over 1--2 seeds. The real source is `results/big20x/` (3mer/6mer/char x 2 seeds, AR).
4. A19, `p11_appendix.tex:615-617`. "50 records per tier" is blanket, but `t_capacity`'s caption
   says "Fixed canary placement, 20 records per tier" and the edge-conditioned audit says "20
   canaries each". Only the from-scratch sweep is carved out.
5. Figure A2, `p07_practice.tex:57` and `:74`. `tables/a4_ident_perseed.tex` gives DNABERT-2
   round~15 single-copy id 0.04/0.04/0.04 own-host, so the span is 0.04 to 0.94, not zero to 0.94.
   But the same table's control own-host id also reaches 0.04, with the footnote "13 of the 36
   control cells are non-zero, none above 0.04", so a bare "4%" would invent a new overstatement.
   The same caption already calls NT's identical 0.04 "already identifies 4% of single copies"
   while calling DNABERT-2's "zero".
6. A2, `p11_appendix.tex:43-44`. "every rate in the paper is all 48 target nucleotides exactly
   right" is false --- Table A2's `id` columns and the LOO top-1 rates are not exact recovery.
7. A14, `p11_appendix.tex:518-520`. Sharper than reported: `p11_appendix.tex:47` itself defines
   "Repetition tiers are 1, 4 and 16 copies; tier 0 is a never-trained canary", so "all three
   repetition tiers" is wrong by the appendix's own definition, not merely loose.
8. A17, `p07_practice.tex:95`. `tab:scale` dashes @2.20 for 1,000 and 2,500 windows, so "every
   cohort size is identified at 0.91 or better" covers five sizes where three reach that loss; the
   following clause already says "every size that reaches it". The table's caption also says "The
   manipulated quantity is the number of chromosome 22 windows, not the number of participants",
   which the prose's "cohort size" fights directly.

**One finding beyond the eight, inside item 3's paragraph, and it is worse than the pointer.**
A13 claims the tokenizers "separate absolutely rather than quantitatively: the character model
memorizes *nothing* ... the \kmer{3} is at chance". The character half holds --- `char_ar_s0` r=16
is median rank 156--204 of 500, rank-1 0.00, 2.000 bits/nt, z +0.45. The 3-mer half does not.
`results/big20x/gate1_report_final.md`, `3mer_ar_s1`, scorer `ar/train`, r=16: **median rank 7 of
500, rank-1 rate 0.20, p<=0.01 rate 0.50, mean z +2.25**, against chance rank-1 0.0020. Seed 0
own-host r=16 is median 52 with z +1.20. So the 16-copy 3-mer canaries carry clear membership
signal and still extract 0%. Collapsing that into "at chance" contradicts the source and also
contradicts this paper's own central distinction; stating it correctly supports the thesis instead.

**Repo hygiene.** `paper/main.tex` is committed with CRLF (258 CR), alone among every tracked paper
`.tex`/`.bib`, while Overleaf's copy is LF. That is backwards from the repo's `core.autocrlf=false`,
`core.eol=lf` rule, and normalising it would make local and Overleaf byte-identical.

Nothing changed in the paper, the figures, Overleaf or `pilot2/` this round.


## 2 November — scoped claim repairs and corrected Figure A2 source joins

Implemented the author-approved corrections in both manuscripts; see note32. A16 now
separates E. coli sixteen-copy extraction from chr22 single-copy LOO; A13 reports the
3-mer own-window sixteen-copy rank-1 values 0%/20% by seed with zero recovery and links
the actual big20x reports. Character zero recovery is not called absence of memory.
The previous 22:00 entry's control interpretation is superseded: round15 matched
own controls are 2%/0%/2%; 4% occurs at final/seed0, not at round15.

A further figure-source defect was found: Figure A2's utility files carry stale
recognition summaries (BPE early 10-record probes and NT mixed-host values).
The plot now uses published 50-record own-window CSV rates: NT seed0 8/30/64%,
BPE round15 4% each and final94/92/96%. MCC and raw data are unchanged.
Configuration/tier/corpus-size statements and the directed quantifier findings were
scoped to their actual measurements. Report text now calls both prefix/LOO powers
diagnostics; legacy JSON fields and decoder calculation are unchanged by AST check.
Both local PDFs remain36/44pages, main9/16, appendix23/24, with zero errors/undefined/
overfull and two existing underfull notices each. Final remote receipts follow in note32.


Final release receipt: manuscript `f506930`, decoder report text `e499131`, LF-only
`7ed9a1e`; initial notes `b7cad3d`; public code `ff722d9`. Submission Overleaf
`e803509`, full Overleaf `2bc7c82`. Both actual remotes were freshly cloned and built:
short36/main9/appendix23; full44/main16/appendix24; errors/undefined/overfull all0,
underfull2 each. All41 short and39 full tracked files are now byte-identical to local,
including main.tex; every rendered page matches the local build. Hard-coded references
pass4/4 and5/5. Final PDFs and checks are in work/claim_cleanup_20261102.


## 2 November — mean linear-probe MCC and Figure A2 closeout

Applied the approved reporting/layout fixes to both manuscript versions. Table A13
distinguishes three-seed BPE MCC ranges from NT seed0; the text names mean
linear-probe MCC, selecting round15, and individual seeds0/1 versus seed2
(round15 versus50). Figure A2 labels the BPE mean explicitly, defines its
mean curves and MCC min–max band, and moves the legend away from the curve.
All raw measurements, other figures, abstract and bibliography are unchanged.
See note33 and its validation receipt for sources, builds and remote identifiers.


## Final synchronization receipt

Paper/code commit6213180; public figure code 627f258; submission Overleaf
d244fe2; full Overleaf 1c52c83. Fresh clones of both actual Overleaf
remotes built successfully:36/44pages, main9/16, appendix23/24, errors0,
undefined0, overfull0, existing underfull2 each. All41/39 tracked files are
byte-identical to local. Every rendered page matches its local build.
Local xref checks pass4/4 and5/5; the same source and remote aux are checked
before final release. Both new validation notes use LF. No measurements changed.
Final PDFs are in work/mcc_scope_20261102.


## 2 November — Figure 2 baseline overlap removed

Separated membership and prefix-recovery endpoints; preserved seed means/ranges and
tabulated single-copy controls. Figure34 note records the exact sources, validation
and remote receipts. Submission remains nine main pages. No measured data changed.


## 2 November — Final citation verification

Citation-audit checked35 actual references and52 occurrences against live primary
sources: all KEEP/SUPPORTS, no mandatory corrections. Broad published-baseline wording
can optionally be clarified; Table9 supports it, so no false-positive correction is
required. Notes35 and canonical audit artifacts retain evidence and limitations.
No manuscript or bibliography edits were made by this audit.

## 3 November — Main-paper self-containment and source provenance

Implemented the author-approved evidence/method repairs in both manuscripts; the
full version is not compressed. See notes/42_main_self_containment_20261103.md.
The same-model four-background HyenaDNA epoch-30 range remains65–100%: synthetic
scores_final.json explicitly records epoch30. Added TablesA17/A18 with raw-source
hashes and a public aggregate manifest; scorer controls are paired with their
headline member cells, not mixed with the pooled500-evaluation control rate.
The controlled-sweep final record duplicates numberedepoch30 in all33 runs;
including it changes current2.40-bit/nt means by0. Corrected the obsolete code
comment. Initial builds: submission body10pages, appendix24; full body18pages.
No headline data, abstracts, bibliography or figure assets changed.


## 3 November — Consistency corrections and utility deduplication

Implemented the author-approved consistency repairs in both manuscripts, preserving
the full version. See notes/43_consistency_and_utility_dedup_20261103.md.
The utility collector merges repeated task panels by training configuration, seed
and checkpoint, includes legacy single-task measurements, and checks hidden48.
238 unique checkpoint cells replace file-weighted aggregation of280 source files.
HyenaDNA final recovery is99/120=82.5%; the prose range is0–6% to36.7–100%.
The 69/73 site counts are retained for different400-window coordinate sets, which
share only six starts; Hamming controls are35.4/35.7 and haplotype proportions
36.25%/36.69%. NT schedules and figure-label wording are corrected.
Eight focused tests and independent42-row/source checks pass; all11 public table
fragments regenerate exactly. Final local builds: submission38pages/main10, full50
pages/main18. No errors/undefined/Overfull; the full version retains its known F1
float-size warning. Abstracts, bibliographies, figures and main CSV are unchanged.

Remote receipt: GitHub implementation93bf65b (generator3aa660d), public codeb89ab11,
submission Overleaf29943a6, full Overleafd9e4dce. Fresh remote clones compile to
38/50 pages with10/18 main pages, source parity44/44 and42/42, and exact PDF page-text
parity with local builds. See43_consistency_remote_20261103.json.


## 3 November - Access conditions and public release repair

Own-window qualifiers now accompany the controlled 0%/92% comparison; fresh-window
0%/0.33% is reported with its synthetic16-copy scope. Corpus-size interpolation uses
the best-loss checkpoint and subsequent branch. Bilingual README rendering and
reproduction setup are repaired. Public manuscript/old appendix sources are removed
from the latest tree at author request, with Git history retained by explicit choice.
Archive-independent table generation preserves all reported cells. See note52 for
validation and final synchronization receipts.
