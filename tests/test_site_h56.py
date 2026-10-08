"""Current H58 page contracts plus retained H56 historical-receipt checks.

H58 is the current inspection-only download and failed its frozen gate. H56B's
old 0.0649 score projection remains invalid historical evidence, never a current
estimate. These tests cover identity, format caveats, D-S semantics, and status.
"""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
EVIDENCE = ROOT / "evidence"
PRIMARY = "GEMSDOE48-H58-OWDS-POSONLY-B2xH33D-20261008-fdbb83476756-zeros-outside.tif"
PRIMARY_REL = f"downloads/{PRIMARY}"
PRIMARY_SHA = "bbd289dd545cd772af3a88631b43233569dcbf4815c69bc5479a53fd73ca3973"
H58_PAGES = ("index.html", "executive-summary.html", "submission-guide.html", "method.html", "validation.html")
H56B = "GEMSDOE48-H56-ds-belief-dotted-x-tip-20261007-9ec0d605c45b-zeros-outside.tif"
H56B_SHA = "4d6548d4ec07a47a25b83d28ebc05d58b57448c1507b460aed52cec395bdb6b5"


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text))


@pytest.fixture(scope="module")
def pages():
    return {name: (DOCS / name).read_text(encoding="utf-8") for name in H58_PAGES}


@pytest.fixture(scope="module")
def page_text(pages):
    return {name: flat(text) for name, text in pages.items()}


def test_current_h58_download_is_top_level_not_replaced_by_historical_artifacts(pages):
    for name in ("index.html", "executive-summary.html"):
        body = pages[name].split("<main", 1)[1]
        target = body.index(f'href="{PRIMARY_REL}"')
        before = body[:target]
        assert "<table" not in before
        assert "download" in body[target:target + 300]
        assert "NOT CLEARED TO SUBMIT" in before or "NOT OK / NOT CLEARED TO SUBMIT" in before
        assert "H55-conduit" not in before


def test_h58_primary_artifact_matches_build_and_local_format_receipts():
    artifact = DOCS / PRIMARY_REL
    assert artifact.is_file()
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert digest == PRIMARY_SHA
    build = json.loads((EVIDENCE / "build_h58_receipt_20261008.json").read_text())
    fmt = json.loads((EVIDENCE / "h58_submission_validation_20261008.json").read_text())
    unique = json.loads((EVIDENCE / "h58_uniqueness_audit_20261008.json").read_text())
    assert build["candidate"]["primary"]["sha256"] == digest
    assert build["candidate"]["submission_authorized"] is False
    assert build["candidate"]["portal_acceptance_tested"] is False
    assert fmt["sha256"] == digest
    assert fmt["all_cells_finite"] is True and fmt["all_cells_in_range_0_1"] is True
    assert fmt["status"] == "PASS_LOCAL_FORMAT_AUDIT_NOT_ORGANIZER_ACCEPTANCE"
    assert unique["candidate"]["sha256"] == digest
    assert unique["scan"]["exact_byte_matches_excluding_companion"] == []
    assert unique["scan"]["exact_in_footprint_pixel_matches_excluding_companion"] == []


def test_h58_preregistered_gate_and_h49_reproduction_support_no_slot():
    holdout = json.loads((EVIDENCE / "holdout_h58_20261008.json").read_text())
    slate = json.loads((EVIDENCE / "hypothesis_slate_h58_20261008.json").read_text())
    assert slate["status"] == "FROZEN_BEFORE_H58_BUILD_AND_HOLDOUT"
    assert holdout["reference_reproduction_check"]["all_pass"] is True
    gate = holdout["necessary_gate"]
    assert gate["passes_both"] is False
    assert gate["weekly_slot_authorized"] is False
    assert holdout["paired_H58_minus_H49"]["catalogue"]["positive_folds"] == 0
    assert holdout["paired_H58_minus_H49"]["sgmc_newer_gt_300m_off_catalogue"]["positive_folds"] == 0


def test_h56b_artifact_remains_a_separate_historical_file():
    artifact = DOCS / "downloads" / H56B
    assert artifact.is_file()
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == H56B_SHA
    fmt = json.loads((EVIDENCE / "h56_format_audit_20261007.json").read_text())
    assert fmt["sha256"] == H56B_SHA
    assert fmt["portal_acceptance_tested"] is False


def test_h58_status_caveat_and_sha_are_on_submitter_pages(page_text):
    for name in ("index.html", "executive-summary.html", "submission-guide.html"):
        text = page_text[name]
        assert PRIMARY in text
        assert PRIMARY_SHA in text
        assert "OK TO DOWNLOAD FOR INSPECTION" in text or "DOWNLOAD FOR INSPECTION: OK" in text
        assert ("NOT CLEARED TO SUBMIT" in text or "NOT OK / NOT CLEARED TO SUBMIT" in text
                or "SUBMIT: NOT OK / NOT CLEARED TO SUBMIT" in text)
        assert ("portal-tested" in text.lower() or "portal acceptance is untested" in text.lower()
                or "neither was uploaded" in text.lower())
        assert "null/nan" in text.lower()


