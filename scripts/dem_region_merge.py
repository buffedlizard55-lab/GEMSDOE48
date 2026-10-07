#!/usr/bin/env python3
"""Mosaic per-tile H50-1 scarp layers onto the official 100 m grid and write a compact GeoTIFF.

Output: data/external/h50_scarp3m_100m.tif, int16, 7 bands, deflate. Encodings (see tags):
  h_gate07, h_gate12, h_all, sigma_mean : centimetres (value/100 = m), clipped to 327 m
  facing_at                             : value/10000
  strike_at                             : value/100 degrees
  cover                                 : value/10000
nodata = -32768. Where tiles overlap, the maximum (height layers) / mean-of-available is used.
"""
from __future__ import annotations

import argparse
import glob
import json
import pathlib

import numpy as np
import rasterio
from rasterio.transform import Affine

GRID_TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
GRID_SHAPE = (3730, 3292)
BANDS = ["h_gate07", "h_gate12", "h_all", "sigma_mean", "facing_at", "strike_at", "cover"]
SCALE = {"h_gate07": 100, "h_gate12": 100, "h_all": 100, "sigma_mean": 100, "facing_at": 10000, "strike_at": 100, "cover": 10000}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", default="scratch/shards")
    ap.add_argument("--out", default="data/external/h50_scarp3m_100m.tif")
    args = ap.parse_args()
    acc = {b: np.full(GRID_SHAPE, np.nan, np.float32) for b in BANDS}
    files = sorted(glob.glob(str(pathlib.Path(args.inp) / "**" / "*.npz"), recursive=True))
    logs = sorted(glob.glob(str(pathlib.Path(args.inp) / "**" / "log_shard*.json"), recursive=True))
    n_ok = 0
    merge_errors = []
    for f in files:
        try:
            d = np.load(f)
            r0, c0 = int(d["row0"]), int(d["col0"])
            h, w = d["h_gate12"].shape
            # clip the tile window to the official grid (edge tiles extend beyond it)
            rr0, cc0 = max(r0, 0), max(c0, 0)
            rr1, cc1 = min(r0 + h, GRID_SHAPE[0]), min(c0 + w, GRID_SHAPE[1])
            if rr1 <= rr0 or cc1 <= cc0:
                merge_errors.append({"file": f, "error": "tile entirely outside the grid"})
                continue
            win = (slice(rr0, rr1), slice(cc0, cc1))
            sub = (slice(rr0 - r0, rr1 - r0), slice(cc0 - c0, cc1 - c0))
            cover = d["cover"][sub]
            for b in BANDS:
                cur = acc[b][win]
                new = np.where(cover > 0, d[b][sub].astype(np.float32), np.nan)
                if b in ("h_gate07", "h_gate12", "h_all", "cover"):
                    acc[b][win] = np.fmax(cur, new)
                else:
                    # attribute of the first tile that covers the cell (overlaps are 6 m strips)
                    acc[b][win] = np.where(np.isnan(cur), new, cur)
            n_ok += 1
        except Exception as exc:  # noqa: BLE001
            merge_errors.append({"file": f, "error": repr(exc)})
    status = []
    for lg in logs:
        status.extend(json.load(open(lg)))
    profile = {"driver": "GTiff", "dtype": "int16", "count": len(BANDS), "height": GRID_SHAPE[0], "width": GRID_SHAPE[1],
               "crs": "EPSG:32611", "transform": GRID_TRANSFORM, "nodata": -32768, "compress": "deflate", "predictor": 2,
               "tiled": True, "blockxsize": 512, "blockysize": 512, "zlevel": 9}
    out = pathlib.Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out, "w", **profile) as dst:
        for i, b in enumerate(BANDS, 1):
            a = acc[b]
            q = np.where(np.isfinite(a), np.clip(np.round(a * SCALE[b]), -32767, 32767), -32768).astype(np.int16)
            dst.write(q, i)
            dst.set_band_description(i, b)
        dst.update_tags(**{f"SCALE_{b}": str(SCALE[b]) for b in BANDS}, DETECTOR="gemsdoe48.scarp3m v1 at 3 m")
    receipt = {"n_tiles_merged": n_ok, "n_npz_files": len(files), "merge_errors": merge_errors, "n_tiles_ok": sum(1 for s in status if s.get("status") == "ok"),
               "n_tiles_failed": sum(1 for s in status if s.get("status") != "ok"),
               "failed": [{"tile": s["tile"], "error": s.get("error")} for s in status if s.get("status") != "ok"],
               "cells_with_cover": int(np.isfinite(acc["cover"]).sum()),
               "source_sha256": {s["tile"]: s.get("source_sha256") for s in status if s.get("status") == "ok"}}
    out.with_suffix(".json").write_text(json.dumps(receipt, indent=1))
    print(json.dumps({k: v for k, v in receipt.items() if k != "source_sha256"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
