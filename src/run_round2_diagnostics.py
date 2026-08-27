"""Second-round reviewer diagnostics for the synthetic ESG Monte Carlo study.

All observations are synthetic. The script tests four conditional properties of the
specified DGP: (1) time-cluster performance under alternative persistence and
heteroskedasticity mechanisms, (2) the mapping from DGP log-SD parameters to
second-stage log-absolute-residual coefficients, (3) two directional selective-
availability stresses, and (4) first-stage fixed-effect sensitivity. It does not
calibrate, estimate, or make claims about real-company ESG coverage or audit quality.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from esg_monte_carlo import (
    fit_second_stage,
    fit_second_stage_prepared,
    load_config,
    mcse,
    prepare_second_stage,
    second_stage_data,
    simulate_panel,
)

ROOT = Path(__file__).resolve().parents[1]


def set_year_dimension(cfg: dict, analysis_time_clusters: int) -> dict:
    """Copy config so a common lag/lead protocol yields the requested clusters."""
    local = copy.deepcopy(cfg)
    start = int(local["project"]["years"][0])
    total_years = int(analysis_time_clusters) + 2
    years = list(range(start, start + total_years))
    local["project"]["years"] = years
    local["estimation"]["analysis_years"] = years[1:-1]
    return local


def seeds(master_seed: int, repetitions: int) -> list[int]:
    return [int(s.generate_state(1)[0]) for s in np.random.SeedSequence(master_seed).spawn(repetitions)]


def safe_covariance(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 2:
        return float("nan")
    return float(np.cov(x, y, ddof=1)[0, 1])


def basic_second_stage_result(df: pd.DataFrame, cfg: dict, *, availability: str = "complete",
                              first_stage_fe: str = "industry_year", availability_seed: int | None = None,
                              include_oracle: bool = False) -> dict:
    """Estimate the interaction using estimated residuals and, when requested, true DGP deviations."""
    use = second_stage_data(df, availability=availability, seed=availability_seed, first_stage_fe=first_stage_fe, cfg=cfg)
    prepared = prepare_second_stage(use)
    firm = fit_second_stage_prepared(prepared, covariance="firm")
    two_way = fit_second_stage_prepared(prepared, covariance="two_way")
    raw_interaction = ((use["esg_lag"] - use["esg_lag"].mean()) / use["esg_lag"].std(ddof=0)) * use["big4_lag"]
    first_stage_error = use["first_stage_residual"].to_numpy() - use["true_deviation"].to_numpy()
    result = {
        "n_obs": len(use),
        "beta_interaction": float(firm["beta"][2]),
        "p_firm": float(firm["p"][2]),
        "p_two_way": float(two_way["p"][2]),
        "error_interaction_covariance": safe_covariance(first_stage_error, raw_interaction.to_numpy()),
    }
    if include_oracle:
        oracle_firm = fit_second_stage_prepared(prepared, outcome="oracle_log_abs_deviation", covariance="firm")
        oracle_two_way = fit_second_stage_prepared(prepared, outcome="oracle_log_abs_deviation", covariance="two_way")
        result.update({
            "oracle_beta_interaction": float(oracle_firm["beta"][2]),
            "oracle_p_firm": float(oracle_firm["p"][2]),
            "oracle_p_two_way": float(oracle_two_way["p"][2]),
        })
    return result


def summarize_binary(rows: list[dict], label: dict) -> dict:
    """Summarize replicate-level diagnostics without discarding their audit trail."""
    frame = pd.DataFrame(rows)
    repetitions = len(frame)
    firm_rate = float((frame["p_firm"] < 0.05).mean())
    two_rate = float((frame["p_two_way"] < 0.05).mean())
    summary = {
        **label,
        "repetitions": repetitions,
        "mean_second_stage_n": float(frame["n_obs"].mean()),
        "mean_beta_interaction": float(frame["beta_interaction"].mean()),
        "mcse_beta_interaction": float(frame["beta_interaction"].std(ddof=1) / math.sqrt(repetitions)),
        "firm_rejection_5pct": firm_rate,
        "firm_mcse": mcse(firm_rate, repetitions),
        "two_way_rejection_5pct": two_rate,
        "two_way_mcse": mcse(two_rate, repetitions),
        "mean_error_interaction_covariance": float(frame["error_interaction_covariance"].mean()),
    }
    if "oracle_beta_interaction" in frame:
        oracle_firm_rate = float((frame["oracle_p_firm"] < 0.05).mean())
        oracle_two_rate = float((frame["oracle_p_two_way"] < 0.05).mean())
        summary.update({
            "mean_oracle_beta_interaction": float(frame["oracle_beta_interaction"].mean()),
            "mcse_oracle_beta_interaction": float(frame["oracle_beta_interaction"].std(ddof=1) / math.sqrt(repetitions)),
            "oracle_firm_rejection_5pct": oracle_firm_rate,
            "oracle_firm_mcse": mcse(oracle_firm_rate, repetitions),
            "oracle_two_way_rejection_5pct": oracle_two_rate,
            "oracle_two_way_mcse": mcse(oracle_two_rate, repetitions),
        })
    return summary


def first_stage_fe_design_diagnostics(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Classical descriptive joint-F/partial-R2 diagnostics for first-stage FE blocks."""
    x_cols = ["growth", "cfo_assets", "q", "cash", "leverage", "firm_age", "investment_lag"]
    y = df["investment"].to_numpy()
    base = np.column_stack([np.ones(len(df)), df[x_cols].to_numpy()])
    beta_base, *_ = np.linalg.lstsq(base, y, rcond=None)
    ssr_base = float(np.sum((y - base @ beta_base) ** 2))
    rows = []
    for spec in cfg["review_round2"]["first_stage_fe_sensitivity"]["specifications"]:
        extras: list[np.ndarray] = []
        if spec == "industry_year":
            group = df["industry"].astype(str) + "_" + df["year"].astype(str)
            extras.append(pd.get_dummies(group, drop_first=True, dtype=float).to_numpy())
        elif spec == "industry_plus_year":
            extras.extend([
                pd.get_dummies(df["industry"], drop_first=True, dtype=float).to_numpy(),
                pd.get_dummies(df["year"], drop_first=True, dtype=float).to_numpy(),
            ])
        elif spec != "none":
            raise ValueError(f"Unknown first-stage FE specification: {spec}")
        design = np.column_stack([base, *extras]) if extras else base
        beta, *_ = np.linalg.lstsq(design, y, rcond=None)
        ssr_full = float(np.sum((y - design @ beta) ** 2))
        rank_base = int(np.linalg.matrix_rank(base))
        rank_full = int(np.linalg.matrix_rank(design))
        added_df = rank_full - rank_base
        residual_df = len(y) - rank_full
        partial_r2 = 0.0 if ssr_base == 0 else max(0.0, (ssr_base - ssr_full) / ssr_base)
        joint_f = float("nan") if added_df == 0 or residual_df <= 0 else ((ssr_base - ssr_full) / added_df) / (ssr_full / residual_df)
        rows.append({
            "first_stage_fe": spec,
            "n_first_stage": len(y),
            "added_fe_df": added_df,
            "joint_f_descriptive": joint_f,
            "partial_r2_fe_block": partial_r2,
            "ssr_without_fe": ssr_base,
            "ssr_with_fe": ssr_full,
        })
    return pd.DataFrame(rows)


