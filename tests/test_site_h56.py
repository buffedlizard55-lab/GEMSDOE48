"""Site contract for the H56 session: the published pages must agree with the
H56 receipts, the verdict banner must be present and consistent with the gates,
and the download must be the first content on the index and executive summary.

Mirrors the shape of tests/test_site_h55.py but reads the H56 evidence files:
  evidence/build_h56_belief_receipt_20261007.json
  evidence/h56_format_audit_20261007.json
  evidence/h56_uniqueness_20261007.json
  evidence/h56f_pruning_holdout_20261007.json
"""
from __future__ import annotations

import hashlib
import html
import json
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
EV = REPO / "evidence"
PAGES = ["index.html", "executive-summary.html", "submission-guide.html"]

PRIMARY_NAME = "GEMSDOE48-H56-ds-belief-dotted-x-tip-20261007-9ec0d605c45b-zeros-outside.tif"
PRIMARY_REL = f"downloads/{PRIMARY_NAME}"
NOTE = ("GEMSDOE48-H56 | Dempster belief[0,1] of dotted-C(0.2778) x tip-H33D(0.2632), "
        "metric-kernel BPA, live-anchored discounts; m(Theta) diagnostic separate; "
        "holdout below H49 -> submit NOT recommended; unscored | id 9ec0d605c45b")


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text))


def needs_site():
    return pytest.mark.skipif(
        not (EV / "build_h56_belief_receipt_20261007.json").exists() or
        not all((DOCS / p).exists() for p in PAGES),
        reason="H56 site or receipts not built; run scripts/build_submission_h56_belief.py "
               "and scripts/validate_h56.py")


@pytest.fixture(scope="module")
def pages():
    return {p: (DOCS / p).read_text() for p in PAGES if (DOCS / p).exists()}


@pytest.fixture(scope="module")
def receipts():
    return {
        "build": json.loads((EV / "build_h56_belief_receipt_20261007.json").read_text()),
        "format": json.loads((EV / "h56_format_audit_20261007.json").read_text()),
        "uniq": json.loads((EV / "h56_uniqueness_20261007.json").read_text()),
        "holdout": json.loads((EV / "h56f_pruning_holdout_20261007.json").read_text()),
    }


@needs_site()
def test_download_is_the_first_content_on_index_and_exec_summary(pages):
    for name in ("index.html", "executive-summary.html"):
        body = pages[name].split("<main", 1)[1]
        link = body.index(f'href="{PRIMARY_REL}"')
        before = body[:link]
        assert "<table" not in before, f"{name}: a table appears before the H56 download button"
        assert "bigbtn" in before, f"{name}: the H56 download button class is missing"
        assert len(before) < 3500, f"{name}: too much content before the H56 one-click download"


@needs_site()
def test_primary_file_exists_and_matches_receipt(receipts):
    fmt = receipts["format"]
    path = REPO / "docs/downloads" / PRIMARY_NAME
    assert path.exists()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == fmt["sha256"]
    assert fmt["all_passed"] is True  # local checks only
    assert all(fmt["checks"].values())
    assert fmt["official_format_acceptance_confirmed"] is False
    assert fmt["outside_bounds_requirement"]["primary_passes_official_null_nan_outside_requirement"] is False


@needs_site()
def test_nan_nodata_twin_matches_official_outside_encoding_but_is_not_portal_cleared():
    receipt_path = EV / "h56b_nan_twin_local_validation_20261007.json"
    receipt = json.loads(receipt_path.read_text())
    assert receipt["status"] == "PASS_LOCAL_FORMAT_AUDIT_NOT_ORGANIZER_ACCEPTANCE"
    path = REPO / receipt["file"]
    assert path.exists()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == receipt["sha256"]
    assert receipt["outside_footprint_encoding"] == "nan"
    assert receipt["nodata"] == "NaN"
    assert receipt["finite_inside_footprint"] is True
    assert receipt["all_in_footprint_range_0_1"] is True
    assert receipt["portal_range_error_immune"] is False
    assert "portal acceptance" not in receipt["status"].lower()


