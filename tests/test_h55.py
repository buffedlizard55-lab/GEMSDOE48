"""Tests for the H55 live-anchored forward model, conduit layer, and emission builder.

Tests that need the git-ignored ``data/raw`` mirrors skip cleanly when those mirrors
have not been restored (``python scripts/restore_h55_inputs.py``), matching the
repository's existing data-dependent-test convention.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import numpy as np
import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gemsdoe48 import conduit, h55, live_model, metric as current_metric  # noqa: E402
from gemsdoe48.dempster_shafer import dempster_combine  # noqa: E402
from gemsdoe48.geotiff import HEIGHT, WIDTH, write_float32_zeros_outside  # noqa: E402
from gemsdoe48.metric import dti_fast, triangular_kernel  # noqa: E402

CORE = REPO / "data/families/dotted_b2_prune_02778.tif"
BACKBONE = REPO / "data/raw/scored/h19_5_01922.tif"
CONDUIT_CSV = REPO / "data/raw/external/gdr_wellspring_in_footprint.csv"
RECEIPT = REPO / "evidence/build_h55_receipt_20261007.json"
CALIBRATION = REPO / "evidence/live_model_calibration_20261007.json"
PRIMARY = REPO / ("docs/downloads/GEMSDOE48-H55-conduit-conflict-priced-"
                  "20261007-055da9855353-zeros-outside.tif")


def needs(path: pathlib.Path):
    return pytest.mark.skipif(not path.exists(), reason=f"mirror absent: {path.name}")


# ---------------------------------------------------------------------------
# metric algebra
# ---------------------------------------------------------------------------

def test_triangular_kernel_reach_and_shape():
    assert triangular_kernel(np.array([0.0, 150.0, 300.0, 301.0])) .tolist() == [1.0, 0.5, 0.0, 0.0]


def test_retired_global_binary_optimality_claim_is_withdrawn():
    """The one-variable derivative cannot establish global raster optimality."""
    assert live_model.MODEL_VALIDITY_STATUS == "INVALIDATED_FORENSIC_ONLY_DO_NOT_USE_FOR_PROMOTION"
    assert "global binary optimality is not established" in current_metric.optimal_value_is_binary()


def test_live_ladder_cli_requires_explicit_forensic_opt_in():
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/live_ladder_analysis.py")],
        cwd=REPO, capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert "--legacy-audit-only" in result.stderr + result.stdout
    assert "invalidated" in (result.stderr + result.stdout).lower()


def test_readme_marks_historical_inversion_builders_forensic_only():
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    for script in ("scripts/calibrate_live_model.py", "scripts/build_submission_h55.py",
                   "scripts/live_ladder_analysis.py"):
        commands = [line for line in readme.splitlines()
                    if script in line and "python" in line]
        assert commands, f"missing historical command for {script}"
        assert all("--legacy-audit-only" in line for line in commands), (script, commands)


# ---------------------------------------------------------------------------
# forward model
# ---------------------------------------------------------------------------

def test_hidden_truth_fit_is_explicit_forensic_reproduction_only():
    with pytest.raises(RuntimeError, match="invalidated FPw=S-TPw surrogate"):
        live_model.fit_hidden_truth([44090, 40199, 37654], [0.2600, 0.2708, 0.2778])
    fit = live_model.fit_hidden_truth(
        [44090, 40199, 37654], [0.2600, 0.2708, 0.2778], legacy_audit_only=True)
    assert fit["validity_status"] == live_model.MODEL_VALIDITY_STATUS
    assert fit["promotion_use"] == "NONE — historical surrogate values only."
    assert "FPw=S-TPw" in fit["invalidation_reason"]
    assert np.isfinite(fit["hidden_truth_px"])  # schema/sanity only, never evidence of truth density


def test_invert_truth_requires_explicit_forensic_opt_in():
    with pytest.raises(RuntimeError, match="invalidated FPw=S-TPw surrogate"):
        live_model.invert_truth(0.2778, 37_654, 14_027.5)
    # The explicit path exists only for forensic reproduction; do not treat its
    # number as an estimate of local or organizer hidden truth.
    value = live_model.invert_truth(0.2778, 37_654, 14_027.5, legacy_audit_only=True)
    assert np.isfinite(value) and value > 0


def test_forward_model_requires_forensic_opt_in_and_labels_outputs():
    with pytest.raises(RuntimeError, match="invalidated FPw=S-TPw surrogate"):
        live_model.ForwardModel(hidden_truth_px=14_027.5, rho=0.068015, target_px=103_805)
    model = live_model.ForwardModel(hidden_truth_px=14_027.5, rho=0.068015,
                                    target_px=103_805, legacy_audit_only=True)
    serialized = model.to_json()
    assert serialized["validity_status"] == live_model.MODEL_VALIDITY_STATUS
    assert serialized["promotion_use"] == "NONE — historical surrogate values only."
    assert "FPw=S-TPw" in serialized["invalidation_reason"]


def test_historical_calibration_receipt_is_explicitly_invalidated():
    if not CALIBRATION.exists():
        pytest.skip("historical calibration receipt not restored")
    receipt = json.loads(CALIBRATION.read_text())
    assert receipt["validity_status"] == live_model.MODEL_VALIDITY_STATUS
    assert "FPw=S-TPw" in receipt["invalidation_reason"]
    assert receipt["promotion_use"] == "NONE — historical surrogate values only."


def test_coverage_is_monotone_under_addition():
    """TPw is a maximum over emitted pixels, so adding a pixel can never reduce it."""
    rng = np.random.default_rng(7)
    target = rng.random((60, 60)) < 0.05
    base = rng.random((60, 60)) < 0.02
    cov0 = live_model.coverage(base, target)
    grown = base.copy()
    grown[30, 30] = True
    grown[10, 10] = True
    cov1 = live_model.coverage(grown, target)
    assert cov1 >= cov0 - 1e-12


# ---------------------------------------------------------------------------
# greedy priced additions
# ---------------------------------------------------------------------------

def test_greedy_incremental_coverage_matches_exact_recomputation_without_a_live_bar():
    rng = np.random.default_rng(11)
    target = rng.random((80, 80)) < 0.06
    core = rng.random((80, 80)) < 0.01
    pool = (rng.random((80, 80)) < 0.30) & ~core
    rows, gains, trace = h55.greedy_priced_additions(core, pool, target, bar=0.0, max_add=60)
    for n in (1, 5, 20, len(rows)):
        if n == 0 or n > len(rows):
            continue
        exact = core.copy()
        exact[rows[:n, 0], rows[:n, 1]] = True
        expected = live_model.coverage(exact, target)
        # This checks geometric bookkeeping only; no live-calibrated threshold is applied.
        actual = trace[n - 1]["coverage"]
        assert abs(actual - expected) <= 1e-5 * max(1.0, expected), (n, expected)
    assert len(gains) == len(trace) == len(rows)


def test_live_pricing_requires_and_marks_a_forensic_only_model():
    with pytest.raises(RuntimeError, match="invalidated FPw=S-TPw surrogate"):
        live_model.ForwardModel(1_000.0, 0.07, 100)
    core = np.zeros((8, 8), dtype=bool)
    pool = np.zeros_like(core)
    target = np.zeros_like(core)
    pool[3, 3] = True
    target[3, 3] = True
    with pytest.raises(RuntimeError, match="invalidated H55 pricing path"):
        h55.price_addition_path(core, pool, target, break_even_bar=0.0,
                                max_add=1, model=object())
    model = live_model.ForwardModel(100.0, 0.5, 1, legacy_audit_only=True)
    result = h55.price_addition_path(core, pool, target, break_even_bar=0.0,
                                    max_add=1, model=model)
    assert result["validity_status"] == live_model.MODEL_VALIDITY_STATUS
    assert result["promotion_use"] == "NONE — historical surrogate outputs only."


def test_dart_throw_enforces_min_separation_and_is_deterministic():
    score = np.zeros((50, 50))
    score[10, 10] = 3.0
    score[10, 12] = 2.0     # 200 m away at 100 m pixels -> excluded by a 3 px rule
    score[10, 20] = 1.0
    score[40, 40] = 0.5
    allowed = score > 0
    first = h55.dart_throw(score, allowed, 3.0, 10)
    second = h55.dart_throw(score, allowed, 3.0, 10)
    assert np.array_equal(first, second), "dart throwing must be deterministic"
    pairs = [(int(a[0]), int(a[1])) for a in first]
    assert (10, 10) in pairs and (10, 12) not in pairs and (10, 20) in pairs
    for i, (r0, c0) in enumerate(pairs):
        for r1, c1 in pairs[i + 1:]:
            assert (r0 - r1) ** 2 + (c0 - c1) ** 2 >= 9 - 1e-9


# ---------------------------------------------------------------------------
# conduit layer
# ---------------------------------------------------------------------------

def test_thermal_tier_rules():
    assert conduit.thermal_tier("Hot", 20.0, None) == 3       # class alone is tier 3
    assert conduit.thermal_tier("", None, 150.0) == 3         # deep reservoir temperature
    assert conduit.thermal_tier("", 50.0, None) == 2
    assert conduit.thermal_tier("", 30.0, 100.0) == 2
    assert conduit.thermal_tier("Warm", 38.9, None) == 1      # Warm maxes out at 38.9 C
    assert conduit.thermal_tier("Cold", 15.0, None) == 0
    assert conduit.thermal_tier("NULL", None, None) == 0
    # the GDR mirror contains 121 records with a trailing space ("Hot "); the reader
    # normalises them, so they must count as Hot rather than be silently dropped
    assert conduit.thermal_tier("Hot ", 20.0, None) == 3


def test_conduit_score_orders_by_tier_then_temperature():
    hot_cool = conduit.conduit_score(3, 40.0, None)
    hot_deep = conduit.conduit_score(3, 40.0, 250.0)
    mid = conduit.conduit_score(2, 120.0, 160.0)
    assert hot_deep > hot_cool
    assert hot_cool > mid


@needs(CONDUIT_CSV)
def test_conduit_reader_drops_the_label_derived_column():
    sites = conduit.read_sites(CONDUIT_CSV)
    assert len(sites) > 20_000
    summary = conduit.summarize(sites)
    assert summary["leaky_columns_dropped"] == ["dist_known_fault_px"]
    assert summary["by_thermal_class"]["Hot"] > 1_500
    assert summary["temp_c"]["max"] > 200.0
    assert summary["geotherm_max_c"]["n_ge_150"] > 100
    tiers = {s.tier for s in sites}
    assert tiers == {0, 1, 2, 3}


@needs(CONDUIT_CSV)
def test_site_arrays_collapse_duplicates_by_maximum():
    sites = conduit.read_sites(CONDUIT_CSV)
    tier, score = conduit.site_arrays(sites, (HEIGHT, WIDTH), min_tier=1)
    assert tier.shape == (HEIGHT, WIDTH)
    assert set(np.unique(tier).tolist()) <= {0, 1, 2, 3}
    assert int((tier >= 1).sum()) < len(sites), "duplicate site reports must collapse"
    assert float(score[tier >= 1].min()) >= 1.0


# ---------------------------------------------------------------------------
# Dempster-Shafer
# ---------------------------------------------------------------------------

def test_dempster_preserves_disagreement_as_unassigned_mass():
    b1 = np.array([[1.0, 1.0, 0.0], [0.0, 0.5, 1.0]])
    b2 = np.array([[1.0, 0.0, 0.0], [1.0, 0.5, 0.0]])
    out = dempster_combine(b1, b2, alpha1=0.6, alpha2=0.6)
    # agreement -> maximal belief; one-sided support -> belief drops AND mTheta rises
    assert out["bel"][0, 0] == pytest.approx(0.84)
    assert out["unc"][0, 0] == pytest.approx(0.16)
    assert out["bel"][0, 1] == pytest.approx(0.375)
    assert out["unc"][0, 1] == pytest.approx(0.25)
    assert out["conflict"][0, 1] == pytest.approx(0.36)
    # K vanishes only at the two corners (0,0) and (1,1); partial agreement at
    # (0.5, 0.5) still carries conflict 0.36*(0.5+0.5-2*0.25) = 0.18
    assert out["conflict"][0, 0] == pytest.approx(0.0)
    assert out["conflict"][0, 2] == pytest.approx(0.0)
    assert out["conflict"][1, 1] == pytest.approx(0.18)
    assert out["conflict"].max() == pytest.approx(0.36)
    # plausibility is belief plus unassigned mass
    assert np.allclose(out["pl"], out["bel"] + out["unc"])
    # masses are a partition of unity after normalisation
    assert np.allclose(out["bel"] + out["not_bel"] + out["unc"], 1.0)


def test_dempster_belief_is_not_the_naive_mean():
    b1 = np.array([[1.0, 1.0, 0.0, 0.0], [0.0, 0.5, 1.0, 0.25]])
    b2 = np.array([[1.0, 0.0, 0.0, 1.0], [1.0, 0.5, 0.0, 0.75]])
    out = dempster_combine(b1, b2, alpha1=0.6, alpha2=0.6)
    naive = 0.5 * (b1 + b2)
    diff = np.abs(out["bel"] - naive)
    assert diff.max() > 0.05
    slope, intercept = np.polyfit(naive.ravel(), out["bel"].ravel(), 1)
    assert np.abs(out["bel"] - (slope * naive + intercept)).mean() > 1e-3


def test_full_conflict_falls_back_to_vacuous_mass_instead_of_dividing_by_zero():
    b1 = np.array([[1.0]])
    b2 = np.array([[0.0]])
    out = dempster_combine(b1, b2, alpha1=1.0, alpha2=1.0)
    assert np.isfinite(out["bel"]).all() and np.isfinite(out["unc"]).all()
    assert out["unc"][0, 0] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# GeoTIFF encoding
# ---------------------------------------------------------------------------

def test_write_float32_zeros_outside_is_range_error_immune(tmp_path):
    footprint = np.zeros((HEIGHT, WIDTH), dtype=bool)
    footprint[100:200, 100:200] = True
    values = np.where(footprint, 1.0, np.nan).astype(np.float32)
    values[150, 150] = 0.0
    profile = {"driver": "GTiff", "width": WIDTH, "height": HEIGHT, "count": 1,
               "dtype": "float32", "crs": "EPSG:32611"}
    out = tmp_path / "x.tif"
    info = write_float32_zeros_outside(out, values, profile, valid_mask=footprint,
                                       description="test", tags={"k": "v"})
    import rasterio
    with rasterio.open(out) as ds:
        back = ds.read(1)
        assert ds.nodata is None
        assert ds.dtypes == ("float32",)
    assert np.isfinite(back).all()
    assert float(back.min()) >= 0.0 and float(back.max()) <= 1.0
    assert np.all(back[~footprint] == 0.0)
    assert info["portal_range_error_immune"] is True
    assert info["encoding"] == "all_finite_zeros_outside"


def test_write_float32_zeros_outside_rejects_out_of_range(tmp_path):
    footprint = np.ones((HEIGHT, WIDTH), dtype=bool)
    profile = {"driver": "GTiff", "width": WIDTH, "height": HEIGHT, "count": 1,
               "dtype": "float32", "crs": "EPSG:32611"}
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        write_float32_zeros_outside(tmp_path / "bad.tif", np.full((HEIGHT, WIDTH), 1.5, np.float32),
                                    profile, valid_mask=footprint, description="bad")


# ---------------------------------------------------------------------------
# built artifacts (data-dependent)
# ---------------------------------------------------------------------------

@needs(RECEIPT)
def test_build_receipt_invalidates_live_model_and_clears_no_slot():
    receipt = json.loads(RECEIPT.read_text())
    assert receipt["validity_status"] == "INVALIDATED_FORENSIC_ONLY_DO_NOT_USE_FOR_PROMOTION"
    assert receipt["submission_decision"].startswith("NOT CLEARED TO SUBMIT")
    assert "FPw=S-TPw" in receipt["invalidation_reason"]
    assert "no organizer receipt links" in receipt["leaderboard_linkage"]
    assert receipt["status"] == "INVALIDATED_FORENSIC_ONLY_NOT_CLEARED_TO_SUBMIT"
    assert receipt["live_model"]["validity_status"] == receipt["validity_status"]
    assert receipt["risk"]["validity_status"] == receipt["validity_status"]
    ds = receipt["dempster_shafer"]
    assert ds["historical_binary_claim_status"].startswith("INVALIDATED")
    assert "why_the_emission_is_binary" not in ds


@needs(PRIMARY)
def test_primary_artifact_is_binary_in_range_and_contains_the_core():
    import rasterio
    with rasterio.open(PRIMARY) as ds:
        values = ds.read(1)
        assert ds.count == 1 and ds.dtypes == ("float32",)
        assert ds.crs.to_string() == "EPSG:32611"
        assert ds.nodata is None
        assert (ds.width, ds.height) == (WIDTH, HEIGHT)
    assert np.isfinite(values).all()
    assert set(np.unique(values).tolist()) == {0.0, 1.0}
    if CORE.exists():
        core = live_model.load_binary(CORE)
        emission = values > 0.5
        assert int((emission & core).sum()) == int(core.sum())
        assert int(emission.sum()) > int(core.sum())


@needs(RECEIPT)
def test_uniqueness_audit_passed():
    path = REPO / "evidence/h55_uniqueness_audit_20261007.json"
    if not path.exists():
        pytest.skip("uniqueness audit not run yet")
    audit = json.loads(path.read_text())
    assert audit["all_checks_passed"] is True
    assert audit["identical_prior_candidates"] == []
    assert audit["byte_collisions"] == []
