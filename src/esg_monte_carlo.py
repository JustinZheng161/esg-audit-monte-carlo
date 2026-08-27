"""Reproducible Monte Carlo diagnostics for ESG, audit quality and investment inefficiency.

The program generates only synthetic firms. It is not an empirical ESG data set and
must not be interpreted as evidence concerning real firms. Model choices are read from
config/dgp.yaml and every run writes tables, figures and a provenance manifest.
"""
from __future__ import annotations

import argparse
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
import yaml

ROOT = Path(__file__).resolve().parents[1]


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -35, 35)))


def pvalue_normal(t: float) -> float:
    return math.erfc(abs(float(t)) / math.sqrt(2.0))


def mcse(p: float, repetitions: int) -> float:
    return float(math.sqrt(max(p * (1 - p), 0.0) / repetitions))


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def demean_matrix(values: np.ndarray, groups: list[np.ndarray], max_iter: int = 200) -> np.ndarray:
    """Alternating-projection demeaning for one or more high-dimensional fixed effects."""
    out = np.asarray(values, dtype=float).copy()
    for _ in range(max_iter):
        before = out.copy()
        for group in groups:
            _, inverse = np.unique(group, return_inverse=True)
            count = np.bincount(inverse).astype(float)
            sums = np.zeros((count.size, out.shape[1]), dtype=float)
            np.add.at(sums, inverse, out)
            out -= sums[inverse] / count[inverse, None]
        if np.max(np.abs(out - before)) < 1e-10:
            break
    return out


def one_way_covariance(x: np.ndarray, residual: np.ndarray, group: np.ndarray, correction: bool = True) -> np.ndarray:
    """CR1 covariance estimator for the OLS coefficient after fixed-effect residualization."""
    n, k = x.shape
    _, inverse = np.unique(group, return_inverse=True)
    clusters = int(inverse.max() + 1)
    scores = np.zeros((clusters, k), dtype=float)
    np.add.at(scores, inverse, x * residual[:, None])
    bread = np.linalg.pinv(x.T @ x)
    cov = bread @ (scores.T @ scores) @ bread
    if correction and clusters > 1 and n > k:
        cov *= (clusters / (clusters - 1)) * ((n - 1) / (n - k))
    return cov


def two_way_covariance(x: np.ndarray, residual: np.ndarray, firm: np.ndarray, year: np.ndarray) -> np.ndarray:
    """Cameron-Gelbach-Miller inclusion-exclusion covariance, with non-negative diagonal safeguard."""
    cell = np.asarray([f"{f}:{y}" for f, y in zip(firm, year)], dtype=object)
    cov = (one_way_covariance(x, residual, firm)
           + one_way_covariance(x, residual, year)
           - one_way_covariance(x, residual, cell, correction=False))
    diagonal = np.maximum(np.diag(cov), 1e-14)
    return cov - np.diag(np.diag(cov)) + np.diag(diagonal)


def fit_fe_ols(y: np.ndarray, x: np.ndarray, fe_groups: list[np.ndarray], firm: np.ndarray, year: np.ndarray,
               covariance: str = "firm") -> dict:
    stacked = np.column_stack([y, x])
    residualized = demean_matrix(stacked, fe_groups)
    yd, xd = residualized[:, 0], residualized[:, 1:]
    beta = np.linalg.pinv(xd.T @ xd) @ (xd.T @ yd)
    residual = yd - xd @ beta
    if covariance == "firm":
        cov = one_way_covariance(xd, residual, firm)
    elif covariance == "two_way":
        cov = two_way_covariance(xd, residual, firm, year)
    else:
        raise ValueError(f"Unknown covariance type: {covariance}")
    se = np.sqrt(np.maximum(np.diag(cov), 1e-14))
    t_values = beta / se
    p_values = np.array([pvalue_normal(t) for t in t_values])
    return {"beta": beta, "se": se, "t": t_values, "p": p_values, "residual": residual, "yd": yd, "xd": xd}


