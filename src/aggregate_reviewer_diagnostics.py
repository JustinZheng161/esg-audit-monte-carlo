"""Aggregate two independent reviewer-diagnostic runs without mixing conditions."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def pooled_rate_and_mcse(group: pd.DataFrame, metric: str) -> tuple[float, float]:
    weights = group["repetitions"].to_numpy(dtype=float)
    values = group[metric].to_numpy(dtype=float)
    rate = float(np.average(values, weights=weights))
    total_repetitions = int(weights.sum())
    return rate, float(np.sqrt(rate * (1.0 - rate) / total_repetitions))


def aggregate(inputs: list[Path], table_name: str, keys: list[str]) -> pd.DataFrame:
    frames = []
    for path in inputs:
        frame = pd.read_csv(path / "tables" / table_name)
        frame["source_run"] = path.name
        frames.append(frame)
    combined = pd.concat(frames, ignore_index=True)
    rows = []
    metrics = ["firm_rejection_5pct", "two_way_rejection_5pct"]
    for key, group in combined.groupby(keys, dropna=False, sort=True):
        key_values = key if isinstance(key, tuple) else (key,)
        row = dict(zip(keys, key_values))
        row["independent_runs"] = int(group["source_run"].nunique())
        row["total_repetitions"] = int(group["repetitions"].sum())
        for metric in metrics:
            rate, se = pooled_rate_and_mcse(group, metric)
            row[metric] = rate
            row[f"{metric}_pooled_mcse"] = se
        for column in ["mean_interaction", "mean_n_obs", "first_stage_n", "second_stage_n", "dgp_years", "analysis_time_clusters", "big4_variance_scale", "effect_scale"]:
            if column in group.columns:
                row[column] = group[column].iloc[0]
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pool independent reviewer diagnostics.")
    parser.add_argument("run_a", type=Path)
    parser.add_argument("run_b", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    inputs = [args.run_a, args.run_b]
    time = aggregate(inputs, "table_6_time_cluster_diagnostics.csv", ["dgp_years", "analysis_time_clusters"])
    big4 = aggregate(inputs, "table_7_big4_mechanism_ablation.csv", ["scenario", "big4_variance_scale"])
    time.to_csv(args.output / "table_6_time_cluster_diagnostics_pooled.csv", index=False)
    big4.to_csv(args.output / "table_7_big4_mechanism_ablation_pooled.csv", index=False)
    print(f"Pooled {len(time)} time-cluster and {len(big4)} Big Four rows to {args.output}")


if __name__ == "__main__":
    main()
