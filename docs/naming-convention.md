# Repository naming convention

## Canonical rule

All tracked **file and directory names** use lowercase kebab-case: lowercase ASCII letters, digits, and hyphens. Names do not contain underscores, spaces, or version suffixes that duplicate Git history. Extensions remain conventional, for example `.py`, `.csv`, `.json`, `.md`, `.png`, `.docx`, and `.pdf`.

| Item | Convention | Example |
|---|---|---|
| Source scripts | Verb or role in kebab-case | `run-paired-primary-diagnostics.py` |
| Tests | `test-` prefix in kebab-case | `test-paired-primary-diagnostics.py` |
| Aggregate tables | `table-<number>-<topic>.csv` | `table-14-paired-cluster-method-difference.csv` |
| Figures | `figure-<number>-<topic>.png` | `figure-6-paired-cluster-method-difference.png` |
| Output directories | Stage plus purpose in kebab-case | `final-run-round3-paired/` |
| Documentation | Lowercase kebab-case where newly added | `paired-cluster-diagnostic.md` |

## Python execution rule

Python permits `python3 path/to/file-name.py` for a hyphenated script but not a standard `import file-name` statement. Local drivers and tests that need the core module therefore use `importlib.import_module("esg-monte-carlo")`. This preserves executable kebab-case filenames without changing function names, configuration keys, CSV column names, or statistical results.

## Scope of the rule

The rule applies to repository file and directory names. It intentionally does **not** rename Python variables, public configuration keys, dataset column names, JSON fields, or external URLs. Those identifiers are machine contracts or external resources, and replacing their underscores would break reproducibility or third-party API compatibility.

## Migration verification

The repository is considered naming-compliant only if the following returns zero tracked basenames containing an underscore:

```bash
git ls-files | awk -F/ '$NF ~ /_/ {print}'
```

After a bulk rename, run the complete test set and a clean-clone boundary scan. The private archive maintains the full rename manifest and confirmation that the associated manuscript and snapshot references were updated.