def simulate_panel(seed: int, n_firms: int, effect_scale: float, cfg: dict) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    years = np.asarray(cfg["project"]["years"], dtype=int)
    t_count = len(years)
    industries = int(cfg["panel"]["industries"])
    base_sigma = float(cfg["simulation"]["base_sigma"])
    full = cfg["simulation"]["full_effect"]
    beta_esg = effect_scale * float(full["esg_log_sd"])
    beta_inter = effect_scale * float(full["esg_big4_log_sd"])

    firm = np.arange(n_firms)
    industry = rng.integers(0, industries, size=n_firms)
    quality = rng.normal(0, 1, size=n_firms)
    opportunity = rng.normal(0, 1, size=n_firms)
    size_latent = rng.normal(0, 1, size=n_firms)
    risk = rng.normal(0, 1, size=n_firms)
    network = rng.binomial(1, sigmoid(-0.1 + 0.25 * (industry - (industries - 1) / 2.0)))
    firm_effect = 0.006 * opportunity + rng.normal(0, 0.004, size=n_firms)
    age0 = rng.integers(3, 36, size=n_firms)

    esg = np.empty((n_firms, t_count), dtype=float)
    esg[:, 0] = np.clip(60 + 5.0 * quality + 0.35 * (industry - (industries - 1) / 2.0)
                        + rng.normal(0, 3.8, n_firms), 0, 100)
    for t in range(1, t_count):
        esg[:, t] = np.clip(
            60 + float(cfg["simulation"]["esg_persistence"]) * (esg[:, t - 1] - 60)
            + 0.90 * quality + 0.35 * (industry - (industries - 1) / 2.0) + 0.55 * t
            + rng.normal(0, float(cfg["simulation"]["esg_innovation_sd"]), n_firms),
            float(cfg["simulation"]["esg_lower"]), float(cfg["simulation"]["esg_upper"]),
        )

    rows: list[dict] = []
    e_std = (esg - esg.mean()) / esg.std(ddof=0)
    prior_investment = np.full(n_firms, 0.12)
    # The variance DGP is deliberately indexed by the *lagged* ESG and Big Four
    # status used in the second-stage regression. This prevents a timing mismatch
    # from being mistaken for lack of statistical power.
    big4_previous = rng.binomial(1, sigmoid(-2.80 + 0.90 * quality + 0.25 * size_latent
                                             + 0.06 * ((esg[:, 0] - 60) / 10.0)
                                             - 0.15 * risk + 0.35 * 0.04 + 0.70 * network))
    for t, year in enumerate(years):
        q = 1.25 + 0.45 * opportunity + 0.18 * quality + 0.06 * t + rng.normal(0, 0.30, n_firms)
        growth = 0.06 + 0.10 * opportunity + 0.02 * quality + rng.normal(0, 0.08, n_firms)
        cash = sigmoid(-1.00 + 0.24 * quality - 0.22 * risk + rng.normal(0, 0.50, n_firms))
        leverage = sigmoid(-0.25 + 0.34 * risk - 0.10 * quality + rng.normal(0, 0.45, n_firms))
        roa = 0.04 + 0.025 * quality - 0.012 * risk + rng.normal(0, 0.018, n_firms)
        cfo_assets = 0.045 + 0.050 * roa + 0.018 * opportunity + rng.normal(0, 0.018, n_firms)
        big4_p = sigmoid(-2.80 + 0.90 * quality + 0.25 * size_latent + 0.06 * ((esg[:, t] - 60) / 10.0)
                         - 0.15 * risk + 0.35 * roa + 0.70 * network)
        big4 = rng.binomial(1, big4_p)
        normal_investment = (0.025 + 0.075 * growth + 0.23 * cfo_assets + 0.070 * q + 0.035 * cash
                             - 0.018 * leverage + 0.004 * industry + 0.035 * prior_investment
                             + firm_effect + 0.001 * t)
        lag_index = max(t - 1, 0)
        log_sigma = (math.log(base_sigma) + beta_esg * e_std[:, lag_index]
                     + beta_inter * e_std[:, lag_index] * big4_previous)
        true_deviation = rng.normal(0, np.exp(log_sigma))
        investment = normal_investment + true_deviation
        for i in range(n_firms):
            rows.append({
                "firm": int(firm[i]), "year": int(year), "industry": int(industry[i]),
                "quality": float(quality[i]), "opportunity": float(opportunity[i]), "risk": float(risk[i]),
                "network": int(network[i]), "firm_age": int(age0[i] + t), "esg": float(esg[i, t]),
                "big4": int(big4[i]), "q": float(q[i]), "growth": float(growth[i]), "cash": float(cash[i]),
                "leverage": float(leverage[i]), "roa": float(roa[i]), "cfo_assets": float(cfo_assets[i]),
                "investment": float(investment[i]), "true_deviation": float(true_deviation[i]),
            })
        prior_investment = investment
        big4_previous = big4
    df = pd.DataFrame(rows).sort_values(["firm", "year"]).reset_index(drop=True)
    df["investment_lag"] = df.groupby("firm")["investment"].shift(1)
    df["esg_lag"] = df.groupby("firm")["esg"].shift(1)
    df["big4_lag"] = df.groupby("firm")["big4"].shift(1)
    df["esg_lead"] = df.groupby("firm")["esg"].shift(-1)
    return df


