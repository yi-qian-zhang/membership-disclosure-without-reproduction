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
| 受控合成 canary | 2-mer / 6-mer 精确恢复率 **0% / 92%** | 植入十六次，匹配 held-out loss **2.40 bits/nt** |

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
- [长附录归档](#appendix-archive)
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

上述命令从公开测量生成 **Figure 2–3 和 20 个 TeX 表格片段**（13 个原表及 7 个精简版），
输出到 Git 忽略的 `reproduced/`。Figure 1 是独立的可编辑 PowerPoint 图，参见
[源文件和导出说明](paper/figures/F1_source.md)。本仓库的 `paper/` 包含图件资源，
不是完整 LaTeX 稿件；重生成图表不需要 TeX。

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
不重新加权或计算统计量。若两个跨模型来源表的标准生成片段缺失，会使用已核实的归档副本。

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
不是 2015 年 phase-3 论文的样本数。论文实验使用历史的按位置替换构造：

```bash
python -m pilot2.human_canary
python -m pilot2.canary_census
```

复现论文记录集时**不要加 `--phased`**。原构造不能保证真实的相位单倍型：400 个窗口中，
审计分类为 145 个已观测单倍型、20 个个体内基因型复合记录、235 个未观测复合记录。
稀有携带者筛选针对锚定位点，不自动适用于整段窗口。

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
python -m pilot2.export_figure_data --root outputs --out reproduced/figure_data.csv```

`sweep.sh` 会激活记录中的 `glm` 环境，其他机器需要相应调整。
训练和重评分需要输入及检查点，不能与只读公开聚合结果的快速开始混为一谈。
上述 CSV 导出写入 `reproduced/`；绘图命令默认仍读取已提交的 `results/`，
新导出不会自动替换论文测量。

<a id="evidence-map"></a>
## 论文证据索引

| 论文内容 / 稳定标签 | 测量文件与生成程序 | 关键范围 |
| --- | --- | --- |
| 配置与批次（`app:config`, `sec:basis`） | `outputs/*/args.json`、`train_summary.json`、归档配置段 | 重叠 DNABERT 的 50 轮 causal 与 150 轮 masked 是不同批次。 |
| 人类记录（`app:haplo`, `app:resources`） | `pilot2/human_canary.py`、`canary_census.py`、`carrier_audit.py`；`results/human_canary_haplotype_audit.json` | 原始 400 个窗口与后来的相位重建不同；69、73 对应不同集合。 |
| 匹配宿主（`app:bh`） | 原 borrowed-host 运行与 `results/figure_data.csv` 的对照行；归档对照段 | own 对照匹配 donor tier；fresh 的背景和偏移独立抽样。 |
| DNABERT-2 轨迹（`tab:ident`） | `results/figure_data.csv`；`pilot2/appendix_tables.py`、`figures_main10.py` | 六个检查点、三个种子、每 tier 50 条；含十六拷贝 fresh 排名。 |
| Hidden-48 误差（`tab:target48`） | `results/target48_audit.json`；`pilot2/target48.py`、`export_figure_data.py` | 按核苷酸坐标裁剪；没有预测字符串的 `legacy_variable` 行不能重新裁剪。 |
| 分词器扫描（`tab:slots`） | `results/kcurve300/`、`results/kcurve/`；`pilot2/kcurve_report.py`、`figures_privacy.py` | 300 nt 主实验与 288 nt 复现分开；逐 run 按 loss 顺序插值。 |
| 参数与位置（`tab:capacity`, `tab:placement`） | `results/figure_data.csv`；归档 `t_capacity.tex`、`t_placement.tex`；`pilot2/appendix_tables.py` | 固定位置、每 tier 20 条、一或两个种子，不是严格等容量的随机位置实验。 |
| 解码代价与诊断（`tab:cost`, `tab:loo`） | 归档表；原 `outputs/chr22_rerun/`；`results/nt_ckpt/`、`results/nt_seeds/` | 解码器、目标、拷贝层级、分母和访问条件须一并读取。 |
| 跨模型来源单元（`tab:hyena30`, `tab:overlap50`） | `results/appendix_source_cells.json`；`pilot2/appendix_source_cells.py` | 含来源路径和哈希；均匀背景 HyenaDNA 的 `scores_final.json` 实际记录 epoch 30。 |
| Scorer 审计（`app:measurement`, `app:bpenorm`） | `bpe_divisor_final.json` 及 E. coli 报告；归档定义 | 2,000 次评估包括 tier 0；500 次合并对照不等于三个 headline 的 50 条对照。 |
| 效用（`tab:a6`, `sec:blind`） | `results/dnabert_gue_ds/utility_downstream.json`、`utility_at_leak.json`；表格和绘图程序 | 配置/检查点去重后合并任务面板；包含零 MCC；冻结探针与微调头分开。 |
| Edge-conditioned 解码 | `results/human_mlm/infill_audit.md`；归档 `t_infill_summary.tex`、`t_infill_cells.csv` | 88 个配置、264 个 tier 行、每行 20 条；完整分组结果已迁入仓库。 |
| 数据划分与语料规模 | 归档 `t_draws.tex` 和实践段；`results/scale22/`、`results/big20x/` | 窗口数不是独立参与者数；20 倍数据也改变更新次数。 |

`outputs/` 指原始运行和检查点目录，不表示公开仓库包含这些文件。
已公开的聚合报告在 `results/`；来源清单标明原始路径，并不承诺分发相应权重。
完整路径、例外条件见[长附录归档](docs/appendix_reference_20261103/README.md)，不要仅凭表号推断命令。

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

合成 canary 十六拷贝的 2-mer / 6-mer 在匹配 loss 2.40 bits/nt 时恢复率为 0% / 92%。
该比较固定主干、目标函数与语料，但不证明目标可预测性相同或 slot 数是唯一原因。
训练终点的 planted covering-token surprise 为 0.824 / 0.0052 bits/目标核苷酸：
计算包含最后一个 token 内的宿主后缀，并按 48 nt 归一化，不是严格 48 nt 事件的边缘概率。
这些训练终点也不是 matched-loss 检查点。

重叠 DNABERT 的 50 轮 causal 微调提供跨模型成员比较，150 轮 masked 微调提供解码及 LOO 诊断。
两批次不共享检查点。

<a id="appendix-archive"></a>
## 长附录归档

[精简前的补充材料](docs/appendix_reference_20261103/README.md) 保存完整源文件、原始表格和 SHA-256 清单。
旧表号对应旧版排版，定位时请使用上面的语义名称与稳定标签。

- **留在论文：**正文与主图、DNABERT-2 全部种子轨迹和 hidden-48 SE、两种窗口的分词器扫描、
  匹配对照、解码预算与诊断边界、scorer 敏感性、数据版本、参数/位置对照、跨模型结果、效用图表及补充实验结论。
- **迁入仓库：**命令、JSON/CSV/程序名、文件级来源、操作与优化细节、开发更正历史、重复论述，
  以及完整 19 单元审计、infilling 分组、划分重抽样和 census 表等详细材料。
- **另行保存：**完整版论文未压缩；原投稿长附录在上述归档中保留。归档是历史版本，当前投稿版决定论文表述。

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
