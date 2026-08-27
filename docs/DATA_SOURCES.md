# Data Sources, Variables, and License Boundary

## Current study data

The reported experiments use **only synthetic observations** generated from `config/dgp.yaml`. The synthetic data set has no mapping to a legal entity, ticker, CIK, real ESG score, auditor, or financial statement. Its purpose is to evaluate the operating characteristics of the declared statistical pipeline.

| Asset | Location | Status | Source label | Public-release treatment |
|---|---|---|---|---|
| Canonical synthetic sample | `data/public/synthetic_example_null.csv` | Included | This project’s deterministic DGP | Public under MIT license |
| Aggregate Monte Carlo tables | `outputs/tables/` | Included | This project’s deterministic DGP | Public under MIT license |
| Distribution and power figures | `outputs/figures/` | Included | This project’s deterministic DGP | Public under MIT license |
| SEC metadata manifest | `data/public/sec_metadata_manifest.csv` | Included | U.S. SEC EDGAR Company Facts API | Public metadata only |
| SEC raw company-facts JSON snapshots | `private/data/raw/sec/` | Excluded | U.S. SEC EDGAR Company Facts API | Private only; regenerate from manifest URLs |

## Actual source collection performed

A five-company SEC metadata snapshot was collected on **2026-08-27 UTC** for Apple, Microsoft, Amazon, JPMorgan Chase, and ExxonMobil. The manifest identifies the CIK, original API URL, UTC collection time, SHA-256 of each private raw response, and the source label. The SEC states that its EDGAR APIs provide company submissions history and extracted XBRL financial statement data in JSON and do not require authentication or API keys [1].

The collection is for **future financial-variable calibration only**. It was not merged into, estimated in, or used to parameterize the synthetic DGP. In particular, it does not identify an ESG measure or a validated audit-quality measure.

## Future empirical extension: required data protocol

A future empirical study must declare the population, period, exchange, fiscal-year convention, industry exclusions, variable formulas, and all transformations before estimation. It should not claim that an ESG vendor score is interchangeable with another provider’s score. Recent systematic reviews note measurement heterogeneity in both ESG–investment-efficiency research and sustainability-assurance quality [2] [3].

| Construct | Candidate source class | Minimum documentation | Public repository rule |
|---|---|---|---|
| Financial statements | SEC EDGAR (US) or licensed market database | XBRL tag, period, units, filed date vs. fiscal period, selection rule | Store extraction code and manifest only; do not publish bulky raw cache by default |
| ESG exposure | Licensed provider or reproducible public-disclosure index | Provider version, score scale, coverage, point-in-time availability, missing-value policy | Never redistribute raw scores unless license explicitly permits |
| Financial audit quality | Auditor identity plus documented proxy | Proxy rationale; auditor-to-office mapping if applicable; disclosure source | Share codebook/mapping logic, not licensed records |
| Sustainability assurance quality | Assurance report/coded provider attributes | Assurance standard, level, provider type, date and coding protocol | Share coding template and permitted source links |
| Investment inefficiency | Firm financial statements | First-stage equation, industry/time cells, trimming/winsorization, treatment of residual | Share reproducible implementation and all assumptions |

## Commercial ESG data restriction

LSEG reports broad ESG coverage and standardized sustainability metrics but states that systematic reproduction or redistribution of its data requires a license [4]. The same conservative rule applies to CSMAR, Wind, Bloomberg, Refinitiv, MSCI, Sustainalytics, Audit Analytics, Compustat, and any data provider that does not grant public redistribution rights. A repository can contain download adapters, variable dictionaries, extraction logs, and empty templates; it must not contain the protected records.

## References

[1] U.S. Securities and Exchange Commission. (2025). *EDGAR application programming interfaces*. [https://www.sec.gov/search-filings/edgar-application-programming-interfaces](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)

[2] Owino, F. J. O., Mathuva, D. M., & Mangena, M. (2026). Integrating environmental, social and governance disclosures factors in investment efficiency: A systematic literature review. *Journal of Applied Accounting Research*, 27(3), 574–593. [https://doi.org/10.1108/JAAR-03-2025-0099](https://doi.org/10.1108/JAAR-03-2025-0099)

[3] Xu, H., Hay, D., & Harrison, J. (2026). Sustainability assurance quality: Indicators and consequences. *Accounting & Finance*, 66(1), 849–886. [https://doi.org/10.1111/acfi.70196](https://doi.org/10.1111/acfi.70196)

[4] LSEG. (2026). *ESG Scores and Data*. [https://www.lseg.com/en/data-analytics/sustainable-finance/sustainability-ratings-and-data](https://www.lseg.com/en/data-analytics/sustainable-finance/sustainability-ratings-and-data)