def second_stage_data(df: pd.DataFrame, include_esg_first_stage: bool = False, missingness: bool = False,
                      seed: int | None = None) -> pd.DataFrame:
    use = df.dropna(subset=["investment_lag", "esg_lag", "big4_lag", "esg_lead"]).copy()
    # First stage: expected investment, industry-by-year fixed effects.
    x_cols = ["growth", "cfo_assets", "q", "cash", "leverage", "firm_age", "investment_lag"]
    if include_esg_first_stage:
        x_cols.append("esg_lag")
    y = use["investment"].to_numpy()
    x = use[x_cols].to_numpy()
    group = (use["industry"].astype(str) + "_" + use["year"].astype(str)).to_numpy()
    first = fit_fe_ols(y, x, [group], use["firm"].to_numpy(), use["year"].to_numpy(), "firm")
    use["expected_investment"] = y - first["residual"]
    use["inefficiency"] = np.abs(first["residual"])
    use["log_inefficiency"] = np.log(np.maximum(use["inefficiency"], 1e-8))
    use["oracle_log_abs_deviation"] = np.log(np.maximum(np.abs(use["true_deviation"]), 1e-8))
    use["industry_year"] = use["industry"].astype(str) + "_" + use["year"].astype(str)
    if missingness:
        rng = np.random.default_rng(seed)
        p_miss = sigmoid(-2.4 - 0.5 * use["quality"].to_numpy() + 0.45 * use["risk"].to_numpy())
        use = use.loc[rng.uniform(size=len(use)) > p_miss].copy()
    return use.reset_index(drop=True)


