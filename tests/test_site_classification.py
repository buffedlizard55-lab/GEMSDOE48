"""Classification and archive-link contracts for older candidate records.

H36/H51/H53 experiments remain reproducible history, but they must not be
promoted back onto the current download landing page as current candidates.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EVIDENCE = ROOT / "evidence"


def test_h49_machine_receipts_do_not_recommend_slot_clearance():
    for path in sorted((DOCS / "data").glob("h49*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        status = data.get("historical_evidence_status", data.get("validity_status", ""))
        assert status, f"{path.name} lacks a historical validity label"
        assert "HISTORICAL" in status or "INVALIDATED" in status, path.name
        assert data.get("promotion_use", "").startswith("NONE"), path.name
    proxy = json.loads((DOCS / "data/h49-quadrant-proxy.json").read_text(encoding="utf-8"))
    assert proxy["gate_pass"] is True  # preserve its dated, protocol-specific proxy result
    assert proxy["legacy_submission_slot_recommendation"] == "CLEARED ON PROXY ONLY - see docs/data/h49-instrument-calibration.json before spending a slot"
    assert proxy["submission_slot_recommendation"].startswith("NOT CLEARED TO SUBMIT")


def test_legacy_h36_parent_is_correctly_distinguished_from_h33d_tip_family():
    archive = (DOCS / "research.html").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    erratum = json.loads((EVIDENCE / "h36_parent_classification_erratum_20261007.json").read_text())
    assert "h36_parent_classification_erratum_20261007.json" in archive
    assert "H36-1 rung30 is not the actual tip/step-over family H33-D" in archive
    assert "H36-1 rung30 is not the tip/step-over family" in readme
    assert "H33-D is the explicit tip/step-over surface" in erratum["correction"]
    assert "CLASSIFICATION_CORRECTED" in erratum["status"]
    assert "H53-RadEdge-1" in erratum["impact"]["h53_radedge_1"]


def test_h53_radedge_is_retained_as_archival_failed_research_not_current_cta():
    archive = (DOCS / "research.html").read_text(encoding="utf-8")
    current_index = (DOCS / "index.html").read_text(encoding="utf-8")
    report = (DOCS / "research/holdout-h53-radedge-results-20261007.md").read_text(encoding="utf-8")
    build = json.loads((EVIDENCE / "build_h53_radedge_receipt_20261007.json").read_text())
    holdout = json.loads((EVIDENCE / "holdout_h53_radedge_20261007.json").read_text())
    path = ROOT / build["candidate"]["path"]
    assert "research/holdout-h53-radedge-results-20261007.md" in archive
    assert "archive only" in archive.lower()
    assert "H53-RadEdge-1 fails the preregistered promotion gate" in report
    assert "H33-D" in report and "radiometric-edge" in report
    assert build["current_disposition"] == "FAILED_PREREGISTERED_PROXY_GATE_NO_SLOT"
    assert build["candidate"]["slot_cleared"] is False
    assert holdout["preregistered_gate"]["passes_preregistered_proxy_gate"] is False
    assert holdout["slot_decision"]["cleared"] is False
    assert path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == build["candidate"]["sha256"]
    # The current landing page deliberately features H56B only; historical H53
    # details remain reachable through the research archive and README.
    assert "H53-DS-RadEdge" not in current_index
    assert "NOT CLEARED TO SUBMIT" in current_index


def test_executive_summary_separates_failed_candidates_from_future_guidance():
    text = (DOCS / "executive-summary.html").read_text(encoding="utf-8")
    assert "NO WEEKLY SUBMISSION SLOT IS CLEARED" in text
    assert "H57-A" in text and "H56-F" in text
    assert "fails combined gate" in text
    assert "Steps for a future submission after clearance" in text
    assert "Do not upload H56B" in text
    assert "future submission" in text.lower()
