"""Pool paired primary diagnostic records across independent master seeds.

The paired Monte Carlo standard error is computed from the within-replication
indicator difference, preserving the dependence between firm-clustered and
two-way test decisions on the same synthetic panel draw.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd


def paired_summary(frame: pd.DataFrame) -> dict:
    repetitions = len(frame)
    difference = frame["two_way_minus_firm"]
    diff_mean = float(difference.mean())
    diff_mcse = float(difference.std(ddof=1) / math.sqrt(repetitions))
    return {
        "scenario": frame["scenario"].iloc[0],
        "firms": int(frame["firms"].iloc[0]),
        "effect_scale": float(frame["effect_scale"].iloc[0]),
        "independent_master_seeds": int(frame["master_seed"].nunique()),
        "combined_outer_repetitions": repetitions,
        "firm_rejection_5pct": float(frame["reject_firm_5pct"].mean()),
        "two_way_rejection_5pct": float(frame["reject_two_way_5pct"].mean()),
        "two_way_minus_firm": diff_mean,
        "paired_difference_mcse": diff_mcse,
        "paired_difference_ci95_low": diff_mean - 1.96 * diff_mcse,
        "paired_difference_ci95_high": diff_mean + 1.96 * diff_mcse,
        "both_reject_count": int(((frame["reject_firm_5pct"] == 1) & (frame["reject_two_way_5pct"] == 1)).sum()),
        "firm_only_reject_count": int(((frame["reject_firm_5pct"] == 1) & (frame["reject_two_way_5pct"] == 0)).sum()),
        "two_way_only_reject_count": int(((frame["reject_firm_5pct"] == 0) & (frame["reject_two_way_5pct"] == 1)).sum()),
        "neither_reject_count": int(((frame["reject_firm_5pct"] == 0) & (frame["reject_two_way_5pct"] == 0)).sum()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate paired synthetic primary diagnostics.")
    parser.add_argument("--seed-dirs", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    frames = [pd.read_csv(directory / "replication-level" / "primary-paired-replicates.csv") for directory in args.seed_dirs]
    pooled = pd.concat(frames, ignore_index=True)
    expected = ["Null", "Half alternative", "Full alternative"]
    summaries = [paired_summary(pooled.loc[pooled["scenario"] == scenario].copy()) for scenario in expected]
    table = pd.DataFrame(summaries)
    destination = args.output / "tables" / "table-14-paired-cluster-method-difference.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(destination, index=False)
    (args.output / "manifest-paired-aggregate.json").write_text(json.dumps({
        "source_seed_dirs": [str(path) for path in args.seed_dirs],
        "paired_mcse": "sample standard deviation of I(two_way reject) - I(firm reject), divided by sqrt(combined outer repetitions)",
        "ci": "normal approximation difference ± 1.96 * paired_difference_mcse",
        "scope": "Synthetic DGP only; aggregate table is public-safe, source replication-level rows remain private.",
    }, indent=2), encoding="utf-8")
    print(f"Wrote paired aggregate table to {destination}")


if __name__ == "__main__":
    main()
