"""Counterexample to H55's historical FP = emitted mass - TP substitution."""
import hashlib
from pathlib import Path

import numpy as np
import pytest

from gems48.metric import dti_result

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / "docs/downloads/GEMSDOE48-H55-conduit-conflict-priced-20261007-055da9855353-zeros-outside.tif"
ACTUAL_SHA = "8f9a9d3d1ea2aed1c99e5ab5260aad9ceb10f4011c4b5a38791509261ddd284a"


def test_prediction_centered_and_truth_centered_credit_are_different():
    pred = np.zeros((1, 5), dtype=np.float32)
    truth = np.zeros((1, 5), dtype=bool)
    pred[0, 1] = 1
    truth[0, 1:3] = True
    result = dti_result(pred, truth)
    # One prediction serves two truth pixels at distances 0 and 100 m.
    assert result.tp == pytest.approx(5 / 3)
    assert result.mass == 1
    assert result.fp == 0
    assert result.fn == pytest.approx(1 / 3)
    assert result.dti == pytest.approx(25 / 29)
    q = result.mass - result.fp
    correct = result.tp / (0.2 * result.tp + 0.2 * result.mass
                           - 0.2 * q + 0.8 * result.truth_pixels + 1e-12)
    assert result.dti == pytest.approx(correct)
    historical = result.tp / (0.2 * result.mass + 0.8 * result.truth_pixels)
    assert historical == pytest.approx(25 / 27)
    assert historical != pytest.approx(result.dti)
    assert result.mass - result.tp < 0  # Cannot possibly be FP.


def test_h55_page_regeneration_retains_erratum():
    from scripts.build_site_h55 import build_index, build_exec, build_method, build_guide
    for render in (build_index, build_exec, build_method, build_guide):
        html = render()
        assert "Research correction — no upload cleared." in html
        assert "metric-identity-erratum-20261007.md" in html
    assert "FPw = S − Q" in build_index()
    assert "FPw  = S − Q" in build_exec()


def test_published_primary_hash_matches_its_receipt():
    import json
    receipt = json.loads((ROOT / "evidence/h55_primary_format_audit_20261007.json").read_text())
    assert receipt["sha256"] == ACTUAL_SHA
    assert hashlib.sha256(PRIMARY.read_bytes()).hexdigest() == ACTUAL_SHA
    assert ACTUAL_SHA in (ROOT / "README.md").read_text()
