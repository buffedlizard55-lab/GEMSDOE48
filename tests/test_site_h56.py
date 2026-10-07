"""H56B-NF site contract: downloadable research artifact, audits, and no-submit verdict."""
from __future__ import annotations

import hashlib
import html
import json
import pathlib
import re

import numpy as np
import rasterio

REPO = pathlib.Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
EV = REPO / "evidence"
PRIMARY_NAME = "GEMSDOE48-H56B-NF-DS-dotted-x-tip-20261007-5bb2c03c981e-nan-outside.tif"
PRIMARY_REL = f"downloads/{PRIMARY_NAME}"
PRIMARY_SHA = "b9530b70065da1f5e9da82caf4f5aaba3d7175dbbbfb2851e4b2ab2dd13aa4f1"
NOTE = (
    "GEMSDOE48-H56B-NF-DS-5bb2c03c981e | relative D-S belief, no catalogue-flank term; "
    "m(Theta), K, support difference separate; research only, unscored, NOT slot-cleared."
)
PAGES = [
    "index.html", "executive-summary.html", "submission-guide.html", "method.html",
    "validation.html", "hypotheses.html", "next-steps.html", "leaderboard.html",
    "irregularities.html", "sources.html",
]


def flat(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text)


def read_json(name: str) -> dict:
    return json.loads((EV / name).read_text(encoding="utf-8"))


def test_download_is_prominent_and_names_the_h56b_noflank_artifact():
    for name in ("index.html", "executive-summary.html"):
        text = (DOCS / name).read_text(encoding="utf-8")
        body = text.split("<main", 1)[1]
        link = body.index(f'href="{PRIMARY_REL}"')
        before = body[:link]
        assert "<table" not in before
        assert "bigbtn" in before
        assert len(before) < 3500
        assert PRIMARY_NAME in text
        assert "DOWNLOAD: OK" in flat(text)
        assert "SUBMIT: NOT RECOMMENDED" in flat(text)


def test_primary_bytes_match_independent_audit_and_geotiff_contract():
    audit = read_json("audit_h56b_noflank_artifact_20261007.json")
    fmt = read_json("h56b_noflank_format_validation_20261007.json")
    path = DOCS / PRIMARY_REL
    assert path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == PRIMARY_SHA
    assert audit["status"] == "PASS_FORMAT_AND_RECOMPUTATION_NOT_VALIDITY_OR_ACCEPTANCE"
    assert audit["primary"]["sha256"] == PRIMARY_SHA
    assert fmt["sha256"] == PRIMARY_SHA
    assert fmt["outside_footprint_encoding"] == "nan"
    assert fmt["portal_range_error_immune"] is False
    assert audit["primary"]["dtype"] == "float32"
    assert audit["primary"]["crs"] == "EPSG:32611"
    assert audit["primary"]["nodata_is_nan"] is True
    assert audit["primary"]["outside_cells_all_nan"] is True
    with rasterio.open(path) as src:
        assert src.count == 1
        assert src.dtypes == ("float32",)
        assert src.crs.to_string() == "EPSG:32611"
        assert (src.height, src.width) == (3730, 3292)
        values = src.read(1)
        valid = src.dataset_mask() > 0
        assert np.isnan(values[~valid]).all()
        assert np.isfinite(values[valid]).all()
        assert 0.0 <= float(values[valid].min()) <= float(values[valid].max()) <= 1.0


def test_download_and_submission_verdict_are_not_conflated():
    holdout = read_json("holdout_h56b_noflank_vs_h49_currentprotocol_20261007.json")
    assert holdout["slot_decision"]["cleared"] is False
    assert holdout["slot_decision"]["submit_recommended"] is False
    for name in ("index.html", "executive-summary.html", "submission-guide.html"):
        text = flat((DOCS / name).read_text(encoding="utf-8"))
        assert "DOWNLOAD: OK" in text
        assert "SUBMIT: NOT RECOMMENDED" in text
        assert "no weekly slot" in text.lower() or "no slot is cleared" in text.lower()
        assert "organizer acceptance" in text.lower() or "organizer accepted" in text.lower()
        assert "portal_range_error_immune=false" in text


def test_holdout_means_and_fold_direction_match_receipt():
    holdout = read_json("holdout_h56b_noflank_vs_h49_currentprotocol_20261007.json")
    assert holdout["metric_direction"]["higher_is_better"] is True
    cat = holdout["targets"]["catalogue_proxy"]
    sgmc = holdout["targets"]["sgmc_off_catalogue_proxy"]
    assert cat["h56b_wins"] == 0 and cat["fold_count"] == 4
    assert sgmc["h56b_wins"] == 0 and sgmc["fold_count"] == 4
    page = flat((DOCS / "index.html").read_text(encoding="utf-8"))
    assert "0.056305" in page and "0.095353" in page
    assert "0.068987" in page and "0.100751" in page
    assert "higher DTI is better" in page
    assert "public-map proxies" in page


def test_mean_comparison_is_recomputed_and_qualified():
    audit = read_json("audit_h56b_noflank_artifact_20261007.json")
    stats = audit["not_the_arithmetic_mean"]
    assert stats["is_identical_to_either_mean"] is False
    page = flat((DOCS / "index.html").read_text(encoding="utf-8"))
    assert f"{stats['normalized_binary_mean_pearson_r']:.6f}" in page
    assert f"{stats['normalized_kernel_mean_pearson_r']:.6f}" in page
    assert f"{stats['normalized_kernel_mean_mae']:.6f}" in page
    assert "high correlation is disclosed" in page.lower()
    assert "non-identity" in page.lower()


