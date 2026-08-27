# ESG, Audit Quality, and Investment Efficiency — Monte Carlo Diagnostic

> **Scope statement.** This repository implements a **synthetic-data Monte Carlo diagnostic**. It does not contain an empirical ESG panel, does not estimate the effect of ESG or audit quality for any real firm, and must not be cited as evidence of a real-world causal relationship.

## Purpose

This package evaluates the operating characteristics of a two-stage residual-based design. The first stage estimates expected investment and defines investment inefficiency as the absolute residual. The second stage regresses log inefficiency on lagged ESG, lagged Big Four status, and their interaction, including firm and industry-by-year fixed effects. The package tests how the design behaves under a documented null and alternative DGP, rather than treating one regression table as conclusive.

The implementation reflects two methodological cautions. First, cluster-robust procedures depend on an adequate number of clusters, and few-cluster settings warrant dedicated calibration [1] [2]. Second, recent multiway-bootstrap work underscores that serially correlated time effects cannot be addressed by simply assuming every two-way estimator is well behaved [3].

## Key findings from the canonical run

The canonical outputs use master seed `20260827`, 1,000 primary repetitions, 300 sensitivity repetitions, and 399 restricted Rademacher wild-bootstrap draws where indicated. A separate full run with master seed `20260828` serves as an independent reproducibility check. The review-extension outputs additionally pool two independent 500-repetition seeds for an 8/18/28-time-cluster gradient and a Big Four selection-versus-direct-variance mechanism ablation.

| Design | Metric | Canonical result | Independent-seed pooled check | Interpretation |
|---|---:|---:|---:|---|
| N=300 null | Firm-clustered 5% rejection rate | 0.072 (MCSE 0.008) | 0.065 (MCSE 0.006; 2,000 repetitions) | Oversized relative to 0.05. |
| N=300 null | Two-way firm–year 5% rejection rate | 0.127 (MCSE 0.011) | 0.111 (MCSE 0.007; 2,000 repetitions) | Substantially oversized with eight analysis years. |
| N=300 null | Restricted firm wild-bootstrap 5% rejection rate | 0.067 (MCSE 0.014) | 0.055 (MCSE 0.009; 600 outer repetitions) | Closer to nominal, but still a calibrated diagnostic rather than a guarantee. |
| N=300 full alternative | Firm-clustered 5% rejection rate | 0.241 (MCSE 0.014) | 0.234 (MCSE 0.009; 2,000 repetitions) | Modest power. |
| N=500 full alternative | Firm-clustered 5% rejection rate | 0.407 (MCSE 0.028) | 0.412 (MCSE 0.020; 600 repetitions) | Larger cross-section raises power. |
| 8/18/28 time clusters, null DGP | Two-way 5% rejection rate | — | 0.086 / 0.076 / 0.070 (MCSE 0.009 / 0.008 / 0.008; 1,000 repetitions each) | Longer time dimension improves but does not fully calibrate two-way inference in this DGP. |
| Big Four selection-only ablation | Firm-clustered interaction rejection | — | 0.056 (MCSE 0.007; 1,000 repetitions) | Preserving selection while removing the direct variance role yields near-null firm-clustered rejection. |

## Repository layout

```text
.
├── config/
│   └── dgp.yaml                       # Declared synthetic DGP and run parameters
├── data/
│   └── public/
│       ├── synthetic_example_null.csv  # Small synthetic example; no real firms
│       └── sec_metadata_manifest.csv   # URL/hash manifest, not raw SEC data
├── docs/
│   ├── DATA_SOURCES.md                 # Source and license guide
│   ├── EXPERIMENT_REPORT.md            # Results and interpretation
│   └── REPOSITORY_BOUNDARY.md          # Public/private release rules
├── outputs/
│   ├── figures/                        # Canonical publication-ready PNG figures
│   ├── tables/                         # Canonical aggregate CSV result tables
│   └── reviewer_diagnostics_pooled/    # Pooled Tables 8–9 and Figures 2–3
├── src/
│   ├── esg_monte_carlo.py              # DGP, estimation, diagnostics, and figures
│   ├── run_reviewer_diagnostics.py     # Time-cluster and Big Four mechanism extensions
│   ├── aggregate_reviewer_diagnostics.py # Correct independent-seed pooling
│   ├── plot_pooled_reviewer_diagnostics.py # Pooled Figures 2–3
│   ├── collect_sec_metadata.py         # Optional metadata tool; not used in reported analysis
│   ├── compare_runs.py                 # Canonical independent-seed aggregation
│   └── build_revised_manuscript.py     # Private manuscript builder; excluded from public release
├── tests/
│   ├── test_pipeline.py                # Deterministic pipeline and observation-flow checks
│   └── benchmark_bootstrap.py          # Cached vs. legacy bootstrap equivalence benchmark
├── requirements.txt
├── .gitignore
└── LICENSE
```

## Reproduce the canonical experiment

Create an isolated environment, install the pinned dependencies, then run the test before running the full experiment.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python tests/test_pipeline.py
python src/esg_monte_carlo.py \
  --reps 1000 --sensitivity-reps 300 --bootstrap-reps 399 \
  --output outputs/final_run_calibrated
python src/esg_monte_carlo.py \
  --seed 20260828 --reps 1000 --sensitivity-reps 300 --bootstrap-reps 399 \
  --output outputs/validation_seed_20260828
python src/compare_runs.py \
  outputs/final_run_calibrated/tables/table_2_monte_carlo_operating_characteristics.csv \
  outputs/validation_seed_20260828/tables/table_2_monte_carlo_operating_characteristics.csv \
  outputs/final_run_calibrated/tables/table_4_independent_seed_crosscheck.csv

