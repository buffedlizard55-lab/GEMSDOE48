"""Audit tests for the 2026-10-07 (later) session artifacts: H51 emission,
H50-B alteration probe, and the restored GeoDAWN radiometric mirror.

These tests re-read the published bytes and receipts rather than re-running
the builders, so they also catch post-build tampering.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

import numpy as np
import pytest

import conftest  # noqa: F401

rasterio = pytest.importorskip("rasterio")

ROOT = conftest.REPO
DOWNLOADS = ROOT / "docs/downloads"
EVIDENCE = conftest.EVIDENCE

SHA_RAD = "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def h51_primary() -> Path:
    hits = sorted(DOWNLOADS.glob("gemsdoe48-h51-plausibility-budget-*-zeros.tif"))
    assert hits, "H51 primary missing"
    return hits[-1]


def h50b_primary() -> Path:
    hits = sorted(DOWNLOADS.glob("gemsdoe48-h50b-alteration-conflict-*-zeros.tif"))
    assert hits, "H50-B primary missing"
    return hits[-1]


@pytest.fixture(scope="module")
def h51_receipt() -> dict:
    return json.loads((EVIDENCE / "build_h51_receipt_20261007.json").read_text())


@pytest.fixture(scope="module")
def h50b_receipt() -> dict:
    return json.loads((EVIDENCE / "h50b_preregistration_20261007.json").read_text())


class TestH51Artifact:
    def test_receipt_hashes_match_bytes(self, h51_receipt):
        primary = ROOT / h51_receipt["primary_file"]
        assert sha256(primary) == h51_receipt["primary_sha256"]
        zip_path = ROOT / h51_receipt["zip_file"]
        assert sha256(zip_path) == h51_receipt["zip_sha256"]
        twin = ROOT / h51_receipt["nan_outside_twin"]["path"]
        assert sha256(twin) == h51_receipt["nan_outside_twin"]["sha256"]

    def test_zip_contains_exactly_the_primary(self, h51_receipt):
        zip_path = ROOT / h51_receipt["zip_file"]
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            assert len(names) == 1
            assert names[0] == Path(h51_receipt["primary_file"]).name

    def test_primary_is_binary_budget_matched_portal_safe(self, h51_receipt):
        with rasterio.open(ROOT / h51_receipt["primary_file"]) as ds:
            assert str(ds.crs) == "EPSG:32611"
            assert (ds.width, ds.height) == (3292, 3730)
            assert ds.dtypes == ("float32",)
            values = ds.read(1)
        assert np.isfinite(values).all()
        assert set(np.unique(values).tolist()) <= {0.0, 1.0}
        assert int((values > 0).sum()) == h51_receipt["preregistration"]["budget"] == 37_654

    def test_nan_twin_matches_template_convention(self, h51_receipt):
        with rasterio.open(ROOT / h51_receipt["nan_outside_twin"]["path"]) as ds:
            assert ds.nodata is not None and np.isnan(ds.nodata)
            values = ds.read(1)
        with rasterio.open(ROOT / "data/source_mirrors/footprint-mask.tif") as ds:
            foot = ds.read(1) == 1
        assert np.array_equal(np.isfinite(values), foot)
        assert float(values[foot].max()) == 1.0

    def test_uniqueness_and_no_score_claim(self, h51_receipt):
        assert h51_receipt["uniqueness"]["hash_collisions"] == []
        assert h51_receipt["organizer_score"] is None
        assert "No organizer score" in h51_receipt["score_claim"]

    def test_emission_is_budget_trimmed_union(self, h51_receipt):
        sd = h51_receipt["set_distances"]
        assert sd["cells_outside_union"] == 0
        assert sd["cells_in_union"] == sd["budget_cells"]
        assert sd["union_cells"] > sd["budget_cells"]

    def test_not_the_naive_mean(self, h51_receipt):
        rc = h51_receipt["rank_correlations"]
        assert rc["pl_vs_naive_mean_in_footprint"] < 0.9999


class TestH50BArtifact:
    def test_radiometric_mirror_sha_and_grid(self):
        mirror = ROOT / "data/source_mirrors/geodawn_rad_u8.tif"
        assert mirror.is_file()
        assert sha256(mirror) == SHA_RAD
        with rasterio.open(mirror) as ds:
            assert str(ds.crs) == "EPSG:32611"
            assert (ds.width, ds.height) == (3292, 3730)
            assert ds.count == 4
            assert list(ds.descriptions) == ["K", "Th", "U", "TC"]

    def test_preregistration_precedes_evaluation(self, h50b_receipt):
        holdout = json.loads((EVIDENCE / "holdout_h50b_20261007.json").read_text())
        assert h50b_receipt["preregistered_utc"] < holdout["evaluated_utc"]

    def test_probe_is_binary_and_honest(self, h50b_receipt):
        with rasterio.open(ROOT / h50b_receipt["primary_file"]) as ds:
            values = ds.read(1)
        assert set(np.unique(values).tolist()) <= {0.0, 1.0}
        assert int((values > 0).sum()) == h50b_receipt["emitted_cells"]
        assert h50b_receipt["organizer_score"] is None

    def test_negative_result_recorded(self):
        holdout = json.loads((EVIDENCE / "holdout_h50b_20261007.json").read_text())
        assert holdout["numeric_gate"]["passed"] is False
        assert holdout["slot_decision"]["cleared"] is False
        assert "NEGATIVE_RESULT" in holdout["status"] or "NOT_SLOT_CLEARED" in holdout["status"]


class TestSessionEvidenceConsistency:
    def test_h51_holdout_gate_failed(self):
        holdout = json.loads((EVIDENCE / "holdout_h51_20261007.json").read_text())
        assert holdout["numeric_gate"]["passed"] is False
        assert holdout["slot_decision"]["cleared"] is False
        sgmc = holdout["sgmc_offcat_results"]
        assert sgmc["h49_yager_pignistic_budget"]["mean_dti"] > sgmc["h51_plausibility_budget"]["mean_dti"]

    def test_current_site_routes_older_artifacts_to_history(self):
        docs = conftest.DOCS
        landing = (docs / "index.html").read_text()
        archive = (docs / "archive-main-pages/pre-h55-20261007/index.html").read_text()
        executive = (docs / "executive-summary.html").read_text()
        assert "Historical H48–H55 surfaces" in landing
        assert "archive-main-pages/pre-h55-20261007/index.html" in landing
        assert h51_primary().name in archive
        assert h50b_primary().name in archive
        assert "research/h51-h50b-results-20261007.md" in executive

    def test_live_pages_have_no_broken_local_links(self):
        broken = []
        for html in sorted(conftest.DOCS.rglob("*.html")):
            if "archive-main-pages" in html.parts:
                continue  # frozen historical snapshots; links documented as stale
            text = html.read_text(encoding="utf-8", errors="ignore")
            for match in re.finditer(r'(?:href|src)="([^"]+)"', text):
                url = match.group(1).split("#")[0]
                if not url or url.startswith(("http://", "https://", "mailto:", "data:")):
                    continue
                if not (html.parent / url).exists():
                    broken.append(f"{html}: {match.group(1)}")
        assert broken == []
