"""Minimal deterministic checks for the ESG Monte Carlo replication pipeline."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from esg_monte_carlo import (  # noqa: E402
    fit_second_stage,
    load_config,
    restricted_wild_cluster_bootstrap,
    second_stage_data,
    simulate_panel,
)


def main() -> None:
    cfg = load_config(ROOT / "config" / "dgp.yaml")
    df = simulate_panel(seed=314159, n_firms=30, effect_scale=1.0, cfg=cfg)
    assert len(df) == 30 * len(cfg["project"]["years"])
    assert df["firm"].nunique() == 30
    assert df["year"].nunique() == len(cfg["project"]["years"])
    assert df.groupby("firm")["investment_lag"].apply(lambda s: s.isna().sum()).eq(1).all()

    analysis = second_stage_data(df)
    assert len(analysis) == 30 * (len(cfg["project"]["years"]) - 2)
    assert np.isfinite(analysis[["inefficiency", "log_inefficiency", "esg_lag"]].to_numpy()).all()

    fitted = fit_second_stage(analysis, covariance="firm")
    assert fitted["beta"].shape == (3,)
    assert np.isfinite(fitted["beta"]).all()
    assert np.isfinite(fitted["se"]).all()
    assert np.all((fitted["p"] >= 0) & (fitted["p"] <= 1))

    wild_p = restricted_wild_cluster_bootstrap(fitted, analysis["firm"].to_numpy(), replications=19, seed=271828)
    assert 0 < wild_p <= 1
    print("Pipeline tests passed.")


if __name__ == "__main__":
    main()
