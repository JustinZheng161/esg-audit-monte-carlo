# Public data and artifact catalog

This catalog is the public repository’s release index. Every reported observation is synthetic. The repository contains the complete set of **safe-to-release** data and artifacts required to inspect the documented aggregate findings and to regenerate the public figure package; it does not contain source-like records, real-company observations, or licensed data.

## Public release layout

| Directory or file | Tracked public content | Release purpose |
|---|---|---|
| `config/dgp.yaml` | One fully documented synthetic DGP configuration. | Single source of truth for the public simulation settings. |
| `data/public/synthetic-example-null.csv` | One small synthetic schema example. | Demonstrates column structure only; it is not a reported replication-level result. |
| `outputs/final-run-round2-pooled/tables/` | Three pooled primary aggregate tables. | Documents the main corrected-sample-flow operating characteristics and representative draws. |
| `outputs/round2-pooled/tables/` | Five pooled time, scale, availability, and first-stage-fixed-effect aggregate tables. | Documents the reported sensitivity diagnostics. |
| `outputs/round2-big4-pooled/tables/` | One pooled Big Four mechanism-ablation table. | Documents the reported ablation diagnostic. |
| `outputs/final-run-round3-paired/tables/` | One paired clustering-method aggregate table. | Documents the paired primary-difference diagnostic. |
| `outputs/**/figures/` | Aggregate-result figure PNGs. | Provides reproducible visual companions to released aggregate tables. |
| `outputs/publication-figures/` | Five optimized-name Nature-style figure sets: PDF, editable SVG, 600-dpi PNG, 600-dpi LZW TIFF, and `figure-source-manifest.json`. | Provides publication-ready artwork and a SHA-256 provenance chain from public aggregate tables. |
| `src/` and `tests/` | Public Python implementation and deterministic tests, including figure export validation. | Reproduces safe public artifacts and verifies their integrity. |
| `docs/` | Protocol, source notes, boundary rules, naming convention, figure specification, and this catalog. | Makes scope, interpretation, and release conditions inspectable. |

The repository currently tracks **11 CSV aggregate/example datasets**, **3 JSON/manifest records**, the complete 20-file Figure 1–5 publication-artwork set plus its manifest, public source code, and deterministic tests. These are all directly versioned in GitHub; no generated public data or figure asset remains only in the local workspace.

## Reproduction entry points

```bash
python3 -m pip install -r requirements.txt
python3 tests/test-pipeline.py
python3 tests/test-reviewer-revision.py
python3 tests/test-paired-primary-diagnostics.py
python3 src/export-publication-figures.py
python3 tests/test-publication-figure-exports.py
```

For full run commands and computational settings, see [`README.md`](../README.md), [`benchmark-and-experiment-protocol.md`](benchmark-and-experiment-protocol.md), and [`publication-figure-specification.md`](publication-figure-specification.md).

## Controlled exclusions

The private companion repository, not this public catalog, retains complete synthetic seed-level and replication-level outputs, editable anonymous manuscript files, rendered manuscript PDFs, detailed review records, and controlled audit evidence. The public repository never releases real-company financial, ESG, audit, regulatory, raw SEC, restricted-vendor, credential, or private-review material. The enforceable release boundary and clean-clone rules are specified in [`repository-boundary.md`](repository-boundary.md).

> **Interpretation boundary:** Aggregate synthetic results describe the stated DGP only. Public availability does not turn these simulated diagnostics into empirical evidence about ESG, audit quality, investment efficiency, companies, providers, or an external population.
