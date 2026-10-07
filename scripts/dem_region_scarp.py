#!/usr/bin/env python3
"""H52-1 region-scale run: USGS 3DEP 1 m tiles -> 3 m -> linear scarp detector -> 100 m cells.

Runs on GitHub-hosted runners (.github/workflows/dem-region-scarp.yml) because the sandbox
cannot reach USGS hosts. Per tile it downloads the verbatim bucket URL from
registry/dem_tiles_pilot.json, block-averages to 3 m, runs gemsdoe48.scarp3m.detect and
aggregates these layers onto the official 100 m grid window of the tile:

    h_gate07   max line-persistent scarp height (m) over 3 m cells with sigma_ctx < 0.7 m
    h_gate12   same with sigma_ctx < 1.2 m
    h_all      ungated max height (m)
    sigma_mean mean context roughness (m)
    facing_at  facing factor at the h_gate12 argmax cell
    strike_at  strike (deg from N) at the h_gate12 argmax cell
    cover      fraction of the 100 m cell covered by valid 3 m samples

Each tile result is a small .npz (window offsets + arrays); scripts/dem_region_merge.py
mosaics them. Failed tiles are logged with the exception; nothing is silently skipped.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import traceback

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gemsdoe48 import scarp3m as S  # noqa: E402
from dem_pilot_fetch import INVENTORY, download, sha256  # noqa: E402

GRID_TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
GRID_SHAPE = (3730, 3292)


def reduce_in_memory(src_path: pathlib.Path, res: float):
    import rasterio
    from rasterio.enums import Resampling
    with rasterio.open(src_path) as src:
        factor = res / abs(src.res[0])
        oh, ow = int(round(src.height / factor)), int(round(src.width / factor))
        data = src.read(1, out_shape=(oh, ow), resampling=Resampling.average, masked=True)
        z = np.ma.filled(data.astype(np.float32), np.nan)
        tr = src.transform * src.transform.scale(src.width / ow, src.height / oh)
        return z, tr, str(src.crs)


def process_tile(rec: dict, workdir: pathlib.Path, res: float) -> dict:
    raw = workdir / rec["filename"]
    t0 = time.time()
    download(rec["url"], raw)
    digest = sha256(raw)
    z, tr, crs = reduce_in_memory(raw, res)
    raw.unlink()
    p = S.ScarpParams(res_m=float(tr[0]))
    out = S.detect(z, p)
    valid = out["valid"]
    h, sig, fac, strike = out["height"], out["sigma_ctx"], out["facing"], out["strike_deg"]
    layers = {}
    def agg(layer, how="max"):
        a, cover, off = S.aggregate_to_grid(layer, valid, tr, GRID_TRANSFORM, GRID_SHAPE, how)
        return a.astype(np.float32), cover.astype(np.float32), off
    layers["h_gate07"], cover, off = agg(np.where(sig < 0.7, h, 0.0))
    layers["h_gate12"], _, _ = agg(np.where(sig < 1.2, h, 0.0))
    layers["h_all"], _, _ = agg(h)
    layers["sigma_mean"], _, _ = agg(sig, "mean")
    # attributes at the gated-12 argmax: encode as argmax index per 100 m cell
    g12 = np.where(sig < 1.2, h, 0.0)
    # per-cell argmax via sorting trick: aggregate (value*1e6 + idx) is unsafe; do explicit loop-free
    rs = GRID_TRANSFORM[0] / tr[0]
    hh, ww = g12.shape
    rows = np.floor((GRID_TRANSFORM[5] - (tr[5] - (np.arange(hh) + 0.5) * tr[0])) / 100.0).astype(np.int64)
    cols = np.floor(((tr[2] + (np.arange(ww) + 0.5) * tr[0]) - GRID_TRANSFORM[2]) / 100.0).astype(np.int64)
    rmin, cmin = off
    oh, ow = layers["h_gate12"].shape
    cell = (rows[:, None] - rmin) * ow + (cols[None, :] - cmin)
    flat_v = np.where(valid, g12, -1.0).ravel()
    flat_c = cell.ravel()
    order = np.lexsort((flat_v, flat_c))  # sort by cell then value; last per cell = argmax
    last = np.r_[np.nonzero(np.diff(flat_c[order]))[0], len(order) - 1]
    best_idx = order[last]
    fac_at = np.full(oh * ow, np.nan, np.float32); str_at = np.full(oh * ow, np.nan, np.float32)
    fac_at[flat_c[best_idx]] = fac.ravel()[best_idx]
    str_at[flat_c[best_idx]] = strike.ravel()[best_idx]
    layers["facing_at"] = fac_at.reshape(oh, ow); layers["strike_at"] = str_at.reshape(oh, ow)
    layers["cover"] = cover
    return {"tile": rec["tile"], "status": "ok", "url": rec["url"], "source_sha256": digest, "src_crs": crs,
            "row0": int(rmin), "col0": int(cmin), "shape": [int(oh), int(ow)], "seconds": round(time.time() - t0, 1),
            "layers": layers}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, required=True)
    ap.add_argument("--nshards", type=int, required=True)
    ap.add_argument("--out", default="scratch/scarp")
    ap.add_argument("--workdir", default="/tmp/scarp_work")
    ap.add_argument("--res", type=float, default=3.0)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    out = pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)
    work = pathlib.Path(args.workdir); work.mkdir(parents=True, exist_ok=True)
    recs = json.load(INVENTORY.open())["records"]
    mine = [r for i, r in enumerate(recs) if i % args.nshards == args.shard]
    if args.limit:
        mine = mine[: args.limit]
    log = []
    for rec in mine:
        try:
            res = process_tile(rec, work, args.res)
            layers = res.pop("layers")
            np.savez_compressed(out / f"{rec['tile']}.npz", row0=res["row0"], col0=res["col0"], **layers)
        except Exception as exc:  # noqa: BLE001
            res = {"tile": rec["tile"], "status": "failed", "url": rec["url"], "error": repr(exc),
                   "trace": traceback.format_exc()[-800:]}
        log.append(res)
        print(json.dumps({k: v for k, v in res.items() if k != "trace"}), flush=True)
    (out / f"log_shard{args.shard:02d}.json").write_text(json.dumps(log, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
