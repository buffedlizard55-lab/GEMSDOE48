#!/usr/bin/env python3
"""H50-1 pilot: evaluate the 3 m linear scarp detector on the two committed pilot tiles.

Instrument: catalogue-adjacency lift. For 100 m cells fully covered by the tile, the share of
cells within 100 m of an existing_faults pixel ("near") among the top-q cells of a layer is
divided by the share among all covered cells. Values > 1 mean the layer concentrates known
faults; this is a *proxy* (the hidden test faults are by construction not in the catalogue),
but it is the only label-free instrument available inside the sandbox, and the same
instrument scored the 2 m u8 descriptors (data/raw/external/lidar_scarp_features_u8.tif)
at <= 1x on these tiles, so the comparison is like-for-like.

Writes evidence/h50_pilot_scarp_eval_20261007.json.
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gemsdoe48 import scarp3m as S  # noqa: E402

TILES = ["x42y425", "x40y427"]
QS = (0.9, 0.95, 0.98)


def lifts(v, dom, near, base):
    v = np.where(dom, v, np.nan)
    o = np.isfinite(v) & (v > 0)
    res = {"eligible_cells": int(o.sum()), "eligible_lift": float(near[o].mean() / base) if o.sum() else None}
    for q in QS:
        thr = np.nanquantile(v[o], q)
        sel = o & (v >= thr)
        res[f"top_{int(round((1 - q) * 100))}pct"] = {"n": int(sel.sum()), "lift": round(float(near[sel].mean() / base), 3)}
    return res


def main() -> int:
    lab = rasterio.open(ROOT / "data/official/labels.tif")
    LAB = lab.read(1)
    cat = LAB == 1
    fp = LAB >= 0
    near = distance_transform_edt(~cat, sampling=(100, 100)) <= 100
    u8 = rasterio.open(ROOT / "data/raw/external/lidar_scarp_features_u8.tif")
    out = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "params": S.ScarpParams().__dict__,
           "instrument": "share of 100 m cells within 100 m of existing_faults among top-q cells / share among all covered cells",
           "tiles": {}}
    for tile in TILES:
        t0 = time.time()
        with rasterio.open(ROOT / f"data/pilot/dem3m/{tile}_3m.tif") as s:
            z = s.read(1).astype(np.float32)
            z[z == -32768] = np.nan
            z = 1000.0 + z / 10.0
            tr = s.transform
        det = S.detect(z, S.ScarpParams(res_m=float(tr[0])))
        valid, h, sig, fac = det["valid"], det["height"], det["sigma_ctx"], det["facing"]
        sig100, cover, (r0, c0) = S.aggregate_to_grid(sig, valid, tr, lab.transform, LAB.shape, "mean")
        H, W = sig100.shape
        win = (slice(r0, r0 + H), slice(c0, c0 + W))
        dom = (cover > 0.9) & fp[win]
        nw = near[win]
        base = float(nw[dom].mean())
        rec = {"covered_cells": int(dom.sum()), "near_cells": int(nw[dom].sum()), "base_near_rate": base,
               "detect_seconds": round(time.time() - t0, 1), "near_rate_lift_by_sigma_ctx_bin": {}, "layers": {}}
        for lo, hi in [(0, 0.2), (0.2, 0.4), (0.4, 0.7), (0.7, 1.2), (1.2, 2.5), (2.5, 1e9)]:
            m = dom & (sig100 >= lo) & (sig100 < hi)
            rec["near_rate_lift_by_sigma_ctx_bin"][f"{lo}-{hi if hi < 1e8 else 'inf'}"] = {
                "n": int(m.sum()), "lift": round(float(nw[m].mean() / base), 3) if m.sum() else None}
        def agg_max(layer):
            a, _, _ = S.aggregate_to_grid(layer, valid, tr, lab.transform, LAB.shape, "max")
            return a
        rec["layers"]["score_ungated_max"] = lifts(agg_max(det["score"]), dom, nw, base)
        rec["layers"]["height_ungated_max"] = lifts(agg_max(h), dom, nw, base)
        for smax in (0.4, 0.7, 1.2):
            rec["layers"][f"height_gate_sigma<{smax}_max"] = lifts(agg_max(np.where(sig < smax, h, 0.0)), dom, nw, base)
            rec["layers"][f"height*facing_gate_sigma<{smax}_max"] = lifts(agg_max(np.where(sig < smax, h * fac, 0.0)), dom, nw, base)
        for b, n in [(1, "u8_band1_ex_max"), (3, "u8_band3_step_max"), (7, "u8_band7_upface_max")]:
            a = u8.read(b)[win].astype(float)
            a[a == 0] = np.nan
            rec["layers"][n] = lifts(a, dom, nw, base)
        out["tiles"][tile] = rec
        print(tile, json.dumps({k: v for k, v in rec["layers"].items() if "gate_sigma<0.7" in k or "u8" in k}, indent=None))
    dst = ROOT / "evidence/h50_pilot_scarp_eval_20261007.json"
    dst.write_text(json.dumps(out, indent=1))
    print("wrote", dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
