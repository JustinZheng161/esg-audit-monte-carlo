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
| `src/esg_monte_carlo.py` | New | Synthetic DGP, fixed-effect residualization, firm/two-way cluster covariance, primary experiments, ablations, placebos, restricted firm wild bootstrap, figures, and manifests. |
| `src/collect_sec_metadata.py` | New | Optional SEC metadata collection; writes raw JSON privately and a source/hash manifest publicly. |
| `src/compare_runs.py` | New | Aggregates independent seed runs while preserving scenario, firm count, and effect-scale identities. |
| `src/build_revised_manuscript.py` | New/private | Builds the revised DOCX from verified outputs; excluded from public release. |
| `tests/test_pipeline.py` | New | Deterministic checks for panel shape, lags, finite estimates, p-value bounds, and bootstrap output. |

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
| Add `tests/benchmark_bootstrap.py` | No performance guardrail | 399-draw N=300 microbenchmark on the supplied Linux environment | Legacy: 0.111737 s; cached: 0.057006 s; **1.960×** speed-up; p-value identical (0.650000) |

This patch is motivated by the computational structure of fast wild-bootstrap implementations described by Roodman, MacKinnon, Nielsen, and Webb (2019), who note that wild-bootstrap inference is particularly amenable to computational optimization. Source: https://doi.org/10.1177/1536867X19830877.

A second recommended scale-out patch, not required for the current N≤500 runs, is to replace the generic alternating-projection demeaning function with a sparse, accelerated high-dimensional fixed-effect solver while preserving the Frisch–Waugh–Lovell residualization target. Guimarães and Portugal (2010) describe an iterative approach for high-dimensional fixed effects with low memory requirements; Correia (2016) develops symmetric projections and conjugate-gradient acceleration. Sources: https://www.iza.org/publications/dp/3935/a-simple-feasible-alternative-procedure-to-estimate-models-with-high-dimensional-fixed-effects and https://scorreia.com/research/hdfe.pdf.