def test_dempster_shafer_terms_and_total_conflict_are_documented():
    method = flat((DOCS / "method.html").read_text(encoding="utf-8"))
    assert "not a direct map of source disagreement" in method
    assert "pre-normalization raw conflict" in method
    assert "raise ValueError" in method
    assert "silently falls back to vacuous mass" in method
    assert "support-difference diagnostic" in method
    assert "calibrated probability model" in method.lower()


def test_short_note_and_separate_diagnostics_exist():
    assert len(NOTE) <= 200
    for name in ("index.html", "submission-guide.html", "executive-summary.html"):
        assert NOTE in flat((DOCS / name).read_text(encoding="utf-8"))
    audit = read_json("audit_h56b_noflank_artifact_20261007.json")
    expected_diags = audit["independent_recomputation"]["diagnostics"]
    for key, expected in expected_diags.items():
        path = REPO / expected["path"]
        assert path.is_file(), f"missing diagnostic {key}"
        with rasterio.open(path) as src:
            assert src.count == 1
            assert src.crs.to_string() == "EPSG:32611"
        assert expected["matches_independent_recomputation"] is True
    page = flat((DOCS / "index.html").read_text(encoding="utf-8"))
    assert "m(Θ) is not a direct disagreement map" in page
    assert "support difference is not a D-S mass" in page


def test_local_uniqueness_and_prior_rebuild_similarity_are_fully_disclosed():
    receipt = read_json("h56b_noflank_uniqueness_20261007.json")
    result = receipt["result"]
    assert result["same_sha256_as_any_searched_raster"] is False
    assert result["exact_in_footprint_pixel_match"] is False
    assert receipt["search_scope"]["same_grid_one_band_rasters_compared_in_footprint"] == 105
    prior = result["prior_h56_zero_outside_comparison"]
    assert prior["max_abs_difference"] > 0.5
    assert prior["top_37654_jaccard"] > 0.99
    withflank = read_json("h56b_uniqueness_audit_20261007.json")
    old_h56 = withflank["result"]["prior_h56_zero_outside_comparison"]
    assert old_h56["max_abs_difference"] < 2e-7
    assert old_h56["top_37654_jaccard"] == 1.0
    report = flat((DOCS / "research/h56b-review-erratum-20261007.md").read_text())
    assert "meaningfully new candidate" in report.lower()
    assert "not" in report.lower()
    assert "post-hoc" in report.lower()


def test_build_stat_and_chronology_corrections_are_preserved():
    build = read_json("build_h56b_noflank_receipt_20261007.json")
    assert build["status"] == "POST_HOC_ABLATION_NOT_PREREGISTERED_NOT_SLOT_CLEARED"
    assert build["artifacts"]["primary"]["sha256"] == PRIMARY_SHA
    correction = read_json("h56b_review_corrections_20261007.json")
    withflank_build = read_json("build_h56b_belief_receipt_20261007.json")
    assert withflank_build["generated_utc"] == correction["correction_2_kernel_mean_max_difference"]["current_build_receipt_generated_utc"]
    mean_fix = correction["correction_2_kernel_mean_max_difference"]
    assert mean_fix["prior_reported_max_abs_difference"] == 0.6666666865348816
    assert mean_fix["current_build_receipt_max_abs_difference"] == 0.4172414541244507
    timing = correction["correction_1_receipt_identity_and_chronology"]
    assert "not the final H56B" in timing["mislabelled_predecessor"]["interpretation"]
    assert timing["h56b_specific_slate"]["frozen_utc"] == "2026-10-07T16:00:00Z"


def test_score_projection_is_retracted_not_repeated_as_prediction():
    for name in ("index.html", "executive-summary.html", "submission-guide.html",
                 "validation.html", "next-steps.html", "leaderboard.html"):
        text = flat((DOCS / name).read_text()).lower()
        if "0.0649" in text:
            assert "invalid" in text or "not supportable" in text
    report = (DOCS / "research/h56b-review-erratum-20261007.md").read_text()
    assert "no score above 0.2778" in report.lower()
    assert "supportable as a prediction" in report.lower()
    assert "0.3195" in report


def test_future_hypothesis_slate_and_chronology_are_linked():
    slate = (DOCS / "research/h57-hypothesis-slate-20261007.md").read_text()
    machine = read_json("hypothesis_slate_h57_20261007.json")
    assert len(machine["candidates"]) == 5
    assert machine["not_a_preregistration_for_prior_results"] is True
    assert "Verified availability now" in slate
    assert "no weekly submission slot is spent" in slate.lower()
    reconciliation = read_json("h56_preregistration_reconciliation_20261007.json")
    assert reconciliation["status"] == "CHRONOLOGY_AND_RANKING_INCONSISTENCIES_FLAGGED"
    assert reconciliation["decision"]["submission_slot_cleared"] is False
    assert "not a verified preregistration" in flat((DOCS / "hypotheses.html").read_text()).lower()


def test_leaderboard_context_is_minimal_and_no_names_are_republished():
    text = flat((DOCS / "leaderboard.html").read_text())
    assert "0.3774" in text and "0.3195 was rank 7" in text and "0.2778 row was rank 13" in text
    for name in ("xiaofanhu", "extradr19", "DARD", "alexoktaba"):
        assert name not in text
    assert "does not poll" in text
    assert "no organizer receipt" in text


def test_no_h56b_site_claims_organizer_score_or_acceptance(pages=None):
    for name in PAGES:
        text = flat((DOCS / name).read_text()).lower()
        for phrase in ("organizer-verified score", "confirmed leaderboard score", "our organizer score"):
            assert phrase not in text, f"{name} includes unsupported phrase {phrase!r}"
    assert "no organizer score exists" in flat((DOCS / "executive-summary.html").read_text()).lower()
