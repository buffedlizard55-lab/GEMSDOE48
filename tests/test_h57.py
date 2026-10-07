"""H57 contract: format, uniqueness, the exact emission, and an independent
re-derivation of the marginal-credit projection that the site publishes.

The scientific assertions here deliberately do NOT trust the build receipt. The
marginal credit is recomputed from the shipped GeoTIFF and the official metric, and
the identity ``sum_g max(K_S - K_A, 0) == T_SGMC(S) - T_SGMC(A)`` is asserted — that
identity is what exposed the per-offset double-count in the exploratory scripts
(``scratch/newcov2.py``, ``scratch/bcv.py``) that first reported 4/4 spatial folds.
"""
from __future__ import annotations

import hashlib
import html
import json
import pathlib
import re

import numpy as np
import pytest
import rasterio
from scipy import ndimage as ndi

REPO = pathlib.Path(__file__).resolve().parents[1]
import sys

if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from gemsdoe48 import metric as M  # noqa: E402

EV = REPO / "evidence"
RECEIPT = EV / "build_h57_receipt_20261007.json"
SLUG = "GEMSDOE48-H57-ds-relief-augmented-20261007-e6b785718c07"
PRIMARY = REPO / "docs" / "downloads" / f"{SLUG}.tif"
PARENT = REPO / "data" / "families" / "dotted_b2_prune_02778.tif"
SHA256 = "28a51fb032b8f2cfd1f04ad3bd429c29d7bb780d36961fea783ff8099130986e"
DOTS = 58031
ALPHA = 0.9324
DENOM_CONST = 11215.3

needs_artifacts = pytest.mark.skipif(
    not (RECEIPT.exists() and PRIMARY.exists()),
    reason="H57 artefacts not built in this checkout")


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


# --------------------------------------------------------------------------- format
@needs_artifacts
def test_primary_matches_the_recorded_sha256():
    assert sha256_file(PRIMARY) == SHA256


@needs_artifacts
def test_primary_is_portal_range_error_immune():
    """The portal rejected an earlier upload with 'Predicted values must be in range
    [0, 1]'. A vectorised ``np.all((v >= 0) & (v <= 1))`` must not fail on a NaN."""
    with rasterio.open(PRIMARY) as ds:
        v = ds.read(1)
        assert ds.count == 1
        assert ds.dtypes[0] == "float32"
        assert (ds.height, ds.width) == (3730, 3292)
        assert str(ds.crs) == "EPSG:32611"
        t = ds.transform
        assert (t.a, t.e, t.c, t.f) == (100.0, -100.0, 243350.0, 4508550.0)
    assert np.isfinite(v).all(), "a NaN anywhere can make a vectorised range check raise/fail"
    assert float(v.min()) >= 0.0 and float(v.max()) <= 1.0
    assert bool(np.all((v >= 0.0) & (v <= 1.0)))


@needs_artifacts
def test_format_audit_receipt_agrees():
    audit = json.loads((EV / "h57_format_audit_20261007.json").read_text())
    assert audit["positive_cells"] == DOTS
    assert audit["all_cells_finite"] and audit["all_cells_in_range_0_1"]
    assert audit["portal_range_error_immune"] is True


# ----------------------------------------------------------------------- uniqueness
@needs_artifacts
def test_uniqueness_receipt_verdict_is_unique():
    u = json.loads((EV / "h57_uniqueness_20261007.json").read_text())
    assert u["candidate"]["sha256"] == SHA256
    assert u["verdict"] == "UNIQUE", u["duplicates_byte_or_support_identical"]
    assert u["max_overlap_excluding_companions"]["identical_support"] is False
    assert u["max_overlap_excluding_companions"]["jaccard"] < 0.05


# ------------------------------------------------------------------------- emission
@needs_artifacts
def test_emission_is_parent_union_lidar_and_avoids_the_catalogue():
    with rasterio.open(REPO / "data" / "official" / "labels.tif") as ds:
        lab = ds.read(1).astype(np.float32)
    footprint, catalogue = lab != -1, lab == 1
    dcat = ndi.distance_transform_edt(~catalogue)
    S, A = positives(PRIMARY), positives(PARENT)
    L = S & ~A
    assert int(S.sum()) == DOTS
    assert int(A.sum()) == 37654
    assert int(L.sum()) == DOTS - 37654
    assert bool((S == (A | L)).all())
    assert int((S & catalogue).sum()) == 0, "dots on published catalogue cells earn nothing"
    assert int((S & ~footprint).sum()) == 0, "no dot may sit outside the footprint"
    assert float(dcat[L].min()) > 2.0, "new dots must clear the 200 m catalogue flank"
    # no new dot may be within kernel reach of a parent dot: that is what makes the
    # addition non-redundant rather than a re-price of coverage the parent already had
    assert bool((M.max_kernel_to_truth(A)[L] == 0).all())


# ------------------------------------------------- independent projection re-derivation
def surrogate_truth() -> np.ndarray:
    """G = SGMC-derived faults & footprint & d(catalogue) > 3  (|G| = 62,122).

    Rebuilt from the tracked official rasters so the test does not depend on the
    gitignored scratch cache.
    """
    with rasterio.open(REPO / "data" / "official" / "labels.tif") as ds:
        lab = ds.read(1).astype(np.float32)
    with rasterio.open(REPO / "data" / "official" / "derived_sgmc_faults_100m.tif") as ds:
        sgmc = ds.read(1) > 0
    footprint, catalogue = lab != -1, lab == 1
    dcat = ndi.distance_transform_edt(~catalogue)
    return sgmc & footprint & (dcat > 3)


