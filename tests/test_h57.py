"""H57-RELIEF artifact integrity and metric-identity regression tests.

These tests preserve local construction/format evidence while preventing the old
FPw=S-TPw surrogate projection and recommendation from becoming current guidance.
They do not treat public-proxy measurements as private-label scores.
"""
from __future__ import annotations

import hashlib
import html
import json
import pathlib
import re
import sys

import numpy as np
import pytest
import rasterio
from scipy import ndimage as ndi

REPO = pathlib.Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

EV = REPO / "evidence"
RECEIPT = EV / "build_h57_receipt_20261007.json"
ERRATUM = EV / "h57_metric_identity_erratum_20261007.json"
SLUG = "GEMSDOE48-H57-ds-relief-augmented-20261007-e6b785718c07"
PRIMARY = REPO / "docs" / "downloads" / f"{SLUG}.tif"
PARENT = REPO / "data" / "families" / "dotted_b2_prune_02778.tif"
SHA256 = "28a51fb032b8f2cfd1f04ad3bd429c29d7bb780d36961fea783ff8099130986e"
DOTS = 58031

needs_artifacts = pytest.mark.skipif(
    not (RECEIPT.exists() and PRIMARY.exists()),
    reason="H57-RELIEF artifacts not present in this checkout")


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def positives(path: pathlib.Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        return np.nan_to_num(ds.read(1).astype(np.float32), nan=0.0) > 0


def flat(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(text))


@needs_artifacts
def test_local_primary_hash_and_grid_match_receipt():
    assert sha256_file(PRIMARY) == SHA256
    receipt = json.loads(RECEIPT.read_text())
    assert receipt["files"]["primary_zeros_outside"]["sha256"] == SHA256
    with rasterio.open(PRIMARY) as ds:
        v = ds.read(1)
        assert ds.count == 1
        assert ds.dtypes[0] == "float32"
        assert (ds.height, ds.width) == (3730, 3292)
        assert str(ds.crs) == "EPSG:32611"
        assert (ds.transform.a, ds.transform.e, ds.transform.c, ds.transform.f) == (
            100.0, -100.0, 243350.0, 4508550.0)
    assert np.isfinite(v).all()
    assert float(v.min()) >= 0.0 and float(v.max()) <= 1.0


@needs_artifacts
def test_format_audit_is_local_not_portal_acceptance():
    audit = json.loads((EV / "h57_format_audit_20261007.json").read_text())
    assert audit["status"] == "PASS_LOCAL_FORMAT_AUDIT_NOT_ORGANIZER_ACCEPTANCE"
    assert audit["sha256"] == SHA256
    assert audit["positive_cells"] == DOTS
    assert audit["all_cells_finite"] and audit["all_cells_in_range_0_1"]
    assert audit.get("organizer_acceptance_tested", False) is False
    assert "NOT_ORGANIZER_ACCEPTANCE" in audit["status"]


@needs_artifacts
def test_local_uniqueness_receipt_is_bounded_and_does_not_claim_organizer_uniqueness():
    u = json.loads((EV / "h57_uniqueness_20261007.json").read_text())
    assert u["candidate"]["sha256"] == SHA256
    assert u["verdict"] == "UNIQUE", u["duplicates_byte_or_support_identical"]
    assert u["compared_files"] == 99
    assert u["max_overlap_excluding_companions"]["identical_support"] is False
    assert u["max_overlap_excluding_companions"]["jaccard"] < 0.05
    assert "local" in u["uniqueness_scope"].lower()
    assert "not organizer-side or global" in u["uniqueness_scope"].lower()
    assert u["organizer_uniqueness_tested"] is False
    assert u["global_uniqueness_established"] is False


@needs_artifacts
def test_emission_is_the_recorded_parent_plus_lidar_support_and_avoids_catalogue():
    with rasterio.open(REPO / "data" / "official" / "labels.tif") as ds:
        lab = ds.read(1).astype(np.float32)
    footprint, catalogue = lab != -1, lab == 1
    dcat = ndi.distance_transform_edt(~catalogue)
    surface, parent = positives(PRIMARY), positives(PARENT)
    lidar = surface & ~parent
    assert int(surface.sum()) == DOTS
    assert int(parent.sum()) == 37654
    assert int(lidar.sum()) == DOTS - 37654
    assert bool((surface == (parent | lidar)).all())
    assert int((surface & catalogue).sum()) == 0
    assert int((surface & ~footprint).sum()) == 0
    assert float(dcat[lidar].min()) > 2.0


@needs_artifacts
@pytest.mark.parametrize("tag", ["belief", "mtheta", "conflict-k", "plausibility"])
def test_dempster_diagnostics_are_finite_and_in_range(tag):
    path = REPO / "docs" / "downloads" / "diagnostics" / f"{SLUG}-diag-{tag}.tif"
    assert path.is_file()
    with rasterio.open(path) as ds:
        values = ds.read(1)
    assert np.isfinite(values).all()
    assert float(values.min()) >= 0.0 and float(values.max()) <= 1.0


@needs_artifacts
def test_belief_differs_from_naive_mean_but_is_not_claimed_as_improved_prediction():
    with rasterio.open(REPO / "docs" / "downloads" / "diagnostics" / f"{SLUG}-diag-belief.tif") as ds:
        belief = ds.read(1).astype(np.float64)
    a = positives(PARENT)
    b = positives(REPO / "data" / "families" / "tip_stepover_r30_02632.tif")
    naive = 0.5 * a + 0.5 * b
    receipt = json.loads(RECEIPT.read_text())
    stats = receipt["not_the_naive_mean"]
    assert stats["pearson_bel_vs_binary_mean"] < 0.95
    assert stats["mean_abs_diff_on_positive_cells"] > 0.05
    assert stats["max_abs_diff_vs_binary_mean"] > 0.5
    assert abs(stats["pearson_bel_vs_binary_mean"] - float(np.corrcoef(belief.ravel(), naive.ravel())[0, 1])) < 1e-6
    assert receipt["dempster"]["mtheta_max"] > 0.0
    assert "unassigned" in receipt.get("dempster_semantics", "unassigned/ignorance").lower()


@needs_artifacts
def test_historical_inversion_is_retained_only_as_invalid_forensic_record():
    receipt = json.loads(RECEIPT.read_text())
    audit = json.loads(ERRATUM.read_text())
    assert receipt["candidate_id"] == "H57-RELIEF"
    assert receipt["verdict"]["download"] == "OK FOR INSPECTION"
    assert receipt["verdict"]["submit"] == "NOT CLEARED TO SUBMIT"
    assert receipt["metric_projection_status"]["status"] == "INVALIDATED_METRIC_IDENTITY_DO_NOT_USE"
    assert receipt["metric_projection_status"]["recomputed_by_current_builder"] is False
    old = audit["withdrawn_metrics"]
    assert old["candidate_dti"] == pytest.approx(0.3844)
    assert old["break_even_credit_per_dot"] == pytest.approx(0.0549)
    assert audit["status"] == "INVALIDATED_METRIC_IDENTITY_DO_NOT_USE"
    assert audit["decision"]["weekly_slot"] == "NOT CLEARED"
    assert audit["decision"]["portal_acceptance"] == "NOT TESTED"


def test_builder_cannot_regenerate_the_invalid_live_projection():
    text = (REPO / "scripts" / "build_submission_h57.py").read_text()
    assert "proxy_projection_LABELLED_PROXY_ONLY" not in text
    assert "DTI_h57" not in text
    assert "marginal_credit_per_lidar_dot" not in text
    assert "does not regenerate live-equivalent DTI" in text
    assert "NOT CLEARED TO SUBMIT" in text


def test_builder_defaults_to_ignored_scratch_outputs_not_archival_files():
    text = (REPO / "scripts" / "build_submission_h57.py").read_text()
    assert 'scratch_dir = ROOT / "scratch" / "h57-relief-rebuild"' in text
    assert 'ap.add_argument("--out-dir", default=str(scratch_dir))' in text
    assert 'ap.add_argument("--receipt", default=str(scratch_dir / "build_h57_receipt.json"))' in text
    assert 'default=str(ROOT / "docs" / "downloads")' not in text
    assert 'default=str(ROOT / "evidence" / "build_h57_receipt_20261007.json")' not in text


def test_current_h57_pages_show_inspection_only_and_clear_namespace():
    report = flat((REPO / "docs" / "research" / "h57-ds-relief-augmented-20261007.md").read_text())
    assert "OK TO DOWNLOAD FOR INSPECTION" in report
    assert "NOT OK / NOT CLEARED TO SUBMIT" in report
    assert "metric-identity correction" in report.lower()
    assert "Neither H57-A refers to this relief artifact" in report
    erratum = flat((REPO / "docs" / "research" / "h57-relief-metric-erratum-20261007.md").read_text())
    assert "INVALIDATED / FORENSIC ONLY" in erratum
    assert "0.3844" in erratum and "not" in erratum.lower()


@pytest.mark.parametrize("name", ["index.html", "executive-summary.html", "submission-guide.html"])
def test_entry_pages_do_not_clear_the_h57_relief_artifact(name):
    text = flat((REPO / "docs" / name).read_text()).lower()
    assert "no weekly" in text and "cleared" in text
    assert "h57-relief" in text
    assert "not cleared to submit" in text


def test_no_h57_active_builder_or_test_treats_projection_as_a_submission_gate():
    source = (REPO / "scripts" / "build_submission_h57.py").read_text().lower()
    tests = (REPO / "tests" / "test_h57.py").read_text().lower()
    assert "metric-optimal binary decision surface" not in source
    invalid_gate = "credit > break_" + "even"
    assert invalid_gate not in tests
