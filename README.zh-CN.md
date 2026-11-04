# 不复现序列的成员泄露

[English](README.md) | **简体中文**

论文 *Membership Disclosure without Sequence Reproduction:
Privacy Leakage from Fine-Tuned Genomic Language Models* 的代码与测量结果。

我们研究微调后的基因组语言模型是否会泄露候选记录的训练成员身份，以及是否能精确恢复序列。
实验涵盖八个公开检查点和一个受控 Transformer，比较上下文访问条件、评分方法、解码协议和分词方式。

## 核心结果

| 实验 | 报告结果 | 条件 |
| --- | --- | --- |
| DNABERT-2，chr22，单拷贝记录 | 未见窗口中的 rank-1 比例 **18–26%**；匹配对照 **0%** | 最终检查点、三个训练种子、每种子 50 条记录、100 个其他候选 |
| 受控合成 canary | 2-mer / 6-mer 精确恢复率 **0% / 92%** | 原训练窗口（own-window）中的前缀解码，植入十六次，匹配 held-out loss **2.40 bits/nt** |

在已报告的 DNABERT-2 单拷贝评估中，两种被测解码器都未精确恢复隐藏的 48 nt 目标，
但两者评估的检查点范围不同。这不是所有模型都零恢复：另一组 NT 实验的单拷贝恢复率
为 8%（250M）和 12–18%（500M）。候选排名**不是个人身份识别，也不是经过低假阳性率校准的成员推断**。
不同训练种子使用相同记录；背景损失匹配不意味着目标可预测性相同，也不能证明 token 槽位数是唯一机制。

## 目录

