"""Export publication-grade figures from the checked public aggregate tables.

The script does not rerun the simulation or change any reported result. It reads only
published aggregate CSV files and writes a vector PDF plus 600-dpi PNG and TIFF files.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BLUE, RED = "#376795", "#c95757"


def configure() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "figure.dpi": 150,
        "savefig.dpi": 600,
    })


def save(fig: plt.Figure, output: Path, stem: str) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for suffix in ("pdf", "png", "tiff"):
        options = {"dpi": 600, "bbox_inches": "tight", "facecolor": "white"}
        if suffix == "tiff":
            # Lossless compression preserves 600-dpi pixels while keeping public clones practical.
            options["pil_kwargs"] = {"compression": "tiff_lzw"}
        fig.savefig(output / f"{stem}.{suffix}", **options)
    plt.close(fig)


def axes_style(axis: plt.Axes, upper: float) -> None:
    axis.set_ylim(0, upper)
    axis.set_yticks(np.arange(0, upper + 0.001, 0.05))
    axis.grid(axis="y", color="#d9d9d9", linewidth=0.6, zorder=0)
    axis.spines[["top", "right"]].set_visible(False)


def figure1(root: Path, output: Path) -> None:
    frame = pd.read_csv(root / "outputs" / "final-run-round2-pooled" / "tables" / "table-6-independent-seed-crosscheck.csv")
    frame = frame.loc[(frame["firms"] == 300) & (frame["repetitions"] == 2000)].copy()
    order = ["Null", "Half alternative", "Full alternative"]
    frame["scenario"] = pd.Categorical(frame["scenario"], categories=order, ordered=True)
    frame = frame.sort_values("scenario")
    positions = np.arange(len(frame)); width = 0.34
    fig, axis = plt.subplots(figsize=(8, 6))
    axis.bar(positions - width / 2, frame["firm_rejection_5pct"], width, yerr=1.96 * frame["firm_rejection_5pct_pooled_mcse"], capsize=4, color=BLUE, label="Firm-clustered", zorder=3)
    axis.bar(positions + width / 2, frame["two_way_rejection_5pct"], width, yerr=1.96 * frame["two_way_rejection_5pct_pooled_mcse"], capsize=4, color=RED, label="Two-way firm–year", zorder=3)
    axis.axhline(0.05, linestyle="--", linewidth=1, color="#333333", label="Nominal 5% size")
    axis.set_xticks(positions, ["Null\n(interaction = 0)", "Half alternative", "Full alternative"])
    axis.set_ylabel("5% interaction rejection probability")
    axis.set_title("Primary operating characteristics (N=300 synthetic firms)")
    axes_style(axis, 0.35); axis.legend(frameon=False, loc="upper left")
    save(fig, output, "figure-1-primary-operating-characteristics")


def figure2(root: Path, output: Path) -> None:
    frame = pd.read_csv(root / "outputs" / "round2-pooled" / "tables" / "table-11-scale-mapping-pooled.csv").sort_values(["firms", "effect_scale"])
    positions = np.arange(len(frame)); width = 0.25
    fig, axis = plt.subplots(figsize=(10, 6))
    axis.bar(positions - width, frame["gamma_inter_log_sd"], width, color="#376795", label="γ_INT (fixed log-SD parameter)", zorder=3)
    axis.bar(positions, frame["mean_oracle_beta3_log_abs_true_deviation"], width, yerr=1.96 * frame["mcse_oracle_beta3"], capsize=3, color="#78b7b2", label="Oracle β₃, log|u*|", zorder=3)
    axis.bar(positions + width, frame["mean_estimated_beta3_log_abs_residual"], width, yerr=1.96 * frame["mcse_estimated_beta3"], capsize=3, color="#c95757", label="Estimated-residual β₃, log|û|", zorder=3)
    axis.axhline(0, linewidth=0.8, color="#333333")
    axis.set_xticks(positions, [f"N={int(row.firms)}\nscale={row.effect_scale:.1f}" for row in frame.itertuples()])
    axis.set_ylabel("Interaction coefficient on DGP-standardized exposure")
    axis.set_title("DGP parameter and second-stage coefficient scale mapping")
    axis.grid(axis="y", color="#d9d9d9", linewidth=0.6, zorder=0); axis.spines[["top", "right"]].set_visible(False)
    axis.legend(frameon=False, fontsize=8, loc="lower left")
    save(fig, output, "figure-2-dgp-to-coefficient-scale-mapping")


def figure3(root: Path, output: Path) -> None:
    frame = pd.read_csv(root / "outputs" / "round2-pooled" / "tables" / "table-10-time-structure-sensitivity-pooled.csv")
    scales = sorted(frame["esg_variance_scale"].unique())
    colors = {0.25: "#4c78a8", 0.60: "#f58518", 0.95: "#54a24b"}
    fig, axes = plt.subplots(1, len(scales), figsize=(10, 6), sharey=True)
    if len(scales) == 1:
        axes = [axes]
    for axis, scale in zip(axes, scales):
        subset = frame.loc[frame["esg_variance_scale"] == scale]
        for persistence, series in subset.groupby("esg_persistence"):
            series = series.sort_values("analysis_time_clusters")
            axis.errorbar(series["analysis_time_clusters"], series["two_way_rejection_5pct"], yerr=1.96 * series["two_way_mcse"], marker="o", markersize=5, linewidth=1.5, capsize=3, color=colors[float(persistence)], label=f"ESG AR(1)={persistence:.2f}")
        axis.axhline(0.05, linestyle="--", linewidth=1, color="#333333", label="Nominal 5% size")
        axis.set_title(f"ESG residual-variance scale = {scale:.0f}")
        axis.set_xlabel("Analysable time clusters")
        axis.set_xticks([8, 28])
        axes_style(axis, 0.12)
    axes[0].set_ylabel("Two-way interaction-null rejection probability")
    axes[-1].legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("Time-structure sensitivity", y=0.97)
    fig.tight_layout()
    save(fig, output, "figure-3-time-structure-sensitivity")


def figure4(root: Path, output: Path) -> None:
    frame = pd.read_csv(root / "outputs" / "round2-big4-pooled" / "tables" / "table-9-big4-mechanism-ablation-pooled.csv").sort_values("big4_variance_scale")
    labels = ["Selection-only\n(direct role = 0)", "Direct variance\nrole retained"]
    positions = np.arange(len(frame)); width = 0.34
    fig, axis = plt.subplots(figsize=(8, 6))
    axis.bar(positions - width / 2, frame["firm_rejection_5pct"], width, yerr=1.96 * frame["firm_mcse"], capsize=4, color=BLUE, label="Firm-clustered", zorder=3)
    axis.bar(positions + width / 2, frame["two_way_rejection_5pct"], width, yerr=1.96 * frame["two_way_mcse"], capsize=4, color=RED, label="Two-way firm–year", zorder=3)
    axis.axhline(0.05, linestyle="--", linewidth=1, color="#333333", label="Nominal 5% size")
    axis.set_xticks(positions, labels)
    axis.set_ylabel("Interaction rejection probability")
    axis.set_title("Big Four mechanism ablation in the synthetic DGP")
    axes_style(axis, 0.40); axis.legend(frameon=False, loc="upper left")
    save(fig, output, "figure-4-big-four-mechanism-ablation")


def figure5(root: Path, output: Path) -> None:
    frame = pd.read_csv(root / "outputs" / "round2-pooled" / "tables" / "table-12-selective-availability-pooled.csv")
    labels = ["Complete", "Adverse\nselective", "Coverage-\naligned"]
    positions = np.arange(len(frame)); width = 0.34
    fig, axis = plt.subplots(figsize=(8, 6))
    axis.bar(positions - width / 2, frame["firm_rejection_5pct"], width, yerr=1.96 * frame["firm_mcse"], capsize=4, color=BLUE, label="Firm-clustered", zorder=3)
    axis.bar(positions + width / 2, frame["two_way_rejection_5pct"], width, yerr=1.96 * frame["two_way_mcse"], capsize=4, color=RED, label="Two-way firm–year", zorder=3)
    axis.axhline(0.05, linestyle="--", linewidth=1, color="#333333", label="Nominal 5% size")
    axis.set_xticks(positions, labels)
    axis.set_ylabel("Interaction rejection probability under full alternative")
    axis.set_title("Sensitivity to synthetic selective-availability mechanisms")
    axes_style(axis, 0.35); axis.legend(frameon=False, loc="upper left")
    save(fig, output, "figure-5-selective-availability-sensitivity")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export vector and 600-dpi publication figures from public aggregate results.")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / "publication-figures")
    args = parser.parse_args()
    configure()
    figure1(ROOT, args.output); figure2(ROOT, args.output); figure3(ROOT, args.output); figure4(ROOT, args.output); figure5(ROOT, args.output)
    print(f"Wrote 5 publication figures as PDF, PNG, and TIFF to {args.output}")


if __name__ == "__main__":
    main()
