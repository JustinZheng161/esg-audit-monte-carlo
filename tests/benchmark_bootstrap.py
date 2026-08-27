"""Non-public microbenchmark for verifying the cached wild-bootstrap implementation."""
import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from esg_monte_carlo import (  # noqa: E402
    fit_second_stage,
    load_config,
    one_way_covariance,
    restricted_wild_cluster_bootstrap,
    second_stage_data,
    simulate_panel,
)


def legacy(fit, firm, replications, seed):
    rng = np.random.default_rng(seed)
    xd, yd = fit["xd"], fit["yd"]
    xr = xd[:, :2]
    br = np.linalg.pinv(xr.T @ xr) @ (xr.T @ yd)
    er = yd - xr @ br
    observed_t = float(fit["t"][2])
    _, inverse = np.unique(firm, return_inverse=True)
    extreme = 0
    for _ in range(replications):
        weights = rng.choice(np.array([-1.0, 1.0]), size=int(inverse.max() + 1))
        ys = xr @ br + er * weights[inverse]
        beta = np.linalg.pinv(xd.T @ xd) @ (xd.T @ ys)
        residual = ys - xd @ beta
        se = math.sqrt(max(one_way_covariance(xd, residual, firm)[2, 2], 1e-14))
        extreme += int(abs(beta[2] / se) >= abs(observed_t))
    return float((extreme + 1) / (replications + 1))


def main():
    cfg = load_config(ROOT / "config" / "dgp.yaml")
    data = second_stage_data(simulate_panel(20260902, 300, 1.0, cfg))
    fit = fit_second_stage(data)
    firm = data["firm"].to_numpy()
    reps, seed = 399, 20260903
    start = time.perf_counter()
    old = legacy(fit, firm, reps, seed)
    legacy_seconds = time.perf_counter() - start
    start = time.perf_counter()
    new = restricted_wild_cluster_bootstrap(fit, firm, reps, seed)
    cached_seconds = time.perf_counter() - start
    assert old == new
    print(f"legacy_seconds={legacy_seconds:.6f}")
    print(f"cached_seconds={cached_seconds:.6f}")
    print(f"speedup={legacy_seconds / cached_seconds:.3f}x")
    print(f"pvalue={new:.6f}")


if __name__ == "__main__":
    main()
