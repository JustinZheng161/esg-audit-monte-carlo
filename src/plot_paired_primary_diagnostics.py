"""Plot paired firm-versus-two-way rejection-rate differences from aggregate synthetic outputs."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot paired cluster-method rejection differences.")
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    table = pd.read_csv(args.table)
    labels = table["scenario"].tolist()
    values = table["two_way_minus_firm"].to_numpy()
    lower = (values - table["paired_difference_ci95_low"].to_numpy())
    upper = (table["paired_difference_ci95_high"].to_numpy() - values)

    fig, ax = plt.subplots(figsize=(8.5, 4.8), constrained_layout=True)
    positions = range(len(table))
    ax.errorbar(positions, values, yerr=[lower, upper], fmt="o", color="black", capsize=5, linewidth=1.3)
    ax.axhline(0, color="0.4", linestyle="--", linewidth=1)
    ax.set_xticks(list(positions), labels)
    ax.set_ylabel("Two-way minus firm rejection frequency")
    ax.set_title("Paired cluster-method difference in the synthetic primary DGP")
    ax.text(0.01, 0.01, "Points are paired means; bars are normal-approximation 95% Monte Carlo intervals.",
            transform=ax.transAxes, fontsize=8, va="bottom")
    ax.set_ylim(min(-0.01, float(table["paired_difference_ci95_low"].min()) - 0.01),
                float(table["paired_difference_ci95_high"].max()) + 0.01)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=220)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