def circular_shift_by_firm(df: pd.DataFrame, column: str, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    shifted = np.empty(len(df), dtype=float)
    for _, index in df.groupby("firm", sort=False).groups.items():
        index = np.asarray(list(index), dtype=int)
        values = df.loc[index, column].to_numpy()
        offset = int(rng.integers(1, len(values)))
        shifted[index] = np.roll(values, offset)
    return shifted


def fit_second_stage(use: pd.DataFrame, outcome: str = "log_inefficiency", exposure: str = "esg_lag",
                     covariance: str = "firm", placebo_seed: int | None = None) -> dict:
    local = use.copy()
    if exposure == "circular_esg":
        if placebo_seed is None:
            raise ValueError("placebo_seed is required for circular ESG placebo")
        local["exposure"] = circular_shift_by_firm(local, "esg_lag", placebo_seed)
    elif exposure == "lead_esg":
        local["exposure"] = local["esg_lead"].to_numpy()
    else:
        local["exposure"] = local["esg_lag"].to_numpy()
    local["exposure_z"] = (local["exposure"] - local["exposure"].mean()) / local["exposure"].std(ddof=0)
    local["interaction"] = local["exposure_z"] * local["big4_lag"]
    y = local[outcome].to_numpy()
    x = local[["exposure_z", "big4_lag", "interaction"]].to_numpy()
    return fit_fe_ols(y, x, [local["firm"].to_numpy(), local["industry_year"].to_numpy()],
                      local["firm"].to_numpy(), local["year"].to_numpy(), covariance)


def restricted_wild_cluster_bootstrap(fit: dict, firm: np.ndarray, replications: int, seed: int) -> float:
    """Restricted Rademacher wild cluster bootstrap-t p-value for the interaction coefficient.

    The coefficient bread, firm inverse index, and CR1 correction are invariant over
    bootstrap draws and are cached outside the inner loop. This preserves the
    statistic while avoiding repeated decompositions and group encoding; see the
    computational rationale for fast wild bootstrap implementations in Roodman et
    al. (2019), https://doi.org/10.1177/1536867X19830877.
    """
    rng = np.random.default_rng(seed)
    xd, yd = fit["xd"], fit["yd"]
    x_restricted = xd[:, :2]
    beta_restricted = np.linalg.pinv(x_restricted.T @ x_restricted) @ (x_restricted.T @ yd)
    residual_restricted = yd - x_restricted @ beta_restricted
    restricted_mean = x_restricted @ beta_restricted
    observed_t = float(fit["t"][2])
    _, inverse = np.unique(firm, return_inverse=True)
    clusters = int(inverse.max() + 1)
    n, k = xd.shape
    bread = np.linalg.pinv(xd.T @ xd)
    cr1_correction = (clusters / (clusters - 1)) * ((n - 1) / (n - k))
    extreme = 0
    for _ in range(replications):
        weights = rng.choice(np.array([-1.0, 1.0]), size=clusters)
        y_star = restricted_mean + residual_restricted * weights[inverse]
        beta = bread @ (xd.T @ y_star)
        residual = y_star - xd @ beta
        scores = np.zeros((clusters, k), dtype=float)
        np.add.at(scores, inverse, xd * residual[:, None])
        covariance = bread @ (scores.T @ scores) @ bread * cr1_correction
        se = math.sqrt(max(covariance[2, 2], 1e-14))
        t_star = beta[2] / se
        extreme += int(abs(t_star) >= abs(observed_t))
    return float((extreme + 1) / (replications + 1))


def one_replication(seed: int, n_firms: int, effect_scale: float, cfg: dict, wild_reps: int = 0) -> dict:
    df = simulate_panel(seed, n_firms, effect_scale, cfg)
    use = second_stage_data(df)
    main = fit_second_stage(use, covariance="firm")
    twoway = fit_second_stage(use, covariance="two_way")
    result = {
        "p_firm": float(main["p"][2]), "p_two_way": float(twoway["p"][2]),
        "beta_interaction": float(main["beta"][2]), "n_obs": int(len(use)),
    }
    if wild_reps:
        result["p_wild_firm"] = restricted_wild_cluster_bootstrap(
            main, use["firm"].to_numpy(), wild_reps, seed + 907
        )
    return result


def monte_carlo(label: str, n_firms: int, effect_scale: float, repetitions: int, base_seed: int, cfg: dict,
                wild_reps: int = 0) -> dict:
    seeds = np.random.SeedSequence(base_seed).spawn(repetitions)
    results = [one_replication(int(s.generate_state(1)[0]), n_firms, effect_scale, cfg, wild_reps) for s in seeds]
    p_firm = np.array([r["p_firm"] for r in results])
    p_two = np.array([r["p_two_way"] for r in results])
    reject = float(np.mean(p_firm < 0.05))
    reject_two = float(np.mean(p_two < 0.05))
    wild_reject = float(np.mean([r["p_wild_firm"] < 0.05 for r in results])) if wild_reps else np.nan
    return {
        "scenario": label, "firms": n_firms, "effect_scale": effect_scale, "repetitions": repetitions,
        "firm_rejection_5pct": reject, "firm_mcse": mcse(reject, repetitions),
        "two_way_rejection_5pct": reject_two, "two_way_mcse": mcse(reject_two, repetitions),
        "wild_firm_rejection_5pct": wild_reject,
        "wild_firm_mcse": mcse(wild_reject, repetitions) if wild_reps else np.nan,
        "wild_bootstrap_draws": wild_reps,
        "mean_interaction": float(np.mean([r["beta_interaction"] for r in results])),
        "mean_n_obs": float(np.mean([r["n_obs"] for r in results])),
    }


def make_figures(null_df: pd.DataFrame, alt_df: pd.DataFrame, summary: pd.DataFrame, figure_dir: Path) -> None:
    figure_dir.mkdir(parents=True, exist_ok=True)
    for title, df, filename in [("Null scenario", null_df, "figure_a1_null_diagnostics.png"),
                                ("Alternative scenario", alt_df, "figure_a2_alternative_diagnostics.png")]:
        use = second_stage_data(df)
        fig, axes = plt.subplots(1, 3, figsize=(12, 3.5), constrained_layout=True)
        panels = [("Lagged ESG", use["esg_lag"], "#4C78A8"), ("Investment rate", use["investment"], "#72B7B2"),
                  ("Estimated inefficiency", use["inefficiency"], "#F58518")]
        for ax, (label, values, color) in zip(axes, panels):
            ax.hist(values, bins=30, color=color, edgecolor="white")
            ax.set_title(label, fontsize=10)
            ax.set_ylabel("Frequency")
        fig.suptitle(f"{title}: distribution diagnostics", fontsize=12)
        fig.savefig(figure_dir / filename, dpi=600, bbox_inches="tight")
        plt.close(fig)
    power = summary.loc[summary["effect_scale"] > 0].copy()
    fig, ax = plt.subplots(figsize=(6.5, 4.0), constrained_layout=True)
    for n, group in power.groupby("firms"):
        group = group.sort_values("effect_scale")
        ax.plot(group["effect_scale"], group["firm_rejection_5pct"], marker="o", label=f"N={n}")
    ax.axhline(0.05, color="black", linestyle="--", linewidth=1, label="Nominal size")
    ax.set_xlabel("Alternative-effect scale")
    ax.set_ylabel("Rejection probability at 5%")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False)
    ax.set_title("Power by sample size and effect scale")
    fig.savefig(figure_dir / "figure_1_power_curve.png", dpi=600, bbox_inches="tight")
    plt.close(fig)


