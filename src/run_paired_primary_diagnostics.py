"""Generate paired primary-scenario replication records for cluster-method comparisons.

Each row retains the firm-clustered and two-way firm-year test outcomes from the
same synthetic panel replication. The output is designed for a paired difference
in rejection frequencies; it is not an empirical firm-level data set.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from esg_monte_carlo import load_config, one_replication

ROOT = Path(__file__).resolve().parents[1]


def replication_seeds(master_seed: int, repetitions: int) -> list[int]:
    """Return deterministic, non-overlapping child seeds for outer repetitions."""
    return [int(child.generate_state(1)[0]) for child in np.random.SeedSequence(master_seed).spawn(repetitions)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run paired primary cluster-method diagnostics on the synthetic DGP.")
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "dgp.yaml")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True, help="Independent master seed.")
    parser.add_argument("--reps", type=int, default=None, help="Outer repetitions per primary scenario.")
    args = parser.parse_args()

    cfg = load_config(args.config)
    repetitions = int(args.reps or cfg["simulation"]["primary_repetitions"])
    firms = int(cfg["panel"]["primary_firms"])
    scenarios = [("Null", 0.0, 11), ("Half alternative", 0.5, 12), ("Full alternative", 1.0, 13)]
    rows: list[dict] = []
    for label, effect_scale, offset in scenarios:
        for replication, rep_seed in enumerate(replication_seeds(int(args.seed) + offset, repetitions), start=1):
            result = one_replication(rep_seed, firms, effect_scale, cfg)
            firm_reject = int(result["p_firm"] < 0.05)
            two_way_reject = int(result["p_two_way"] < 0.05)
            rows.append({
                "master_seed": int(args.seed),
                "scenario": label,
                "firms": firms,
                "effect_scale": effect_scale,
                "replication": replication,
                "replication_seed": rep_seed,
                "p_firm": result["p_firm"],
                "p_two_way": result["p_two_way"],
                "reject_firm_5pct": firm_reject,
                "reject_two_way_5pct": two_way_reject,
                "two_way_minus_firm": two_way_reject - firm_reject,
                "beta_interaction": result["beta_interaction"],
                "n_obs": result["n_obs"],
            })
    destination = args.output / "replication_level" / "primary_paired_replicates.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(destination, index=False)
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "master_seed": int(args.seed),
        "outer_repetitions_per_scenario": repetitions,
        "scenarios": [scenario[0] for scenario in scenarios],
        "paired_definition": "two_way_minus_firm = I(p_two_way < 0.05) - I(p_firm < 0.05) within the same outer replication",
        "config_sha256": hashlib.sha256(args.config.read_bytes()).hexdigest(),
        "python": sys.version,
        "platform": platform.platform(),
        "scope": "Synthetic DGP only; records must remain private because they are replication-level audit outputs.",
    }
    (args.output / "manifest_paired_primary.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} paired synthetic replication records to {destination}")


if __name__ == "__main__":
    main()
