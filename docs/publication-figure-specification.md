# Publication-figure specification

## Purpose and scope

This package provides print-oriented versions of Figures 1–5. Each figure is regenerated from an already released aggregate synthetic-results table. The export process does **not** rerun a simulation, read a private replication-level file, or use real-company data.

| Figure | Optimized output stem | Released table | Figure content |
|---|---|---|---|
| Figure 1 | `figure-01-primary-cluster-inference` | `outputs/final-run-round2-pooled/tables/table-6-independent-seed-crosscheck.csv` | Primary N=300 firm-clustered and two-way rejection probabilities |
| Figure 2 | `figure-02-dgp-scale-mapping` | `outputs/round2-pooled/tables/table-11-scale-mapping-pooled.csv` | Fixed DGP interaction parameter and oracle/estimated-residual coefficients |
| Figure 3 | `figure-03-time-cluster-sensitivity` | `outputs/round2-pooled/tables/table-10-time-structure-sensitivity-pooled.csv` | Two-way interaction-null rejection sensitivity |
| Figure 4 | `figure-04-big-four-mechanism-ablation` | `outputs/round2-big4-pooled/tables/table-9-big4-mechanism-ablation-pooled.csv` | Big Four mechanism ablation |
| Figure 5 | `figure-05-availability-sensitivity` | `outputs/round2-pooled/tables/table-12-selective-availability-pooled.csv` | Selective-availability sensitivity |

## Nature-style delivery formats and technical settings

Each optimized stem uses zero-padded figure order plus a concise scientific descriptor, and is supplied as editable vector `PDF` and `SVG`, plus 600-dpi `PNG` and losslessly compressed 600-dpi `TIFF`, under `outputs/publication-figures/`. The exporter uses a 7.2×4.2-inch double-column layout (7.2×3.6 inches for the two-panel Figure 3), matching the 183-mm double-column guidance while remaining well below the 247-mm page depth. It uses a sans-serif stack that resolves to Liberation Sans in the reproducible Linux build; 7-pt body lettering, 6-pt ticks and legend text, and 8-pt bold panel labels conform to Nature’s stated 5–7-pt lettering range and multi-panel exception [1] [2].

All figures use black lettering, clean outward ticks, labelled axes, 0.6–0.75-pt strokes, solid fills, no background gridlines, and a colour-blind-accessible blue/vermillion/teal/orange palette. The settings implement Nature’s requirements for accessible palettes, visible axes/ticks, standard sans-serif fonts, RGB artwork, and editable vector text [1] [2]. The file `figure-source-manifest.json` records the exact public aggregate CSV, SHA-256 source-table hash, generator path, and output hashes for every figure.

The uncertainty bars are **normal-approximation intervals of ±1.96 × MCSE**. Figure 2 displays no uncertainty bar for `γ_INT`, because it is a fixed DGP parameter; only the oracle and estimated-residual coefficients receive MCSE-based bars. In Figures 1, 4, and 5, blue denotes firm-clustered and vermillion denotes two-way firm–year results.

## Regeneration

```bash
python3 src/export-publication-figures.py
```

The command writes PDF, editable SVG, PNG, TIFF, and `figure-source-manifest.json` to `outputs/publication-figures/`. To direct files elsewhere, add `--output /path/to/directory`. Verify the full public source-to-asset chain with `python3 tests/test-publication-figure-exports.py`.

## Release boundary

Only the rendered files, SVG vector source, generator code, provenance manifest, and checked aggregate tables are released. Manuscript files, full synthetic repetition-level outputs, reviewer material, and any real or restricted data remain outside this repository; see [repository-boundary.md](repository-boundary.md).

## References

[1] [Nature, *Initial submission* — Figure guidance](https://www.nature.com/nature/for-authors/initial-submission).

[2] [Nature Research Figure Guide, *Preparing figures — our specifications*](https://research-figure-guide.nature.com/figures/preparing-figures-our-specifications/).
