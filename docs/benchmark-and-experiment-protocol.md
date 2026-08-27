# 基准定位、性能优化与扩展实验协议

**版本：** 2026-08-27
**适用范围：** 本文档仅适用于本仓库的**纯合成蒙特卡洛统计诊断**。其不包含、也不推断任何真实企业的 ESG、审计质量或投资效率关系。

## 1. 任务定义与可比性结论

本项目评估一个确定性公开的数据生成过程（DGP）下的两阶段面板估计管线。第一阶段在完整的合成 firm-year 面板中拟合预期投资；第二阶段以对数绝对估计残差为结果变量，回归滞后 ESG、滞后 Big Four 审计师指示变量及其交互项，并报告 firm-clustered、two-way firm–year 与受限 firm-level wild-bootstrap 诊断。核心评价量是**空假设拒绝率（尺寸）**、**备择下拒绝率**、**系数均值**与其**蒙特卡洛标准误（MCSE）**。

> 该任务不是机器学习预测、文本分类、问答或 ESG 评级任务。因此，分类 F1/AUC、问答准确率、文本生成评分和经验回归系数都不能作为本项目的共同“性能分数”。

Google Scholar 检索结果、arXiv 的 ESG 基准论文与 Papers with Code 入口核验均未给出在 DGP、样本流、估计量、固定效应及推断规则上与本项目一致的公开排行榜。Papers with Code 的 ESG 搜索入口在核验日重定向至 Hugging Face 趋势论文页，未返回同协议榜单。这个观察只限定于该检索路径，并不表示 ESG 领域没有其他研究。因而，本仓库不声称 SOTA，也不生成伪造的 SOTA 排名。

## 2. 三个规模可核验的 ESG 数据集/基准

下表用于界定领域资源，**不用于将本项目的拒绝率与其指标做数值比较**。

| 数据集或基准 | 公开规模与来源 | 原始任务与主要指标 | 与本项目的可比性 |
|---|---:|---|---|
| Corporate Sustainability Disclosure Dataset | 29,134 份中国上市公司 MD&A 文本 [1] | 以词典扩展与 TF–IDF 构造企业年度可持续披露指数 | 可支持未来披露代理研究；没有本 DGP 的投资残差、Big Four 时序或 Monte Carlo 尺寸目标。 |
| ESG Benchmark | 310 份 2010–2024 DJIA 公司 ESG/财务报告；291 个问题（132/114/45）[2] | 三层 ESG 智能体问答与报告生成 | 文档/问题是单位；问答或报告质量不是二阶段统计诊断指标。 |
| ESG-Activities | 1,325 个 EU taxonomy 标签文本片段；核心人工集 265 个（212 train / 53 test），外加 1,060 个合成训练句 [3] | ESG 活动文本匹配/分类 | 适用于潜在 NLP 扩展；不应与 $\beta_3$、MCSE、检验尺寸或功效混列。 |

## 3. Top-5 相关工作对照表：不是 SOTA 排行榜

由于不存在共同的经验风险或共同试验协议，下表保留用户要求的五项对照结构，但明确其是**研究设计地图**，而非 SOTA 表。任何把异质数据、异质样本和异质统计量排序为“Top-5”的做法都会误导读者。

| 对照研究/资源 | 年份 | 数据或对象 | 报告指标/贡献 | 链接 | 为什么不能与本项目数值比较 |
|---|---:|---|---|---|---|
| Biddle, Hilary & Verdi | 2009 | 经验会计研究 | 残差式投资偏离的研究传统 | [论文 DOI][4] | 是实证财务报告质量研究，而非预设 DGP 下的拒绝率评估。 |
| Cameron, Gelbach & Miller | 2008 | 聚类误差回归模拟/推断 | cluster bootstrap-t 推断 | [论文 DOI][5] | 提供推断方法依据，但没有 ESG–Big Four 合成交互 DGP。 |
| Xue | 2025 | 理论模型 | ESG 披露精度、市场力量与投资激励 | [论文 DOI][6] | 解析模型，不报告可与本仓库同口径的 Monte Carlo 尺寸或功效。 |
| Zhao et al. ESG Benchmark | 2026 | 310 份公司报告、291 个问题 | ESG 智能体问答/分析评估 | [arXiv][2] | 指标为 AI 任务质量，不是面板回归的 $\beta_3$ 或拒绝频率。 |
| Birti, Osborne & Maurino ESG-Activities | 2025 | 1,325 个标签文本片段 | ESG 文本活动识别 | [arXiv][3] | 分类/匹配任务；训练集包含合成扩增，且没有共同结果变量。 |

