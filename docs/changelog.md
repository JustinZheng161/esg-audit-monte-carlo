# Revision and Code Change Log

## Scope warning

The supplied materials included an original DOCX manuscript but **no pre-existing source-code repository**. Accordingly, the code below is a new, documented reproduction implementation rather than a patch to unknown prior code. The manuscript changes are based on the supplied paper and the newly executed synthetic experiments.

## Manuscript changes

| Original state | Revised state | Reason |
|---|---|---|
| Abstract presented a parameter-specific Monte Carlo study but did not quantify finite-sample miscalibration across independent seeds. | Abstract reports the synthetic-only boundary, two independent seeds, rejection frequencies with MCSEs, and the revised inference conclusion. | Prevents overstatement and makes the diagnostic contribution explicit. |
| Variance description could be read as contemporaneous ESG/Big Four while the second-stage regressors were lagged. | DGP explicitly indexes variance to lagged ESG and lagged Big Four. | Aligns data generation with estimand timing. |
| Two-way clustering was treated as a preferred standard error despite eight time clusters. | Firm clustering becomes the primary baseline; two-way is a stress diagnostic; firm-level restricted wild bootstrap is calibrated. | Directly responds to few-time-cluster risk. |
| Main results emphasized one simulation draw and one p-value. | Adds 1,000-repetition primary runs, two independent master seeds, MCSEs, sample-size sensitivity, and a cross-seed table. | Separates simulation uncertainty from substantive inference. |
| Big Four served as an implicit audit-quality measure. | Adds explicit construct limitation and future alternative-proxy protocol. | Aligns with recent sustainability-assurance measurement literature. |
| Data availability mentioned a ZIP without an inspectable code pathway. | Adds separate data availability and code availability statements, repository boundary, source registry, environment, and test commands. | Makes reproducibility auditable. |
| References were almost entirely foundational. | Adds recent 2025–2026 literature on ESG disclosure/investment, ESG–investment SLR, sustainability assurance quality, and multiway wild bootstrap. | Updates research positioning and supports revisions. |

## New code modules

| File | Status | Function |
|---|---|---|
| `src/esg-monte-carlo.py` | New | Synthetic DGP, fixed-effect residualization, firm/two-way cluster covariance, primary experiments, ablations, placebos, restricted firm wild bootstrap, figures, and manifests. |
| `src/collect-sec-metadata.py` | New | Optional SEC metadata collection; writes raw JSON privately and a source/hash manifest publicly. |
| `src/compare-runs.py` | New | Aggregates independent seed runs while preserving scenario, firm count, and effect-scale identities. |
| `src/build-revised-manuscript.py` | New/private | Builds the revised DOCX from verified outputs; excluded from public release. |
| `tests/test-pipeline.py` | New | Deterministic checks for panel shape, lags, finite estimates, p-value bounds, and bootstrap output. |

## Critical code correction: timing alignment

The initial implementation was corrected before the canonical run. The original code fragment below used the contemporaneous variables in the variance DGP while the outcome regression used lags.

```diff
- log_sigma = math.log(base_sigma) + beta_esg * e_std[:, t] + beta_inter * e_std[:, t] * big4
+ # Match the lagged ESG and Big Four regressors used in the second stage.
+ lag_index = max(t - 1, 0)
+ log_sigma = (math.log(base_sigma) + beta_esg * e_std[:, lag_index]
+              + beta_inter * e_std[:, lag_index] * big4_previous)
```

The corrected version also carries the prior-period audit proxy across the simulation loop.

```diff
+ big4_previous = initial_big4_draw
  for t, year in enumerate(years):
      ...
+     big4_previous = big4
```

## Critical code correction: independent-run aggregation

The first cross-seed aggregation grouped only by scenario label. Because `Null` and `Full alternative` occur at N=100, 300, and 500, this would incorrectly pool different sample sizes. The aggregation key was corrected before the revised paper was generated.

```diff
- combined.groupby("scenario")
+ combined.groupby(["scenario", "firms", "effect_scale"])
```

## Verification history

| Check | Result |
|---|---|
| Initial smoke test | Failed due to missing `PyYAML`; dependency added. |
| Second smoke test | Found a per-row vector indexing error; corrected. |
| Third smoke test | Found placebo reindexing error after lag filtering; corrected. |
| Timing-alignment smoke test | Confirmed expected negative mean interaction under alternatives. |
| Canonical full run | Completed 9 scenarios; 1,000 primary / 300 sensitivity / 399 wild-bootstrap draws. |
| Independent full run | Completed same configuration with master seed `20260828`. |
| Automated tests | Passed. |
| Manuscript rendering | Checked after DOCX-to-PDF conversion; a cross-page table issue was fixed and rechecked. |

The original data/analysis code was not provided, so no claim is made that these files reproduce an unavailable prior implementation byte-for-byte.


## Performance optimization: cached wild-bootstrap algebra

The pre-optimization bootstrap loop recomputed the OLS bread matrix and firm-group inverse index for every bootstrap draw. The revised implementation caches the coefficient bread, the restricted fitted mean, the firm inverse encoding, the number of clusters, and the CR1 finite-sample correction outside the inner loop. Each draw now recomputes only its bootstrap response, coefficient score, and residual score aggregation.