def run_time_structure(cfg: dict, repetitions: int, master_seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    settings = cfg["review_round2"]["time_structure"]
    rows, replicate_rows = [], []
    offset = 1000
    for clusters in settings["analysis_time_clusters"]:
        local = set_year_dimension(cfg, int(clusters))
        for persistence in settings["esg_persistence_values"]:
            for variance_scale in settings["residual_variance_esg_scales"]:
                results = []
                for seed in seeds(master_seed + offset, repetitions):
                    df = simulate_panel(seed, int(local["panel"]["primary_firms"]), 0.0, local,
                                        esg_persistence_override=float(persistence),
                                        esg_effect_scale=float(variance_scale),
                                        interaction_effect_scale=0.0)
                    results.append(basic_second_stage_result(df, local))
                label = {
                    "analysis_time_clusters": int(clusters),
                    "dgp_years": int(clusters) + 2,
                    "esg_persistence": float(persistence),
                    "esg_variance_scale": float(variance_scale),
                    "first_stage_n": int(local["panel"]["primary_firms"]) * (int(clusters) + 2),
                    "second_stage_n": int(local["panel"]["primary_firms"]) * int(clusters),
                }
                rows.append(summarize_binary(results, label))
                replicate_rows.extend([{**label, "replication": replication + 1, **result}
                                       for replication, result in enumerate(results)])
                offset += 1
    return (pd.DataFrame(rows).sort_values(["analysis_time_clusters", "esg_variance_scale", "esg_persistence"]),
            pd.DataFrame(replicate_rows))


def run_scale_mapping(cfg: dict, repetitions: int, master_seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    full = cfg["dgp"]["log_sigma_mapping"]["full_alternative"]
    rows, replicate_rows = [], []
    offset = 3000
    for firms in cfg["review_round2"]["scale_mapping"]["firm_counts"]:
        for effect_scale in cfg["review_round2"]["scale_mapping"]["effect_scales"]:
            oracle_beta, estimated_beta = [], []
            for seed in seeds(master_seed + offset, repetitions):
                df = simulate_panel(seed, int(firms), float(effect_scale), cfg)
                use = second_stage_data(df, cfg=cfg)
                # Use the DGP-standardized lagged exposure without re-standardizing it
                # to identify the oracle log-|u*| population mapping on the DGP scale.
                oracle = fit_second_stage(use, outcome="oracle_log_abs_deviation", exposure="dgp_esg_z_lag", covariance="firm", standardize_exposure=False)
                estimated = fit_second_stage(use, outcome="log_inefficiency", exposure="dgp_esg_z_lag", covariance="firm", standardize_exposure=False)
                oracle_beta.append(float(oracle["beta"][2]))
                estimated_beta.append(float(estimated["beta"][2]))
            gamma_inter = float(effect_scale) * float(full["esg_big4_log_sd"])
            label = {
                "firms": int(firms),
                "effect_scale": float(effect_scale),
                "repetitions": repetitions,
                "gamma_inter_log_sd": gamma_inter,
            }
            rows.append({
                **label,
                "mean_oracle_beta3_log_abs_true_deviation": float(np.mean(oracle_beta)),
                "mcse_oracle_beta3": float(np.std(oracle_beta, ddof=1) / math.sqrt(repetitions)),
                "mean_estimated_beta3_log_abs_residual": float(np.mean(estimated_beta)),
                "mcse_estimated_beta3": float(np.std(estimated_beta, ddof=1) / math.sqrt(repetitions)),
                "oracle_minus_gamma": float(np.mean(oracle_beta) - gamma_inter),
                "estimated_minus_oracle": float(np.mean(estimated_beta) - np.mean(oracle_beta)),
            })
            replicate_rows.extend([{**label, "replication": replication + 1,
                                    "oracle_beta3_log_abs_true_deviation": o,
                                    "estimated_beta3_log_abs_residual": e}
                                   for replication, (o, e) in enumerate(zip(oracle_beta, estimated_beta))])
            offset += 1
    return pd.DataFrame(rows).sort_values(["firms", "effect_scale"]), pd.DataFrame(replicate_rows)


def run_availability(cfg: dict, repetitions: int, master_seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, replicate_rows = [], []
    labels = [
        ("Complete synthetic panel", "complete"),
        ("Adverse selective-availability stress", "adverse_selective"),
        ("Coverage-aligned selective-availability stress", "coverage_aligned"),
    ]
    for index, (label, availability) in enumerate(labels):
        results = []
        for rep_seed in seeds(master_seed + 4000 + index, repetitions):
            df = simulate_panel(rep_seed, int(cfg["panel"]["primary_firms"]), 1.0, cfg)
            results.append(basic_second_stage_result(df, cfg, availability=availability, availability_seed=rep_seed + 7919))
        condition = {"availability_scenario": label, "availability_code": availability}
        rows.append(summarize_binary(results, condition))
        replicate_rows.extend([{**condition, "replication": replication + 1, **result}
                               for replication, result in enumerate(results)])
    return pd.DataFrame(rows), pd.DataFrame(replicate_rows)


def run_first_stage_fe(cfg: dict, repetitions: int, master_seed: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows, replicate_rows = [], []
    for index, specification in enumerate(cfg["review_round2"]["first_stage_fe_sensitivity"]["specifications"]):
        results = []
        for rep_seed in seeds(master_seed + 5000 + index, repetitions):
            df = simulate_panel(rep_seed, int(cfg["panel"]["primary_firms"]), 1.0, cfg)
            results.append(basic_second_stage_result(df, cfg, first_stage_fe=specification, include_oracle=True))
        condition = {"first_stage_fe": specification}
        rows.append(summarize_binary(results, condition))
        replicate_rows.extend([{**condition, "replication": replication + 1, **result}
                               for replication, result in enumerate(results)])
    representative = simulate_panel(master_seed + 5999, int(cfg["panel"]["primary_firms"]), 1.0, cfg)
    return pd.DataFrame(rows), first_stage_fe_design_diagnostics(representative, cfg), pd.DataFrame(replicate_rows)


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
    parser = argparse.ArgumentParser(description="Run round-two synthetic reviewer diagnostics.")
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "dgp.yaml")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reps", type=int, default=None, help="Outer repetitions per condition and seed.")
    parser.add_argument("--seed", type=int, required=True, help="Independent master seed.")
    args = parser.parse_args()
    cfg = load_config(args.config)
    reps = int(args.reps or cfg["review_round2"]["extension_repetitions_per_seed"])
    output = args.output
    tables, figures = output / "tables", output / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    time_structure, time_replicates = run_time_structure(cfg, reps, int(args.seed))
    scale_mapping, scale_replicates = run_scale_mapping(cfg, reps, int(args.seed))
    availability, availability_replicates = run_availability(cfg, reps, int(args.seed))
    fe_sensitivity, fe_design, fe_replicates = run_first_stage_fe(cfg, reps, int(args.seed))
    time_structure.to_csv(tables / "table_10_time_structure_sensitivity.csv", index=False)
    scale_mapping.to_csv(tables / "table_11_scale_mapping.csv", index=False)
    availability.to_csv(tables / "table_12_selective_availability.csv", index=False)
    fe_sensitivity.to_csv(tables / "table_13_first_stage_fe_sensitivity.csv", index=False)
    fe_design.to_csv(tables / "table_a3_first_stage_fe_design_diagnostics.csv", index=False)
    replicate_dir = output / "replication_level"
    replicate_dir.mkdir(parents=True, exist_ok=True)
    time_replicates.to_csv(replicate_dir / "time_structure_replicates.csv", index=False)
    scale_replicates.to_csv(replicate_dir / "scale_mapping_replicates.csv", index=False)
    availability_replicates.to_csv(replicate_dir / "availability_replicates.csv", index=False)
    fe_replicates.to_csv(replicate_dir / "first_stage_fe_replicates.csv", index=False)
    plot_time_structure(time_structure, figures / "figure_4_time_structure_sensitivity.png")
    plot_scale_mapping(scale_mapping, figures / "figure_5_scale_mapping.png")
    plot_availability(availability, figures / "figure_6_selective_availability.png")

    config_bytes = args.config.read_bytes()
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "master_seed": int(args.seed),
        "outer_repetitions_per_condition": reps,
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "python": sys.version,
        "platform": platform.platform(),
        "scope": "Synthetic DGP diagnostics only; no real-company data are used, calibrated, or implied.",
        "experiments": ["time_structure", "scale_mapping", "selective_availability", "first_stage_fe_sensitivity"],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Completed round-two diagnostics with {reps} repetitions per condition. Outputs: {output}")


if __name__ == "__main__":
    main()