## 4. 当前表现：仅可量化内部统计校准差距

外部“性能差距”是**不适用（N/A）**，因为不存在同协议的基准分数。可量化的是相对于预注册的名义显著性水平 $\alpha=0.05$ 的内部校准差距。主 N=300 合成 DGP 采用两条独立主种子、合并 $R=2,000$；这些数字来自公开聚合表，而非任何真实样本。

| 情景与推断 | 当前拒绝率 | 名义 5% 的差距 | MCSE | 解读边界 |
|---|---:|---:|---:|---|
| 交互项空假设，firm-clustered | 0.0640 | +1.40 个百分点 | 0.00547 | 该 DGP 中略高于名义水平；不是一般有效性判断。 |
| 交互项空假设，two-way firm–year | 0.1035 | +5.35 个百分点 | 0.00681 | 当前最重要的校准风险；仅适用于八个可分析时间簇的主 DGP。 |
| 交互项空假设，firm wild bootstrap（$R=600$） | 0.0433 | −0.67 个百分点 | 0.00831 | 受限 firm-level 诊断，并非 multiway wild bootstrap。 |
| 完全备择，firm-clustered | 0.2460 | 不适用 | 0.00963 | 在设定的合成效应下的可检测性，不是现实效应大小。 |
| 完全备择，two-way firm–year | 0.2870 | 不适用 | 0.01012 | 同上；不得解释为外部优越性。 |

## 5. 代码审计：三个瓶颈与两个已实现补丁

### 5.1 瓶颈

| 优先级 | 瓶颈 | 原因 | 影响范围 | 本轮处置 |
|---:|---|---|---|---|
| 1 | 同一二阶段设计被重复固定效应残差化 | 对相同的 ESG、Big Four、交互项和 FE，每个协方差或 oracle 结果变量原先单独执行交替投影。 | `basic_second_stage_result` 的 firm、two-way 与 oracle 分支。 | 已实现设计缓存和结果变量独立投影。 |
| 2 | wild bootstrap 内层重复分组加总 | 每个 Rademacher draw 都构造 cluster scores，造成大量 Python/数组层小操作。 | 399 个内层抽样及任何更高抽样数。 | 已实现固定组成员矩阵的确定性批量收缩。 |
| 3 | `simulate_panel` 中以逐行字典追加创建 DataFrame | 运行时间随 firm-years 线性累计，并在更大面板或更多重复时扩大。 | 所有 Monte Carlo 条件。 | 本轮不替换：逐行到向量化重写会改变随机数消费顺序和 CSV 浮点序列，需先在独立分支完成逐行哈希回归审计。 |

### 5.2 补丁 A：复用二阶段 FE 设计

**替换文件：** `src/esg-monte-carlo.py`、`src/run-round2-diagnostics.py`、`tests/test-pipeline.py`。新增 `PreparedSecondStage`、`prepare_second_stage()` 与 `fit_second_stage_prepared()`：固定的回归量设计只被投影一次；每个结果变量仍独立进行固定效应残差化。该重构保持 Frisch–Waugh–Lovell 的估计逻辑，并避免把 outcome 投影错误地在不同结果变量间复用。高维固定效应计算的可扩展性动机与文献中的迭代 FE 估计工作一致 [7] [8]。

| 对象 | 修改前 | 修改后 | 不变量 |
|---|---|---|---|
| `basic_second_stage_result()` | 对 firm、two-way、oracle firm、oracle two-way 分别调用完整二阶段拟合。 | 构造一次 `PreparedSecondStage`，对每个 outcome/covariance 复用 `xd`。 | 同一 2,400 行分析样本；结果变量仍独立残差化。 |
| 回归测试 | 仅检查单路径结果有限。 | 比较兼容包装器与 prepared 路径的 $\beta$、SE、p 值（`rtol=atol=1e-12`）。 | 通过。 |