| Patch | Replaced bottleneck | Validation | Result |
|---|---|---|---|
| Cache invariant linear-algebra and cluster encoding in `restricted_wild_cluster_bootstrap` | Per-draw `pinv(X'X)`, `np.unique(firm)`, and covariance helper setup | Exact p-value equivalence test against the legacy loop for an identical synthetic draw and seed | Passed |
| Add `tests/benchmark-bootstrap.py` | No performance guardrail | 399-draw N=300 microbenchmark on the supplied Linux environment | Legacy: 0.111737 s; cached: 0.057006 s; **1.960×** speed-up; p-value identical (0.650000) |

This patch is motivated by the computational structure of fast wild-bootstrap implementations described by Roodman, MacKinnon, Nielsen, and Webb (2019), who note that wild-bootstrap inference is particularly amenable to computational optimization. Source: https://doi.org/10.1177/1536867X19830877.

A second recommended scale-out patch, not required for the current N≤500 runs, is to replace the generic alternating-projection demeaning function with a sparse, accelerated high-dimensional fixed-effect solver while preserving the Frisch–Waugh–Lovell residualization target. Guimarães and Portugal (2010) describe an iterative approach for high-dimensional fixed effects with low memory requirements; Correia (2016) develops symmetric projections and conjugate-gradient acceleration. Sources: https://www.iza.org/publications/dp/3935/a-simple-feasible-alternative-procedure-to-estimate-models-with-high-dimensional-fixed-effects and https://scorreia.com/research/hdfe.pdf.

## 2026-08-27 — First-round reviewer revision

| Review issue | Before | After | Verification |
|---|---|---|---|
| Main effective N | Text could be read without a full observation flow; review memo cited an unexplained N=2,000. | New Table 3 specifies 3,000 raw/first-stage rows, 2,700 post-lag rows, 2,400 main second-stage rows, and 2,169 only for MAR-like stress. | `tests/test-pipeline.py`; regenerated Tables 5–7. |
| DGP transparency | Several DGP constants appeared only as code literals. | All generating constants are explicit in `config/dgp.yaml`; the manuscript Table 1 is derived from this single source of truth. | Configuration-completeness test; anonymous DOCX visual check. |
| MCSE disclosure | Result tables displayed parenthetical MCSE without an explicit in-text formula. | Section 2.2 and Section 3 define `sqrt[p̂(1−p̂)/R]`; pooled tables use combined rejection counts and total R. | Canonical formula assertion and CSV/table cross-check. |
| Few time clusters | Eight analysis years were described as a stress diagnostic without a time-dimension gradient. | Two independent 500-repetition seeds run 8/18/28 analysis time clusters; Table 8/Figure 2 report pooled size and MCSE. | `outputs/reviewer-diagnostics-pooled/`. |
| Big Four construct | Direct residual-variance interaction and the proxy limitation were not separately tested. | The DGP now accepts `big4_variance_scale`; Table 9/Figure 3 contrast direct-role and selection-only conditions. | Deterministic selection/ESG-stream equivalence test; two independent pooled runs. |
| SEC metadata wording | Manuscript mentioned an unused company metadata snapshot. | Anonymous paper now states that no real-company financial, ESG, audit, regulatory, or commercial records enter analysis. | Data/code availability statements and public-boundary scan. |
| Anonymous CRediT | Narrative statement included `manuscript editing assistance`. | Standard anonymized CRediT role statement only. | Anonymous-text scan and final DOCX review. |

## 2026-08-27 — Round-two reviewer revision

### Corrected implementation

- Corrected the sample flow so the first-stage expected-investment equation is fitted on the full 3,000-row synthetic primary panel, using the documented initial investment state for the first lag. The common second-stage lag/lead protocol remains 2,400 rows.
- Retired prior main and reviewer numerical claims that were generated before this first-stage correction. Reported primary results now reside under `outputs/final-run-round2-*` and the two-seed pooled directory.
- Extended `compare-runs.py` to generate the pooled N=300 grouped-bar Figure 1 with separate firm-clustered and two-way firm–year bars and 95% Monte Carlo intervals.

### New reviewer diagnostics

- Added `run-round2-diagnostics.py` and `aggregate-round2-diagnostics.py`. They preserve replication-level results and pool binary rates from all outer repetitions; coefficient-mean MCSEs use the replication-level sample standard deviation divided by the square root of the pooled repetition count.
- Added a time-structure grid varying 8/28 analysable time clusters, ESG persistence (0.25/0.60/0.95), and ESG-dependent residual-variance scale (0/1) under an interaction null.
- Added an oracle/estimated-residual scale-mapping grid that distinguishes DGP \(\gamma_{INT}\) in log-SD units from second-stage \(\beta_3\) values on log absolute true-deviation or estimated-residual scales.
- Replaced the former “MAR-like” label with adverse selective-availability stress and added a non-calibrated coverage-aligned synthetic sensitivity.
- Added first-stage fixed-effect sensitivity for industry×year, industry+year, and no fixed effects, including oracle outcomes and reference-panel joint-F/partial-\(R^2\) diagnostics.
- Added corrected-sample-flow Big Four mechanism ablation runner and aggregator. Both scenarios retain the Big Four logistic selection equation; the selection-only condition removes only the direct residual-variance role.

### Manuscript and release documentation

- Rebuilt `esg-audit-investment-efficiency-round2-revised-anonymous.docx` from only corrected pooled outputs. The manuscript unifies terminology as “Big Four auditor indicator,” adds scale-mapping and residual-proxy limitations, conditions time-cluster claims on the DGP, and relocates research positioning to Appendix Table B1.
- Added `response-to-reviewers-round2.md`, `round2-result-and-figure-check.md`, and a private final-submission author-replacement checklist.
- Updated the public README, repository boundary whitelist, and deterministic reviewer-revision test contract.