@needs_site()
def test_verdict_banner_matches_the_gates(pages, receipts):
    """The banner must state exactly what the gates computed — never optimism."""
    verdict = receipts["format"]["verdict"]
    assert verdict["banner"] == "DOWNLOAD OK FOR INSPECTION - SUBMIT NOT RECOMMENDED"
    assert verdict["official_outside_bounds_rule_confirmed"] is False
    assert verdict["submit_recommended"] is False
    idx = flat(pages["index.html"])
    assert "DOWNLOAD: OK" in idx
    assert "SUBMIT: NOT RECOMMENDED" in idx
    assert "0.032347" in idx and "0.070552" in idx
    assert "0.095353" in idx and "0.100751" in idx
    assert "0.2778" in idx  # owner-reported family result is shown with caveat


@needs_site()
def test_not_naive_mean_numbers_are_published(pages, receipts):
    build = receipts["build"]
    r_bin = build["not_the_naive_mean"]["vs_binary_mean"]["pearson_r_footprint"]
    idx = flat(pages["index.html"])
    assert f"{r_bin:.3f}" in idx, "Pearson r vs the binary naive mean must be on the page"
    assert "m(Θ)" in idx or "m(Theta)" in idx


@needs_site()
def test_paste_ready_note_on_index_and_guide(pages):
    for name in ("index.html", "submission-guide.html"):
        assert NOTE in flat(pages[name]), f"{name} must carry the paste-ready H56 note"


@needs_site()
def test_sha_and_name_on_index_and_guide(pages, receipts):
    sha = receipts["format"]["sha256"]
    for name in ("index.html", "submission-guide.html"):
        assert sha in pages[name], f"{name} does not carry the full H56 SHA-256"
        assert PRIMARY_NAME in pages[name]


@needs_site()
def test_diagnostics_labelled_not_submissions(pages):
    for name in ("index.html", "executive-summary.html"):
        assert "not submissions" in flat(pages[name])
    for layer in ("mtheta", "conflict", "plausibility", "support-disagreement"):
        p = DOCS / "downloads/diagnostics" / f"gemsdoe48-h56-{layer}-9ec0d605c45b.tif"
        assert p.exists(), f"missing diagnostic layer {layer}"
    assert "residual ignorance" in flat(pages["index.html"])
    assert "not a pure disagreement map" in flat(pages["index.html"])


@needs_site()
def test_no_organizer_score_claim_on_h56_pages(pages):
    banned = ["organizer-verified score", "official score of", "confirmed leaderboard score",
              "we scored", "our score is"]
    for name, text in pages.items():
        low = text.lower()
        for phrase in banned:
            assert phrase not in low, f"{name} claims {phrase!r}"
        assert "UNSCORED" in text or "No organizer score exists" in text


@needs_site()
def test_h56f_report_matches_machine_receipt(receipts):
    report = (DOCS / "research/h56f-pruning-results-20261007.md").read_text()
    hold = receipts["holdout"]
    cat = hold["results"]["catalogue_public_proxy"]["scores"]
    sgmc = hold["results"]["SGMC_off_catalogue_gt300m_public_proxy"]["scores"]
    h56b_cat = cat["H56B_graded_belief"]["mean_dti"]
    h56b_sgmc = sgmc["H56B_graded_belief"]["mean_dti"]
    assert f"| H56B graded belief | graded | {h56b_cat:.6f} | {h56b_sgmc:.6f} |" in report
    for rung, key in (("0.90", "H56F_Bel_ge_0.90"), ("0.95", "H56F_Bel_ge_0.95"),
                      ("0.99", "H56F_Bel_ge_0.99")):
        cat_score = cat[key]["mean_dti"]
        sgmc_score = sgmc[key]["mean_dti"]
        assert f"H56-F, threshold {rung}" in report
        assert f"| {cat_score:.6f} | {sgmc_score:.6f} |" in report


def test_dated_leaderboard_snapshot_is_not_misreported_or_used_for_file_attribution():
    snapshot = json.loads((DOCS / "data/leaderboard_20261007.json").read_text())
    assert snapshot["retrieved_utc"] == "2026-10-07"
    by_rank = {row["rank"]: row for row in snapshot["rows"]}
    assert by_rank[1]["best_public"] == 0.3774
    assert by_rank[7]["best_public"] == 0.3195
    assert by_rank[13]["participant"] == "extradr19"
    assert by_rank[13]["best_public"] == 0.2778
    assert "not identify any local TIFF" in snapshot["attribution_warning"]
    page = (DOCS / "leaderboard.html").read_text()
    assert "required recovered-truth units" in page
    assert "withdrawn" in page
    assert "reachability" in page
