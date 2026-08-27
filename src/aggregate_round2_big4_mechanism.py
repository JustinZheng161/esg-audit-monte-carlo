"""Pool corrected-sample-flow Big Four mechanism ablations from independent seeds."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def coefficient_mcse(values: pd.Series) -> float:
    return float(values.std(ddof=1) / math.sqrt(len(values)))


def rate(values: pd.Series) -> tuple[float, float]:
    p = float((values < 0.05).mean())
    return p, float(math.sqrt(p * (1 - p) / len(values)))


def plot(summary: pd.DataFrame, output: Path) -> None:
    x = np.arange(len(summary))
    width = 0.36
    fig, ax = plt.subplots(figsize=(7.8, 4.3), constrained_layout=True)
    ax.bar(x - width / 2, summary["firm_rejection_5pct"], width,
           yerr=1.96 * summary["firm_mcse"], capsize=3,
           label="Firm-clustered", color="#4C78A8")
    ax.bar(x + width / 2, summary["two_way_rejection_5pct"], width,
           yerr=1.96 * summary["two_way_mcse"], capsize=3,
           label="Two-way firm–year", color="#E45756")
    ax.axhline(0.05, color="black", linewidth=1, linestyle="--", label="Nominal 5% size")
    ax.set_xticks(x, ["Direct variance\nrole retained", "Selection-only\n(direct role = 0)"])
    ax.set_ylabel("Interaction rejection probability")
    ax.set_title("Big Four mechanism ablation in the synthetic DGP")
    ax.legend(frameon=False)
    fig.savefig(output, dpi=600, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pool corrected Big Four mechanism-ablation replicates.")
    parser.add_argument("--seed-dirs", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if len(args.seed_dirs) < 2:
        raise ValueError("At least two independent seed directories are required.")
    frames = []
    seeds = []
    for directory in args.seed_dirs:
        frame = pd.read_csv(directory / "replication_level" / "big4_mechanism_replicates.csv")
        master_seed = int(json.loads((directory / "manifest.json").read_text(encoding="utf-8"))["master_seed"])
        frame.insert(0, "master_seed", master_seed)
        frames.append(frame)
        seeds.append(master_seed)
    data = pd.concat(frames, ignore_index=True)
    summaries = []
    for (scenario, scale), group in data.groupby(["scenario", "big4_variance_scale"], sort=False):
        firm_rate, firm_mcse = rate(group["p_firm"])
        two_rate, two_mcse = rate(group["p_two_way"])
        summaries.append({
            "scenario": scenario,
            "big4_variance_scale": float(scale),
            "repetitions": int(len(group)),
            "independent_master_seeds": int(group["master_seed"].nunique()),
            "mean_second_stage_n": float(group["n_obs"].mean()),
            "mean_interaction": float(group["interaction_coefficient"].mean()),
            "mcse_mean_interaction": coefficient_mcse(group["interaction_coefficient"]),
            "firm_rejection_5pct": firm_rate,
            "firm_mcse": firm_mcse,
            "two_way_rejection_5pct": two_rate,
            "two_way_mcse": two_mcse,
        })
    output = args.output
    tables, figures = output / "tables", output / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame(summaries)
    summary.to_csv(tables / "table_9_big4_mechanism_ablation_pooled.csv", index=False)
    plot(summary, figures / "figure_3_big4_mechanism_ablation_pooled.png")
    (output / "manifest.json").write_text(json.dumps({
        "master_seeds": sorted(seeds),
        "pooling_rule": {
            "binary_rates": "recomputed from all replicate-level p-values; MCSE=sqrt(p*(1-p)/R)",
            "coefficient_means": "mean over all replicate-level coefficients; MCSE=sample_sd/sqrt(R)",
        },
        "scope": "Synthetic DGP only; both scenarios retain the Big Four selection equation. No real-company data are used, calibrated, or implied.",
    }, indent=2), encoding="utf-8")
    print(f"Pooled corrected Big Four mechanism ablations from seeds {sorted(seeds)} into {output}")


if __name__ == "__main__":
    main()
