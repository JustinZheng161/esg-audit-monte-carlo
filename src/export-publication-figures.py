"""Export publication-grade figures from the checked public aggregate tables.

The script does not rerun the simulation or change any reported result. It reads only
published aggregate CSV files and writes a vector PDF plus 600-dpi PNG and TIFF files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
# Nature-style, colour-blind-accessible palette with solid fills and black lettering.
BLUE, VERMILION, TEAL, SKY, ORANGE, BLACK, GREY = (
    "#0072B2", "#D55E00", "#009E73", "#56B4E9", "#E69F00", "#222222", "#6E6E6E"
)
EXPORT_SUFFIXES = ("pdf", "svg", "png", "tiff")
FIGURE_SOURCES = {
    "figure-01-primary-cluster-inference": Path("outputs/final-run-round2-pooled/tables/table-6-independent-seed-crosscheck.csv"),
    "figure-02-dgp-scale-mapping": Path("outputs/round2-pooled/tables/table-11-scale-mapping-pooled.csv"),
    "figure-03-time-cluster-sensitivity": Path("outputs/round2-pooled/tables/table-10-time-structure-sensitivity-pooled.csv"),
    "figure-04-big-four-mechanism-ablation": Path("outputs/round2-big4-pooled/tables/table-9-big4-mechanism-ablation-pooled.csv"),
    "figure-05-availability-sensitivity": Path("outputs/round2-pooled/tables/table-12-selective-availability-pooled.csv"),
}


def configure() -> None:
    """Apply Nature-compatible, editable vector-art defaults at final figure size."""
    plt.rcParams.update({
        # Arial/Helvetica resolve to Liberation Sans in the reproducible Linux build.
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans"],
        "font.size": 7,
        "axes.titlesize": 7,
        "axes.labelsize": 7,
        "xtick.labelsize": 6,
        "ytick.labelsize": 6,
        "legend.fontsize": 6,
        "axes.linewidth": 0.6,
        "lines.linewidth": 0.75,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "figure.dpi": 150,
        "savefig.dpi": 600,
    })


def save(fig: plt.Figure, output: Path, stem: str) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for suffix in EXPORT_SUFFIXES:
        # Preserve the declared 7.2-inch double-column canvas; do not tight-crop it.
        options = {"dpi": 600, "facecolor": "white"}
        if suffix == "tiff":
            # Lossless compression preserves 600-dpi pixels while keeping public clones practical.
            options["pil_kwargs"] = {"compression": "tiff_lzw"}
        target = output / f"{stem}.{suffix}"
        fig.savefig(target, **options)
        if suffix == "svg":
            # Matplotlib wraps vector paths across lines with trailing spaces; remove
            # only those spaces so the editable XML also passes a strict Git check.
            target.write_text(
                "\n".join(line.rstrip() for line in target.read_text(encoding="utf-8").splitlines()) + "\n",
                encoding="utf-8",
            )
    plt.close(fig)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_source_manifest(output: Path) -> None:
    """Record public-table provenance and immutable hashes for every export asset."""
    records = []
    for stem, source in FIGURE_SOURCES.items():
        source_path = ROOT / source
        records.append({
            "stem": stem,
            "generator": "src/export-publication-figures.py",
            "source_table": source.as_posix(),
            "source_table_sha256": sha256(source_path),
            "assets": {suffix: sha256(output / f"{stem}.{suffix}") for suffix in EXPORT_SUFFIXES},
        })
    manifest = {
        "schema_version": 1,
        "description": "Public aggregate-table provenance for editable publication figures.",
        "figures": records,
    }
    (output / "figure-source-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


def axes_style(axis: plt.Axes, upper: float) -> None:
    """Use clean axes and outward ticks; Nature guidance avoids background gridlines."""
    axis.set_ylim(0, upper)
    axis.set_yticks(np.arange(0, upper + 0.001, 0.05))
    axis.spines[["top", "right"]].set_visible(False)
    axis.spines[["left", "bottom"]].set_linewidth(0.6)
    axis.tick_params(direction="out", length=3, width=0.6, pad=2)


def single_panel_layout(fig: plt.Figure, *, bottom: float = 0.18) -> None:
    """Maximize the active plotting region within the fixed double-column canvas."""
    fig.subplots_adjust(left=0.13, right=0.985, bottom=bottom, top=0.97)


def figure1(root: Path, output: Path) -> None:
    frame = pd.read_csv(root / "outputs" / "final-run-round2-pooled" / "tables" / "table-6-independent-seed-crosscheck.csv")
    frame = frame.loc[(frame["firms"] == 300) & (frame["repetitions"] == 2000)].copy()
    order = ["Null", "Half alternative", "Full alternative"]
    frame["scenario"] = pd.Categorical(frame["scenario"], categories=order, ordered=True)
    frame = frame.sort_values("scenario")
    positions = np.arange(len(frame)); width = 0.34
    fig, axis = plt.subplots(figsize=(7.2, 4.2))
    error = {"ecolor": BLACK, "elinewidth": 0.7, "capthick": 0.7}
    axis.bar(positions - width / 2, frame["firm_rejection_5pct"], width, yerr=1.96 * frame["firm_rejection_5pct_pooled_mcse"], capsize=2, color=BLUE, edgecolor=BLACK, linewidth=0.3, error_kw=error, label="Firm-clustered", zorder=3)
    axis.bar(positions + width / 2, frame["two_way_rejection_5pct"], width, yerr=1.96 * frame["two_way_rejection_5pct_pooled_mcse"], capsize=2, color=VERMILION, edgecolor=BLACK, linewidth=0.3, error_kw=error, label="Two-way firm–year", zorder=3)
    axis.axhline(0.05, linestyle=(0, (3, 2)), linewidth=0.7, color=GREY, label="Nominal 5% size")
    axis.set_xticks(positions, ["Null\n(interaction = 0)", "Half alternative", "Full alternative"])
    axis.set_ylabel("5% interaction rejection probability (proportion)")
    axes_style(axis, 0.35); axis.legend(frameon=False, loc="upper left", handlelength=1.7)
    single_panel_layout(fig)
    save(fig, output, "figure-01-primary-cluster-inference")


def figure2(root: Path, output: Path) -> None:
    frame = pd.read_csv(root / "outputs" / "round2-pooled" / "tables" / "table-11-scale-mapping-pooled.csv").sort_values(["firms", "effect_scale"])
    positions = np.arange(len(frame)); width = 0.25
    fig, axis = plt.subplots(figsize=(7.2, 4.2))
    error = {"ecolor": BLACK, "elinewidth": 0.7, "capthick": 0.7}
    # γ_INT is fixed by the DGP and deliberately has no MCSE or uncertainty bar.
    axis.bar(positions - width, frame["gamma_inter_log_sd"], width, color=BLUE, edgecolor=BLACK, linewidth=0.3, label="γ_INT (fixed DGP parameter)", zorder=3)
    axis.bar(positions, frame["mean_oracle_beta3_log_abs_true_deviation"], width, yerr=1.96 * frame["mcse_oracle_beta3"], capsize=2, color=TEAL, edgecolor=BLACK, linewidth=0.3, error_kw=error, label="Oracle β₃, log|u*|", zorder=3)
    axis.bar(positions + width, frame["mean_estimated_beta3_log_abs_residual"], width, yerr=1.96 * frame["mcse_estimated_beta3"], capsize=2, color=VERMILION, edgecolor=BLACK, linewidth=0.3, error_kw=error, label="Estimated-residual β₃, log|û|", zorder=3)
    axis.axhline(0, linewidth=0.6, color=GREY)
    axis.set_xticks(positions, [f"N={int(row.firms)}\nscale={row.effect_scale:.1f}" for row in frame.itertuples()])
    axis.set_ylabel("Interaction coefficient (standardized-exposure scale)")
    axis.spines[["top", "right"]].set_visible(False)
    axis.spines[["left", "bottom"]].set_linewidth(0.6)
    axis.tick_params(direction="out", length=3, width=0.6, pad=2)
    axis.legend(frameon=False, loc="lower left", handlelength=1.7)
    single_panel_layout(fig, bottom=0.20)
    save(fig, output, "figure-02-dgp-scale-mapping")


def figure3(root: Path, output: Path) -> None:
    frame = pd.read_csv(root / "outputs" / "round2-pooled" / "tables" / "table-10-time-structure-sensitivity-pooled.csv")
    scales = sorted(frame["esg_variance_scale"].unique())
    styles = {0.25: (BLUE, "o"), 0.60: (ORANGE, "s"), 0.95: (TEAL, "^")}
    fig, axes = plt.subplots(1, len(scales), figsize=(7.2, 3.6), sharey=True)
    if len(scales) == 1:
        axes = [axes]
    for axis, scale in zip(axes, scales):
        subset = frame.loc[frame["esg_variance_scale"] == scale]
        panel = chr(ord("a") + scales.index(scale))
        axis.text(-0.13, 1.05, panel, transform=axis.transAxes, fontsize=8, fontweight="bold", va="bottom")
        for persistence, series in subset.groupby("esg_persistence"):
            series = series.sort_values("analysis_time_clusters")
            color, marker = styles[float(persistence)]
            axis.errorbar(series["analysis_time_clusters"], series["two_way_rejection_5pct"], yerr=1.96 * series["two_way_mcse"], marker=marker, markersize=4, linewidth=0.75, capsize=2, elinewidth=0.6, color=color, markeredgecolor=BLACK, markeredgewidth=0.25, label=f"ESG AR(1)={persistence:.2f}")
        axis.axhline(0.05, linestyle=(0, (3, 2)), linewidth=0.7, color=GREY, label="Nominal 5% size")
        axis.set_title(f"Residual-variance scale = {scale:.0f}", loc="left", pad=7)
        axis.set_xlabel("Analysable time clusters (count)")
        axis.set_xticks([8, 28])
        axes_style(axis, 0.12)
    axes[0].set_ylabel("Two-way rejection probability (proportion)")
    axes[-1].legend(frameon=False, loc="upper left", handlelength=1.7)
    fig.subplots_adjust(wspace=0.10, left=0.13, right=0.985, bottom=0.18, top=0.94)
    save(fig, output, "figure-03-time-cluster-sensitivity")


def figure4(root: Path, output: Path) -> None:
    frame = pd.read_csv(root / "outputs" / "round2-big4-pooled" / "tables" / "table-9-big4-mechanism-ablation-pooled.csv").sort_values("big4_variance_scale")
    labels = ["Selection-only\n(direct role = 0)", "Direct variance\nrole retained"]
    positions = np.arange(len(frame)); width = 0.34
    fig, axis = plt.subplots(figsize=(7.2, 4.2))
    error = {"ecolor": BLACK, "elinewidth": 0.7, "capthick": 0.7}
    axis.bar(positions - width / 2, frame["firm_rejection_5pct"], width, yerr=1.96 * frame["firm_mcse"], capsize=2, color=BLUE, edgecolor=BLACK, linewidth=0.3, error_kw=error, label="Firm-clustered", zorder=3)
    axis.bar(positions + width / 2, frame["two_way_rejection_5pct"], width, yerr=1.96 * frame["two_way_mcse"], capsize=2, color=VERMILION, edgecolor=BLACK, linewidth=0.3, error_kw=error, label="Two-way firm–year", zorder=3)
    axis.axhline(0.05, linestyle=(0, (3, 2)), linewidth=0.7, color=GREY, label="Nominal 5% size")
    axis.set_xticks(positions, labels)
    axis.set_ylabel("Interaction rejection probability (proportion)")
    axes_style(axis, 0.40); axis.legend(frameon=False, loc="upper left", handlelength=1.7)
    single_panel_layout(fig)
    save(fig, output, "figure-04-big-four-mechanism-ablation")


def figure5(root: Path, output: Path) -> None:
    frame = pd.read_csv(root / "outputs" / "round2-pooled" / "tables" / "table-12-selective-availability-pooled.csv")
    labels = ["Complete", "Adverse\nselective", "Coverage-\naligned"]
    positions = np.arange(len(frame)); width = 0.34
    fig, axis = plt.subplots(figsize=(7.2, 4.2))
    error = {"ecolor": BLACK, "elinewidth": 0.7, "capthick": 0.7}
    axis.bar(positions - width / 2, frame["firm_rejection_5pct"], width, yerr=1.96 * frame["firm_mcse"], capsize=2, color=BLUE, edgecolor=BLACK, linewidth=0.3, error_kw=error, label="Firm-clustered", zorder=3)
    axis.bar(positions + width / 2, frame["two_way_rejection_5pct"], width, yerr=1.96 * frame["two_way_mcse"], capsize=2, color=VERMILION, edgecolor=BLACK, linewidth=0.3, error_kw=error, label="Two-way firm–year", zorder=3)
    axis.axhline(0.05, linestyle=(0, (3, 2)), linewidth=0.7, color=GREY, label="Nominal 5% size")
    axis.set_xticks(positions, labels)
    axis.set_ylabel("Interaction rejection probability (proportion)")
    axes_style(axis, 0.35); axis.legend(frameon=False, loc="upper left", handlelength=1.7)
    single_panel_layout(fig)
    save(fig, output, "figure-05-availability-sensitivity")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export vector and 600-dpi publication figures from public aggregate results.")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "publication-figures")
    args = parser.parse_args()
    configure()
    figure1(ROOT, args.output); figure2(ROOT, args.output); figure3(ROOT, args.output); figure4(ROOT, args.output); figure5(ROOT, args.output)
    write_source_manifest(args.output)
    print(f"Wrote 5 publication figures as PDF, editable SVG, PNG, and TIFF to {args.output}")


if __name__ == "__main__":
    main()
