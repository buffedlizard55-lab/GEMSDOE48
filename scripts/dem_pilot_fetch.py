#!/usr/bin/env python3
"""H50 pilot: fetch a handful of official USGS 3DEP 1 m DEM tiles and store 2 m copies.

The development sandbox cannot reach ``prd-tnm.s3.amazonaws.com`` (every USGS host
returns HTTP 000 there), so this script runs on a GitHub-hosted runner via
``.github/workflows/dem-pilot.yml``. It downloads the verbatim bucket URLs recorded in
``registry/dem_tiles_pilot.json`` (inherited from the sibling inventory, itself resolved
against the authoritative USGS S3 listing), records the SHA-256 of every original
download, and writes a block-averaged 2 m float32 GeoTIFF per tile (deflate, predictor 3)
plus a provenance JSON. Nothing is reconstructed or guessed: a missing/failed tile is
logged as failed.

USGS 3DEP products carry no use restrictions; acknowledge "Map services and data
available from U.S. Geological Survey, National Geospatial Program."
(https://www.usgs.gov/3d-elevation-program/about-3dep-products-services)

Usage: python scripts/dem_pilot_fetch.py --tiles x42y425,x30y436 --out scratch/dem_pilot --res 2
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "registry" / "dem_tiles_pilot.json"


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: pathlib.Path, attempts: int = 4) -> None:
    for i in range(attempts):
        try:
            subprocess.run(["curl", "-fsSL", "--retry", "3", "-o", str(dest), url], check=True, timeout=1800)
            return
        except subprocess.CalledProcessError:
            time.sleep(10 * (i + 1))
    raise RuntimeError(f"download failed: {url}")


def reduce_tile(src_path: pathlib.Path, dst_path: pathlib.Path, res: float, compact: bool = False) -> dict:
    import rasterio
    from rasterio.enums import Resampling

    with rasterio.open(src_path) as src:
        factor = res / abs(src.res[0])
        if factor < 1:
            raise ValueError("requested resolution finer than source")
        out_h = int(round(src.height / factor))
        out_w = int(round(src.width / factor))
        data = src.read(1, out_shape=(out_h, out_w), resampling=Resampling.average, masked=True)
        arr = np.ma.filled(data.astype(np.float32), np.nan)
        transform = src.transform * src.transform.scale(src.width / out_w, src.height / out_h)
        meta = {
            "src_crs": str(src.crs), "src_transform": list(src.transform)[:6], "src_shape": [src.height, src.width],
            "src_res": [abs(src.res[0]), abs(src.res[1])], "src_nodata": src.nodata, "src_dtype": src.dtypes[0],
            "out_shape": [out_h, out_w], "out_transform": list(transform)[:6], "out_res_m": res,
            "valid_fraction": float(np.isfinite(arr).mean()),
            "z_min": float(np.nanmin(arr)) if np.isfinite(arr).any() else None,
            "z_max": float(np.nanmax(arr)) if np.isfinite(arr).any() else None,
        }
        if compact:
            # int16 decimetres relative to 1000 m: covers -2276 m .. 4276 m, 0.1 m precision.
            q = np.where(np.isfinite(arr), np.round((arr - 1000.0) * 10.0), -32768.0)
            q = np.clip(q, -32767, 32767).astype(np.int16)
            meta.update({"encoding": "int16 decimetres: z_m = 1000 + value/10; nodata -32768"})
            profile = {
                "driver": "GTiff", "dtype": "int16", "count": 1, "height": out_h, "width": out_w,
                "crs": src.crs, "transform": transform, "nodata": -32768, "compress": "deflate", "predictor": 2,
                "tiled": True, "blockxsize": 512, "blockysize": 512, "zlevel": 9,
            }
            with rasterio.open(dst_path, "w", **profile) as dst:
                dst.write(q, 1)
                dst.update_tags(ENCODING="z_m = 1000 + value/10", SOURCE_URL="see dem_pilot_receipt.json")
        else:
            profile = {
                "driver": "GTiff", "dtype": "float32", "count": 1, "height": out_h, "width": out_w,
                "crs": src.crs, "transform": transform, "nodata": np.nan, "compress": "deflate", "predictor": 3,
                "tiled": True, "blockxsize": 512, "blockysize": 512, "zlevel": 6,
            }
            with rasterio.open(dst_path, "w", **profile) as dst:
                dst.write(arr, 1)
    return meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiles", required=True, help="comma-separated tile ids, e.g. x42y425,x30y436")
    ap.add_argument("--out", default="scratch/dem_pilot")
    ap.add_argument("--res", type=float, default=2.0)
    ap.add_argument("--workdir", default="/tmp/dem_pilot_work")
    ap.add_argument("--compact", action="store_true", help="write int16 decimetre GeoTIFFs (small enough to commit)")
    args = ap.parse_args()

    out = pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)
    work = pathlib.Path(args.workdir); work.mkdir(parents=True, exist_ok=True)
    inv = json.load(INVENTORY.open())
    by_tile = {r["tile"]: r for r in inv["records"]}
    receipt = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "res_m": args.res, "tiles": []}
    for tile in [t.strip() for t in args.tiles.split(",") if t.strip()]:
        rec = by_tile.get(tile)
        entry = {"tile": tile, "status": "missing-from-inventory"}
        if rec is not None:
            raw = work / rec["filename"]
            try:
                t0 = time.time()
                download(rec["url"], raw)
                digest = sha256(raw)
                dst = out / f"{tile}_{args.res:g}m.tif"
                meta = reduce_tile(raw, dst, args.res, compact=args.compact)
                entry = {"tile": tile, "status": "ok", "url": rec["url"], "project": rec["project"],
                         "source_bytes": raw.stat().st_size, "source_sha256": digest,
                         "output": dst.name, "output_bytes": dst.stat().st_size, "output_sha256": sha256(dst),
                         "seconds": round(time.time() - t0, 1), **meta}
            except Exception as exc:  # noqa: BLE001 - logged, never hidden
                entry = {"tile": tile, "status": "failed", "url": rec["url"], "error": repr(exc)}
            finally:
                if raw.exists():
                    raw.unlink()
        receipt["tiles"].append(entry)
        print(json.dumps(entry))
    (out / "dem_pilot_receipt.json").write_text(json.dumps(receipt, indent=2))
    return 0 if all(t["status"] == "ok" for t in receipt["tiles"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
