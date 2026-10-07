from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def test_legacy_lidar_h53_is_explicitly_labeled_as_h36_not_tip_family():
    text = (DOCS / "index.html").read_text(encoding="utf-8")
    assert "H36-1 rung30" in text
    assert "not</b> the actual tip/step-over family" in text
    assert "not as a test of B2 × H33-D" in text
    assert "h36_parent_classification_erratum_20261007.json" in text


def test_radedge_landing_card_offers_unique_tiff_and_disclaims_upload():
    text = (DOCS / "index.html").read_text(encoding="utf-8")
    assert 'id="h53-radedge"' in text
    assert 'GEMSDOE48-H53-DS-RadEdge-B2xH33D-20261007-4c01fcf2ad8c-nan-outside.tif' in text
    assert 'GEMSDOE48-H53-DS-RadEdge-B2xH33D-4c01fcf2ad8c' in text
    assert "research only; gate failed" in text
    assert "H33-D, the explicitly identified tip/step-over parent" in text


def test_executive_summary_separates_future_steps_from_failed_candidates():
    text = (DOCS / "executive-summary.html").read_text(encoding="utf-8")
    assert 'id="h53-radedge"' in text
    assert "Do not spend a weekly slot" in text
    assert "future cleared candidate only" in text
    assert "H36-1 rung30" in text
    assert "not the actual tip/step-over family" in text
