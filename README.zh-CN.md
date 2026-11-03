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

**字体：**绘图需要 Arial。可以安装该字体，或将环境变量 `GLMEXT_FONT_DIR`
设为包含常规、粗体、斜体和粗斜体 TTF 文件的本地目录。仓库不分发字体。
只生成表格时不需要 Arial。

上述命令从已发布测量结果生成 **Figure 2–3 和 13 个表格片段**，输出到 Git 忽略的
`reproduced/`。Figure 1 是独立的可编辑 PowerPoint 图，参见
[源文件与导出说明](paper/figures/F1_source.md)。
仓库中的 `paper/` 只包含图件资源，不是完整的 LaTeX 稿件。

## 根据需求选择入口

- **核查论文数字：**[测量结果说明](results/README.md)。
- **重新生成图表或训练模型：**[详细复现指南](docs/REPRODUCING.md)。
- **寻找实现：**[代码导航](pilot2/README.md)。
- **区分当前入口与历史材料：**[仓库整理说明](docs/REPOSITORY.md)。
- **追踪实验与更正：**[实验笔记索引](notes/README.md)。

以上详细技术文档目前保留英文；中英文首页提供相同命令和实验边界。

## 发布范围

实验原始输入来自公开来源。仓库包含聚合测量及去除敏感字段的评估记录，
不提供完整的人类 canary 集合、样本关联信息或包含这些记录的微调权重。
重建输入并重新训练，与从已发布结果重生成表格，是不同的复现流程。

历史 JSON 的 `loo_bound` 等字段名为兼容性而保留。
对全部已报告模型族，这些幂值都是**条件预测诊断指标，不是 48 nt 恢复率的严格上界**。
历史报告和日志可能保留后来撤回的解释，请结合测量结果说明阅读。

## 致谢与许可

本工作基于 Alexander Nemecek 的 GLM-Memorization 框架及公开的基因组模型实现。
前作为 Nemecek 等人的 *Quantifying memorization and privacy risks in genomic language models*
（ACM-BCB 2026）。本仓库采用 [Apache License 2.0](LICENSE)。

附录迁出的命令、文件映射及详细实验说明见[论文复现与证据索引](docs/PAPER_PROTOCOLS.md)，其中也保留了精简前的长附录快照。
