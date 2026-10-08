"""Regression checks for the manually maintained active GEMSDOE48 pages.

The generated H55 site is retired. These checks protect the current H58
no-submit status, artifact, attribution limits, and metric/D-S corrections,
while keeping H48-H57 receipts historical rather than current score evidence.
"""
from __future__ import annotations

import hashlib
import html
import json
from html.parser import HTMLParser
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
ACTIVE_PAGES = [
    "index.html", "executive-summary.html", "submission-guide.html", "method.html",
    "hypotheses.html", "validation.html", "leaderboard.html", "irregularities.html",
    "sources.html", "next-steps.html", "research.html",
]
H58A = "GEMSDOE48-H58-OWDS-POSONLY-B2xH33D-20261008-fdbb83476756-zeros-outside.tif"
H58A_SHA256 = "bbd289dd545cd772af3a88631b43233569dcbf4815c69bc5479a53fd73ca3973"


class NestingParser(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
            "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__()
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.VOID:
            return
        if not self.stack:
            self.errors.append(f"unexpected closing tag </{tag}>")
        elif self.stack[-1] != tag:
            self.errors.append(f"</{tag}> closes <{self.stack[-1]}>")
            self.stack.pop()
        else:
            self.stack.pop()


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text))


@pytest.fixture(scope="module")
def pages():
    return {name: (DOCS / name).read_text(encoding="utf-8") for name in ACTIVE_PAGES}


@pytest.fixture(scope="module")
def page_text(pages):
    return {name: flat(text) for name, text in pages.items()}


def test_active_pages_are_well_formed_and_have_no_template_placeholders(pages):
    for name, text in pages.items():
        assert text.lstrip().lower().startswith("<!doctype html>"), name
        assert text.rstrip().lower().endswith("</html>"), name
        assert "<style>" in text or 'rel="stylesheet"' in text, name
        parser = NestingParser()
        parser.feed(text)
        assert parser.errors == [], (name, parser.errors)
        assert parser.stack == [], (name, parser.stack)
        assert not re.search(r"\{(?:esc|fmt)\(", text), name


def test_relative_links_resolve(pages):
    for name, text in pages.items():
        for raw_href in re.findall(r'href="([^"]+)"', text):
            href = html.unescape(raw_href).split("#", 1)[0].split("?", 1)[0]
            if not href or href.startswith(("http://", "https://", "mailto:", "tel:")):
                continue
            target = (DOCS / href).resolve()
            assert target.exists(), f"{name} links to a missing local file: {href}"


def test_current_download_is_obvious_and_submit_verdict_is_unambiguous(page_text):
    for name in ("index.html", "executive-summary.html", "submission-guide.html"):
        text = page_text[name]
        assert H58A in text, f"{name} must identify the current H58-A artifact"
        assert "OK TO DOWNLOAD" in text or "DOWNLOAD FOR INSPECTION: OK" in text, name
        assert "NOT OK" in text or "NOT CLEARED TO SUBMIT" in text, name
        assert ("NO WEEKLY" in text or "no weekly submission slot" in text.lower()
                or "no candidate in this checkout is slot-cleared" in text.lower()), name
    for name in ("index.html", "executive-summary.html"):
        text = page_text[name]
        assert f'href="downloads/{H58A}"' in text, name
        assert 'download>' in text or 'download ' in text, name
        assert "<table" not in text.split(f'href="downloads/{H58A}"', 1)[0], name


def test_download_bytes_hash_and_current_format_caveat():
    artifact = DOCS / "downloads" / H58A
    assert artifact.is_file()
    assert hashlib.sha256(artifact.read_bytes()).hexdigest() == H58A_SHA256
    for name in ("index.html", "submission-guide.html", "executive-summary.html"):
        text = (DOCS / name).read_text()
        assert H58A_SHA256 in text, f"{name} must show the exact downloaded file hash"
        assert "null/NaN" in text or "null/NaN outside" in text
        assert ("portal-tested" in text.lower() or "portal acceptance is untested" in text.lower()
                or "neither was uploaded" in text.lower())


