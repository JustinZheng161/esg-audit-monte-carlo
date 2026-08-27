# 数据与方法来源账本

**检索基准日：** 2026-08-27（GMT+8）
**适用范围：** ESG、审计质量、投资效率与蒙特卡洛统计诊断研究。
**使用原则：** 以下条目均已访问原始提供方或期刊页面；搜索结果摘要不作为唯一依据。原始商业数据不复制到公开仓库。

## A. 数据来源与许可边界

| ID | 来源 | 可获得变量/规模 | 用途 | 访问与发布边界 | 一手来源 |
|---|---|---|---|---|---|
| D1 | U.S. SEC EDGAR `data.sec.gov` | 公司申报史和 10-K/10-Q/20-F 等 XBRL 财务事实；无须 API key，JSON 结构实时更新 | 为未来美国样本校准财务变量（资产、现金、CFO、收入、固定资产、负债等）提供公共路径 | 原始 API 响应可按 SEC 条款抓取；公开仓库仅存下载脚本、字段映射、合成示例和聚合校验值 | [SEC EDGAR API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) |
| D2 | LSEG ESG Scores and Data | 2026-03 数据页称覆盖 16,000+ 公司、240+ 标准化指标和 2,000+ 底层数据点 | 为未来 ESG 评分选择与点时校准提供专业数据源选择 | 需要客户访问；网页条款明确系统性复制、再分发需要许可。因此不抓取、不上传原始得分；公开仓库仅放数据字典与获取说明 | [LSEG ESG Scores and Data](https://www.lseg.com/en/data-analytics/sustainable-finance/sustainability-ratings-and-data) |
| D3 | CSMAR/Wind/Bloomberg ESG | 中国 A 股财务、治理、审计与 ESG 变量，原稿拟议实证路径 | 未来中国样本的受限校准来源 | 许可数据不被本任务下载；私人仓库只保留未含原始数据的变量映射与审计记录，原文件不得同步至 GitHub | 原稿第 5 节/原稿参考研究 [Wang et al., 2022](https://doi.org/10.3389/fpsyg.2022.948674) |
| D4 | 合成 DGP 数据 | 300 家合成企业 × 2015–2024 年；由公开脚本确定性生成 | 当前论文唯一实际实验数据 | 可公开：仅合成样例、配置和聚合表。完整运行产物私密保存，以减少仓库体积并保留审计追溯 | 本项目 `config/dgp.yaml` 与 `src/`（待生成） |

## B. 关键方法与研究定位来源

| ID | 文献/机构 | 经核验的可用结论 | 在本项目中的使用方式 | 链接 |
|---|---|---|---|---|
| M1 | Biddle, Hilary & Verdi (2009) | 财务报告质量与投资效率的实证测量传统；残差式投资偏离是相关研究的重要基线 | 支撑残差式投资偏离构造的文献背景，而非证明本模拟设计的因果有效性 | [DOI](https://doi.org/10.1016/j.jacceco.2009.09.002) |
| M2 | Richardson (2006) | 过度投资与自由现金流的研究框架 | 支撑正常投资方程的企业投资文献定位 | [DOI](https://doi.org/10.1007/s11142-006-9012-3) |
| M3 | Cameron, Gelbach & Miller (2008) | 少簇环境下常规渐近检验可能过度拒绝；提出 cluster bootstrap-t 改进 | 用于设计 bootstrap 与尺寸校准对照，而不是预设某一自助法必然有效 | [DOI](https://doi.org/10.1162/rest.90.3.414) |
| M4 | Cameron & Miller (2015) | 聚类稳健推断涉及少簇、多维聚类、固定效应等实际复杂情形 | 支撑将 firm clustering 设为基线、将 eight-year two-way clustering 作为待校准对象 | [论文 PDF](https://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2014_July_09.pdf) |
| M5 | Hounyo & Lin (2026) | 给出允许串行相关时间效应的多维 wild bootstrap 推断，并报告模拟证据 | 用于新增多维 wild bootstrap 稳健性试验，取代“pairs bootstrap 自动纠偏”的不充分表述 | [DOI](https://doi.org/10.1080/07350015.2025.2546454) |
| M6 | Xue (2025), *The Accounting Review* | 理论分析 ESG 披露精度、市场力量与投资；已正式刊于 TAR 100(5), 439–467 | 作为最新高水平研究定位，不能与本蒙特卡洛设计做性能/SOTA排序 | [DOI](https://doi.org/10.2308/TAR-2023-0707) |
| M7 | Owino, Mathuva & Mangena (2026), *JAAR* | 系统综述 2000–2023 年 92 篇经同行评审文献，并指出跨研究设计差异会影响 ESG—投资效率证据 | 支撑本文将“设计诊断”与“实证结论”严格分离的动机 | [DOI](https://doi.org/10.1108/JAAR-03-2025-0099) |
| M8 | Xu, Hay & Harrison (2026), *Accounting & Finance* | 系统综述 2004–2024 文献，将可持续鉴证质量指标组织为投入、过程、输出、背景与后果 | 支撑用 Big Four 之外的审计/鉴证质量替代指标进行稳健性设计 | [DOI](https://doi.org/10.1111/acfi.70196) |
| M9 | Wang, Yu & Li (2022), *Frontiers in Psychology* | 使用 2011–2020 中国 A 股样本、Bloomberg ESG，讨论 ESG、审计质量与投资效率的关联 | 仅作为原稿主题的实证先行研究；不复制其数据或将其关系宣称为本模拟的结果 | [DOI](https://doi.org/10.3389/fpsyg.2022.948674) |
| M10 | Zheng et al. (2025), *European Journal of Finance* | 使用中国和美国银行面板，检验 ESG、投资效率与环境不确定性；正式发表信息可核验 | 作为近期跨市场实证背景；不用于校准本项目 DGP 的参数 | [DOI](https://doi.org/10.1080/1351847X.2025.2585972) |

## C. 文献更新建议

原稿已具有多篇经典投资效率与聚类推断文献，但缺少近两年的领域地图。建议新增 M5–M10，并在参考文献中分别注明其角色：**方法推断（M5）、主题综述（M7–M8）、高水平理论定位（M6）、近期实证背景（M9–M10）**。不将它们称为“模型 SOTA”，因为本文是统计诊断而非机器学习基准任务。

## D. 来源核验限制

LSEG 和部分期刊全文受访问/许可限制。本账本只引用其页面可核验的出版信息、摘要或数据产品说明；不转述无法访问的全文结果，不复制受限数据库内容。
