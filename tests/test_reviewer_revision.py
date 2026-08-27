"""Deterministic checks for first-round reviewer revision artifacts."""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT.parent
POOLED = ROOT / "outputs" / "reviewer_diagnostics_pooled"
DOCX = AUDIT / "private" / "manuscript" / "ESG_Audit_InvestmentEfficiency_round1_revised_anonymous.docx"


def main() -> None:
    time = pd.read_csv(POOLED / "table_6_time_cluster_diagnostics_pooled.csv").sort_values("analysis_time_clusters")
    assert time["analysis_time_clusters"].tolist() == [8, 18, 28]
    assert time["dgp_years"].tolist() == [10, 20, 30]
    assert time["first_stage_n"].tolist() == [3000, 6000, 9000]
    assert time["second_stage_n"].tolist() == [2400, 5400, 8400]
    assert time["total_repetitions"].tolist() == [1000, 1000, 1000]
    for _, row in time.iterrows():
        expected = math.sqrt(row["two_way_rejection_5pct"] * (1 - row["two_way_rejection_5pct"]) / row["total_repetitions"])
        assert math.isclose(row["two_way_rejection_5pct_pooled_mcse"], expected, rel_tol=1e-12)
    assert time.loc[time["analysis_time_clusters"] == 28, "two_way_rejection_5pct"].item() < time.loc[time["analysis_time_clusters"] == 8, "two_way_rejection_5pct"].item()

    big4 = pd.read_csv(POOLED / "table_7_big4_mechanism_ablation_pooled.csv").sort_values("big4_variance_scale")
    assert big4["big4_variance_scale"].tolist() == [0.0, 1.0]
    assert big4["total_repetitions"].tolist() == [1000, 1000]
    assert big4["second_stage_n"].tolist() == [2400, 2400]
    selection_only = big4.loc[big4["big4_variance_scale"] == 0.0].iloc[0]
    retained = big4.loc[big4["big4_variance_scale"] == 1.0].iloc[0]
    assert abs(selection_only["mean_interaction"]) < 0.01
    assert retained["firm_rejection_5pct"] > selection_only["firm_rejection_5pct"]

    for name in ["figure_2_time_cluster_size_pooled.png", "figure_3_big4_mechanism_ablation_pooled.png"]:
        assert (POOLED / "figures" / name).is_file()

    # The editable anonymous manuscript is intentionally private. When the test is
    # executed in the author-controlled repository, it additionally audits the
    # DOCX wording; a public clean clone verifies only releasable code and outputs.
    if DOCX.is_file():
        document = Document(DOCX)
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        for required in [
            "300 × 8 = 2,400", "Table 3. Observation flow", "sqrt[p̂(1−p̂)/R]",
            "selection-only ablation", "[Author name(s) withheld for review]",
            "No real-company financial, ESG, audit, regulatory, or commercial data",
        ]:
            assert required in text, f"Missing required manuscript revision: {required}"
        for forbidden in ["manuscript editing assistance", "five-company SEC Company Facts metadata snapshot"]:
            assert forbidden not in text, f"Deprecated manuscript wording remains: {forbidden}"
        assert "N=2,000" not in text, "Main effective N remains ambiguous in manuscript text."
        print("Reviewer-revision tests passed, including private anonymous-manuscript audit.")
    else:
        print("Reviewer-revision tests passed; private anonymous-manuscript audit skipped in public clone.")


if __name__ == "__main__":
    main()
