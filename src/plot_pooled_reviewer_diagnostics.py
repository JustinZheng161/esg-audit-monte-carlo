"""Create publication figures from pooled reviewer-diagnostic result tables."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    time = pd.read_csv(args.input / "table_6_time_cluster_diagnostics_pooled.csv").sort_values("analysis_time_clusters")
    big4 = pd.read_csv(args.input / "table_7_big4_mechanism_ablation_pooled.csv")

    fig, ax = plt.subplots(figsize=(6.8, 4.2), constrained_layout=True)
    for metric, se, label, color in [
        ("firm_rejection_5pct", "firm_rejection_5pct_pooled_mcse", "Firm-clustered", "#4C78A8"),
        ("two_way_rejection_5pct", "two_way_rejection_5pct_pooled_mcse", "Two-way firm–year", "#E45756"),
    ]:
        ax.errorbar(time["analysis_time_clusters"], time[metric], yerr=1.96 * time[se], marker="o",
                    capsize=3, linewidth=1.8, color=color, label=label)
    ax.axhline(0.05, color="black", linestyle="--", linewidth=1, label="Nominal 5% size")
    ax.set_xlabel("Number of analysable time clusters")
    ax.set_ylabel("Null rejection probability")
    ax.set_ylim(0.0, 0.12)
    ax.set_xticks(time["analysis_time_clusters"])
    ax.set_title("Time-cluster gradient: pooled independent-seed diagnostics")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.savefig(args.output / "figure_2_time_cluster_size_pooled.png", dpi=600, bbox_inches="tight")
    plt.close(fig)

    labels = ["Direct Big Four\nvariance role retained", "Selection-only\nBig Four role"]
    x = np.arange(len(labels))
    width = 0.34
    fig, ax = plt.subplots(figsize=(6.8, 4.2), constrained_layout=True)
    for offset, (metric, label, color) in enumerate([
        ("firm_rejection_5pct", "Firm-clustered", "#4C78A8"),
        ("two_way_rejection_5pct", "Two-way firm–year", "#E45756"),
    ]):
        values = big4[metric].to_numpy()
        errors = big4[f"{metric}_pooled_mcse"].to_numpy()
        ax.bar(x + (offset - 0.5) * width, values, width, color=color, label=label,
               yerr=1.96 * errors, capsize=3)
    ax.axhline(0.05, color="black", linestyle="--", linewidth=1, label="Nominal 5% size")
    ax.set_xticks(x, labels)
    ax.set_ylabel("Interaction rejection probability")
    ax.set_ylim(0, 0.32)
    ax.set_title("Big Four mechanism ablation: pooled independent-seed diagnostics")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    fig.savefig(args.output / "figure_3_big4_mechanism_ablation_pooled.png", dpi=600, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
