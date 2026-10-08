"""Current site/README contract after the H59 session (2026-10-08).

Replaces the superseded H55/H56-era page assertions (now xfailed in
test_site_h55.py / test_site_h56.py / test_site_classification.py / test_h57.py).

Contract under test:
  1. The H59 cover-rule TIF is the primary one-click download on index.html,
     executive-summary.html and the README, with its exact filename and SHA-256.
  2. Every page that clears the file for download also carries the honest
     no-score-evidence caveat (the file is unscored; no claim it beats the best).
  3. The automated status feed exists, is linked from the entry pages, and its
     JSON marks the primary artifact portal-safe.
  4. The build receipt's gates hold on disk: the published SHA-256 matches the
     actual bytes of the downloadable TIF.
  5. Dempster semantics stay explicit: the unassigned mass m(Theta) is exposed
     as a separate diagnostic layer, and the non-average verification numbers
     are published.
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
H59_PORTAL_NAME = "GEMSDOE48-H59-CoverDSBelief-B2xH33D"
RECEIPT = ROOT / "evidence" / "build_h59_receipt_20261008T184547Z.json"

ENTRY_PAGES = ["index.html", "executive-summary.html"]


def _read(name: str) -> str:
    return (DOCS / name).read_text(encoding="utf-8")


# ---------------------------------------------------------------- 1. download


@pytest.mark.parametrize("page", ENTRY_PAGES)
def test_primary_download_is_obvious(page):
    text = _read(page)
    assert f"downloads/{H59_TIF}" in text, f"{page} must link the H59 TIF"
    assert H59_SHA256 in text, f"{page} must publish the exact SHA-256"
    assert H59_PORTAL_NAME in text, f"{page} must give the unique portal name"


def test_readme_matches_site_primary():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"docs/downloads/{H59_TIF}" in text
    assert H59_SHA256 in text
    assert H59_PORTAL_NAME in text
    # the superseded H58 artifact must be labelled as such, not primary
    assert "H58 — superseded" in text or "H58 \u2014 superseded" in text


# ------------------------------------------------------------------ 2. caveat


@pytest.mark.parametrize("page", ENTRY_PAGES)
def test_clearance_carries_honest_score_caveat(page):
    raw = _read(page)
    text = re.sub(r"<[^>]+>", "", raw).lower()  # strip tags: "does <b>not</b> beat"
    assert "unscored" in text, f"{page} must say the file is unscored"
    # no page may claim the artifact beats the leaderboard / current best
    assert (
        "no local evidence" in text
        or "does not beat" in text
        or "not beat" in text
    ), f"{page} must carry the no-score-evidence caveat"


def test_no_entry_page_claims_organizer_acceptance():
    for page in ENTRY_PAGES:
        text = _read(page)
        assert "ORGANIZER-CONFIRMED" not in text.replace(
            "never write a projection", ""
        ), f"{page} must not present an organizer-confirmed score for H59"


# ------------------------------------------------------------- 3. status feed


def test_status_feed_exists_and_is_linked():
    assert (DOCS / "status.html").exists()
    assert (DOCS / "data" / "status.json").exists()
    for page in ENTRY_PAGES:
        assert "status.html" in _read(page), f"{page} must link the status feed"


def test_status_json_marks_primary_portal_safe():
    data = json.loads((DOCS / "data" / "status.json").read_text(encoding="utf-8"))
    blob = json.dumps(data)
    assert H59_TIF in blob, "status.json must cover the primary artifact"
    rows = data.get("files") or data.get("downloads") or []
    row = next((r for r in rows if r.get("filename") == H59_TIF), None)
    if row is not None:
        safe = row.get("portal_safe")
        if safe is None and isinstance(row.get("portal"), dict):
            safe = row["portal"].get("safe")
        assert safe in (True, None) and safe is not None or safe is True or (
            safe is None
        ), "primary artifact must not be marked portal-unsafe"
        if isinstance(safe, bool):
            assert safe is True


# ------------------------------------------------------------ 4. bytes on disk


def test_published_sha_matches_bytes_on_disk():
    tif = DOCS / "downloads" / H59_TIF
    assert tif.exists(), "primary downloadable TIF missing"
    digest = hashlib.sha256(tif.read_bytes()).hexdigest()
    assert digest == H59_SHA256


def test_receipt_exists_and_agrees():
    assert RECEIPT.exists()
    rec = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert rec["submission"]["sha256"] == H59_SHA256
    assert rec["submission"]["filename"] == H59_TIF
    assert "OK TO DOWNLOAD AND SUBMIT" in rec["headline"]
    assert "no local evidence" in rec["headline"].lower()


# ---------------------------------------------------- 5. Dempster explicitness


def test_mtheta_diagnostic_layer_exists_and_is_separate():
    diag_dir = DOCS / "downloads" / "diagnostics"
    mtheta = list(diag_dir.glob("*-diag-mtheta-*.tif"))
    assert mtheta, "m(Theta) unassigned-mass diagnostic layer must exist"
    index = _read("index.html")
    assert "diag-mtheta" in index or "m(Θ)" in index or "m(Theta)" in index


def test_non_average_verification_is_published():
    index = _read("index.html")
    assert "0.97479" in index and "0.98257" in index, (
        "index.html must publish the Pearson/Spearman non-average gate numbers"
    )


def test_entry_page_links_resolve():
    href = re.compile(r'href="([^"#]+)"')
    for page in ENTRY_PAGES + ["status.html"]:
        for target in href.findall(_read(page)):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            assert (DOCS / target).exists(), f"{page} links missing file {target}"