- [快速开始](#quick-start)
- [图表来源与生成口径](#provenance)
- [重新训练与测量](#model-measurements)
- [解码命令与预算](#decoders)
- [受控分词器扫描](#tokenizer-sweep)
- [论文证据索引](#evidence-map)
- [发布范围与解释边界](#release-boundaries)
- [补充审计细节](#supplementary-details)
- [论文与公开复现材料](#manuscript-artifacts)
- [仓库导航与检查](#navigation)

<a id="quick-start"></a>
## 快速开始：重生成图表

从新克隆的仓库根目录运行。此流程不需要 GPU、模型权重或基因组数据下载。

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

**字体：**绘图需要 Arial。可以安装字体，或将 `GLMEXT_FONT_DIR` 设为包含常规、粗体、
斜体和粗斜体 TTF 文件的本地目录。仓库不分发字体；缺失时会明确报错，不会静默替换。
只生成表格不需要 Arial。

上述命令从公开测量生成 **Figure 2–3 和 22 个 TeX 表格片段**（13 个原表及 9 个精简排版片段），
输出到 Git 忽略的 `reproduced/`。公开仓库不包含论文稿件或可编辑图件资源。
Figure 1 是作者制作的示意图；定量图表的生成程序仍在仓库中，重生成这些图表不需要 TeX。

<a id="provenance"></a>
## 图表来源与生成口径

`figures_main10` 生成正文两张定量图。Figure 1 通过 Microsoft PowerPoint 导出，
其中训练终点的 surprise 数值来自 `results/kcurve_per_nt.json`。
`results/figure_data.csv` 提供主要轨迹，其余 JSON/Markdown 测量报告提供补充表格数据，
详见[测量结果说明](results/README.md)。

`appendix_source_cells` 从聚合清单重建 HyenaDNA 第 30 轮与重叠 DNABERT 全量 50 条记录的表格。
如果持有原始 `outputs/`，可运行 `python -m pilot2.appendix_source_cells --root .`
独立重数原始评估并输出来源哈希。清单也记录成员与对照的 scorer 审计，不包含序列或记录身份标识。

六任务效用表使用 `results/dnabert_gue_ds/utility_downstream.json` 的未舍入聚合值和覆盖信息。
同一训练配置、种子、检查点的重复任务面板先合并，再计算均值；各任务使用可用种子，
不是每个任务与轮次都齐全的平衡面板。快速开始中的命令不需要私有输出即可生成效用表。
如需从原始评估重新生成聚合清单：

```bash
python -m pilot2.analyze_downstream \
  --root outputs/dnabert_gue_ds outputs/dnabert_gue_ds2 outputs/dnabert_yeast_ds \
         outputs/hyena_gue_ds outputs/hyena_gue_ds2 outputs/hyena_yeast_ds \
  --out-dir reproduced/utility
```

其他附录定量图也可从公开聚合结果重建：

```bash
python -m pilot2.figures_privacy --out reproduced/figures
```

精简表格式化程序复制数值单元，仅调整展示标签和移除表注中的程序文件名；
不重新加权或计算统计量。`results/compact_table_cells.json` 保存解码代价、条件诊断及
语料规模表的原数值和科学条件，生成这些表不需要论文或历史 TeX 源文件。

<a id="model-measurements"></a>
## 重新训练与测量

原训练环境为 Python 3.10.18、PyTorch 2.1.1 / CUDA 12.1、transformers 4.29.2、
tokenizers 0.13.3。核心依赖记录在 `requirements-paper.txt`，具体模型后端可能需要额外包。
协作仓库中的 `requirements/requirements.txt` 是更广的环境快照，并非最小安装方案。
完整 GPU 训练与上面的轻量图表复现是两条独立流程。

```bash
python -m pip install -r requirements-paper.txt
export GLMEXT_DATA=/path/to/genomic-inputs
```

将 IGSR GRCh38 recall 的 `ALL.chr22.GRCh38.phased.vcf.gz` 与匹配的 chr22 参考
FASTA `chr22.fa` 放到 `$GLMEXT_DATA/human/`。VCF 的 2,548 个样本属于 GRCh38 recall，
不是 2015 年 phase-3 论文的样本数。该相位化调用集于 2019 年 3 月 12 日公告，
染色体 22 的 VCF 文件日期为 2019 年 2 月 27 日，其参考序列标识为
`GRCh38_full_analysis_set_plus_decoy_hla.fa`，即包含 decoy 和 HLA 序列的 GRCh38 组装。
这些是上游数据文件名，不是脚本；`chr22.fa` 则是构造程序要求的本地染色体输入文件名。
具体文件名和文件日期在此记录，论文附录只保留科学数据集和参考组装名称。
论文实验使用历史的按位置替换构造：

```bash
python -m pilot2.human_canary
python -m pilot2.canary_census --npz "$GLMEXT_DATA/human/canaries_chr22.npz" \
  --out reproduced/human_canary_census.json
```

复现论文记录集时**不要加 `--phased`**。原构造不能保证真实的相位单倍型：400 个窗口中，
审计分类为 145 个已观测单倍型、20 个个体内基因型复合记录、235 个未观测复合记录。
稀有携带者筛选针对锚定位点，不自动适用于整段窗口。

运行 NT 示例前请使用单独环境：原 NT 任务实际使用 Transformers 4.44.2 和 tokenizers 0.19.1，
而上面的 DNABERT-2 环境使用 4.29.2 和 0.13.3。将上游
[NT v2 250M 检查点](https://huggingface.co/InstaDeepAI/nucleotide-transformer-v2-250m-multi-species)
下载到 `pilot2.nt` 要求的目录结构：

```bash
python -m venv .venv-nt
source .venv-nt/bin/activate
python -m pip install "numpy==1.24.3" "torch==2.1.1" "transformers==4.44.2" \
  "tokenizers==0.19.1" "huggingface_hub==0.24.6"
export NT_ROOT=/path/to/pretrained-nt
python - <<'PY'
import os
from pathlib import Path
from huggingface_hub import snapshot_download
name = "nucleotide-transformer-v2-250m-multi-species"
snapshot_download(repo_id=f"InstaDeepAI/{name}",
                  local_dir=str(Path(os.environ["NT_ROOT"]) / name),
                  ignore_patterns=["jax_model/*"])
PY
```

每个启动 NT 训练或解码的 shell 都要导出 `NT_ROOT`。它下面的 250M 子目录名必须为
`nucleotide-transformer-v2-250m-multi-species`，包含 `config.json`、`vocab.txt`、权重及模型 Python 文件。
使用 [500M 检查点](https://huggingface.co/InstaDeepAI/nucleotide-transformer-v2-500m-multi-species) 时，
将下载名中的 `250m` 换成 `500m`，训练参数改为 `--size 500m`。
加载器以 `trust_remote_code=True` 读取本地模型，缺失时不会自动下载。
该下载命令取得上游当前快照，不保证等于历史训练使用的权重修订。

下面是一个 NT 250M 微调示例：

```bash
python -m pilot2.nt --size 250m --data human --epochs 50 --mask_rate 0.15 \
  --canary_npz "$GLMEXT_DATA/human/canaries_chr22.npz" \
  --probes_per_tier 50 --pool 100 --seed 0 --out outputs/nt_human_s0
python -m pilot2.recon_audit --root outputs/nt_human_s0 --ckpt ckpt_ep50.pt --restarts 128
```

其他实验应结合对应运行的 `args.json`、带日期的 `pilot2/queue_*.sh` 与论文配置读取，
一个通用示例不能复现所有表格单元。该 NT 示例保存 `ckpt_ep<N>.pt`；其他后端的命名可能不同，
请以各次运行记录为准。

<a id="decoders"></a>
## 解码命令与预算

| 协议 | 更新单位或用途 | 报告预算 |
| --- | --- | --- |
| Prefix | 模型词表中的逐步生成 | 一次从左到右的 greedy 生成；无 beam、采样或重启 |
| `pilot2/recon_audit.py` | 非重叠 token 的 re-masking ICM | NT 重测：128 次重启，最多 6 轮 sweep |
| `pilot2/recon_overlap.py` | 重叠 k-mer 的核苷酸更新 | 主重测：16 次重启、4 轮 |
| `pilot2/recon_bpe.py` | 重新分词后的 BPE 核苷酸候选 | 历史主测：16 次重启、4 轮；共同区间修正另作审计 |

从仓库根目录运行，并在启动命令的 shell 中显式设置 `GLMEXT_DATA`。
非交互 shell 不一定读取 `.bashrc`。以下路径要求已有重建后的运行目录；
使用新输出名或隔离副本，避免覆盖历史结果。

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

最后一条命令复现的是**历史的按候选覆盖长度相除的 BPE scorer**。
共同区间修正应使用 `--score fixed` 和另一个输出名；论文只在 seed 0 最终检查点的 60 个单元上审计了它，
不是整条三种子轨迹。早期搜索使用 32 次重启，主 chr22 核苷酸搜索使用 16 次，token 搜索使用 128 次。
Token re-masking 的 `--chunk 1` 可复现历史单行计算路径；更大的 bf16 batch 可能改变近似平局的 argmax，
不保证跨所有平台逐位一致。

Prefix 在每一步对允许的 token 取 argmax，并回填自己的预测。一次从左到右生成并不是整条记录只调用模型一次，
而是每个生成 slot 调用一次。48 nt 评价终点也不意味着边界对齐后的输入恰好透露 48 nt，
或评价时要求覆盖边界的完整 token 都正确。

<a id="tokenizer-sweep"></a>
## 受控分词器扫描

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
```

`sweep.sh` 会激活记录中的 `glm` 环境，其他机器需要相应调整。
训练和重评分需要输入及检查点，不能与只读公开聚合结果的快速开始混为一谈。
上述 CSV 导出写入 `reproduced/`；绘图命令默认仍读取已提交的 `results/`，
新导出不会自动替换论文测量。

<a id="evidence-map"></a>
## 论文证据索引

| 论文内容 / 稳定标签 | 测量文件与生成程序 | 关键范围 |
| --- | --- | --- |
| 配置与批次（`app:config`, `sec:basis`） | `outputs/*/args.json`、`train_summary.json`、模型入口和带日期的启动脚本 | 重叠 DNABERT 的 50 轮 causal 与 150 轮 masked 是不同批次。 |
| 人类记录（`app:haplo`, `app:resources`） | `pilot2/human_canary.py`、`canary_census.py`、`pilot2/canary_haplotype_audit.py`；`results/human_canary_haplotype_audit.json` | 原始 400 个窗口与后来的相位重建不同；69、73 对应不同集合。 |
| 匹配宿主（`app:bh`） | 原 borrowed-host 运行与 `results/figure_data.csv` 的对照行；配对对照行 | own 对照匹配 donor tier；fresh 的背景和偏移独立抽样。 |
| DNABERT-2 轨迹（`tab:ident`） | `results/figure_data.csv`；`pilot2/appendix_tables.py`、`figures_main10.py` | 六个检查点、三个种子、每 tier 50 条；含十六拷贝 fresh 排名。 |
| Hidden-48 误差（`tab:target48`） | `results/target48_audit.json`；`pilot2/target48.py`、`export_figure_data.py` | 按核苷酸坐标裁剪；没有预测字符串的 `legacy_variable` 行不能重新裁剪。 |
| 分词器扫描（`tab:slots`） | `results/kcurve300/`、`results/kcurve/`；`pilot2/kcurve_report.py`、`figures_privacy.py` | 300 nt 主实验与 288 nt 复现分开；逐 run 按 loss 顺序插值。 |
| 参数与位置（`tab:capacity`, `tab:placement`） | `results/figure_data.csv`；生成的 `t_capacity.tex`、`t_placement.tex`；`pilot2/appendix_tables.py` | 固定位置、每 tier 20 条、一或两个种子，不是严格等容量的随机位置实验。 |
| 解码代价与诊断（`tab:cost`, `tab:loo`） | `results/compact_table_cells.json`、`pilot2/compact_appendix.py`；原 `outputs/chr22_rerun/`；`results/nt_ckpt/`、`results/nt_seeds/` | 解码器、目标、拷贝层级、分母和访问条件须一并读取。 |
| 跨模型来源单元（`tab:hyena30`, `tab:overlap50`） | `results/appendix_source_cells.json`；`pilot2/appendix_source_cells.py` | 含来源路径和哈希；均匀背景 HyenaDNA 的 `scores_final.json` 实际记录 epoch 30。 |
| Scorer 审计（`app:measurement`, `app:bpenorm`） | `bpe_divisor_final.json` 及 E. coli 报告；`pilot2/score.py` 中的定义 | 2,000 次评估包括 tier 0；500 次合并对照不等于三个 headline 的 50 条对照。 |
| 效用（`tab:a6`, `sec:blind`） | `results/dnabert_gue_ds/utility_downstream.json`、`utility_at_leak.json`；表格和绘图程序 | 配置/检查点去重后合并任务面板；包含零 MCC；冻结探针与微调头分开。 |
| Edge-conditioned 解码 | `results/human_mlm/infill_audit.md`；生成的 `t_infill_summary.tex`、`t_infill_cells.csv` | 88 个配置、264 个 tier 行、每行 20 条；完整分组可从公开审计报告重新生成。 |
| 数据划分与语料规模 | 生成的 `t_draws.tex`；`results/scale22/`、`results/big20x/` | 窗口数不是独立参与者数；20 倍数据也改变更新次数。 |

`outputs/` 指原始运行和检查点目录，不表示公开仓库包含这些文件。
已公开的聚合报告在 `results/`；来源清单标明原始路径，并不承诺分发相应权重。
完整路径见来源清单，批次例外条件见下文；不要仅凭表号推断命令。

<a id="release-boundaries"></a>
## 发布范围与解释边界

原始输入来自公开来源。仓库提供聚合测量和去除敏感字段的评估记录，
不分发完整稀有记录集合、锚定位点到样本的关联信息、或包含这些记录的微调权重。
重新构造并训练与重放已发布表格不同。三个训练种子重复使用同一记录集，不是独立队列复现。
一次数值重放导致抽取率变化六个百分点，不能由此估计通用数值方差或保证成员排名始终稳定。

`bound`、`loo_bound` 等历史 JSON 字段为兼容性保留名字和数值，其含义是条件预测幂值诊断，
不是经过证明的恢复上界。搜索评价裁剪后的 48 nt，token LOO 可能评价完整覆盖 token；
batch 与单行路径的数值也可能不同，且存在边界已对齐的反例。提前停止不能恢复该逐记录证书，
BPE 的零恢复也不能验证它。历史附录中的完整状态命题要求更新映射、约束、数值运算和 tie-breaking
全部相同，并不为已报告输出提供证书。

合成 canary 十六拷贝的 2-mer / 6-mer，在匹配 loss 2.40 bits/nt 时，
原训练窗口（own-window）中的前缀恢复率为 0% / 92%。同一 matched loss 的 fresh-window
逐种子插值均值分别为 0% / 0.33%（6-mer 三种子为 1%、0%、0%）。
该访问条件比较限于这组十六拷贝合成实验。实验固定主干、目标函数与语料，
但不证明目标可预测性相同或 slot 数是唯一原因。
训练终点的 planted covering-token surprise 为 0.824 / 0.0052 bits/目标核苷酸：
计算包含最后一个 token 内的宿主后缀，并按 48 nt 归一化，不是严格 48 nt 事件的边缘概率。
这些训练终点也不是 matched-loss 检查点。

重叠 DNABERT 的 50 轮 causal 微调提供跨模型成员比较，150 轮 masked 微调提供解码及 LOO 诊断。
两批次不共享检查点。

<a id="supplementary-details"></a>
## 补充审计细节

这些细节对应进一步精简的附录。论文保留主要轨迹、误差及对照；精简效用表只列最佳 held-out
与最终检查点，`appendix_tables` 生成的完整 `a6_downstream.tex` 仍保留六个初始检查点行。
`compact_appendix` 只选择并复制数值行，不重新计算均值。
此外，300 nt 与 288 nt 分词器实验分成同一张续表的两个片段，保留全部种子和数值，字号不变。

### 测量批次与条件预测诊断

统一数值基础的解码重测包括 10 月 23 日的 19 个 chr22 运行/检查点组合及 10 月 19 日的
7 个 E. coli 组合。更早的目标函数、位置、edge-conditioned、下游与容量对照，并未全部在
10 月 18 日服务器重启后重跑。一次配对重放使抽取率改变六个百分点，而 rank-1 和 held-out loss
保持报告精度一致；这不构成数值方差估计。

DNABERT-2 最终检查点、seed 0、单拷贝的平均 LOO 准确率为 0.945，逐记录幂值的均值为 0.268；
先平均准确率再取 48 次幂则是 0.065。这是不同的聚合方式，不是恢复概率，仍受检查点、种子、
裁剪终点以及 LOO 提供其余真实目标位置等条件限制。

正文保留的人类单拷贝子集结果为：兼容记录 fresh-window 命中 5/21、5/21、8/21，
未观测复合记录为 1/23、3/23、0/23。按等位数量分组则为 27/78 对 6/72 次评分：
26 条单变异与 24 条多变异记录各重复用于三个训练种子，不是独立参与者样本。

### 单独的微调分类头比较

该实验不同于效用表的冻结探针：最多 20,000 条标注序列训练两轮，而已发表方案按任务训练
三至五轮并使用完整划分。包含零值的所有可用 MCC，共 476 次评估进入 252 个模型/轮次/任务汇总。
从最佳 held-out 到最终检查点，DNABERT-2 的微调头在六个任务中的四个上升。
其各任务最佳分数仍低于同数据集已发表 DNABERT-2 分数，差值如下：

| 任务 | MCC 差值 |
| --- | ---: |
| H3 | 0.039 |
| Promoter | 0.049 |
| TF dataset 0 | 0.057 |
| H3K4me3 | 0.069 |
| Core promoter | 0.085 |
| Splice | 0.095 |

比较使用同数据集的普通 DNABERT-2 行，来源见
`results/dnabert_gue_ds/utility_downstream.json`。TF 比较 dataset 0，而不是五个数据集均值。
这些缩减 recipe 下的比较不能宣称 benchmark parity。

### 成员/对照划分重抽样

这里的 **excess 定义为同一检查点下，非成员 surprise 减去成员 surprise，单位 bits/nt**，
对应 `pilot2/analyze_matched.py`。它不是参与者识别率，也不能证明全部分数差都由训练成员身份造成。

四次划分重抽样显示，预训练时的初始偏移不是可固定扣除的量。报告中各划分的 round-1 excess
为 0.00 +/- 0.05，round-50 excess 对初始偏移的回归斜率为 0.05--0.19。
其中三个划分可做 matched-loss 比较，第四个的损失分支没有共同范围。
可比较划分中，单拷贝 excess 的变化范围为 0.06--0.27 bits/nt，十六拷贝为 0.07--0.64。
完整结果保留在 `pilot2.appendix_tables` 重新生成的 `t_draws.tex` 及
`results/human_ds2345/`、`results/human_ds3456/`、`results/human_ds4567/` 的报告中。
这支持在各评估条件内设置对照，不证明对新参与者样本稳定。

语料规模表的插值只使用每个运行的最佳 held-out loss 检查点及其后检查点，再按 loss 排序；
这是该表特有的最优点后分支限定。matched loss 只是在同一预测损失水平比较，**不能独立控制优化更新次数**：
更新次数仍与语料规模混杂，参与者构成也不是被操纵的变量。

<a id="manuscript-artifacts"></a>
## 论文与公开复现材料

当前公开版本不包含论文源文件、可编辑图件或历史附录源文件。完整版稿件和备份另行保留。
本 README 汇集复现命令、批次限定和审计细节；`results/` 保存已发布测量与来源清单。
快速开始中的命令可重新生成定量图和表格片段。历史实验笔记仍用于记录过程，
其中已撤回的解释不代表当前论文主张。

<a id="navigation"></a>
## 仓库导航与检查

- [测量说明](results/README.md)：来源与指标口径。
- [代码导航](pilot2/README.md)：当前实验与分析入口。
- [仓库整理说明](docs/REPOSITORY.md)：当前与历史材料。
- [实验笔记](notes/README.md)：实验及更正记录；旧解释可能已被撤回，须结合当前论文阅读。

`pilot2/` 为本研究代码，`results/` 为测量结果，`notes/` 为实验日志；`pilot/` 是冻结的早期实现。
可选回归检查：

```bash
python -m unittest discover -s tests -v
```

## 致谢与许可

本工作基于 Alexander Nemecek 的 GLM-Memorization 框架及公开基因组模型后端。
前作为 Nemecek 等人的 *Quantifying memorization and privacy risks in genomic language models*
（ACM-BCB 2026）。采用 [Apache License 2.0](LICENSE)。
