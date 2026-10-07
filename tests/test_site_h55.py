"""H55 history remains auditable without publishing retracted score bounds as fact."""
from __future__ import annotations

import hashlib
import json
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
RECEIPT_PATH = REPO / "evidence/build_h55_receipt_20261007.json"
PAGES = [
    "index.html", "executive-summary.html", "submission-guide.html", "method.html",
    "hypotheses.html", "validation.html", "irregularities.html", "sources.html",
    "next-steps.html", "leaderboard.html",
]


def receipt() -> dict:
    return json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))


def test_historical_h55_artifact_remains_reproducibly_pinned():
    data = receipt()
    info = data["files"]["primary_zeros_outside"]
    path = REPO / info["path"]
    assert path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == info["sha256"]
    assert info["all_cells_finite"] is True
    assert info["all_cells_in_range_0_1"] is True
    assert info["portal_range_error_immune"] is True
    assert info["encoding"] == "all_finite_zeros_outside"
    assert "H55" in data["submission_name"]


def test_h55_is_historical_not_the_featured_or_recommended_download():
    primary_name = pathlib.Path(receipt()["files"]["primary_zeros_outside"]["path"]).name
    for name in ("index.html", "executive-summary.html"):
        text = (DOCS / name).read_text(encoding="utf-8")
        assert primary_name not in text
        assert "historical" in text.lower()
        assert "weekly slot" in text.lower()
    executive = (DOCS / "executive-summary.html").read_text(encoding="utf-8")
    assert "research/h55-live-model-ceiling-and-candidate-20261007.md" in executive


def test_invalid_h55_score_projection_and_ceiling_are_explicitly_retracted():
    report = (DOCS / "research/h55-live-model-ceiling-and-candidate-20261007.md").read_text(encoding="utf-8")
    assert "CORRECTION" in report
    assert "FPw = S - TPw" in report
    assert "private-label bounds" in report
    assert "not score predictions" in report
    assert "No weekly slot is cleared" in report
    assert "Some binary maximizer exists" in report or "some binary maximizer exists" in report
    erratum = (DOCS / "research/metric-identity-erratum-20261007.md").read_text(encoding="utf-8")
    assert "FPw = S − Q" in erratum or "FPw = S - Q" in erratum
    assert "0.2843" in report
    assert "generally false under the official metric" in report


def test_current_decision_pages_do_not_turn_historical_values_into_predictions():
    for name in PAGES:
        text = (DOCS / name).read_text(encoding="utf-8").lower()
        if "0.0649" in text or "0.2843" in text:
            assert any(word in text for word in ("invalid", "historical", "retracted", "superseded")), name
    index = (DOCS / "index.html").read_text(encoding="utf-8")
    assert "metric-identity-erratum-20261007.md" in index
    assert "invalid as score bounds" in index


def test_h55_error_ledger_is_preserved_without_promoting_its_old_gate():
    html = (DOCS / "irregularities.html").read_text(encoding="utf-8")
    markdown = (DOCS / "irregularities.md").read_text(encoding="utf-8")
    for i in range(1, 11):
        tag = f"IR-H55-{i:02d}"
        assert tag in html
        assert tag in markdown
    assert "FPw=S−TPw" in markdown
    assert "not supportable" in markdown.lower()


def test_h55_diagnostic_files_are_still_receipted():
    data = receipt()
    diagnostics = data["files"]["diagnostics"]
    assert diagnostics
    for info in diagnostics.values():
        path = REPO / info["path"]
        assert path.is_file(), info["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == info["sha256"]
