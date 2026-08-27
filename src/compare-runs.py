"""Aggregate independent Monte Carlo runs without mixing their scenario definitions."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def pooled_mcse(p: float, n: int) -> float:
    return float(np.sqrt(p * (1.0 - p) / n))


def plot_primary_grouped_bars(summary: pd.DataFrame, destination: Path) -> None:
    """Plot the primary N=300 results with inference choices shown side by side."""
    order = ["Null", "Half alternative", "Full alternative"]
    data = summary.loc[(summary["firms"] == 300) & summary["scenario"].isin(order)].copy()
    data["scenario"] = pd.Categorical(data["scenario"], categories=order, ordered=True)
    data = data.sort_values("scenario")
    if len(data) != len(order):
        raise ValueError("Primary N=300 null, half-alternative, and full-alternative rows are required for Figure 1.")
    x = np.arange(len(data))
    width = 0.36
    fig, ax = plt.subplots(figsize=(8.4, 4.6), constrained_layout=True)
    ax.bar(x - width / 2, data["firm_rejection_5pct"], width,
           yerr=1.96 * data["firm_rejection_5pct_pooled_mcse"], capsize=3,
           label="Firm-clustered", color="#4C78A8")
    ax.bar(x + width / 2, data["two_way_rejection_5pct"], width,
           yerr=1.96 * data["two_way_rejection_5pct_pooled_mcse"], capsize=3,
           label="Two-way firm–year", color="#E45756")
    ax.axhline(0.05, color="black", linestyle="--", linewidth=1, label="Nominal 5% size")
    ax.set_xticks(x, ["Null\n(interaction = 0)", "Half alternative", "Full alternative"])
    ax.set_ylabel("5% interaction rejection probability")
    ax.set_title("Primary operating characteristics (N=300 synthetic firms)")
    ax.legend(frameon=False)
    fig.savefig(destination, dpi=600, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_a", type=Path)
    parser.add_argument("run_b", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--figure-output", type=Path, default=None,
                        help="Optional destination for the pooled primary grouped-bar figure.")
    args = parser.parse_args()
    a, b = pd.read_csv(args.run_a), pd.read_csv(args.run_b)
    a["run"] = "Seed 20260827"
    b["run"] = "Seed 20260828"
    combined = pd.concat([a, b], ignore_index=True)
    summary_rows = []
    for (scenario, firms, effect_scale), group in combined.groupby(["scenario", "firms", "effect_scale"], sort=False):
        row = {"scenario": scenario, "firms": int(firms), "effect_scale": float(effect_scale),
               "runs": int(group["run"].nunique()), "repetitions": int(group["repetitions"].sum())}
        for metric in ["firm_rejection_5pct", "two_way_rejection_5pct", "wild_firm_rejection_5pct", "mean_interaction"]:
            valid = group[[metric, "repetitions"]].dropna()
            if valid.empty:
                row[metric] = np.nan
                row[f"{metric}_pooled_mcse"] = np.nan
            elif metric == "mean_interaction":
                row[metric] = float(np.average(valid[metric], weights=valid["repetitions"]))
                row[f"{metric}_pooled_mcse"] = np.nan
            else:
                p = float(np.average(valid[metric], weights=valid["repetitions"]))
                n = int(valid["repetitions"].sum())
                row[metric] = p
                row[f"{metric}_pooled_mcse"] = pooled_mcse(p, n)
        summary_rows.append(row)
    result = pd.DataFrame(summary_rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    if args.figure_output is not None:
        args.figure_output.parent.mkdir(parents=True, exist_ok=True)
        plot_primary_grouped_bars(result, args.figure_output)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