在固定的 300 firms、2,400 二阶段行、12 次单进程运行条件下，含 oracle 的完整诊断路径由 **0.031169 s/run** 降至 **0.028204 s/run**，即 **9.5134%**。首末次统计输出的最大已报告绝对差分别为 $2.22\times10^{-15}$ 与 $8.67\times10^{-17}$。这只是当前宿主上的回归基准，不是硬件无关承诺。

### 5.3 补丁 B：批量受限 wild cluster bootstrap

**替换文件：** `src/esg-monte-carlo.py`、`tests/test-pipeline.py`。`restricted_wild_cluster_bootstrap()` 新增 `batch_size=64`，预先固定受限模型、bread、CR1 修正和 cluster-membership 矩阵；随后按确定性批次生成 Rademacher 权重并以 `einsum` 汇总 score。限制、随机种子、有限样本修正和极端统计量判定均保持不变。快速 wild bootstrap 的此类固定结构复用与 Roodman 等的计算论证一致 [9]。

| 对象 | 修改前 | 修改后 | 不变量 |
|---|---|---|---|
| 内层 scores | 每个 draw 创建并散点累加 cluster score。 | 每批 draw 通过固定成员矩阵进行张量收缩。 | Rademacher 流、受限统计量、CR1 和 p 值定义不变。 |
| 回归测试 | 与遗留逐 draw 实现比较。 | 同时比较 `batch_size=64`、`batch_size=1` 与遗留实现。 | 固定种子、19 draws 下 p 值完全一致。 |

在固定 399 draws 的单一二阶段设计上，该路径由 **0.039747 s** 降至 **0.034912 s**，即 **12.1643%**；固定种子 p 值在前后均为 **0.9275**。批量大小可按内存预算调整；不应将此工程加速错误表述为统计方法改进。

## 6. 后续实验：两组消融与一组鲁棒性检验

以下是**预先登记的扩展设计**，不是已完成的结果。若运行，将把每个种子/重复层输出保留在私有仓库，只把合并表、图、配置和代码公开。

| 试验 | 仅改变的成分 | 保持固定的成分 | 主输出 | 预期图表结构 |
|---|---|---|---|---|
| 消融 A：Big Four 直接方差角色剂量 | `big4_variance_scale ∈ {0, 0.5, 1.0}` | 选择方程、ESG 过程、样本流、种子结构、所有其余 DGP 参数 | $\beta_3$ 均值、firm/two-way 拒绝率、MCSE | **Figure E1**：三组横轴，每组显示估计 $\beta_3$（左轴）和两种拒绝率（右轴或分面）；附 95% MC 区间。 |
| 消融 B：生成结果变量传递 | `log|û|`、winsorized `log|û|`、`|û|`、oracle `log|u^*|` | 相同面板、二阶段暴露与 FE、推断、可得性条件 | 与已知 $\gamma_{INT}$ 的偏离、平均 SE、拒绝率 | **Figure E2**：以 outcome 为行、sample size 为列的 forest plot；虚线为 DGP $\gamma_{INT}$。 |
| 鲁棒性 R：时间簇与多维推断压力网格 | 时间簇 `8, 14, 28`；firm-clustered、two-way 与经独立验证的 multiway bootstrap | 主 DGP 的暴露尺度、样本流和空假设效应 | 空假设尺寸、MCSE、运行耗时 | **Figure E3**：时间簇横轴、拒绝率纵轴、方法颜色分组、每一 DGP 持久性一个分面；5% 水平线。 |

若执行鲁棒性 R，任何 multiway bootstrap 都必须以其准确实现、聚类维度和权重分布单独验证；受限 firm-level bootstrap 不可改名为 multiway 方法。多维推断与序列相关时间效应的近期方法可作为实现审查依据 [10]。

## 7. 公平内部对照必须固定的三项设置

由于不存在外部 SOTA 协议，下列是**内部可比性**而非 “对齐 SOTA” 的强制固定项。

