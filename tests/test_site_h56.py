"""H56-specific contract tests for the current static research pages.

The 0.0649 H56B score projection is superseded and must never be presented as a
current estimate. These tests check the corrected receipt, exact file identity,
format caveat, D-S semantics, and current download/submit verdict.
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
PRIMARY = "GEMSDOE48-H56-ds-belief-dotted-x-tip-20261007-9ec0d605c45b-zeros-outside.tif"
PRIMARY_REL = f"downloads/{PRIMARY}"
PRIMARY_SHA = "4d6548d4ec07a47a25b83d28ebc05d58b57448c1507b460aed52cec395bdb6b5"
H56_PAGES = ("index.html", "executive-summary.html", "submission-guide.html", "method.html", "validation.html")


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text))


@pytest.fixture(scope="module")
def pages():
    return {name: (DOCS / name).read_text(encoding="utf-8") for name in H56_PAGES}


@pytest.fixture(scope="module")
def page_text(pages):
    return {name: flat(text) for name, text in pages.items()}


def test_current_download_is_top_level_and_not_replaced_by_historical_h55(pages):
    for name in ("index.html", "executive-summary.html"):
        body = pages[name].split("<main", 1)[1]
        target = body.index(f'href="{PRIMARY_REL}"')
        before = body[:target]
        assert "<table" not in before
        assert "download" in body[target:target + 300]
        assert "NOT CLEARED TO SUBMIT" in before or "NOT OK / NOT CLEARED TO SUBMIT" in before
        assert "H55-conduit" not in before


def test_primary_artifact_matches_current_format_and_identity_receipts():
    artifact = DOCS / PRIMARY_REL
    assert artifact.is_file()
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert digest == PRIMARY_SHA
    fmt = json.loads((EVIDENCE / "h56_format_audit_20261007.json").read_text())
    unique = json.loads((EVIDENCE / "h56_uniqueness_20261007.json").read_text())
    assert fmt["sha256"] == digest
    assert fmt["local_core_format_passed"] is True
    assert fmt["official_outside_policy_passed"] is False
    assert fmt["portal_acceptance_tested"] is False
    assert unique["sha256"] == digest and unique["pass"] is True
    assert unique["canonical_footprint_comparisons"] == 73


def test_h56_status_caveat_and_sha_are_on_submitter_pages(page_text):
    for name in ("index.html", "executive-summary.html", "submission-guide.html"):
        text = page_text[name]
        assert PRIMARY in text
        assert PRIMARY_SHA in text
        assert "OK TO DOWNLOAD FOR INSPECTION" in text or "DOWNLOAD FOR INSPECTION: OK" in text
        assert ("NOT CLEARED TO SUBMIT" in text or "NOT OK / NOT CLEARED TO SUBMIT" in text
                or "SUBMIT: NOT OK / NOT CLEARED TO SUBMIT" in text)
        assert "portal acceptance is untested" in text.lower()
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
    text = " ".join(flat((DOCS / name).read_text()) for name in H56_PAGES)
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