@needs_artifacts
def test_marginal_credit_recomputed_from_the_shipped_file():
    G = surrogate_truth()
    assert int(G.sum()) == 62122
    gi = np.flatnonzero(G.ravel())
    S, A = positives(PRIMARY), positives(PARENT)
    K_A = M.max_kernel_to_truth(A).ravel()
    K_S = M.max_kernel_to_truth(S).ravel()
    t_a, t_s = float(K_A[gi].sum()), float(K_S[gi].sum())
    gain = np.maximum(K_S[gi] - K_A[gi], 0.0)
    # the identity that the exploratory scripts violated by accumulating per offset
    assert abs(gain.sum() - (t_s - t_a)) < 1e-6
    n_new = int((S & ~A).sum())
    credit = ALPHA * gain.sum() / n_new
    dti_parent = ALPHA * t_a / (0.2 * int(A.sum()) + DENOM_CONST)
    dti_h57 = ALPHA * t_s / (0.2 * int(S.sum()) + DENOM_CONST)
    break_even = 0.2 * dti_parent
    r = json.loads(RECEIPT.read_text())["proxy_projection_LABELLED_PROXY_ONLY"]
    assert abs(t_a - r["T_SGMC_parent"]) < 0.5
    assert abs(t_s - r["T_SGMC_h57"]) < 0.5
    assert abs(credit - r["marginal_credit_per_lidar_dot"]) < 1e-3
    assert abs(dti_h57 - r["DTI_h57"]) < 5e-4
    # the actual decision criterion: the candidate must beat the metric's break-even
    assert credit > break_even, f"credit {credit:.4f} <= break-even {break_even:.4f}"
    assert credit / break_even > 2.0, "margin too thin to spend a weekly slot"
    assert dti_h57 > dti_parent + 0.05


@needs_artifacts
def test_every_spatial_block_is_disclosed_including_the_one_that_fails():
    blocks = json.loads(RECEIPT.read_text())["proxy_projection_LABELLED_PROXY_ONLY"]["spatial_blocks"]
    assert len(blocks) == 4
    assert sum(1 for b in blocks if b["pass"]) == 3, (
        "the receipt must keep reporting the block that fails, not hide it")
    worst = min(blocks, key=lambda b: b["G"])
    assert worst["pass"] is False
    assert worst["G"] < 5000, "the failing block should be the truth-poor one"


# -------------------------------------------------------------- Dempster–Shafer layers
@needs_artifacts
@pytest.mark.parametrize("tag", ["belief", "mtheta", "conflict-k", "plausibility"])
def test_diagnostic_layers_are_normalised(tag):
    p = REPO / "docs" / "downloads" / "diagnostics" / f"{SLUG}-diag-{tag}.tif"
    assert p.exists()
    with rasterio.open(p) as ds:
        v = ds.read(1)
    assert np.isfinite(v).all() and float(v.min()) >= 0.0 and float(v.max()) <= 1.0


@needs_artifacts
def test_belief_is_not_the_naive_mean_of_the_two_parents():
    with rasterio.open(REPO / "docs" / "downloads" / "diagnostics" / f"{SLUG}-diag-belief.tif") as ds:
        bel = ds.read(1).astype(np.float64)
    A, B = positives(PARENT), positives(REPO / "data" / "families" / "tip_stepover_r30_02632.tif")
    naive = 0.5 * A + 0.5 * B
    r = json.loads(RECEIPT.read_text())["not_the_naive_mean"]
    assert r["pearson_bel_vs_binary_mean"] < 0.95, "belief would be indistinguishable from the mean"
    assert r["mean_abs_diff_on_positive_cells"] > 0.05
    assert r["max_abs_diff_vs_binary_mean"] > 0.5
    assert abs(r["pearson_bel_vs_binary_mean"] - float(np.corrcoef(bel.ravel(), naive.ravel())[0, 1])) < 1e-6
    m = json.loads(RECEIPT.read_text())["dempster"]
    assert m["mtheta_max"] > 0.0, "the unassigned mass m(Theta) must be shipped, not averaged away"


# ------------------------------------------------------------------------------- site
def page(name: str) -> str:
    return (REPO / "docs" / name).read_text()


@pytest.mark.parametrize("name", ["index.html", "executive-summary.html", "submission-guide.html"])
def test_h57_download_is_the_first_content_on_every_entry_page(name):
    body = page(name).split("<main", 1)[1]
    link = body.index(f'href="downloads/{SLUG}.tif"')
    before = body[:link]
    assert "<table" not in before, f"{name}: a table appears before the one-click download"
    assert "bigbtn" in before
    assert len(before) < 3500, f"{name}: too much content before the download button"


@pytest.mark.parametrize("name", ["index.html", "executive-summary.html", "submission-guide.html"])
def test_verdict_is_unmistakable_and_both_halves_are_stated(name):
    text = flat(page(name))
    assert "DOWNLOAD: OK" in text, f"{name}: the download verdict is missing"
    assert "SUBMIT: RECOMMENDED" in text, f"{name}: the submit verdict is missing"
    assert "0.3844" in text, f"{name}: the projection is missing"
    assert "proxy" in text.lower(), f"{name}: the projection must be labelled as a proxy"
    assert SLUG in text, f"{name}: the submission name is missing"


@pytest.mark.parametrize("name", ["index.html", "executive-summary.html", "submission-guide.html"])
def test_paste_ready_note_and_sha_are_published(name):
    text = page(name)
    assert "58,031 dots. id e6b785718c07" in flat(text)
    assert SHA256 in text


def test_superseded_candidates_are_not_advertised_as_submissions():
    """H55/H56 lost on the forward model; they must not read as cleared submissions."""
    for name in ("index.html", "executive-summary.html"):
        text = flat(page(name))
        assert "SUBMIT: NOT RECOMMENDED" in text or "Superseded" in text
