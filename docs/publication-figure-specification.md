# Publication-figure specification

## Purpose and scope

This package provides print-oriented versions of Figures 1–5. Each figure is regenerated from an already released aggregate synthetic-results table. The export process does **not** rerun a simulation, read a private replication-level file, or use real-company data.

| Figure | Released table | Figure content |
|---|---|---|
| Figure 1 | `outputs/final-run-round2-pooled/tables/table-6-independent-seed-crosscheck.csv` | Primary N=300 firm-clustered and two-way rejection probabilities |
| Figure 2 | `outputs/round2-pooled/tables/table-11-scale-mapping-pooled.csv` | Fixed DGP interaction parameter and oracle/estimated-residual coefficients |
| Figure 3 | `outputs/round2-pooled/tables/table-10-time-structure-sensitivity-pooled.csv` | Two-way interaction-null rejection sensitivity |
| Figure 4 | `outputs/round2-big4-pooled/tables/table-9-big4-mechanism-ablation-pooled.csv` | Big Four mechanism ablation |
| Figure 5 | `outputs/round2-pooled/tables/table-12-selective-availability-pooled.csv` | Selective-availability sensitivity |

## Delivery formats and technical settings

Each figure is supplied as vector `PDF`, 600-dpi `PNG`, and 600-dpi `TIFF` under `outputs/publication-figures/`. The exporter uses an 8×6-inch minimum layout (10×6 inches for Figure 2 and 10×6 inches for Figure 3), 10-pt base text, 9-pt axis tick labels, and complete y-axis ticks. These settings provide a reproducible technical source package; authors should still apply the selected journal’s final artwork instructions at submission.

The uncertainty bars are **normal-approximation intervals of ±1.96 × MCSE**. Figure 2 displays no uncertainty bar for `γ_INT`, because it is a fixed DGP parameter; only the oracle and estimated-residual coefficients receive MCSE-based bars. In Figures 1, 4, and 5, blue denotes firm-clustered and red denotes two-way firm–year results.

## Regeneration

```bash
python3 src/export-publication-figures.py
```

The command writes all three formats to `outputs/publication-figures/`. To direct files elsewhere, add `--output /path/to/directory`.

## Release boundary

Only the rendered files built from the public aggregate tables are released. Manuscript files, full synthetic repetition-level outputs, reviewer material, and any real or restricted data remain outside this repository; see [repository-boundary.md](repository-boundary.md).
