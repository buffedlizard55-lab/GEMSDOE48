"""Tests for the H55 live-anchored forward model, conduit layer, and emission builder.

Tests that need the git-ignored ``data/raw`` mirrors skip cleanly when those mirrors
have not been restored (``python scripts/restore_h55_inputs.py``), matching the
repository's existing data-dependent-test convention.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gemsdoe48 import conduit, h55, live_model  # noqa: E402
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


def test_single_truth_marginal_credit_special_case():
    """Special case: TP changes by k, FP by 1-k, and FN by -k.

    The derivative sign is that of k - 0.2*DTI in this one-pixel setup only;
    this is not a universal raster-level break-even threshold.
    """
    t0, d0 = 5209.5, 18752.4
    for k in (0.02, 0.0556, 0.14, 0.9):
        signs = set()
        for v in (0.05, 0.25, 0.5, 0.75, 1.0):
            lo = (t0 + (v - 1e-4) * k) / (d0 + 0.2 * (v - 1e-4))
            hi = (t0 + (v + 1e-4) * k) / (d0 + 0.2 * (v + 1e-4))
            signs.add(np.sign(hi - lo))
        assert len(signs) == 1, f"sign of the derivative must not depend on v (k={k})"
        expected = np.sign(k - 0.2 * (t0 / d0))
        assert signs.pop() == expected or expected == 0


# ---------------------------------------------------------------------------
# forward model
# ---------------------------------------------------------------------------

def test_hidden_truth_fit_is_stable_and_positive():
    fit = live_model.fit_hidden_truth([44090, 40199, 37654], [0.2600, 0.2708, 0.2778])
    g = fit["hidden_truth_px"]
    assert 12_000.0 < g < 16_500.0, g
    # the three pairwise closed-form solutions must agree to a few percent
    closed = [p["closed_form_G"] for p in fit["pairwise_closed_form"]]
    assert max(closed) / min(closed) - 1.0 < 0.15, closed
    # the shared TPw implied by the nested ladder must be the same from every rung
    t = [live * (0.2 * s + 0.8 * g) for s, live in zip([44090, 40199, 37654],
                                                       [0.2600, 0.2708, 0.2778])]
    assert (max(t) - min(t)) / np.mean(t) < 0.005, t


def test_invert_truth_round_trips():
    g = 14_027.5
    for s in (37_654, 44_090, 121_131):
        for dti in (0.19, 0.26, 0.2778, 0.32):
            t = live_model.invert_truth(dti, s, g)
            assert abs(t / (0.2 * s + 0.8 * g) - dti) < 1e-12


def test_forward_model_dataclass_bounds():
    model = live_model.ForwardModel(hidden_truth_px=14_027.5, rho=0.068015, target_px=103_805)
    assert abs(model.break_even_credit(0.2778) - 0.05556) < 1e-4
    # adding mass with no coverage can only lower the score
    assert model.worst_case_dti(75_206.8, 37_654, 1_000) < model.dti(75_206.8, 37_654)
    # ... and adding credit raises it
    assert model.scenario_dti(75_206.8, 37_654, 1_000, 0.2) > model.dti(75_206.8, 37_654)
    assert model.tpw_needed(0.3195, 37_654) > model.tpw_needed(0.2778, 37_654)


@needs(BACKBONE)
@needs(CORE)
def test_calibration_reproduces_the_live_ladder():
    receipt = json.loads(CALIBRATION.read_text()) if CALIBRATION.exists() else None
    if receipt is None:
        pytest.skip("calibration receipt not built yet")
    rms = receipt["rho_fit"]["rms_relative_error_pct"]
    assert rms < 3.0, rms
    assert len(receipt["artifacts"]) == 8
    # the nested triple must invert to one shared TPw
    t = {a["key"]: a["live"] * (0.2 * a["emitted"] + 0.8 * receipt["hidden_truth_fit"]["hidden_truth_px"])
         for a in receipt["artifacts"]}
    triple = [t[k] for k in ("A_d2_8", "B_prune100", "C_prune200")]
    assert (max(triple) - min(triple)) / np.mean(triple) < 0.005, triple


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

def test_greedy_incremental_coverage_matches_exact_recomputation():
    rng = np.random.default_rng(11)
    target = rng.random((80, 80)) < 0.06
    core = rng.random((80, 80)) < 0.01
    pool = (rng.random((80, 80)) < 0.30) & ~core
    model = live_model.ForwardModel(1_000.0, 0.07, int(target.sum()))
    priced = h55.price_addition_path(core, pool, target, break_even_bar=0.2 * 0.27 / 0.07,
                                     max_add=60, model=model)
    rows = priced["rows"]
    for n in (1, 5, 20, len(rows)):
        if n == 0 or n > len(rows):
            continue
        exact = core.copy()
        exact[rows[:n, 0], rows[:n, 1]] = True
        expected = live_model.coverage(exact, target)
        # gains are float32; the incremental total may drift by ~1e-5 relative
        assert abs(priced["path"][n]["coverage"] - expected) <= 1e-5 * max(1.0, expected), (n, expected)


def test_greedy_stops_at_the_bar_and_respects_the_safety_prefix():
    rng = np.random.default_rng(3)
    target = rng.random((70, 70)) < 0.05
    core = rng.random((70, 70)) < 0.01
    pool = (rng.random((70, 70)) < 0.4) & ~core
    model = live_model.ForwardModel(1_000.0, 0.07, int(target.sum()))
    bar = 0.2 * 0.27 / 0.07
    priced = h55.price_addition_path(core, pool, target, break_even_bar=bar,
                                     max_add=500, model=model, safety_factor=1.25)
    gains = priced["gains"]
    assert (gains[:priced["n_admitted_at_break_even"]] >= bar - 1e-9).all()
    robust = priced["robust_n"]
    assert robust <= priced["n_admitted_at_break_even"]
    assert (gains[:robust] >= 1.25 * bar - 1e-9).all()
    if robust < len(gains):
        assert gains[robust] < 1.25 * bar + 1e-9
    # the robust prefix is a prefix of the path, so its DTI is on the path
    assert priced["robust_prefix"]["n"] == robust


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

def test_dempster_reports_residual_ignorance_and_raw_conflict_separately():
    b1 = np.array([[1.0, 1.0, 0.0], [0.0, 0.5, 1.0]])
    b2 = np.array([[1.0, 0.0, 0.0], [1.0, 0.5, 0.0]])
    out = dempster_combine(b1, b2, alpha1=0.6, alpha2=0.6)
    # The closed-form example: residual m(Theta) rises as normalized-away K rises.
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


def test_full_conflict_is_rejected_because_normalized_rule_is_undefined():
    b1 = np.array([[1.0]])
    b2 = np.array([[0.0]])
    with pytest.raises(ValueError, match="undefined"):
        dempster_combine(b1, b2, alpha1=1.0, alpha2=1.0)


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
def test_build_receipt_is_internally_consistent():
    r = json.loads(RECEIPT.read_text())
    e = r["emission"]
    assert e["positive_pixels"] == e["core_px"] + e["a2_px"] + e["a1_px"]
    assert e["core_preserved_exactly"] is True
    assert e["on_catalogue_positive_pixels"] == 0
    assert e["within_200m_of_catalogue_positive_pixels"] == 0
    assert e["outside_footprint_positive_pixels"] == 0
    assert e["unique_values"] == [0.0, 1.0]
    risk = r["risk"]
    # the pre-registered floor must hold: worst case >= 0.2778 - 0.0100
    assert risk["floor_all_added_pixels_zero_credit"]["live_equivalent"] >= 0.2778 - 0.0100 - 1e-6
    assert risk["floor_all_added_pixels_zero_credit"]["within_pre_registered_floor"] is True
    assert risk["coverage_bookkeeping_check_incremental_vs_exact"]["match"] is True
    # every scenario with more credit must score higher than the zero-credit case
    band = risk["scenario_band"]
    assert all(band[i]["dti_live_equivalent"] <= band[i + 1]["dti_live_equivalent"] + 1e-12
               for i in range(len(band) - 1))
    # the naive union of the two families must be priced BELOW the untouched core
    union = r["live_model"]["union_of_both_families_priced"]
    assert union["delta_vs_C_model"] < 0
    ds = r["dempster_shafer"]
    assert ds["not_the_naive_mean"]["is_the_naive_mean"] is False
    assert ds["not_the_naive_mean"]["best_affine_fit_mean_abs_residual"] > 1e-3
    assert 0.15 <= ds["mtheta_max"] <= 0.26
    assert ds["conflict_K_max"] == pytest.approx(0.36)


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
