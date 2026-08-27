# Public/Private Repository Boundary and Sync Procedure

## Repository map

| Repository | Visibility | Purpose | Included assets | Explicit exclusions |
|---|---|---|---|---|
| `esg-audit-monte-carlo` | Public | Reproducible synthetic statistical diagnostics | Code, test suite, YAML configuration, synthetic example, aggregate tables, figures, source/ license documentation | Manuscript DOCX/PDF, raw SEC responses, full simulation output archives, commercial data, keys |
| `esg-audit-monte-carlo-private` | Private | Author-controlled research record and full audit trail | Original/revised manuscripts, full output runs, internal audit notes, raw public-source snapshots, permitted internal metadata | API keys, plaintext credentials, unauthorized third-party data redistribution |

## Sync algorithm

1. Generate all code and outputs in the private working tree.
2. Run the deterministic tests and full experiment.
3. Validate the result manifest, table schema, figure readability, and source registry.
4. Copy only the whitelist below to the public release tree.
5. Run a secret scan and an excluded-pattern scan on the public release tree.
6. Commit and push the public and private repositories independently.

| Whitelist class | Public path | Reason |
|---|---|---|
| Experiment code | `src/esg_monte_carlo.py`, `src/collect_sec_metadata.py`, `src/compare_runs.py` | Required for replication |
| Configuration | `config/dgp.yaml` | Makes all synthetic assumptions explicit |
| Test | `tests/test_pipeline.py` | Enables basic reproducibility check |
| Synthetic data | `data/public/synthetic_example_null.csv` | Demonstrates schema without real firms |
| Public metadata | `data/public/sec_metadata_manifest.csv` | Source traceability without raw API files |
| Results | `outputs/final_run_calibrated/tables/*.csv`, `outputs/final_run_calibrated/figures/*.png` | Documents canonical aggregate findings |
| Documentation | `README.md`, `docs/*.md`, `requirements.txt`, `LICENSE`, `.gitignore` | Reuse, data governance, and provenance |

## Prohibited public patterns

```text
*.docx, *.pdf, .env*, *token*, *secret*, *credential*, private/, data/raw/, data/restricted/,
CSMAR/, Wind/, Bloomberg/, Refinitiv/, MSCI/, Sustainalytics/, AuditAnalytics/, Compustat/
```

The pattern list is conservative: names alone do not prove data sensitivity, but any match must receive an explicit manual review before publication.

## Data synchronization rule

‘Data synchronization’ does **not** mean copying every local file to a public repository. The public repository synchronizes only synthetic examples, source manifests, and aggregate outputs. The private repository may mirror those files plus the author-controlled manuscript and full internal artifacts. Raw or licensed data remain local/controlled even in a private remote repository unless the owner’s license and organizational policy specifically allow remote storage.

## Operational command sequence

```bash
# Build a clean public release tree from the private working directory.
rsync -a --delete \
  --include='README.md' --include='LICENSE' --include='requirements.txt' --include='.gitignore' \
  --include='config/***' --include='src/esg_monte_carlo.py' \
  --include='src/collect_sec_metadata.py' --include='src/compare_runs.py' \
  --include='tests/***' --include='data/public/***' \
  --include='outputs/final_run_calibrated/tables/***' \
  --include='outputs/final_run_calibrated/figures/***' \
  --include='docs/***' --exclude='*' \
  /path/to/private-working-tree/ /path/to/esg-audit-monte-carlo/

# Required negative checks before public push.
# Run a credential scanner approved by your organization, then run the file-boundary check.
find . -type f \( -iname '*.docx' -o -iname '*.pdf' -o -path '*/data/raw/*' -o -path '*/data/restricted/*' \) -print
```

The file-boundary command should report **no public-release files**. Any unexpected file is a release blocker. The credential scan must also return clean before publication.