| 固定设置 | 建议值 | 理由 |
|---|---|---|
| DGP 面板与样本流 | 300 firms × 10 DGP years；第一阶段 3,000 行；第二阶段 2,400 lag/lead-valid 行 | 避免方法差异被不相同的终端 lead 排除或首阶段样本缩减混淆。 |
| 随机化与 Monte Carlo 精度 | 两个独立 master seeds；每 seed 每条件至少 1,000 outer repetitions | 主发布将有合并 $R=2,000$，可计算拒绝率 MCSE；扩展条件必须报告 seed 与合并方式。 |
| 推断合约 | $\alpha=0.05$；firm-clustered 主结果；two-way 仅压力诊断；受限 firm wild bootstrap 以至少 399 draws 为比较基线 | 保持本稿已验证定义，避免把不同层级的 bootstrap 或不同阈值混入同一表。 |

## 8. 更权威的未来实证数据路径

这两项推荐面向**未来独立实证项目**，不是本项目数据，也不会被下载、校准或上传到当前公开仓库。

| 候选来源 | 公开性与规模 | 推荐理由 | 必要限制 |
|---|---|---|---|
| U.S. SEC Financial Statement Data Sets / EDGAR | SEC 官方公开数据集覆盖 2009-01 至 2026-06，按季度更新，从 XBRL 申报提取财务报表表内数值，并含 SIC [11] | 一手、可审计、适合透明构造资产、现金流、投资、杠杆、行业和时间变量。 | 不提供商业 ESG 评分或标准化审计师标签；必须做实体解析、点时对齐、概念映射和缺失审计。 |
| LSEG ESG Scores and Data + 许可的财务数据库联结 | 截至 2026-03，LSEG 页面称覆盖 16K+ 公司、240+ 标准化指标与 2K+ 底层数据点 [12] | ESG 构念和跨市场覆盖更系统，可作为受控的评分敏感性设计输入。 | 需要许可；系统复制、再分发或商业使用受条款约束。原始/派生供应商数据不得进入任一公开仓库。 |

## 9. 可复现发布模板

### 9.1 README 最小模板

```markdown
# <项目名称>

## Scope
This repository contains <synthetic/public> materials only. It does not contain <restricted data / credentials / manuscript files>.

## Task and estimand
State the unit of analysis, DGP or data source, model, estimand, primary metric, and non-claims.

## Repository layout
List source, configuration, public example, aggregate outputs, tests, and documentation.

## Environment
python3 -m pip install -r requirements.txt

## Reproduction
1. Run deterministic tests.
2. Run lightweight smoke command.
3. Run full commands, state expected time and output locations.

## Data and code availability
Identify public artifacts and explicitly list excluded restricted/private materials.

## Citation
Provide a stable paper citation or an anonymous-package citation.
```

### 9.2 `requirements.txt` 合并清单

当前仓库已采用锁定版本。合并时应保留数值计算、YAML、图表、DOCX 解析和 HTTP 层，不应新增未被代码调用的包。

```text
numpy==2.5.1
pandas==3.0.5
PyYAML==6.0.2
matplotlib==3.11.1
python-docx==1.2.0
requests==2.32.5
```

### 9.3 `.gitignore` 合并清单

应合并 Python 缓存/虚拟环境、密钥、私有稿件、原始或许可数据、大型可再生中间输出和 IDE 文件规则。最低规则如下；公开包应只显式反选 `data/public/*.csv` 这类经审查资产。

```gitignore
__pycache__/
*.py[cod]
.venv/
.env
.env.*
!.env.example
*.pem
*.key
credentials.json
secrets.*
private/
../private/
*.docx
*.pdf
!docs/*.pdf
data/raw/
data/private/
data/restricted/
!data/public/
!data/public/*.csv
outputs/smoke_test*/
outputs/validation_seed_*/
outputs/**/*.parquet
outputs/**/*.pkl
outputs/**/*.npy
.vscode/
.idea/
.ipynb_checkpoints/
```

### 9.4 从初始化到推送的完整命令序列