def test_h58_name_and_note_are_provenance_only_and_never_recommend_upload(page_text):
    guide = page_text["submission-guide.html"]
    assert "short note retained for provenance only" in guide.lower()
    assert "failed its frozen comparison against h49" in guide.lower()
    assert "NOT CLEARED" in guide


def test_dempster_mass_semantics_and_naive_mean_comparison_are_explicit(page_text):
    for name in ("index.html", "executive-summary.html", "method.html", "irregularities.html"):
        text = page_text[name]
        assert "m(θ)" in text.lower() or "m(theta)" in text.lower(), name
        assert "unassigned" in text.lower() or "ignorance" in text.lower(), name
        assert ("raw conflict" in text.lower() or "pre-normalization conflict" in text.lower()
                or "raw k is conflict" in text.lower()), name
    method = page_text["method.html"]
    assert "0.986600" in method and "0.996679" in method
    assert "not pixelwise equal" in method


def test_invalid_score_projections_are_labelled_historical_not_reused(page_text):
    for name in ("index.html", "executive-summary.html", "validation.html", "leaderboard.html"):
        text = page_text[name]
        assert "FPw" in text or "fpw" in text.lower(), name
        assert "invalid" in text.lower() or "not a general identity" in text.lower(), name
    erratum = (DOCS / "research/metric-identity-erratum-20261007.md").read_text()
    assert "FPw = S - Q" in erratum
    assert "Gate-2 calibration is also under review" in erratum
    assert "INVALIDATED_DO_NOT_USE_FOR_PROMOTION" in (ROOT / "scripts/audit_candidate.py").read_text()


def test_leaderboard_snapshot_and_local_file_attribution_are_careful(page_text):
    text = page_text["leaderboard.html"]
    assert "0.3774" in text and "0.3195" in text and "0.2778" in text
    assert "rank #13" in text.lower() or "#13" in text
    assert "extradr19" in text
    assert "unverified" in text.lower()
    assert "local b2" in text.lower() or "local b2 tiff" in text.lower()
    assert "local file-to-leaderboard" in page_text["index.html"].lower() or "file-to-score" in page_text["index.html"].lower()


def test_training_inventory_does_not_claim_a_ready_supervised_pipeline(page_text):
    text = page_text["index.html"] + page_text["next-steps.html"] + flat((ROOT / "README.md").read_text())
    assert "supervised train/inference pipeline" in text
    assert "absent" in text.lower()
    assert "ready to run" not in text.lower() or "unsupported" in text.lower()
    audit = json.loads((ROOT / "evidence/training_inventory_20261007.json").read_text())
    assert audit["assessment"]["supervised_train_and_inference_pipeline_present"] is False


def test_h58_slate_and_h57_archive_are_referenced_without_claiming_success(page_text):
    hypotheses = page_text["hypotheses.html"]
    for code in ("H58-A", "H58-B", "H58-C", "H58-D", "H58-E"):
        assert code in hypotheses
    assert "H58-A" in page_text["validation.html"]
    assert "failed" in page_text["index.html"].lower()
    assert "failed its preregistered h49 public-proxy gate" in page_text["index.html"].lower()
    assert "H57-RELIEF" in page_text["submission-guide.html"]
    assert "historical h57 slate" in hypotheses.lower()


def test_irregularity_register_marks_old_metric_inversions_invalid(page_text):
    text = page_text["irregularities.html"]
    for i in range(1, 11):
        assert f"IR-H55-{i:02d}" in text
    assert "invalidated" in text.lower()
    md = flat((DOCS / "irregularities.md").read_text())
    assert "is established as the competition's hidden-label count" in md
    assert "invalid" in md.lower()
    assert "producer's projection is also not a valid score estimate" in md


def test_legacy_h55_site_builder_cannot_overwrite_current_pages():
    from scripts.build_site_h55 import main
    with pytest.raises(SystemExit, match="is retired"):
        main()
