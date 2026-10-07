"""Historical parent-family labels remain explicit after site consolidation."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def test_legacy_h36_parent_classification_is_preserved_and_corrected():
    index = (DOCS / "index.html").read_text(encoding="utf-8")
    summary = (DOCS / "executive-summary.html").read_text(encoding="utf-8")
    erratum = (ROOT / "evidence/h36_parent_classification_erratum_20261007.json").read_text(encoding="utf-8")
    for page in (index, summary):
        assert "H36-1 rung30" in page
        assert "H19-5/rung-30 repacking" in page
        assert "not the actual tip/step-over" in page
        assert "h36_parent_classification_erratum_20261007.json" in page
    assert "H33-D is the explicit tip/step-over parent" in erratum


def test_radedge_negative_result_is_linked_from_current_site():
    index = (DOCS / "index.html").read_text(encoding="utf-8")
    summary = (DOCS / "executive-summary.html").read_text(encoding="utf-8")
    report = (DOCS / "research/holdout-h53-radedge-results-20261007.md").read_text(encoding="utf-8")
    assert "research/holdout-h53-radedge-results-20261007.md" in index
    assert "research/holdout-h53-radedge-results-20261007.md" in summary
    assert "GEMSDOE48-H53-DS-RadEdge-B2xH33D-4c01fcf2ad8c" in report
    assert "H53-RadEdge-1 fails the preregistered promotion gate" in report
    assert "Do not spend a weekly submission slot" in report
    assert "explicitly identified tip/step-over construction" in report


def test_executive_summary_separates_future_plan_from_failed_candidates():
    text = (DOCS / "executive-summary.html").read_text(encoding="utf-8")
    assert "Five unbuilt hypotheses" in text
    assert "No new geological detector was implemented" in text
    assert "no weekly slot unless an idea first beats" in text
    assert "public proxy" in text.lower()