```bash
# 新仓库；默认私有，确认公开边界后才改为公开。
git init
git branch -M main
git add README.md requirements.txt .gitignore src/ tests/ config/ data/public/ outputs/ docs/
git diff --cached --check
git commit -m "chore: initialize reproducible synthetic package"
gh repo create <owner>/<repo> --private --source=. --remote=origin --push

# 每次公开发布前：测试、边界扫描、提交与推送。
python3 tests/test-pipeline.py
python3 tests/test-reviewer-revision.py
git grep -nEi '(credential|api[_-]?key|secret|token|BEGIN [A-Z ]*PRIVATE KEY)' -- . ':!docs/repository-boundary.md' || true
find . -type f \( -name '*.docx' -o -name '*.pdf' \) -not -path './docs/*' -print
git add <reviewed-public-files>
git diff --cached --check
git commit -m "<scoped change>"
git push origin main

# 私有归档单独在私有仓库中执行；绝不以通配符跨仓库复制。
cd ../<private-repo>
git add <reviewed-private-files>
git diff --cached --check
git commit -m "<private scoped change>"
git push origin main
```

## 10. 发布前物理核查清单

| 核查域 | 必须检查的物理证据 | 通过标准 |
|---|---|---|
| 数据来源 | 每张表、图、README、稿件段落均能追溯到 `config/`、公开聚合 CSV 或带 URL 的来源台账。 | 无无来源数值；无把供应商覆盖写成 DGP 校准。 |
| 数值 | 重新计算主要拒绝率、MCSE 和表中四舍五入；核对合并 $R$。 | 与来源 CSV 一致；二元 MCSE 用合并重复数而非种子 MCSE 均值。 |
| 代码 | `tests/test-pipeline.py` 与 `tests/test-reviewer-revision.py` 完整通过。 | 退出码为 0；新优化路径有等价性测试。 |
| 图表 | 文件存在、600 dpi、图注与表内数值/推断标签一致、无裁切。 | 打开图像实际检查可读性；没有把 two-way 诊断标成主结论。 |
| 论文 | Title、Abstract、Methods、Results、Limitations、Data/Code Availability、CRediT、COI 与参考文献完整。 | 不添加未运行结果、不称 SOTA、不改变已核验结论。 |
| 开放边界 | 扫描 `.docx`、`.pdf`、种子/重复级输出、原始 SEC、许可 ESG、凭据及评审材料。 | 公开仓库零命中；私有仓库只保留经许可的受控材料。 |
| 远程状态 | 检查公开与私有仓库各自 `main` 的 commit、clean clone 和测试。 | 本地/远程 SHA 一致；clean clone 可通过公开测试。 |

## 参考文献

[1]: https://www.nature.com/articles/s41597-023-02093-3 "Tian et al. (2023), A dataset on corporate sustainability disclosure"
[2]: https://arxiv.org/html/2601.08676v1 "Zhao et al. (2026), Advancing ESG Intelligence"
[3]: https://arxiv.org/html/2502.21112v1 "Birti, Osborne & Maurino (2025), Optimizing LLMs for ESG Activity Detection"
[4]: https://doi.org/10.1016/j.jacceco.2009.09.002 "Biddle, Hilary & Verdi (2009)"
[5]: https://doi.org/10.1162/rest.90.3.414 "Cameron, Gelbach & Miller (2008)"
[6]: https://doi.org/10.2308/TAR-2023-0707 "Xue (2025), ESG disclosure, market forces, and investment"
[7]: https://www.iza.org/publications/dp/3935/a-simple-feasible-alternative-procedure-to-estimate-models-with-high-dimensional-fixed-effects "Guimarães & Portugal (2010)"
[8]: https://scorreia.com/research/hdfe.pdf "Correia (2016), A feasible estimator for linear models with multi-way fixed effects"
[9]: https://doi.org/10.1177/1536867X19830877 "Roodman et al. (2019), Fast and wild"
[10]: https://doi.org/10.1080/07350015.2025.2546454 "Hounyo & Lin (2026), Wild bootstrap inference with multiway clustering"
[11]: https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets "U.S. SEC Financial Statement Data Sets"
[12]: https://www.lseg.com/en/data-analytics/sustainable-finance/sustainability-ratings-and-data "LSEG ESG Scores and Data"
