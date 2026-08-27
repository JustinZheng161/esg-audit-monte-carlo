# Public/Private Repository Boundary and Sync Procedure

## Repository map

| Repository | Visibility | Purpose | Included assets | Explicit exclusions |
|---|---|---|---|---|
| `esg-audit-monte-carlo` | Public | Reproduce the documented **synthetic** statistical diagnostics | DGP configuration; runtime code; deterministic tests; a small synthetic example; aggregate pooled tables and figures; source and boundary documentation | Manuscript DOCX/PDF; manuscript generator; full seed-level/repetition-level output; raw SEC files; restricted/vendor data; credentials |
| `esg-audit-monte-carlo-private` | Private | Author-controlled research record and delivery archive | Public release plus anonymous manuscript, full synthetic outputs, review materials, rendering checks, and permitted internal audit artifacts | API keys, plaintext credentials, and unauthorized third-party data redistribution |

> **Release principle.** “Data synchronization” does not mean publishing all local files. The public repository contains only the minimum synthetic inputs and aggregate evidence needed to reproduce the reported diagnostic claims. The private archive is also not a license override: raw or licensed third-party data may be retained only where storage is permitted.

## Public whitelist for the round-two release

| Whitelist class | Public path(s) | Rationale |
|---|---|---|
| Core simulation and pooling code | `src/esg-monte-carlo.py`; `src/compare-runs.py`; `src/run-round2-diagnostics.py`; `src/aggregate-round2-diagnostics.py`; `src/run-round2-big4-mechanism.py`; `src/aggregate-round2-big4-mechanism.py`; `src/export-publication-figures.py` | Regenerates corrected-sample-flow diagnostics and publication-grade figures from checked aggregate tables |
| Configuration | `config/dgp.yaml` | Provides the sole executable description of synthetic assumptions |
| Tests | `tests/test-pipeline.py`; `tests/test-reviewer-revision.py`; `tests/test-publication-figure-exports.py` | Checks synthetic sample flow, pooling rules, aggregate artifact contract, and public source-to-figure reconstruction |
| Synthetic example only | `data/public/synthetic-example-null.csv` | Demonstrates schema without real firms |
| Pooled main evidence | `outputs/final-run-round2-pooled/tables/*.csv`; `outputs/final-run-round2-pooled/figures/figure-1-primary-operating-characteristics-pooled.png` | Corrected primary results and dual-inference visual |
| Pooled second-round evidence | `outputs/round2-pooled/tables/*.csv`; `outputs/round2-pooled/figures/*.png`; `outputs/round2-pooled/manifest.json` | Time structure, scale mapping, availability, and first-stage FE diagnostics |
| Pooled Big Four mechanism evidence | `outputs/round2-big4-pooled/tables/*.csv`; `outputs/round2-big4-pooled/figures/*.png`; `outputs/round2-big4-pooled/manifest.json` | Corrected-sample-flow selection-only ablation |
| Publication figure package | `outputs/publication-figures/*.pdf`; `outputs/publication-figures/*.svg`; `outputs/publication-figures/*.png`; `outputs/publication-figures/*.tiff`; `outputs/publication-figures/figure-source-manifest.json` | Editable vector PDF/SVG, 600-dpi raster versions, and source-table SHA-256 provenance for Figures 1–5 generated only from public aggregate tables |
| Documentation | `README.md`; `docs/*.md`; `requirements.txt`; `LICENSE`; `.gitignore` | Reproduction, provenance, and governance documentation |

The private manuscript builder (`src/build-revised-manuscript.py`) is intentionally excluded from the public release because it embeds anonymous manuscript text and writes a private DOCX. It contains no reported real-company data but is not necessary to reproduce published numerical outputs.

## Prohibited public files and patterns

```text
*.docx, manuscript/*.pdf, .env*, *token*, *secret*, *credential*, private/, review-round2/,
outputs/final-run-round2-seed-*/, outputs/round2-seed-*/, outputs/round2-big4-seed-*/,
outputs/*/replication-level/, data/raw/, data/restricted/, CSMAR/, Wind/, Bloomberg/,
Refinitiv/, MSCI/, Sustainalytics/, AuditAnalytics/, Compustat/
```

Names alone do not establish sensitivity. Nevertheless, every matching candidate is a release blocker until manually resolved. No raw SEC Company Facts snapshot is cited, analyzed, or released in this project.

## Sync procedure

1. Run the deterministic tests and generate all final outputs in the protected working area.
2. Validate manifests, table schemas, source wording, and figure readability. The manuscript DOCX/PDF check remains private.
3. Populate a clean public checkout only with the whitelist paths above.
4. Run boundary and credential scans on the public checkout. The scans must return no prohibited artifacts and no secrets.
5. Commit and push public and private repositories independently.
6. Clean-clone the public remote into a directory that is not adjacent to any private archive, then rerun public tests and a lightweight synthetic smoke run.

## Reference sync command

```bash
# Run from the public checkout. Replace WORK with the protected working directory.
WORK=/path/to/esg-audit/reproducibility
rsync -a --delete \
  --include='README.md' --include='LICENSE' --include='requirements.txt' --include='.gitignore' \
  --include='config/***' --include='src/esg-monte-carlo.py' --include='src/compare-runs.py' \
  --include='src/run-round2-diagnostics.py' --include='src/aggregate-round2-diagnostics.py' \
  --include='src/run-round2-big4-mechanism.py' --include='src/aggregate-round2-big4-mechanism.py' \
  --include='src/export-publication-figures.py' --include='tests/***' --include='data/public/synthetic-example-null.csv' --include='docs/***' \
  --include='outputs/final-run-round2-pooled/tables/***' \
  --include='outputs/final-run-round2-pooled/figures/figure-1-primary-operating-characteristics-pooled.png' \
  --include='outputs/round2-pooled/tables/***' --include='outputs/round2-pooled/figures/***' \
  --include='outputs/round2-pooled/manifest.json' \
  --include='outputs/round2-big4-pooled/tables/***' --include='outputs/round2-big4-pooled/figures/***' \
  --include='outputs/round2-big4-pooled/manifest.json' \
  --include='outputs/publication-figures/***' \
  --exclude='*' "$WORK/" .

# Required negative checks before public push.
find . -type f \( -iname '*.docx' -o \( -iname '*.pdf' ! -path './outputs/publication-figures/*.pdf' \) \
  -o -path '*/private/*' -o -path '*/review-round2/*' -o -path '*/data/raw/*' \
  -o -path '*/data/restricted/*' -o -path '*/outputs/*seed*/*' \
  -o -path '*/outputs/*/replication-level/*' \) -print

grep -RInE --exclude-dir='.git' --exclude='*.png' --exclude='*.csv' \
  '(OPENAI_API_KEY|api[_-]?key|secret|password|token)' .
```

The `find` command must have **no output**. The grep command needs manual review: terms used in explanatory documentation (for example, “credential scan”) are allowed, but any real secret or environment value is a release blocker.
