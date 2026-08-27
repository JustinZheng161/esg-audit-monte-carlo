"""Minimal deterministic checks for the ESG Monte Carlo replication pipeline."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from esg_monte_carlo import (  # noqa: E402
    fit_second_stage,
    load_config,
    mcse,
    one_way_covariance,
    restricted_wild_cluster_bootstrap,
    second_stage_data,
    simulate_panel,
)


def legacy_wild_bootstrap(fit, firm, replications, seed):
    """Pre-optimization reference calculation for equivalence testing."""
    import math
    rng = np.random.default_rng(seed)
    xd, yd = fit["xd"], fit["yd"]
    restricted_x = xd[:, :2]
    restricted_beta = np.linalg.pinv(restricted_x.T @ restricted_x) @ (restricted_x.T @ yd)
    restricted_residual = yd - restricted_x @ restricted_beta
    observed_t = float(fit["t"][2])
    _, inverse = np.unique(firm, return_inverse=True)
    extreme = 0
    for _ in range(replications):
        weights = rng.choice(np.array([-1.0, 1.0]), size=int(inverse.max() + 1))
        y_star = restricted_x @ restricted_beta + restricted_residual * weights[inverse]
        beta = np.linalg.pinv(xd.T @ xd) @ (xd.T @ y_star)
        residual = y_star - xd @ beta
        se = math.sqrt(max(one_way_covariance(xd, residual, firm)[2, 2], 1e-14))
        extreme += int(abs(beta[2] / se) >= abs(observed_t))
    return float((extreme + 1) / (replications + 1))


def main() -> None:
    cfg = load_config(ROOT / "config" / "dgp.yaml")
    required_dgp_sections = {"latent_variables", "esg", "big4_selection", "covariates", "investment_equation", "log_sigma_mapping"}
    assert required_dgp_sections.issubset(cfg["dgp"]), "DGP parameter disclosure is incomplete."
    assert cfg["dgp"]["esg"]["persistence"] == 0.95
    assert cfg["dgp"]["log_sigma_mapping"]["full_alternative"]["esg_big4_log_sd"] == -0.12
    df = simulate_panel(seed=314159, n_firms=30, effect_scale=1.0, cfg=cfg)
    assert len(df) == 30 * len(cfg["project"]["years"])
    assert df["firm"].nunique() == 30
    assert df["year"].nunique() == len(cfg["project"]["years"])
    assert df.groupby("firm")["investment_lag"].apply(lambda s: s.isna().sum()).eq(1).all()

    analysis = second_stage_data(df)
    assert len(analysis) == 30 * (len(cfg["project"]["years"]) - 2)
    assert analysis["year"].min() == cfg["project"]["years"][1]
    assert analysis["year"].max() == cfg["project"]["years"][-2]
    assert sorted(analysis["year"].unique().tolist()) == cfg["estimation"]["analysis_years"]
    assert np.isfinite(analysis[["inefficiency", "log_inefficiency", "esg_lag"]].to_numpy()).all()
    assert mcse(0.05, 1000) == np.sqrt(0.05 * 0.95 / 1000)

    # The mechanism ablation preserves selection/ESG streams but removes only the
    # Big Four direct variance interaction from the synthetic DGP.
    selection_only = simulate_panel(seed=314159, n_firms=30, effect_scale=1.0, cfg=cfg, big4_variance_scale=0.0)
    assert np.array_equal(df["big4"].to_numpy(), selection_only["big4"].to_numpy())
    assert np.array_equal(df["esg"].to_numpy(), selection_only["esg"].to_numpy())
    assert not np.array_equal(df["true_deviation"].to_numpy(), selection_only["true_deviation"].to_numpy())

    fitted = fit_second_stage(analysis, covariance="firm")
    assert fitted["beta"].shape == (3,)
    assert np.isfinite(fitted["beta"]).all()
    assert np.isfinite(fitted["se"]).all()
    assert np.all((fitted["p"] >= 0) & (fitted["p"] <= 1))

    firm = analysis["firm"].to_numpy()
    wild_p = restricted_wild_cluster_bootstrap(fitted, firm, replications=19, seed=271828)
    legacy_p = legacy_wild_bootstrap(fitted, firm, replications=19, seed=271828)
    assert 0 < wild_p <= 1
    assert wild_p == legacy_p, "Caching optimization changed the wild-bootstrap p-value."
    print("Pipeline tests passed.")


if __name__ == "__main__":
    main()
