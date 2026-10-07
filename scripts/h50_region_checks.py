#!/usr/bin/env python3
"""Label-free checks of the H50-1 region product: catalogue-adjacency lift (<=100 m) of the top-2 %
cells of several 100 m rankers, per quadrant, plus the roughness-band flag alone.
Writes evidence/h50_region_detector_checks_20261007.json."""
from __future__ import annotations
import json, pathlib, time
import numpy as np, rasterio
from scipy.ndimage import distance_transform_edt
ROOT = pathlib.Path(__file__).resolve().parents[1]

def main() -> int:
    s = rasterio.open(ROOT / "data/external/h50_scarp3m_100m.tif"); tags = s.tags()
    def band(i, name):
        a = s.read(i).astype(np.float32); a[a == s.nodata] = np.nan; return a / float(tags["SCALE_" + name])
    h07, h12, hall, sig, cov = band(1, "h_gate07"), band(2, "h_gate12"), band(3, "h_all"), band(4, "sigma_mean"), band(7, "cover")
    lab = rasterio.open(ROOT / "data/official/labels.tif").read(1); fp = lab >= 0; cat = lab == 1
    near = distance_transform_edt(~cat, sampling=(100, 100)) <= 100
    covered = fp & (cov >= 0.9); H, W = lab.shape
    quad = np.zeros((H, W), int); quad[:H // 2, W // 2:] = 1; quad[H // 2:, :W // 2] = 2; quad[H // 2:, W // 2:] = 3; qn = ["NW", "NE", "SW", "SE"]
    out = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "covered_cells": int(covered.sum()),
           "base_near_rate": float(near[covered].mean()), "rankers": {}}
    def test(name, r, q=0.98):
        v = np.where(covered & np.isfinite(r) & (r > 0), r, np.nan); thr = np.nanquantile(v, q); top = covered & (v >= thr)
        rec = {"quantile": q, "threshold": float(thr), "selected": int(top.sum()), "lift_all": float(near[top].mean() / near[covered].mean()), "by_quadrant": {}}
        for k in range(4):
            m = covered & (quad == k); t = top & (quad == k)
            rec["by_quadrant"][qn[k]] = {"selected": int(t.sum()), "lift": float(near[t].mean() / near[m].mean())}
        out["rankers"][name] = rec; print(name, round(rec["lift_all"], 2), {k: round(v["lift"], 2) for k, v in rec["by_quadrant"].items()})
    test("h_gate12", h12); test("h_gate07", h07); test("h_all", hall); test("h12_over_sigma", h12 / (sig + 0.15))
    test("h12_in_sigma_0.4_1.2", np.where((sig >= 0.4) & (sig < 1.2), h12, np.nan))
    band_flag = np.where((sig >= 0.7) & (sig < 2.5), 1.0, np.nan)
    v = covered & np.isfinite(band_flag)
    rec = {"description": "cells with 0.7 <= sigma_mean < 2.5 m, no ranking", "selected": int(v.sum()), "lift_all": float(near[v].mean() / near[covered].mean()), "by_quadrant": {}}
    for k in range(4):
        m = covered & (quad == k); t = v & (quad == k); rec["by_quadrant"][qn[k]] = {"selected": int(t.sum()), "lift": float(near[t].mean() / near[m].mean())}
    out["rankers"]["roughness_band_0.7_2.5_flag"] = rec; print("band flag", round(rec["lift_all"], 2))
    out["lift_by_sigma_bin_all_covered"] = {}
    for lo, hi in [(0, 0.1), (0.1, 0.2), (0.2, 0.4), (0.4, 0.7), (0.7, 1.2), (1.2, 2.5), (2.5, 1e9)]:
        m = covered & (sig >= lo) & (sig < hi)
        out["lift_by_sigma_bin_all_covered"][f"{lo}-{hi if hi < 1e8 else 'inf'}"] = {"n": int(m.sum()), "lift": float(near[m].mean() / near[covered].mean())}
    (ROOT / "evidence/h50_region_detector_checks_20261007.json").write_text(json.dumps(out, indent=1))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
