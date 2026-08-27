"""Corrected-sample-flow Big Four mechanism ablation for round-two revision.

The two scenarios retain the same synthetic Big Four logistic selection equation.
Only the direct Big Four multiplier in the lagged residual-variance interaction is
changed. Results are diagnostic properties of the specified DGP, not evidence about
real auditors or ESG assurance.
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

from esg_monte_carlo import fit_second_stage, load_config, mcse, second_stage_data, simulate_panel

ROOT = Path(__file__).resolve().parents[1]


def seeds(master_seed: int, repetitions: int) -> list[int]:
    return [int(seed.generate_state(1)[0]) for seed in np.random.SeedSequence(master_seed).spawn(repetitions)]


def summarize(rows: list[dict], label: dict) -> dict:
    frame = pd.DataFrame(rows)
    repetitions = len(frame)
    firm_rate = float((frame["p_firm"] < 0.05).mean())
    two_way_rate = float((frame["p_two_way"] < 0.05).mean())
    return {
        **label,
        "repetitions": repetitions,
        "mean_second_stage_n": float(frame["n_obs"].mean()),
        "mean_interaction": float(frame["interaction_coefficient"].mean()),
        "mcse_mean_interaction": float(frame["interaction_coefficient"].std(ddof=1) / math.sqrt(repetitions)),
        "firm_rejection_5pct": firm_rate,
        "firm_mcse": mcse(firm_rate, repetitions),
        "two_way_rejection_5pct": two_way_rate,
        "two_way_mcse": mcse(two_way_rate, repetitions),
    }


def plot(table: pd.DataFrame, destination: Path) -> None:
    x = np.arange(len(table))
    width = 0.36
    fig, ax = plt.subplots(figsize=(7.8, 4.3), constrained_layout=True)
    ax.bar(x - width / 2, table["firm_rejection_5pct"], width, label="Firm-clustered", color="#4C78A8")
    ax.bar(x + width / 2, table["two_way_rejection_5pct"], width, label="Two-way firm–year", color="#E45756")
    ax.axhline(0.05, color="black", linewidth=1, linestyle="--", label="Nominal 5% size")
    ax.set_xticks(x, ["Direct variance\nrole retained", "Selection-only\n(direct role = 0)"])
    ax.set_ylabel("Interaction rejection probability")
    ax.set_title("Big Four mechanism ablation in the synthetic DGP")
    ax.legend(frameon=False)
    fig.savefig(destination, dpi=600, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run corrected-sample-flow Big Four mechanism ablation.")
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "dgp.yaml")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reps", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()

    cfg = load_config(args.config)
    settings = [
        ("Full alternative: direct Big Four variance role retained", 1.0),
        ("Selection-only: direct Big Four variance role set to zero", 0.0),
    ]
    summary_rows, replicate_rows = [], []
    for index, (scenario, multiplier) in enumerate(settings):
        rows = []
        label = {"scenario": scenario, "big4_variance_scale": multiplier}
        for replication, rep_seed in enumerate(seeds(int(args.seed) + 7000 + index, int(args.reps)), start=1):
            panel = simulate_panel(rep_seed, int(cfg["panel"]["primary_firms"]), 1.0, cfg,
                                   big4_variance_scale=multiplier)
            use = second_stage_data(panel, cfg=cfg)
            firm = fit_second_stage(use, covariance="firm")
            two_way = fit_second_stage(use, covariance="two_way")
            result = {
                "n_obs": len(use),
                "interaction_coefficient": float(firm["beta"][2]),
                "p_firm": float(firm["p"][2]),
                "p_two_way": float(two_way["p"][2]),
            }
            rows.append(result)
            replicate_rows.append({**label, "replication": replication, **result})
        summary_rows.append(summarize(rows, label))

    output = args.output
    tables, figures, replicates = output / "tables", output / "figures", output / "replication_level"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    replicates.mkdir(parents=True, exist_ok=True)
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(tables / "table_9_big4_mechanism_ablation.csv", index=False)
    pd.DataFrame(replicate_rows).to_csv(replicates / "big4_mechanism_replicates.csv", index=False)
    plot(summary, figures / "figure_3_big4_mechanism_ablation.png")
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "master_seed": int(args.seed),
        "outer_repetitions_per_scenario": int(args.reps),
        "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
        "python": sys.version,
        "platform": platform.platform(),
        "scope": "Synthetic DGP only; both scenarios retain the Big Four selection equation. No real-company data are used, calibrated, or implied.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Completed corrected Big Four mechanism ablation with {args.reps} repetitions per scenario: {output}")


if __name__ == "__main__":
    main()