def write_manifest(output_dir: Path, cfg: dict, args: argparse.Namespace) -> None:
    config_bytes = (ROOT / "config" / "dgp.yaml").read_bytes()
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__, "pandas": pd.__version__, "matplotlib": matplotlib.__version__,
        "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
        "base_seed": int(cfg["project"]["seed"]),
        "primary_repetitions": int(args.reps), "sensitivity_repetitions": int(args.sensitivity_reps),
        "bootstrap_replications": int(args.bootstrap_reps),
        "scope": "Synthetic DGP only. No record denotes a real firm or supports a substantive ESG claim.",
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run reproducible ESG Monte Carlo diagnostic experiments.")
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "dgp.yaml")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs")
    parser.add_argument("--reps", type=int, default=None, help="Primary N=300 repetitions.")
    parser.add_argument("--sensitivity-reps", type=int, default=None, help="N=100/N=500 and robustness repetitions.")
    parser.add_argument("--bootstrap-reps", type=int, default=None, help="Wild bootstrap draws for the representative run.")
    parser.add_argument("--seed", type=int, default=None, help="Override the configured master seed for an independent replication.")
    args = parser.parse_args()
    cfg = load_config(args.config)
    if args.seed is not None:
        cfg["project"]["seed"] = int(args.seed)
    args.reps = args.reps or int(cfg["simulation"]["primary_repetitions"])
    args.sensitivity_reps = args.sensitivity_reps or int(cfg["simulation"]["sensitivity_repetitions"])
    args.bootstrap_reps = args.bootstrap_reps or int(cfg["simulation"]["bootstrap_replications"])
    output = args.output
    table_dir, figure_dir = output / "tables", output / "figures"
    table_dir.mkdir(parents=True, exist_ok=True)

    seed = int(cfg["project"]["seed"])
    primary_n = int(cfg["panel"]["primary_firms"])
    rows = [
        monte_carlo("Null", primary_n, 0.0, args.reps, seed + 11, cfg),
        monte_carlo("Half alternative", primary_n, 0.5, args.reps, seed + 12, cfg),
        monte_carlo("Full alternative", primary_n, 1.0, args.reps, seed + 13, cfg),
        monte_carlo("Null", int(cfg["panel"]["small_firms"]), 0.0, args.sensitivity_reps, seed + 14, cfg),
        monte_carlo("Full alternative", int(cfg["panel"]["small_firms"]), 1.0, args.sensitivity_reps, seed + 15, cfg),
        monte_carlo("Null", int(cfg["panel"]["large_firms"]), 0.0, args.sensitivity_reps, seed + 16, cfg),
        monte_carlo("Full alternative", int(cfg["panel"]["large_firms"]), 1.0, args.sensitivity_reps, seed + 17, cfg),
        # Finite-sample inference calibration: 300 independently simulated draws
        # with a restricted Rademacher wild cluster bootstrap-t at the firm level.
        monte_carlo("Null (wild bootstrap diagnostic)", primary_n, 0.0, args.sensitivity_reps, seed + 18, cfg, args.bootstrap_reps),
        monte_carlo("Full alternative (wild bootstrap diagnostic)", primary_n, 1.0, args.sensitivity_reps, seed + 19, cfg, args.bootstrap_reps),
    ]
    summary = pd.DataFrame(rows)
    summary.to_csv(table_dir / "table_2_monte_carlo_operating_characteristics.csv", index=False)

    null_df = simulate_panel(seed + 100, primary_n, 0.0, cfg)
    alt_df = simulate_panel(seed + 101, primary_n, 1.0, cfg)
    single_rows = []
    for scenario, df in [("Null", null_df), ("Full alternative", alt_df)]:
        use = second_stage_data(df)
        for model, exposure in [("Main", "esg_lag"), ("Firm-block circular placebo", "circular_esg"), ("Lead placebo", "lead_esg")]:
            fit = fit_second_stage(use, exposure=exposure, placebo_seed=seed + len(single_rows) + 200)
            single_rows.append({"scenario": scenario, "model": model, "n_obs": len(use),
                                "esg_coefficient": fit["beta"][0], "esg_pvalue": fit["p"][0],
                                "interaction_coefficient": fit["beta"][2], "interaction_pvalue": fit["p"][2]})
    pd.DataFrame(single_rows).to_csv(table_dir / "table_1_representative_draws.csv", index=False)

    base_use = second_stage_data(alt_df)
    main_fit = fit_second_stage(base_use)
    wild_p = restricted_wild_cluster_bootstrap(main_fit, base_use["firm"].to_numpy(), args.bootstrap_reps, seed + 300)
    robust_rows = []
    for name, data, outcome in [
        ("Main log absolute residual", base_use, "log_inefficiency"),
        ("Raw absolute residual", base_use, "inefficiency"),
        ("Oracle log true deviation", base_use, "oracle_log_abs_deviation"),
        ("First stage includes lagged ESG", second_stage_data(alt_df, include_esg_first_stage=True), "log_inefficiency"),
        ("MAR-like ESG missingness", second_stage_data(alt_df, missingness=True, seed=seed + 301), "log_inefficiency"),
    ]:
        fit = fit_second_stage(data, outcome=outcome)
        robust_rows.append({"diagnostic": name, "n_obs": len(data), "interaction_coefficient": fit["beta"][2],
                            "firm_clustered_se": fit["se"][2], "firm_clustered_pvalue": fit["p"][2]})
    robust_rows.append({"diagnostic": f"Restricted Rademacher wild bootstrap-t ({args.bootstrap_reps} draws)",
                        "n_obs": len(base_use), "interaction_coefficient": main_fit["beta"][2],
                        "firm_clustered_se": main_fit["se"][2], "firm_clustered_pvalue": wild_p})
    pd.DataFrame(robust_rows).to_csv(table_dir / "table_3_robustness_and_ablation.csv", index=False)

    null_df.head(3000).to_csv(ROOT / "data" / "public" / "synthetic_example_null.csv", index=False)
    make_figures(null_df, alt_df, summary, figure_dir)
    write_manifest(output, cfg, args)
    print(f"Completed {len(summary)} Monte Carlo scenarios. Outputs: {output}")


if __name__ == "__main__":
    main()
