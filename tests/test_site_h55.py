"""The published site must agree with the receipts it is generated from.

`scripts/build_site_h55.py` reads every number out of a receipt, so these tests catch two failure
modes: a page that was hand-edited away from the receipts, and a receipt field that changed shape
without the pages being rebuilt.
"""
from __future__ import annotations

import html
import json
import pathlib
import re

import pytest


def flat(text: str) -> str:
    """Unescape entities and collapse whitespace so tests compare prose, not markup."""
    return re.sub(r"\s+", " ", html.unescape(text))

REPO = pathlib.Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
PAGES = ["index.html", "executive-summary.html", "submission-guide.html", "method.html",
         "hypotheses.html", "validation.html", "irregularities.html", "sources.html",
         "next-steps.html"]

RECEIPT = REPO / "evidence/build_h55_receipt_20261007.json"


def needs_site():
    return pytest.mark.skipif(
        not (RECEIPT.exists() and all((DOCS / p).exists() for p in PAGES)),
        reason="site or receipts not built; run scripts/build_submission_h55.py then "
               "scripts/build_site_h55.py")


@pytest.fixture(scope="module")
def receipt():
    return json.loads(RECEIPT.read_text())


@pytest.fixture(scope="module")
def pages():
    return {p: (DOCS / p).read_text() for p in PAGES if (DOCS / p).exists()}


@pytest.fixture(scope="module")
def flatpages(pages):
    return {k: flat(v) for k, v in pages.items()}


@needs_site()
def test_every_page_is_well_formed_html(pages):
    for name, text in pages.items():
        assert text.startswith("<!doctype html>"), name
        assert text.rstrip().endswith("</html>"), name
        assert "<style>" in text and "</style>" in text, name
        # no unrendered f-string expressions
        assert not re.search(r"\{[A-Za-z_][A-Za-z0-9_'\"]*\}", text), name


@needs_site()
def test_relative_links_resolve(pages):
    for name, text in pages.items():
        for href in re.findall(r'href="([^"#?]+)"', text):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            target = (DOCS / href).resolve()
            assert target.exists(), f"{name} links to a missing file: {href}"


@needs_site()
def test_download_is_the_first_content_on_index_and_exec_summary(receipt, pages):
    # Both same-day H56 sessions (this session's H56B graded belief and the concurrent
    # open-world OWDS candidate) are the current one-click research downloads and must sit
    # above the preserved H55 card. Keep the H55 receipt checks below for its historical
    # section, but do not let it displace either H56 at the top.
    h56_receipt = REPO / "evidence/build_h56_receipt_20261007.json"
    belief_receipt = REPO / "evidence/build_h56_belief_receipt_20261007.json"
    h57_receipt = REPO / "evidence/build_h57_receipt_20261007.json"
    if h57_receipt.exists():
        # the H57 session cleared a candidate; its download is now the first content.
        primary = json.loads(h57_receipt.read_text())["files"][
            "primary_zeros_outside"]["path"].split("/")[-1]
    elif h56_receipt.exists():
        current = json.loads(h56_receipt.read_text())
        primary = current["candidate"]["primary"]["path"].split("/")[-1]
    else:
        primary = receipt["files"]["primary_zeros_outside"]["path"].split("/")[-1]
    for name in ("index.html", "executive-summary.html"):
        text = pages[name]
        body = text.split("<main", 1)[1]
        link = body.index(f'href="downloads/{primary}"')
        # the only things before it are the header copy and the two download-card leads.
        before = body[:link]
        assert "<table" not in before, f"{name}: a table appears before the current download button"
        assert "bigbtn" in before, f"{name}: the current download button class is missing"
        assert len(before) < 9000, f"{name}: too much content before the current one-click download"
        if belief_receipt.exists():
            belief_primary = (json.loads(belief_receipt.read_text())["artifacts"]
                              ["primary_zeros"].split("/")[-1])
            belief_link = body.index(f'href="downloads/{belief_primary}"')
            assert belief_link < len(body), f"{name}: H56B belief download missing"
            h55_primary = receipt["files"]["primary_zeros_outside"]["path"].split("/")[-1]
            h55_link = body.index(f'href="downloads/{h55_primary}"')
            assert belief_link < h55_link and link < h55_link, (
                f"{name}: a current H56 download must sit above the preserved H55 card")


@needs_site()
def test_primary_download_exists_and_matches_the_receipt(receipt):
    info = receipt["files"]["primary_zeros_outside"]
    path = REPO / info["path"]
    assert path.exists()
    assert path.stat().st_size == info["bytes"]
    import hashlib
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == info["sha256"]
    assert info["all_cells_finite"] is True
    assert info["all_cells_in_range_0_1"] is True
    assert info["portal_range_error_immune"] is True
    assert info["nodata"] is None
    assert info["encoding"] == "all_finite_zeros_outside"


