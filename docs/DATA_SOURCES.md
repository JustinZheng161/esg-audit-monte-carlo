# Data Sources, Variables, and License Boundary

## Current reported analysis

Every observation used in the reported tables and figures is **synthetically generated** from `config/dgp.yaml`. The dataset has no mapping to a legal entity, ticker, CIK, real ESG score, auditor, financial statement, or commercial data provider. It exists solely to diagnose the finite-sample behavior of a fully declared statistical workflow.

| Public asset | Location | Source label | Release status |
|---|---|---|---|
| Synthetic schema example | `data/public/synthetic_example_null.csv` | This project’s deterministic synthetic DGP | Included |
| Pooled main aggregate results | `outputs/final_run_round2_pooled/` | This project’s synthetic Monte Carlo DGP | Included |
| Pooled round-two aggregate diagnostics | `outputs/round2_pooled/`; `outputs/round2_big4_pooled/` | This project’s synthetic Monte Carlo DGP | Included |
| DGP configuration | `config/dgp.yaml` | This project’s synthetic assumptions | Included |

No SEC, ESG-vendor, auditor, or financial-statement dataset is an input to the reported DGP, calibration, table, or figure. The package has no external empirical data dependency.

## Variable boundary

| Construct in the synthetic DGP | Meaning inside this package | What it does **not** mean |
|---|---|---|
| ESG | Bounded, persistent synthetic exposure generated from declared latent components and innovations | A vendor score, a disclosure measure, or a real-company ESG observation |
| Big Four auditor indicator | Binary synthetic status created by a documented logistic assignment equation | A validated measure of financial-reporting audit quality or sustainability-assurance quality |
| Investment residual | Difference between synthetic investment and a fitted synthetic first-stage expectation | Directly observed economic inefficiency in a real firm |
| Availability stress | Deliberately constructed missingness/observation mechanism for sensitivity analysis | An empirical estimate of ESG coverage by any provider |

## Future empirical extension: minimum protocol

A future empirical study must pre-specify the population, period, exchange, fiscal-year convention, industry exclusions, variable formulas, point-in-time availability, and all transformations before estimation. It should not treat ESG scores from different providers as interchangeable. Recent reviews document heterogeneous measurement and research designs in ESG–investment-efficiency and sustainability-assurance research [1] [2].

| Construct | Candidate source class | Minimum documentation | Public repository rule |
|---|---|---|---|
| Financial statements | SEC EDGAR or a licensed market database | XBRL tag; fiscal period; units; filed date; selection rule | Share code and a permitted metadata record, not raw cache by default |
| ESG exposure | Licensed provider or reproducible public-disclosure index | Provider version; score scale; coverage; point-in-time availability; missing-value rule | Never redistribute raw scores unless the license expressly permits it |
| Financial audit measure | Auditor identity plus documented proxy | Proxy rationale; auditor-to-office mapping if applicable; source | Share codebook/mapping logic, not licensed records |
| Sustainability assurance measure | Assurance report or permitted coded attributes | Standard; assurance level; provider type; date; coding protocol | Share templates and permitted links only |
| Investment-residual proxy | Firm financial statements | First-stage model; cells; trimming; residual handling | Share reproducible implementation and assumptions |

## Commercial data restriction

Provider coverage pages may be cited for context, but they do not license data redistribution or calibrate this package. LSEG states that systematic reproduction or redistribution of its data requires a license [3]. The same conservative rule applies to CSMAR, Wind, Bloomberg, Refinitiv, MSCI, Sustainalytics, Audit Analytics, Compustat, and similar sources. A public repository may contain source code, dictionaries, manifests, and empty templates only where permitted; it must not contain protected records.

## References

[1] Owino, F. J. O., Mathuva, D. M., & Mangena, M. (2026). Integrating environmental, social and governance disclosures factors in investment efficiency: A systematic literature review. *Journal of Applied Accounting Research*, 27(3), 574–593. [https://doi.org/10.1108/JAAR-03-2025-0099](https://doi.org/10.1108/JAAR-03-2025-0099)

[2] Xu, H., Hay, D., & Harrison, J. (2026). Sustainability assurance quality: Indicators and consequences. *Accounting & Finance*, 66(1), 849–886. [https://doi.org/10.1111/acfi.70196](https://doi.org/10.1111/acfi.70196)

[3] LSEG. (2026). *ESG Scores and Data*. [https://www.lseg.com/en/data-analytics/sustainable-finance/sustainability-ratings-and-data](https://www.lseg.com/en/data-analytics/sustainable-finance/sustainability-ratings-and-data)
