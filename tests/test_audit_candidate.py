"""Unit checks for the mass-neutral candidate audit tool (GEMSDOE48-GATE-2)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("audit_candidate", ROOT / "scripts" / "audit_candidate.py")
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def test_constants_match_documented_protocol():
    assert audit.ALPHA == 0.2 and audit.BETA == 0.8 and audit.RADIUS_M == 300.0
    assert audit.LIVE_TRUTH_PX == 14307
    assert audit.INCUMBENT_LIVE_DTI == 0.2778
    assert audit.EXPECTED_GRID == (3730, 3292)
    assert abs(0.2 * audit.INCUMBENT_LIVE_DTI - 0.05556) < 1e-9


def test_grid_ok_accepts_competition_grid_and_rejects_deviations():
    good = {"bands": 1, "dtype": "float32", "epsg": 32611, "shape": [3730, 3292]}
    assert audit.grid_ok(good)
    assert not audit.grid_ok({**good, "bands": 2})
    assert not audit.grid_ok({**good, "dtype": "float64"})
    assert not audit.grid_ok({**good, "epsg": 4326})
    assert not audit.grid_ok({**good, "shape": [3292, 3730]})


def test_decide_identical_support_is_flagged_not_passed():
    verdict, reasons = audit.decide(
        format_ok=True, identical=True, equal_mass_delta=0.0, n_added=0,
        density_matched_credit=0.0, bar_live=0.05556, bar_proxy=0.0191)
    assert verdict == "IDENTICAL_TO_INCUMBENT"
    assert "identical_support_to_incumbent" in reasons


def test_decide_passes_only_with_density_and_additions():
    verdict, reasons = audit.decide(
        format_ok=True, identical=False, equal_mass_delta=-0.001, n_added=0,
        density_matched_credit=0.0, bar_live=0.05556, bar_proxy=0.0191)
    assert verdict == "PASS_MASS_NEUTRAL" and reasons == []
    verdict, reasons = audit.decide(
        format_ok=True, identical=False, equal_mass_delta=-0.010, n_added=0,
        density_matched_credit=0.0, bar_live=0.05556, bar_proxy=0.0191)
    assert verdict == "FAIL_MASS_NEUTRAL"
    assert any("equal_mass" in reason for reason in reasons)


@pytest.mark.parametrize("credit, expected", [(0.0099, True), (0.0500, True), (0.0560, False)])
def test_decide_additions_bar(credit, expected):
    _, reasons = audit.decide(
        format_ok=True, identical=False, equal_mass_delta=0.0, n_added=100,
        density_matched_credit=credit, bar_live=0.05556, bar_proxy=0.0191)
    failed = any("added_cells_below_live_break_even_bar" in reason for reason in reasons)
    assert failed is expected


def test_gate2_receipts_are_internally_consistent():
    receipts = sorted((ROOT / "evidence").glob("audit_gate2_*_20261007.json"))
    assert receipts, "expected the committed GATE-2 receipts"
    for path in receipts:
        report = json.loads(path.read_text())
        assert report["schema"] == "GEMSDOE48-candidate-audit-v1"
        counts = report["counts"]
        assert counts["candidate_cells"] - counts["added_cells"] <= counts["incumbent_cells"]
        if report["verdict"] == "FAIL_MASS_NEUTRAL":
            assert report["reasons"], path.name
        if report["verdict"] == "IDENTICAL_TO_INCUMBENT":
            assert abs(report["equal_mass"]["delta_vs_incumbent"]) < 1e-9
