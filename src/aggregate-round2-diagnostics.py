"""Pool two independent seed-level round-two synthetic diagnostic runs.

All rates are recomputed from replicate-level records, not averaged from seed summaries.
For a binary rate, MCSE is sqrt(p*(1-p)/R). For a coefficient mean, MCSE is
the sample standard deviation across all stored independent repetitions divided by
sqrt(R). The script is intentionally limited to synthetic output directories.
"""
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


TIME_KEYS = [
    "analysis_time_clusters", "dgp_years", "esg_persistence", "esg_variance_scale",
    "first_stage_n", "second_stage_n",
]
SCALE_KEYS = ["firms", "effect_scale", "gamma_inter_log_sd"]
AVAILABILITY_KEYS = ["availability_scenario", "availability_code"]
FE_KEYS = ["first_stage_fe"]


def read_replicates(seed_dir: Path, filename: str) -> pd.DataFrame:
    """Read one stored replicate-level file and attach its independent master seed."""
    frame = pd.read_csv(seed_dir / "replication-level" / filename)
    manifest = json.loads((seed_dir / "manifest.json").read_text(encoding="utf-8"))
    frame.insert(0, "master_seed", int(manifest["master_seed"]))
    return frame


def coefficient_mcse(values: pd.Series) -> float:
    values = values.dropna()
    if len(values) < 2:
        return float("nan")
    return float(values.std(ddof=1) / math.sqrt(len(values)))


def rate_and_mcse(p_values: pd.Series) -> tuple[float, float]:
    rate = float((p_values < 0.05).mean())
    return rate, float(math.sqrt(rate * (1 - rate) / len(p_values)))


