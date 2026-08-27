"""Aggregate independent Monte Carlo runs without mixing their scenario definitions."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def pooled_mcse(p: float, n: int) -> float:
    return float(np.sqrt(p * (1.0 - p) / n))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_a", type=Path)
    parser.add_argument("run_b", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    a, b = pd.read_csv(args.run_a), pd.read_csv(args.run_b)
    a["run"] = "Seed 20260827"
    b["run"] = "Seed 20260828"
    combined = pd.concat([a, b], ignore_index=True)
    summary_rows = []
    for (scenario, firms, effect_scale), group in combined.groupby(["scenario", "firms", "effect_scale"], sort=False):
        row = {"scenario": scenario, "firms": int(firms), "effect_scale": float(effect_scale),
               "runs": int(group["run"].nunique()), "repetitions": int(group["repetitions"].sum())}
        for metric in ["firm_rejection_5pct", "two_way_rejection_5pct", "wild_firm_rejection_5pct", "mean_interaction"]:
            valid = group[[metric, "repetitions"]].dropna()
            if valid.empty:
                row[metric] = np.nan
                row[f"{metric}_pooled_mcse"] = np.nan
            elif metric == "mean_interaction":
                row[metric] = float(np.average(valid[metric], weights=valid["repetitions"]))
                row[f"{metric}_pooled_mcse"] = np.nan
            else:
                p = float(np.average(valid[metric], weights=valid["repetitions"]))
                n = int(valid["repetitions"].sum())
                row[metric] = p
                row[f"{metric}_pooled_mcse"] = pooled_mcse(p, n)
        summary_rows.append(row)
    result = pd.DataFrame(summary_rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
