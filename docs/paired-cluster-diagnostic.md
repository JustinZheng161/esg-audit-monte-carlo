# 配对聚类方法差异诊断

## 目的与范围

本文件记录 **Table-1 合成 DGP** 下 firm-clustered 与 two-way firm-year 5% 拒绝频率的直接配对比较。其目的不是为任何估计器建立通用优劣排序，也不提供关于真实 ESG、审计质量或投资效率关系的实证证据。两个拒绝决定来自**同一**合成面板重复，因此比较必须保留这种联合结构。

## 定义

在情景 \(s\) 的第 \(r\) 个外层重复中，令：

\[
D_{sr}=I(p^{two-way}_{sr}<0.05)-I(p^{firm}_{sr}<0.05).
\]

公开表报告 \(\bar D_s\)、配对 Monte Carlo standard error（MCSE）和常规 95% Monte Carlo interval：

\[
MCSE(\bar D_s)=sd(D_{sr})/\sqrt{R}, \qquad \bar D_s \pm 1.96\,MCSE(\bar D_s).
\]

此 MCSE 利用同一重复内的关联；它不是将两种边际拒绝率的 MCSE 独立相加。该正态近似 MC 区间描述本次合成重复的模拟不确定性，而不是总体参数的置信区间。

## 当前复算结果

两个独立 master seeds（20260827、20260828）各运行 1,000 次，因而每一主情景合并 \(R=2,000\) 次外层重复。聚合结果位于 [`outputs/final-run-round3-paired/tables/table-14-paired-cluster-method-difference.csv`](../outputs/final-run-round3-paired/tables/table-14-paired-cluster-method-difference.csv)，图形位于 [`outputs/final-run-round3-paired/figures/figure-6-paired-cluster-method-difference.png`](../outputs/final-run-round3-paired/figures/figure-6-paired-cluster-method-difference.png)。

| 情景 | Firm rate | Two-way rate | Two-way − firm | 配对 MCSE | 95% MC interval |
|---|---:|---:|---:|---:|---:|
| Null | 0.0640 | 0.1035 | 0.0395 | 0.0055 | [0.0287, 0.0503] |
| Half alternative | 0.1155 | 0.1585 | 0.0430 | 0.0062 | [0.0309, 0.0551] |
| Full alternative | 0.2460 | 0.2870 | 0.0410 | 0.0072 | [0.0270, 0.0550] |

在 primary-null 行，四格联合计数为 both reject=105、firm only=23、two-way only=102、neither=1,770。由此可见，在此 DGP 的这次复算中，two-way 的空假设拒绝频率高于 firm-clustered；这一条件性结果不得泛化为所有时间簇、所有误差相关结构或真实面板的规则。

## 复现命令与发布边界

完整的重复级记录包含每一合成面板的 p 值与拒绝指示，故只能存放于私有归档。公开仓库保留以下可执行脚本、聚合 CSV 与图形：

```bash
# 在公开仓库根目录；每个 seed 运行一次，输出必须指向私有目录。
python3 src/run-paired-primary-diagnostics.py \
  --seed 20260827 --reps 1000 --output /private/seed-20260827
python3 src/run-paired-primary-diagnostics.py \
  --seed 20260828 --reps 1000 --output /private/seed-20260828

# 从两个私有 seed 目录生成可公开的聚合表。
python3 src/aggregate-paired-primary-diagnostics.py \
  --seed-dirs /private/seed-20260827 /private/seed-20260828 \
  --output /public-safe/paired-primary

python3 src/plot-paired-primary-diagnostics.py \
  --table /public-safe/paired-primary/tables/table-14-paired-cluster-method-difference.csv \
  --output /public-safe/paired-primary/figures/figure-6-paired-cluster-method-difference.png
```

运行 `python3 tests/test-paired-primary-diagnostics.py` 可验证配对差异、联合 MCSE、区间和四格计数的计算契约。

## 方法学背景

多维聚类协方差与 bootstrap 推断的适用性取决于具体误差相关结构、有效簇数和设计；本项目的条件性配对报告旨在避免仅凭两个边际 MCSE 宣称差异。[1] [2]

## 参考文献

[1]: https://doi.org/10.1198/jbes.2010.07136 "Cameron, Gelbach, and Miller (2011), Robust inference with multiway clustering"
[2]: https://doi.org/10.3368/jhr.50.2.317 "Cameron and Miller (2015), A practitioner’s guide to cluster-robust inference"
