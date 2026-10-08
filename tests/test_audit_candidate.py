"""Tests for the retired Gate-2 tool's fail-closed forensic status."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("audit_candidate", ROOT / "scripts" / "audit_candidate.py")
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def test_metric_grid_constants_and_gate_invalidation_are_documented():
    assert audit.ALPHA == 0.2 and audit.BETA == 0.8 and audit.RADIUS_M == 300.0
    assert audit.LIVE_TRUTH_PX > 0  # retained only for explicit forensic reproduction
    assert audit.EXPECTED_GRID == (3730, 3292)
    assert "RETIRED" in audit.__doc__
    assert "not valid for promotion" in audit.__doc__
    assert "universal live break-even bar" in audit.__doc__
    assert "only follows under" in audit.__doc__


def test_grid_ok_accepts_competition_grid_and_rejects_deviations():
    good = {"bands": 1, "dtype": "float32", "epsg": 32611, "shape": [3730, 3292]}
    assert audit.grid_ok(good)
    assert not audit.grid_ok({**good, "bands": 2})
    assert not audit.grid_ok({**good, "dtype": "float64"})
    assert not audit.grid_ok({**good, "epsg": 4326})
    assert not audit.grid_ok({**good, "shape": [3292, 3730]})


def test_legacy_verdict_logic_requires_explicit_forensic_opt_in():
    args = dict(format_ok=True, identical=True, equal_mass_delta=0.0, n_added=0,
                density_matched_credit=0.0, bar_live=0.05556, bar_proxy=0.0191)
    with pytest.raises(RuntimeError, match="invalidated Gate-2"):
        audit.decide(**args)
    # The old value can be reproduced only when explicitly called forensic.
    verdict, _ = audit.decide(**args, legacy_audit_only=True)
    assert verdict == "IDENTICAL_TO_INCUMBENT"


def test_cli_refuses_default_execution_before_reading_inputs():
    result = subprocess.run([sys.executable, str(ROOT / "scripts/audit_candidate.py"), "missing.tif"],
                            cwd=ROOT, capture_output=True, text=True)
    assert result.returncode != 0
    assert "invalidated" in (result.stderr + result.stdout).lower()
    assert "--legacy-audit-only" in (result.stderr + result.stdout)


def test_gate2_receipts_preserve_but_invalidate_old_verdicts():
    receipts = sorted((ROOT / "evidence").glob("audit*.json"))
    marked = 0
    for path in receipts:
        report = json.loads(path.read_text())
        if "legacy_verdict" not in report:
            continue
        marked += 1
        assert report["validity_status"] == "INVALIDATED_FORENSIC_ONLY_DO_NOT_USE_FOR_PROMOTION"
        assert report["verdict"] == "INVALIDATED_FOR_FORENSIC_REPRODUCTION_ONLY"
        assert report["legacy_verdict"] in {"IDENTICAL_TO_INCUMBENT", "FAIL_MASS_NEUTRAL", "PASS_MASS_NEUTRAL"}
        assert "promotion decisions are invalidated" in report["warning"].lower()
    assert marked == 17


def test_credit_density_rollup_is_invalidated():
    report = json.loads((ROOT / "evidence/credit_density_audit_20261007.json").read_text())
    assert report["validity_status"] == "INVALIDATED_FORENSIC_ONLY_DO_NOT_USE_FOR_PROMOTION"
    assert "invalidated" in report["warning"].lower()
    assert "historical_instrument_invalidated" in report
