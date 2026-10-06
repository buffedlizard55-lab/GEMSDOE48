"""End-to-end checks against the committed deliverable.

These tests need the raw inputs and the built artifact, neither of which is in
Git.  They skip cleanly when the data is absent, so the suite is green on a
fresh clone and meaningful on a restored workspace.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
TIF = ROOT / "docs" / "downloads" / "gemsdoe48-h49-ds-conflict-balanced-20261006-e6f08013888b.tif"
AUDIT = ROOT / "docs" / "downloads" / "gemsdoe48-h49-ds-conflict-balanced-20261006-audit.json"
SHA256 = "e6f08013888b625db7d187d79bb75ba36c45d068081b77a3dd405ab7eec3d472"

rasterio = pytest.importorskip("rasterio")

needs_artifacts = pytest.mark.skipif(
    not (TIF.exists() and AUDIT.exists()),
    reason="built deliverable not present; run scripts/build_submission.py",
)
needs_raw = pytest.mark.skipif(
    not all((RAW / f).exists() for f in ("dotted.tif", "tip.tif", "labels.tif", "sample_submission.tif")),
    reason="raw inputs not restored; run scripts/fetch_inputs.sh",
)


def _read(path: Path, bidx: int = 1):
    with rasterio.open(path) as ds:
        return ds.read(bidx), ds.profile


@needs_artifacts
def test_audit_reports_a_full_format_pass():
    audit = json.loads(AUDIT.read_text())
    assert audit["format_pass"] is True
    fmt = audit["format_checks"]
    assert fmt["portal_range_ok"] is True
    assert fmt["bands"] == 1
    assert fmt["dtype"] == "float32"
    assert fmt["epsg"] == 32611
    assert tuple(fmt["shape"]) == (3730, 3292)
    assert fmt["nodata"] is None
    assert fmt["all_finite"] is True
    assert fmt["out_of_range_count"] == 0
    assert fmt["min"] >= 0.0 and fmt["max"] <= 1.0


@needs_artifacts
def test_independent_reread_is_finite_and_in_unit_interval():
    arr, _ = _read(TIF)
    assert arr.dtype == np.float32
    assert arr.shape == (3730, 3292)
    assert np.isfinite(arr).all(), "portal rejects non-finite values"
    assert arr.min() >= 0.0 and arr.max() <= 1.0, "portal: 'Predicted values must be in range [0, 1]'"
    assert (arr > 0).sum() == 47_905


@needs_artifacts
def test_artifact_hash_matches_the_reported_sha256():
    import hashlib
    h = hashlib.sha256(TIF.read_bytes()).hexdigest()
    assert h == SHA256, "deliverable changed; update README, docs and this assertion together"


@needs_artifacts
def test_audit_recorded_the_not_the_average_result():
    audit = json.loads(AUDIT.read_text())
    check = audit["not_the_average_check"]
    assert check["pass"] is True
    assert check["pixel_identical_to_naive_mean"] is False
    assert abs(check["pearson_vs_naive_mean"]) < 0.95


@needs_artifacts
@needs_raw
def test_submission_is_not_the_naive_mean_nor_either_parent():
    from gems48.evidence import pignistic, minmax_unit, kernel_support
    from gems48.evidence import combine_yager, discounted_binary_mass

    sub, _ = _read(TIF)
    dotted, _ = _read(RAW / "dotted.tif")
    tip, _ = _read(RAW / "tip.tif")
    dotted = np.nan_to_num(dotted.astype(np.float64), nan=0.0)
    tip = np.nan_to_num(tip.astype(np.float64), nan=0.0)
    naive = 0.5 * (dotted + tip)

    assert not np.array_equal(sub.astype(np.float64), naive)
    assert not np.array_equal(sub.astype(np.float64), np.float64(dotted > 0))
    assert not np.array_equal(sub.astype(np.float64), np.float64(tip > 0))
    assert not np.array_equal(sub.astype(np.float64), np.float64((dotted > 0) | (tip > 0)))

    # and its support genuinely mixes the parents
    s = sub > 0
    assert (s & (dotted > 0) & (tip > 0)).sum() > 0      # agreement
    assert (s & (dotted > 0) & (tip == 0)).sum() > 0     # dotted-only
    assert (s & (tip > 0) & (dotted == 0)).sum() > 0     # tip-only
    assert (s & (dotted == 0) & (tip == 0)).sum() > 0    # compromise cells


@needs_artifacts
@needs_raw
def test_yager_conserves_mass_and_keeps_conflict():
    from gems48.evidence import combine_dempster, combine_yager, conjunctive_components
    from gems48.evidence import discounted_binary_mass, minmax_unit, kernel_support

    with rasterio.open(RAW / "dotted.tif") as ds:
        dotted = ds.read(1)
    with rasterio.open(RAW / "tip.tif") as ds:
        tip = ds.read(1)
    sd = kernel_support(np.nan_to_num(dotted, nan=0.0) > 0, 3)
    st = kernel_support(np.nan_to_num(tip, nan=0.0) > 0, 3)
    a = discounted_binary_mass(minmax_unit(sd), 0.90)
    b = discounted_binary_mass(minmax_unit(st), 0.802)

    m_f, m_n, m_t, K = conjunctive_components(a, b)
    assert float(m_f.min()) >= -1e-12 and float(m_n.min()) >= -1e-12
    assert np.abs(m_f + m_n + m_t + K - 1.0).max() < 1e-12

    y_f, y_n, y_t, y_K = combine_yager(a, b)
    assert np.abs(y_f + y_n + y_t - 1.0).max() < 1e-12
    assert np.abs(y_t - (m_t + K)).max() < 1e-12       # Yager transfers conflict to Theta

    # the classical rule is the one that destroys conflict; make sure we did not use it
    d_f, d_n, d_K = combine_dempster(a, b)
    assert int((K > 1e-6).sum()) > 0
    on_conflict = K > 0.1
    assert int(on_conflict.sum()) > 0
    # Yager keeps the conflict visible as unassigned mass; Dempster's normalisation
    # divides it away into the two crisp hypotheses.
    d_unassigned = 1.0 - d_f - d_n
    assert bool((y_t[on_conflict] > 0.0).all())
    assert bool((y_t[on_conflict] > d_unassigned[on_conflict]).all())
    assert bool((y_t[on_conflict] >= K[on_conflict] - 1e-12).all())
    assert float(d_unassigned[on_conflict].max()) < float(y_t[on_conflict].min())


@needs_raw
def test_h49_beats_the_dotted_parent_on_the_blocked_holdout():
    from gems48.metric import dti_result as dti
    from gems48.evidence import combine_yager, discounted_binary_mass, kernel_support, minmax_unit, pignistic

    with rasterio.open(RAW / "dotted.tif") as ds:
        dotted = np.nan_to_num(ds.read(1).astype(np.float64), nan=0.0)
    with rasterio.open(RAW / "tip.tif") as ds:
        tip = np.nan_to_num(ds.read(1).astype(np.float64), nan=0.0)
    with rasterio.open(RAW / "labels.tif") as ds:
        labels = np.nan_to_num(ds.read(1).astype(np.float64), nan=0.0)

    sub, _ = _read(TIF)
    sub = sub.astype(np.float64)
    # same proxy truth as scripts/validate_proxy.py: SGMC faults, off the public catalogue
    sgmc_raw = RAW / "external" / "derived_sgmc_faults_100m_u8.tif"
    assert sgmc_raw.exists()
    with rasterio.open(sgmc_raw) as ds:
        sgmc = (ds.read(1) > 0).astype(np.float64)
    truth = (sgmc * (labels == 0)).astype(np.float64)

    def blocks(n=4):
        h, w = truth.shape
        bs, bt = h // n, w // n
        for i in range(n):
            for j in range(n):
                yield (slice(i * bs, (i + 1) * bs if i < n - 1 else h),
                       slice(j * bt, (j + 1) * bt if j < n - 1 else w))

    def blocked(pred):
        vals = []
        for sl in blocks():
            t = truth[sl]
            if t.sum() < 50:
                continue
            vals.append(dti(pred[sl], t).dti)
        return float(np.mean(vals)), len(vals)

    h49, n = blocked(sub)
    parent, _ = blocked(dotted)
    assert n == 11
    assert h49 > parent, (h49, parent)
