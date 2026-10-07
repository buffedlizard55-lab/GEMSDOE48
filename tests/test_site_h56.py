"""Site contract for the H56 session: the published pages must agree with the
H56 receipts, the verdict banner must be present and consistent with the gates,
and the download must be the first content on the index and executive summary.

Mirrors the shape of tests/test_site_h55.py but reads the H56 evidence files:
  evidence/build_h56_belief_receipt_20261007.json
  evidence/h56_format_audit_20261007.json
  evidence/h56_uniqueness_20261007.json
  evidence/holdout_h56_spatial_20261007.json
  evidence/h56_live_model_projection_20261007.json
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
# The H57 session cleared a candidate for submission, so H57's one-click download now
# sits above the (superseded) H56 card.  The site invariant is unchanged in substance:
# the *cleared* candidate's download must be the first content on the page.
CLEARED_NAME = "GEMSDOE48-H57-ds-relief-augmented-20261007-e6b785718c07.tif"
CLEARED_REL = f"downloads/{CLEARED_NAME}"
NOTE = ("GEMSDOE48-H56 | Dempster belief[0,1] of dotted-C(0.2778) x tip-H33D(0.2632), "
        "metric-kernel BPA, live-anchored discounts; m(Theta) diagnostic separate; "
        "live-model proj 0.0649 -> submit NOT recommended; unscored | id 9ec0d605c45b")


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
        "proj": json.loads((EV / "h56_live_model_projection_20261007.json").read_text()),
    }


@needs_site()
def test_download_is_the_first_content_on_index_and_exec_summary(pages):
    for name in ("index.html", "executive-summary.html"):
        body = pages[name].split("<main", 1)[1]
        link = body.index(f'href="{CLEARED_REL}"')
        before = body[:link]
        assert "<table" not in before, f"{name}: a table appears before the cleared download button"
        assert "bigbtn" in before, f"{name}: the cleared download button class is missing"
        assert len(before) < 3500, f"{name}: too much content before the cleared one-click download"
        assert body.index(f'href="{PRIMARY_REL}"') > link, (
            f"{name}: the superseded H56 download must sit below the cleared H57 one")


@needs_site()
def test_primary_file_exists_and_matches_receipt(receipts):
    fmt = receipts["format"]
    path = REPO / "docs/downloads" / PRIMARY_NAME
    assert path.exists()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == fmt["sha256"]
    assert fmt["all_passed"] is True
    assert all(fmt["checks"].values())


@needs_site()
def test_verdict_banner_matches_the_gates(pages, receipts):
    """The banner must state exactly what the gates computed — never optimism."""
    verdict = receipts["format"]["verdict"]
    assert verdict["banner"] == "DOWNLOAD OK - SUBMIT NOT RECOMMENDED"
    idx = flat(pages["index.html"])
    assert "DOWNLOAD: OK" in idx
    assert "SUBMIT: NOT RECOMMENDED" in idx
    # the projection quoted on the page is the receipt's projection, rounded
    proj = verdict["reasons"]["live_projection"]
    assert f"{proj:.4f}".rstrip("0").rstrip(".") in idx or f"{proj:.4f}" in idx
    assert "0.2778" in idx  # the incumbent is named next to the verdict


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
    for layer in ("mtheta", "conflict", "plausibility"):
        p = DOCS / "downloads/diagnostics" / f"gemsdoe48-h56-{layer}-9ec0d605c45b.tif"
        assert p.exists(), f"missing diagnostic layer {layer}"


@needs_site()
def test_no_organizer_score_claim_on_h56_pages(pages):
    banned = ["organizer-verified score", "official score of", "confirmed leaderboard score",
              "we scored", "our score is"]
    for name, text in pages.items():
        low = text.lower()
        for phrase in banned:
            assert phrase not in low, f"{name} claims {phrase!r}"
        assert "UNSCORED" in text or "No organizer score exists" in text
