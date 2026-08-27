"""Unit tests for paired firm-versus-two-way rejection diagnostics."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from aggregate_paired_primary_diagnostics import paired_summary  # noqa: E402


def main() -> None:
    frame = pd.DataFrame({
        "scenario": ["Null"] * 4,
        "firms": [300] * 4,
        "effect_scale": [0.0] * 4,
        "master_seed": [1, 1, 2, 2],
        "reject_firm_5pct": [0, 1, 0, 1],
        "reject_two_way_5pct": [1, 1, 0, 0],
        "two_way_minus_firm": [1, 0, 0, -1],
    })
    summary = paired_summary(frame)
    assert summary["combined_outer_repetitions"] == 4
    assert summary["independent_master_seeds"] == 2
    assert summary["firm_rejection_5pct"] == 0.5
    assert summary["two_way_rejection_5pct"] == 0.5
    assert summary["two_way_minus_firm"] == 0.0
    assert round(summary["paired_difference_mcse"], 12) == round((2 / 3) ** 0.5 / 2, 12)
    assert (summary["both_reject_count"], summary["firm_only_reject_count"], summary["two_way_only_reject_count"], summary["neither_reject_count"]) == (1, 1, 1, 1)
    assert summary["paired_difference_ci95_low"] < 0 < summary["paired_difference_ci95_high"]
    print("Paired primary diagnostic tests passed.")


if __name__ == "__main__":
    main()