# Reviewer-requested time-cluster and Big Four mechanism extensions
python src/run_reviewer_diagnostics.py --reps 500 --year-grid 10 20 30 \
  --seed 20260827 --output outputs/reviewer_diagnostics_seed_20260827
python src/run_reviewer_diagnostics.py --reps 500 --year-grid 10 20 30 \
  --seed 20260828 --output outputs/reviewer_diagnostics_seed_20260828
python src/aggregate_reviewer_diagnostics.py \
  outputs/reviewer_diagnostics_seed_20260827 \
  outputs/reviewer_diagnostics_seed_20260828 \
  --output outputs/reviewer_diagnostics_pooled
python src/plot_pooled_reviewer_diagnostics.py \
  --input outputs/reviewer_diagnostics_pooled \
  --output outputs/reviewer_diagnostics_pooled/figures
```

Expected execution time in the supplied Linux environment is about four minutes per complete seed run. Every invocation writes `manifest.json` containing the configuration hash, package versions, seeds, and run counts.

## Data governance and source policy

The current study has **no external empirical data dependency**. All analysis observations are generated locally from `config/dgp.yaml`, which is the single source of truth for every disclosed DGP parameter. The optional `src/collect_sec_metadata.py` utility is not invoked by any reported experiment, calibration, table, or figure. It is retained only as a separately documented future-extension utility; raw responses are deliberately excluded from the public repository. The SEC describes the underlying interface as providing filing history and XBRL facts in JSON without an API key [4].

ESG vendor data must not be silently substituted or redistributed. For example, LSEG reports broad ESG coverage but explicitly restricts systematic reproduction and redistribution without a license [5]. Raw CSMAR, Wind, Bloomberg, Refinitiv, MSCI, Sustainalytics, and similar commercial data belong in a controlled private environment. The repository documents the data dictionary and acquisition protocol but does not ship the licensed records.

| Asset | Public repository | Private repository / local controlled storage |
|---|---:|---:|
| Source code and configuration | Yes | Mirror allowed |
| Synthetic example data and aggregated result tables | Yes | Mirror allowed |
| Full simulation work files and internal audit logs | No | Yes |
| Original and revised manuscript DOCX | No | Yes |
| SEC raw API responses | No | Yes |
| Licensed ESG/audit/financial data and `.env` files | Never | Local controlled storage only |

## Methodological interpretation

The results are **operating characteristics**, not an SOTA leaderboard. Relevant ESG, audit-quality, and investment-efficiency studies use distinct populations and estimands, so it would be misleading to rank them by a common ‘best score.’ The accompanying paper instead includes a research-positioning table. The residual-based investment approach is connected to prior investment-efficiency research [6] [7], while current reviews document substantial heterogeneity in ESG–investment-efficiency and sustainability-assurance measurement practices [8] [9].

## Citation

If this code is used, cite the accompanying paper after the author finalizes and archives the version of record. Until then, cite the repository commit hash and state that it contains synthetic-data simulation code only.

## License

The code and synthetic assets are released under the MIT License. Third-party source data and the manuscript are excluded from this license.

## References

[1] Cameron, A. C., Gelbach, J. B., & Miller, D. L. (2008). Bootstrap-based improvements for inference with clustered errors. *Review of Economics and Statistics*, 90(3), 414–427. [https://doi.org/10.1162/rest.90.3.414](https://doi.org/10.1162/rest.90.3.414)

[2] Cameron, A. C., & Miller, D. L. (2015). A practitioner’s guide to cluster-robust inference. *Journal of Human Resources*, 50(2), 317–372. [https://doi.org/10.3368/jhr.50.2.317](https://doi.org/10.3368/jhr.50.2.317)

[3] Hounyo, U., & Lin, J. (2026). Wild bootstrap inference with multiway clustering and serially correlated time effects. *Journal of Business & Economic Statistics*, 44(2), 601–612. [https://doi.org/10.1080/07350015.2025.2546454](https://doi.org/10.1080/07350015.2025.2546454)

[4] U.S. Securities and Exchange Commission. (2025). *EDGAR application programming interfaces*. [https://www.sec.gov/search-filings/edgar-application-programming-interfaces](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)

[5] LSEG. (2026). *ESG Scores and Data*. [https://www.lseg.com/en/data-analytics/sustainable-finance/sustainability-ratings-and-data](https://www.lseg.com/en/data-analytics/sustainable-finance/sustainability-ratings-and-data)

[6] Biddle, G. C., Hilary, G., & Verdi, R. S. (2009). How does financial reporting quality relate to investment efficiency? *Journal of Accounting and Economics*, 48(2–3), 112–131. [https://doi.org/10.1016/j.jacceco.2009.09.002](https://doi.org/10.1016/j.jacceco.2009.09.002)

[7] Richardson, S. (2006). Over-investment of free cash flow. *Review of Accounting Studies*, 11, 159–189. [https://doi.org/10.1007/s11142-006-9012-3](https://doi.org/10.1007/s11142-006-9012-3)

[8] Owino, F. J. O., Mathuva, D. M., & Mangena, M. (2026). Integrating environmental, social and governance disclosures factors in investment efficiency: A systematic literature review. *Journal of Applied Accounting Research*, 27(3), 574–593. [https://doi.org/10.1108/JAAR-03-2025-0099](https://doi.org/10.1108/JAAR-03-2025-0099)

[9] Xu, H., Hay, D., & Harrison, J. (2026). Sustainability assurance quality: Indicators and consequences. *Accounting & Finance*, 66(1), 849–886. [https://doi.org/10.1111/acfi.70196](https://doi.org/10.1111/acfi.70196)