def summarize_common(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    rows: list[dict] = []
    for key, group in frame.groupby(keys, sort=False, dropna=False):
        key_values = key if isinstance(key, tuple) else (key,)
        row = dict(zip(keys, key_values))
        firm_rate, firm_mcse = rate_and_mcse(group["p_firm"])
        two_rate, two_mcse = rate_and_mcse(group["p_two_way"])
        row.update({
            "repetitions": int(len(group)),
            "independent_master_seeds": int(group["master_seed"].nunique()),
            "mean_second_stage_n": float(group["n_obs"].mean()),
            "mean_beta_interaction": float(group["beta_interaction"].mean()),
            "mcse_beta_interaction": coefficient_mcse(group["beta_interaction"]),
            "firm_rejection_5pct": firm_rate,
            "firm_mcse": firm_mcse,
            "two_way_rejection_5pct": two_rate,
            "two_way_mcse": two_mcse,
            "mean_error_interaction_covariance": float(group["error_interaction_covariance"].mean()),
        })
        if "oracle_beta_interaction" in group.columns:
            of_rate, of_mcse = rate_and_mcse(group["oracle_p_firm"])
            ot_rate, ot_mcse = rate_and_mcse(group["oracle_p_two_way"])
            row.update({
                "mean_oracle_beta_interaction": float(group["oracle_beta_interaction"].mean()),
                "mcse_oracle_beta_interaction": coefficient_mcse(group["oracle_beta_interaction"]),
                "oracle_firm_rejection_5pct": of_rate,
                "oracle_firm_mcse": of_mcse,
                "oracle_two_way_rejection_5pct": ot_rate,
                "oracle_two_way_mcse": ot_mcse,
            })
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_scale(frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for key, group in frame.groupby(SCALE_KEYS, sort=False, dropna=False):
        firms, effect_scale, gamma = key
        oracle = group["oracle_beta3_log_abs_true_deviation"]
        estimated = group["estimated_beta3_log_abs_residual"]
        mean_oracle = float(oracle.mean())
        mean_estimated = float(estimated.mean())
        rows.append({
            "firms": int(firms),
            "effect_scale": float(effect_scale),
            "gamma_inter_log_sd": float(gamma),
            "repetitions": int(len(group)),
            "independent_master_seeds": int(group["master_seed"].nunique()),
            "mean_oracle_beta3_log_abs_true_deviation": mean_oracle,
            "mcse_oracle_beta3": coefficient_mcse(oracle),
            "mean_estimated_beta3_log_abs_residual": mean_estimated,
            "mcse_estimated_beta3": coefficient_mcse(estimated),
            "oracle_minus_gamma": mean_oracle - float(gamma),
            "estimated_minus_oracle": mean_estimated - mean_oracle,
        })
    return pd.DataFrame(rows).sort_values(["firms", "effect_scale"])


def plot_time_structure(table: pd.DataFrame, destination: Path) -> None:
    scales = sorted(table["esg_variance_scale"].unique())
    fig, axes = plt.subplots(1, len(scales), figsize=(6.2 * len(scales), 4.2), constrained_layout=True, sharey=True)
    if len(scales) == 1:
        axes = [axes]
    for axis, scale in zip(axes, scales):
        subset = table.loc[table["esg_variance_scale"] == scale]
        for persistence, group in subset.groupby("esg_persistence"):
            group = group.sort_values("analysis_time_clusters")
            axis.errorbar(group["analysis_time_clusters"], group["two_way_rejection_5pct"],
                          yerr=1.96 * group["two_way_mcse"], marker="o", capsize=3,
                          label=f"ESG AR(1)={persistence:.2f}")
        axis.axhline(0.05, color="black", linestyle="--", linewidth=1, label="Nominal 5% size")
        axis.set_xlabel("Analysable time clusters")
        axis.set_title(f"ESG-dependent residual variance scale = {scale:.0f}")
        axis.legend(frameon=False, fontsize=8)
    axes[0].set_ylabel("Two-way interaction rejection probability under interaction null")
    fig.savefig(destination, dpi=600, bbox_inches="tight")
    plt.close(fig)


def plot_scale_mapping(table: pd.DataFrame, destination: Path) -> None:
    plot = table.loc[table["effect_scale"] > 0].copy()
    labels = [f"N={int(r.firms)}\nscale={r.effect_scale:.1f}" for r in plot.itertuples()]
    x = np.arange(len(plot))
    width = 0.25
    fig, ax = plt.subplots(figsize=(8.5, 4.4), constrained_layout=True)
    ax.bar(x - width, plot["gamma_inter_log_sd"], width, label="DGP γ_INT (log-SD)", color="#4C78A8")
    ax.bar(x, plot["mean_oracle_beta3_log_abs_true_deviation"], width, label="Oracle mean β₃ (log|u*|)", color="#72B7B2")
    ax.bar(x + width, plot["mean_estimated_beta3_log_abs_residual"], width, label="Estimated-residual mean β₃ (log|û|)", color="#E45756")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Interaction coefficient on DGP-standardized exposure")
    ax.set_title("DGP parameter and second-stage coefficient scale mapping")
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(destination, dpi=600, bbox_inches="tight")
    plt.close(fig)


def plot_availability(table: pd.DataFrame, destination: Path) -> None:
    desired_order = ["complete", "adverse_selective", "coverage_aligned"]
    table = table.set_index("availability_code").loc[desired_order].reset_index()
    x = np.arange(len(table))
    width = 0.36
    fig, ax = plt.subplots(figsize=(8.5, 4.4), constrained_layout=True)
    ax.bar(x - width / 2, table["firm_rejection_5pct"], width, label="Firm-clustered", color="#4C78A8")
    ax.bar(x + width / 2, table["two_way_rejection_5pct"], width, label="Two-way firm–year", color="#E45756")
    ax.axhline(0.05, color="black", linestyle="--", linewidth=1, label="Nominal 5% size")
    ax.set_xticks(x, ["Complete", "Adverse\nselective", "Coverage-\naligned"])
    ax.set_ylabel("Interaction rejection probability under full alternative")
    ax.set_title("Sensitivity to synthetic selective-availability mechanisms")
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(destination, dpi=600, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pool replicate-level second-round diagnostics.")
    parser.add_argument("--seed-dirs", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if len(args.seed_dirs) < 2:
        raise ValueError("At least two independent seed directories are required.")

    out_tables = args.output / "tables"
    out_figures = args.output / "figures"
    out_tables.mkdir(parents=True, exist_ok=True)
    out_figures.mkdir(parents=True, exist_ok=True)

    time = pd.concat([read_replicates(d, "time-structure-replicates.csv") for d in args.seed_dirs], ignore_index=True)
    scale = pd.concat([read_replicates(d, "scale-mapping-replicates.csv") for d in args.seed_dirs], ignore_index=True)
    availability = pd.concat([read_replicates(d, "availability-replicates.csv") for d in args.seed_dirs], ignore_index=True)
    fe = pd.concat([read_replicates(d, "first-stage-fe-replicates.csv") for d in args.seed_dirs], ignore_index=True)

    time_summary = summarize_common(time, TIME_KEYS).sort_values(["analysis_time_clusters", "esg_variance_scale", "esg_persistence"])
    scale_summary = summarize_scale(scale)
    availability_summary = summarize_common(availability, AVAILABILITY_KEYS)
    fe_summary = summarize_common(fe, FE_KEYS)

    time_summary.to_csv(out_tables / "table-10-time-structure-sensitivity-pooled.csv", index=False)
    scale_summary.to_csv(out_tables / "table-11-scale-mapping-pooled.csv", index=False)
    availability_summary.to_csv(out_tables / "table-12-selective-availability-pooled.csv", index=False)
    fe_summary.to_csv(out_tables / "table-13-first-stage-fe-sensitivity-pooled.csv", index=False)

    reference_diagnostics = []
    for directory in args.seed_dirs:
        diagnostic = pd.read_csv(directory / "tables" / "table-a3-first-stage-fe-design-diagnostics.csv")
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        diagnostic.insert(0, "master_seed", int(manifest["master_seed"]))
        reference_diagnostics.append(diagnostic)
    pd.concat(reference_diagnostics, ignore_index=True).to_csv(
        out_tables / "table-a3-first-stage-fe-design-reference-panels.csv", index=False
    )

    provenance = {
        "seed_directories": [str(d) for d in args.seed_dirs],
        "master_seeds": sorted(int(x) for x in time["master_seed"].unique()),
        "pooling_rule": {
            "binary_rates": "recomputed from all replicate-level p-values; MCSE=sqrt(p*(1-p)/R)",
            "coefficient_means": "mean over all replicate-level coefficients; MCSE=sample_sd/sqrt(R)",
            "first_stage_fe_design": "two reference-panel diagnostics retained separately by master seed; no pseudo-MCSE is reported",
        },
        "scope": "Synthetic DGP diagnostics only; no real-company data are used, calibrated, or implied.",
    }
    (args.output / "manifest.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")

    plot_time_structure(time_summary, out_figures / "figure-4-time-structure-sensitivity-pooled.png")
    plot_scale_mapping(scale_summary, out_figures / "figure-5-scale-mapping-pooled.png")
    plot_availability(availability_summary, out_figures / "figure-6-selective-availability-pooled.png")
    print(f"Pooled {len(time['master_seed'].unique())} independent seeds into {args.output}")


if __name__ == "__main__":
    main()