@needs_site()
def test_pages_quote_the_receipt_numbers_verbatim(receipt, flatpages):
    name = receipt["submission_name"]
    note = flat(receipt["paste_ready_note"])
    sha = receipt["files"]["primary_zeros_outside"]["sha256"]
    px = f"{receipt['emission']['positive_pixels']:,}"
    for page in ("index.html", "executive-summary.html", "submission-guide.html"):
        assert name in flatpages[page], f"{page} does not name the submission"
    # the full digest must be on the two pages a submitter actually reads
    for page in ("index.html", "submission-guide.html"):
        assert sha in flatpages[page], f"{page} does not carry the full primary SHA-256"
    assert note in flatpages["submission-guide.html"], "the paste-ready note must be on the guide"
    assert note in flatpages["index.html"], "the paste-ready note must be on the download card"
    assert px in flatpages["index.html"]


@needs_site()
def test_no_page_claims_an_organizer_score(receipt, pages):
    banned = ["organizer-verified score", "official score of", "confirmed leaderboard score",
              "we scored", "our score is"]
    for name, text in pages.items():
        low = text.lower()
        for phrase in banned:
            assert phrase not in low, f"{name} claims {phrase!r}"
    for name, text in pages.items():
        assert "No organizer score exists" in text or "UNSCORED" in text or "not slot" in text \
            or "slot is cleared" in text, f"{name} does not carry the no-organizer-score caveat"


@needs_site()
def test_diagnostic_layers_are_labelled_not_submissions(receipt, flatpages):
    diag = receipt["files"]["diagnostics"]
    assert set(diag) == {"bel", "plausibility", "mtheta", "conflict"}
    for layer, info in diag.items():
        path = REPO / info["path"]
        assert path.exists(), layer
        assert 0.0 <= info["min"] <= info["max"] <= 1.0, layer
    guide = flatpages["submission-guide.html"]
    assert "diagnostic layers for a geologist and are not submissions" in guide


@needs_site()
def test_hypothesis_page_carries_every_required_field(pages):
    slate = json.loads((REPO / "evidence/hypothesis_slate_h55_20261007.json").read_text())
    assert len(slate["hypotheses"]) >= 3
    required = ("layers", "physical_signature", "why_it_catches_a_missing_fault",
                "difference_from_repository", "data_source", "data_obtainable_verified",
                "expected_dti", "cost", "status")
    for hyp in slate["hypotheses"]:
        for field in required:
            assert field in hyp and hyp[field] not in ("", None), (hyp["id"], field)
    page = pages["hypotheses.html"]
    for hyp in slate["hypotheses"]:
        assert hyp["id"] in page, f"{hyp['id']} missing from hypotheses.html"
    assert slate["irregularities"], "no irregularities recorded"
    assert len(slate["irregularities"]) >= 5


@needs_site()
def test_irregularities_page_matches_the_markdown_record(pages):
    text = pages["irregularities.html"]
    md = (REPO / "docs/irregularities.md").read_text()
    for i in range(1, 11):
        tag = f"IR-H55-{i:02d}"
        assert tag in text, f"{tag} missing from irregularities.html"
        assert tag in md, f"{tag} missing from docs/irregularities.md"


@needs_site()
def test_ceiling_claim_is_present_and_negative(pages):
    """The site must state the ceiling result, not just the candidate."""
    text = pages["index.html"]
    assert "0.2843" in text or "0.28435" in text
    assert "unreachable" in text.lower() or "NO" in text
    assert "0.3774" in text and "0.3195" in text


GATE2 = REPO / "evidence/audit_gate2_h55_20261007.json"


@needs_site()
def test_the_failed_gate_is_disclosed_on_every_decision_page(pages):
    """A failing gate must never be silently dropped from the published site."""
    if not GATE2.exists():
        pytest.skip("GATE-2 receipt absent")
    gate = json.loads(GATE2.read_text())
    assert gate["verdict"].startswith("FAIL"), gate["verdict"]
    credit = f"{gate['additions']['density_matched_credit_per_cell']:.4f}"
    for page in ("index.html", "executive-summary.html", "validation.html"):
        text = pages[page]
        assert "FAIL_MASS_NEUTRAL" in text, f"{page} hides the GATE-2 verdict"
        assert credit in text, f"{page} omits the density-matched added-cell credit"
        assert "0.0556" in text or "0.05556" in text, f"{page} omits the break-even bar"
    # and the pessimistic live-equivalent that follows from it must be shown too
    assert "0.2736" in pages["index.html"]
