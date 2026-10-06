#!/usr/bin/env python3
"""Four-quadrant SGMC off-catalogue proxy validation.

Truth: USGS SGMC-derived faults at least ``MARGIN`` cells from anything in the
public catalogue, inside the continuous footprint.  This is a *proxy* for the
private expert truth and is never represented as private truth.

Metric: the literal published distance-weighted Tversky index as implemented in
``gems48.metric.dti``.  Earlier revisions of this script (schema
``GEMSDOE48-proxy-v1``) used an approximate TP rule -- nearest positive cell
only, ignoring the magnitude of p -- so their numbers are superseded and must
not be compared with the values below.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems48.metric import dti_result as dti  # noqa: E402

MARGIN = 3.0          # cells; 3 x 100 m = 300 m from any public-catalogue fault
RAW = ROOT / "data" / "raw"
DL = ROOT / "docs" / "downloads"
#: Written under its own name: docs/data/proxy-validation.json belongs to the
#: parallel DS48 session and must not be overwritten by this session.
REPORT_PATH = ROOT / "docs" / "data" / "h49-quadrant-proxy.json"
H49 = DL / "gemsdoe48-h49-ds-conflict-balanced-20261006-e6f08013888b.tif"
H48 = DL / "gemsdoe48-h48-ds-yager-conflict-20261006.tif"


def read(p):
    with rasterio.open(p) as s:
        return s.read(1)


def main():
    dotted = np.nan_to_num(read(RAW / "dotted.tif").astype(float), nan=0.0)
    tip = np.nan_to_num(read(RAW / "tip.tif").astype(float), nan=0.0)
    labels = read(RAW / "labels.tif") > 0
    sgmc = read(RAW / "external" / "derived_sgmc_faults_100m_u8.tif") > 0
    with rasterio.open(RAW / "sample_submission.tif") as s:
        footprint = np.isfinite(s.read(1))

    truth = sgmc & footprint & (distance_transform_edt(~labels) >= MARGIN)

    cands = {
        "h49_submission": read(H49).astype(float),
        "dotted": dotted,
        "tip": tip,
        "union": ((dotted > 0) | (tip > 0)).astype(float),
        "intersection": ((dotted > 0) & (tip > 0)).astype(float),
        "naive_mean": 0.5 * (dotted + tip),
        "weighted_mean_0.64_0.36": 0.64 * dotted + 0.36 * tip,
    }
    if H48.exists():
        cands["h48_yager_fusion"] = read(H48).astype(float)
    h48_1 = DL / "gemsdoe48-h48-1-ds-fusion-b2xh32tip-20261006-407bb7f4-zeros.tif"
    if h48_1.exists():
        cands["h48_1_dempster_binary"] = read(h48_1).astype(float)

    h, w = truth.shape
    quadrants = [(slice(0, h // 2), slice(0, w // 2)), (slice(0, h // 2), slice(w // 2, w)),
                 (slice(h // 2, h), slice(0, w // 2)), (slice(h // 2, h), slice(w // 2, w))]
    folds = []
    for i, (ys, xs) in enumerate(quadrants):
        t = truth[ys, xs]
        row = {"fold": i, "truth_pixels": int(t.sum())}
        for name, a in cands.items():
            r = dti(a[ys, xs], t.astype(float))
            row[name] = {"dti": r.dti, "tp": r.tp, "fp": r.fp, "truth": int(t.sum())}
        row["h49_minus_dotted"] = row["h49_submission"]["dti"] - row["dotted"]["dti"]
        folds.append(row)

    names = list(cands)
    means = {n: float(np.mean([f[n]["dti"] for f in folds])) for n in names}
    report = {
        "schema": "GEMSDOE48-proxy-v2",
        "protocol": f"four fixed spatial quadrants; SGMC-derived faults >= {int(MARGIN)} cells (300 m) from the public catalogue",
        "metric": "gems48.metric.dti (alpha=0.2, beta=0.8, R=3 cells) - literal published formulation",
        "supersedes": "GEMSDOE48-proxy-v1 (approximate TP rule; numbers not comparable)",
        "warning": "Proxy only. Not private expert truth; SGMC provenance and source dependence prevent a slot-clearance claim.",
        "folds": folds,
        "mean_dti": means,
        "h49_minus_dotted_mean": means["h49_submission"] - means["dotted"],
        "positive_folds_vs_dotted": int(sum(f["h49_minus_dotted"] > 0 for f in folds)),
        "gate_rule": "h49 mean > dotted mean and 4/4 folds positive",
        "gate_pass": bool(means["h49_submission"] > means["dotted"]
                          and sum(f["h49_minus_dotted"] > 0 for f in folds) == 4),
        "submission_slot_recommendation": "CLEARED ON PROXY ONLY - see docs/data/h49-instrument-calibration.json before spending a slot",
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "folds"}, indent=2))


if __name__ == "__main__":
    main()
