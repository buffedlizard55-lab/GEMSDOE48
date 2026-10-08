"""Current site contract after reconciling the H58-A branch with H59 main.

Tests preserve the explicit no-slot rule, distinguish downloads from submission
permission, and ensure local file predicates are never presented as organizer
portal acceptance.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

H59_TIF = "gemsdoe48-h59-cover-ds-belief-b2xh33d-20261008T184547Z-b79c4c61d8d8.tif"
H59_SHA256 = "f1584187b459baf47f75e5daf64de6f7696f9feb14910d3cf2762f7a1119597a"
H58A_TIF = "GEMSDOE48-H58-OWDS-POSONLY-B2xH33D-20261008-fdbb83476756-zeros-outside.tif"
H58A_SHA256 = "bbd289dd545cd772af3a88631b43233569dcbf4815c69bc5479a53fd73ca3973"
H59_RECEIPT = ROOT / "evidence/build_h59_receipt_20261008T184547Z.json"
RECONCILIATION = ROOT / "evidence/submission_gate_reconciliation_20261008.json"
ACTIVE_PAGES = (
    "index.html", "executive-summary.html", "submission-guide.html", "validation.html",
    "hypotheses.html", "leaderboard.html", "irregularities.html", "sources.html",
    "next-steps.html", "research.html", "status.html",
)


def _read(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


def test_no_submission_slot_is_cleared_in_current_records():
    rec = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
    assert rec["decision"]["status"] == "NO_SUBMISSION_SLOT_CLEARED"
    assert rec["decision"]["submission_made_this_session"] is False
    assert rec["decision"]["weekly_limit_reported_by_user"] == 3
    assert rec["decision"]["slots_used_reported_by_user"] == 0
    assert rec["current_inspection_artifact"]["current_disposition"] == (
        "DOWNLOAD_FOR_INSPECTION_ONLY_NOT_CLEARED_TO_SUBMIT"
    )
    for name in ACTIVE_PAGES:
        text = re.sub(r"<[^>]+>", " ", _read(name)).lower()
        assert "no weekly submission slot is cleared" in text or "no slot" in text, name
        assert "ok to download and submit" not in text, name


def test_download_artifacts_have_exact_sha_and_are_referenced_as_inspection_only():
    for filename, digest in ((H59_TIF, H59_SHA256), (H58A_TIF, H58A_SHA256)):
        artifact = DOCS / "downloads" / filename
        assert artifact.is_file()
        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == digest
    for page in ("index.html", "executive-summary.html", "submission-guide.html"):
        text = _read(page)
        assert H59_TIF in text and H59_SHA256 in text, page
        assert H58A_TIF in text or "H58-A" in text, page
        low = text.lower()
        assert "inspection" in low and ("not cleared" in low or "no slot" in low), page


def test_h58a_failed_matched_h49_gate_and_stays_an_ablation():
    rec = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
    h58 = rec["failed_matched_candidate"]
    assert h58["matched_h49_gate_passed"] is False
    assert h58["catalogue"]["positive_folds"] == 0
    assert h58["sgmc_newer_off_catalogue"]["positive_folds"] == 0
    assert h58["catalogue"]["paired_mean_delta_dti"] < 0
    assert h58["sgmc_newer_off_catalogue"]["paired_mean_delta_dti"] < 0
    assert "not a new geological detector" in h58["local_uniqueness_scope"]
    page = _read("index.html")
    assert "0.055301" in page and "0.066341" in page and "0/4" in page
    slate = _read("hypotheses.html")
    for code in ("basement-step / gravity-edge", "focal-mechanism", "3DEP", "Landsat"):
        assert code.lower() in slate.lower()


def test_h59_is_inspection_only_and_comparisons_are_not_misreported():
    rec = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
    h59 = rec["current_inspection_artifact"]
    assert h59["portal_upload_or_acceptance_tested"] is False
    assert h59["holdout"]["same_protocol_h49_comparison_reported"] is False
    assert h59["holdout"]["slot_gate_passed"] is False
    assert h59["holdout"]["sgmc_off_catalogue_dti"] == pytest.approx(0.091687)
    assert h59["holdout"]["sgmc_union_dti"] == pytest.approx(0.097540)
    assert h59["holdout"]["sgmc_dotted_parent_dti"] == pytest.approx(0.095402)
    assert h59["holdout"]["sgmc_tip_parent_dti"] == pytest.approx(0.095693)
    for page in ("index.html", "validation.html", "leaderboard.html", "status.html"):
        text = _read(page)
        assert "0.0917" in text and "0.0957" in text, page


def test_local_status_feed_does_not_claim_portal_safety_or_acceptance():
    data = json.loads((DOCS / "data/status.json").read_text(encoding="utf-8"))
    assert data["decision"]["status"] == "NO_SUBMISSION_SLOT_CLEARED"
    assert data["current_inspection_artifact"]["current_disposition"] == (
        "DOWNLOAD_FOR_INSPECTION_ONLY_NOT_CLEARED_TO_SUBMIT"
    )
    audit = data["current_inspection_artifact"]["local_audit"]
    assert audit["whole_array_all_in_0_1"] is True
    assert audit["outside_all_zero"] is True
    assert audit["outside_all_nan"] is False
    assert audit["local_published_format_checks_pass"] is False
    assert audit["organizer_portal_acceptance_tested"] is False
    rows = {row["file"]: row for row in data["files"]}
    assert rows[H58A_TIF]["whole_array_all_in_0_1"] is True
    nan_name = H58A_TIF.replace("-zeros-outside.tif", "-nan-outside.tif")
    assert rows[nan_name]["outside_all_nan"] is True
    assert rows[nan_name]["whole_array_all_in_0_1"] is False
    assert all(row.get("organizer_portal_acceptance_tested") is False for row in data["files"])
    status_html = _read("status.html").lower()
    assert "local byte checks only" in status_html
    assert "portal-safe" not in status_html


def test_old_build_headline_is_explicitly_historical_not_current():
    rec = json.loads(RECONCILIATION.read_text(encoding="utf-8"))
    old = rec["current_inspection_artifact"]["historic_build_receipt_wording"]
    assert "OK TO DOWNLOAD AND SUBMIT" in old
    assert "historical build record" in _read("status.html").lower()
    report = _read("research/h59-method-results-20261008.md")
    assert "superseded" in report.lower()
    assert "current_disposition" in report
    assert "Current decision: download for inspection only" in _read("research/review-20261008-ds-fusion.md")


def test_portal_error_and_official_mask_are_carefully_described():
    for page in ("index.html", "submission-guide.html", "validation.html", "irregularities.html"):
        low = _read(page).lower()
        assert "cause" in low and "unknown" in low, page
        assert "acceptance" in low, page
    mask = _read("research/leaderboard-and-mask-clarification-20261008.md").lower()
    assert "pixel-exact" in mask
    assert "no 300 m mask buffer" in mask or "no 300m mask buffer" in mask
    assert "0.2778" in _read("leaderboard.html")
    assert "0.3195" in _read("leaderboard.html")
    assert "0.3774" in _read("leaderboard.html")


def test_build_script_cannot_reintroduce_submission_clearance_wording():
    source = (ROOT / "scripts/build_submission_h59.py").read_text(encoding="utf-8")
    assert '"submission_slot_cleared": False' in source
    assert "DOWNLOAD FOR INSPECTION ONLY; NOT CLEARED TO SUBMIT" in source
    assert "portal_safe" not in source
    assert "organizer portal" in source.lower()


def test_h59_receipt_hash_matches_but_historical_verdict_is_not_current():
    assert H59_RECEIPT.is_file()
    receipt = json.loads(H59_RECEIPT.read_text(encoding="utf-8"))
    assert receipt["submission"]["sha256"] == H59_SHA256
    assert receipt["submission"]["filename"] == H59_TIF
    assert "OK TO DOWNLOAD AND SUBMIT" in receipt["headline"]
    assert "historic_build_receipt_wording" in json.loads(
        RECONCILIATION.read_text(encoding="utf-8")
    )["current_inspection_artifact"]


def test_active_entry_page_links_resolve():
    href = re.compile(r'href="([^"#]+)"')
    for page in ACTIVE_PAGES:
        for target in href.findall(_read(page)):
            if target.startswith(("http://", "https://", "mailto:", "tel:")):
                continue
            clean = target.split("?", 1)[0]
            assert (DOCS / clean).exists(), f"{page} links to missing {clean}"