def test_h56b_naive_mean_comparison_is_receipt_based(page_text):
    receipt = json.loads((EVIDENCE / "build_h56_belief_receipt_20261007.json").read_text())
    pearson_binary = receipt["not_the_naive_mean"]["vs_binary_mean"]["pearson_r_footprint"]
    pearson_kernel = receipt["not_the_naive_mean"]["vs_kernel_mean"]["pearson_r_footprint"]
    text = page_text["method.html"]
    assert f"{pearson_binary:.6f}" in text
    assert f"{pearson_kernel:.6f}" in text
    assert receipt["not_the_naive_mean"]["is_identical_to_either_mean"] is False
    assert "not pixelwise equal" in text


def test_h56b_diagnostics_are_separate_layers_not_submission_alternatives(page_text):
    receipt = json.loads((EVIDENCE / "build_h56_belief_receipt_20261007.json").read_text())
    assert receipt["artifacts"]["diagnostics_are_submissions"] is False
    for name in ("index.html", "executive-summary.html", "method.html"):
        text = page_text[name]
        assert "unassigned" in text.lower() or "ignorance" in text.lower()
        assert ("raw conflict" in text.lower() or "pre-normalization conflict" in text.lower()
                or "raw k is conflict" in text.lower())
    for layer in ("mtheta", "conflict", "plausibility"):
        path = DOCS / "downloads/diagnostics" / f"gemsdoe48-h56-{layer}-9ec0d605c45b.tif"
        assert path.is_file(), f"missing H56B {layer} diagnostic"


def test_old_h56_projection_is_historical_and_invalidated():
    text = " ".join(flat((DOCS / name).read_text()) for name in H58_PAGES)
    assert "0.0649" in text
    assert "historical" in text.lower() and "invalid" in text.lower()
    projection = json.loads((EVIDENCE / "h56_live_model_projection_20261007.json").read_text())
    assert projection["validity_status"] == "INVALIDATED_SURROGATE_DO_NOT_USE"
    assert projection["valid_for_decision_gate"] is False
    assert "generally unequal" in projection["invalidity_reason"].lower()
    assert "not organizer-score estimates" in projection["invalidity_reason"].lower()
    erratum = (DOCS / "research/h56b-metric-erratum-20261007.md").read_text()
    assert "not ok / not cleared to submit" in erratum.lower()


def test_no_h56_page_claims_private_label_or_organizer_acceptance(page_text):
    banned = ("organizer confirms a score of", "official score: ",
              "confirmed leaderboard score of", "we scored ", "our score is ")
    for name, text in page_text.items():
        low = text.lower()
        for phrase in banned:
            assert phrase not in low, f"{name} contains unsupported claim {phrase!r}"
        assert "unscored" in low or "no organizer score exists" in low or "not cleared" in low


def test_historical_score_inversion_claims_are_forensic_not_current_guidance():
    h50 = (DOCS / "research/h50-method-20261007.md").read_text(encoding="utf-8").lower()
    h50_slate = (DOCS / "research/hypotheses-20261007.md").read_text(encoding="utf-8").lower()
    h52 = (DOCS / "research/hypotheses-h52-20261007.md").read_text(encoding="utf-8").lower()
    h56 = (DOCS / "research/hypotheses-h56-20261007.md").read_text(encoding="utf-8").lower()
    h55_slate = (DOCS / "research/hypothesis-slate-h55-20261007.md").read_text(encoding="utf-8").lower()
    h49 = (DOCS / "research/holdout-h49-results-20261006.md").read_text(encoding="utf-8").lower()
    h53_results = (DOCS / "research/holdout-h53-results-20261007.md").read_text(encoding="utf-8").lower()
    h53_slate = (DOCS / "research/hypotheses-h53-20261007.md").read_text(encoding="utf-8").lower()
    assert "historical h50 result record" in h50
    assert "fpw = s - q" in h50
    assert "not score estimates or thresholds" in h50
    assert "did not establish" in h50
    assert "+0.0247±0.0005" in h50_slate and "forensic only" in h50_slate
    assert "historical h52 slate — forensic only" in h52
    assert "must not be cited as valid estimates" in h52
    assert "current h57 slate" in h52
    assert "archived / forensic-only h56 slate" in h56
    assert "0.2727` live-score kill value below is withdrawn" in h56
    assert "failed at all three preregistered thresholds" in h56
    assert "live ladder already proved the mechanism" not in h56
    assert "historical planning record" in h55_slate
    assert "withdrawn—not measured private-label facts" in h55_slate
    assert "expected-live-change bracket" in h49 and "are withdrawn" in h49
    assert "does not prove that removed dots earned zero credit" in h53_results
    assert "cannot answer that" in h53_results
    assert "claims that higher live scores require new signal are invalid" in h53_slate
    assert "metric-identity erratum" in h53_slate
