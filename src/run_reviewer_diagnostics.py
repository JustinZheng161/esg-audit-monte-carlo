"""Reviewer-requested Monte Carlo extensions for the synthetic ESG diagnostic.

This script never downloads or analyses real-company observations. It tests whether
finite-sample behavior changes when the time-cluster count changes and whether the
Big Four selection mechanism alone can create the second-stage interaction signal.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from esg_monte_carlo import load_config, monte_carlo

ROOT = Path(__file__).resolve().parents[1]


def set_year_dimension(cfg: dict, dgp_years: int) -> tuple[dict, int]:
    """Return a copied configuration with dgp_years and lead/lag-valid analysis years."""
    local = copy.deepcopy(cfg)
    start = int(local["project"]["years"][0])
    years = list(range(start, start + dgp_years))
    local["project"]["years"] = years
    local["estimation"]["analysis_years"] = years[1:-1]
    return local, len(years[1:-1])


def make_time_cluster_figure(table: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.6, 4.1), constrained_layout=True)
    for metric, se_metric, label, color in [
        ("firm_rejection_5pct", "firm_mcse", "Firm-clustered", "#4C78A8"),
        ("two_way_rejection_5pct", "two_way_mcse", "Two-way firm–year", "#E45756"),
    ]:
        ax.errorbar(table["analysis_time_clusters"], table[metric], yerr=1.96 * table[se_metric],
                    marker="o", capsize=3, linewidth=1.6, label=label, color=color)
    ax.axhline(0.05, color="black", linestyle="--", linewidth=1, label="Nominal 5% size")
    ax.set_xlabel("Number of analysable time clusters")
    ax.set_ylabel("Null rejection probability")
    ax.set_ylim(0, max(0.16, float(table[["firm_rejection_5pct", "two_way_rejection_5pct"]].max().max() + 0.03)))
    ax.set_title("Few-time-cluster diagnostic under the null DGP")
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(path, dpi=600, bbox_inches="tight")
    plt.close(fig)


def make_big4_figure(table: pd.DataFrame, path: Path) -> None:
    long = table.melt(id_vars=["scenario"],
                      value_vars=["firm_rejection_5pct", "two_way_rejection_5pct"],
                      var_name="inference", value_name="rejection")
    names = list(table["scenario"])
    x = np.arange(len(names))
    width = 0.36
    fig, ax = plt.subplots(figsize=(7.0, 4.1), constrained_layout=True)
    for offset, (metric, label, color) in enumerate([
        ("firm_rejection_5pct", "Firm-clustered", "#4C78A8"),
        ("two_way_rejection_5pct", "Two-way firm–year", "#E45756"),
    ]):
        values = table[metric].to_numpy()
        ax.bar(x + (offset - 0.5) * width, values, width, color=color, label=label)
    ax.axhline(0.05, color="black", linestyle="--", linewidth=1, label="Nominal 5% size")
    ax.set_xticks(x, names, rotation=12, ha="right")
    ax.set_ylabel("Interaction rejection probability")
    ax.set_ylim(0, min(1, max(0.15, float(long["rejection"].max() + 0.05))))
    ax.set_title("Big Four mechanism ablation")
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(path, dpi=600, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run reviewer-requested synthetic Monte Carlo extensions.")
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "dgp.yaml")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reps", type=int, default=500, help="Outer repetitions per scenario.")
    parser.add_argument("--seed", type=int, default=None, help="Independent master seed override.")
    parser.add_argument("--year-grid", type=int, nargs="+", default=[10, 20, 30])
    args = parser.parse_args()
    cfg = load_config(args.config)
    if args.seed is not None:
        cfg["project"]["seed"] = int(args.seed)
    master_seed = int(cfg["project"]["seed"])
    n_firms = int(cfg["panel"]["primary_firms"])
    output = args.output
    table_dir, figure_dir = output / "tables", output / "figures"
    table_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    time_rows = []
    for index, dgp_years in enumerate(args.year_grid):
        local, clusters = set_year_dimension(cfg, int(dgp_years))
        result = monte_carlo(
            label=f"Null, {clusters} analysis time clusters",
            n_firms=n_firms,
            effect_scale=0.0,
            repetitions=int(args.reps),
            base_seed=master_seed + 1000 + index,
            cfg=local,
        )
        result["dgp_years"] = int(dgp_years)
        result["analysis_time_clusters"] = clusters
        result["first_stage_n"] = n_firms * dgp_years
        result["second_stage_n"] = n_firms * clusters
        time_rows.append(result)
    time_table = pd.DataFrame(time_rows).sort_values("analysis_time_clusters")
    time_table.to_csv(table_dir / "table_6_time_cluster_diagnostics.csv", index=False)
    make_time_cluster_figure(time_table, figure_dir / "figure_2_time_cluster_size.png")

    baseline = monte_carlo(
        label="Full alternative: Big Four direct variance role retained",
        n_firms=n_firms,
        effect_scale=1.0,
        repetitions=int(args.reps),
        base_seed=master_seed + 2001,
        cfg=cfg,
        big4_variance_scale=1.0,
    )
    selection_only = monte_carlo(
        label="Selection-only: Big Four direct variance role set to zero",
        n_firms=n_firms,
        effect_scale=1.0,
        repetitions=int(args.reps),
        base_seed=master_seed + 2002,
        cfg=cfg,
        big4_variance_scale=0.0,
    )
    big4_table = pd.DataFrame([baseline, selection_only])
    big4_table["first_stage_n"] = n_firms * len(cfg["project"]["years"])
    big4_table["second_stage_n"] = n_firms * len(cfg["project"]["years"][1:-1])
    big4_table.to_csv(table_dir / "table_7_big4_mechanism_ablation.csv", index=False)
    make_big4_figure(big4_table, figure_dir / "figure_3_big4_mechanism_ablation.png")

    config_bytes = args.config.read_bytes()
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "master_seed": master_seed,
        "outer_repetitions_per_scenario": int(args.reps),
        "year_grid": [int(v) for v in args.year_grid],
        "primary_firms": n_firms,
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "scope": "Synthetic DGP only. No real-company data are used or implied.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Completed reviewer diagnostics. Outputs: {output}")


if __name__ == "__main__":
    main()
