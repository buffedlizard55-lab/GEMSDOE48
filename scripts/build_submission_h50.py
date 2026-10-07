#!/usr/bin/env python3
"""Build the H50-1 candidate family: C (0.2778 dotted prune) + lidar-scarp additions.

Inputs
  --base    data/families/dotted_b2_prune_02778.tif   (C: 37,654 binary dots, NaN outside)
  --scarp   data/external/h50_scarp3m_100m.tif          (CI product of scripts/dem_region_merge.py)
  labels / footprint / SGMC proxies from the repository mirrors.

Construction (pre-registered in docs/research/hypotheses-h50-20261007.md §4)
  1. eligible = footprint & cover >= --cover-min & height(layer) > 0
               & distance to catalogue > 200 m (C's own rule) & not within 200 m of a C dot
  2. rank eligible cells by the gated line-persistent scarp height, descending
  3. greedy Poisson-disk thinning (min 2.83 px, same spacing as the dotted family),
     also enforced against the existing C dots
  4. emit the first n additions for each n in --n-add; candidate = C ∪ additions (binary)

Diagnostics written to --report (JSON):
  * detector lift per quadrant (label-free check: top-q eligible-before-exclusion cells vs the
    catalogue-adjacency base rate inside the lidar footprint)
  * for each n: dots, prediction mass, mean/per-fold DTI on the newer-SGMC >300 m off-catalogue
    proxy and on the raw-SGMC proxy, using the identical fold geometry as run_spatial_holdout.py,
    together with C, union and H49 reference scores.
Nothing here touches the official holdout script; the chosen n is re-scored with it separately.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from run_spatial_holdout import quadrants, score_fold, sha256_file  # noqa: E402

PIX_MIN_DIST = 2.8284271247461903  # Poisson-disk spacing of the dotted family (px)


def read_band(path: pathlib.Path, band: int = 1):
    with rasterio.open(path) as src:
        return src.read(band), src.profile


def scarp_layers(path: pathlib.Path) -> dict[str, np.ndarray]:
    out = {}
    with rasterio.open(path) as src:
        tags = src.tags()
        for i, name in enumerate(src.descriptions, 1):
            a = src.read(i).astype(np.float32)
            nod = a == src.nodata
            a = a / float(tags[f"SCALE_{name}"])
            a[nod] = np.nan
            out[name] = a
    return out


def poisson_thin(order_rows, order_cols, occupied: np.ndarray, n_max: int, min_dist: float):
    """Greedy thinning: accept a cell if no accepted/base dot lies within min_dist pixels."""
    r = int(np.ceil(min_dist))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    disk = (yy * yy + xx * xx) <= min_dist * min_dist
    H, W = occupied.shape
    occ = np.pad(occupied.copy(), r)
    kept_r, kept_c = [], []
    for row, col in zip(order_rows, order_cols):
        win = occ[row:row + 2 * r + 1, col:col + 2 * r + 1]
        if np.any(win & disk):
            continue
        occ[row + r, col + r] = True
        kept_r.append(int(row)); kept_c.append(int(col))
        if len(kept_r) >= n_max:
            break
    return np.array(kept_r, dtype=np.int64), np.array(kept_c, dtype=np.int64)


def write_candidate(path: pathlib.Path, binary: np.ndarray, footprint: np.ndarray, profile: dict, nan_outside: bool):
    arr = np.where(footprint, binary.astype(np.float32), np.nan if nan_outside else 0.0).astype(np.float32)
    prof = dict(profile)
    prof.update(driver="GTiff", dtype="float32", count=1, nodata=np.nan if nan_outside else None,
                compress="deflate", predictor=2, tiled=False)
    prof.pop("blockxsize", None); prof.pop("blockysize", None)
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **prof) as dst:
        dst.write(arr, 1)
    return sha256_file(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=pathlib.Path, default=ROOT / "data/families/dotted_b2_prune_02778.tif")
    ap.add_argument("--scarp", type=pathlib.Path, default=ROOT / "data/external/h50_scarp3m_100m.tif")
    ap.add_argument("--layer", default="h_gate12")
    ap.add_argument("--cover-min", type=float, default=0.9)
    ap.add_argument("--min-height", type=float, default=0.0, help="metres; additional absolute floor")
    ap.add_argument("--n-add", default="500,1000,2000,3000,4000,6000,8000")
    ap.add_argument("--labels", type=pathlib.Path, default=ROOT / "data/raw/labels_catalogue.tif")
    ap.add_argument("--footprint", type=pathlib.Path, default=ROOT / "data/source_mirrors/footprint-mask.tif")
    ap.add_argument("--sgmc", type=pathlib.Path, default=ROOT / "data/official/derived_sgmc_faults_100m.tif")
    ap.add_argument("--sgmc-raw", type=pathlib.Path, default=ROOT / "data/raw/sgmc_faults_100m.tif")
    ap.add_argument("--tip", type=pathlib.Path, default=ROOT / "data/raw/tip_h33d_stepover.tif")
    ap.add_argument("--h49", type=pathlib.Path,
                    default=ROOT / "docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif")
    ap.add_argument("--out-dir", type=pathlib.Path, default=ROOT / "scratch/h50")
    ap.add_argument("--report", type=pathlib.Path, default=ROOT / "evidence/h50_candidate_sweep_20261007.json")
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    t0 = time.time()
    base, profile = read_band(args.base)
    C = np.nan_to_num(base, nan=0.0) > 0
    labels, _ = read_band(args.labels)
    footprint = read_band(args.footprint)[0] == 1
    catalogue = (labels > 0) & footprint
    sgmc = read_band(args.sgmc)[0] > 0
    sgmc_raw = read_band(args.sgmc_raw)[0] > 0
    tip = np.nan_to_num(read_band(args.tip)[0], nan=0.0) > 0
    h49 = np.nan_to_num(read_band(args.h49)[0], nan=0.0) > 0
    d_cat = distance_transform_edt(~catalogue, sampling=(100.0, 100.0))
    d_C = distance_transform_edt(~C, sampling=(100.0, 100.0))
    layers = scarp_layers(args.scarp)
    height = layers[args.layer]
    cover = layers["cover"]
    covered = footprint & np.isfinite(cover) & (cover >= args.cover_min)

    # --- label-free detector check per quadrant (before the catalogue exclusion) ---
    blocks = quadrants(*labels.shape)
    near = d_cat <= 100.0
    detector_check = {}
    hv = np.where(covered & np.isfinite(height) & (height > 0), height, np.nan)
    for q in (0.98, 0.99):
        thr_global = np.nanquantile(hv, q)
        for name, core in blocks.items():
            dom = covered & core
            base_rate = float(near[dom].mean()) if dom.sum() else float("nan")
            sel = dom & (hv >= thr_global)
            detector_check[f"{name}_top{int(round((1 - q) * 100))}pct"] = {
                "covered_cells": int(dom.sum()), "selected": int(sel.sum()),
                "base_near_rate": base_rate,
                "lift": float(near[sel].mean() / base_rate) if sel.sum() and base_rate > 0 else None}
    detector_check["global_threshold_m_top2pct"] = float(np.nanquantile(hv, 0.98))
    detector_check["global_threshold_m_top1pct"] = float(np.nanquantile(hv, 0.99))

    # --- eligible additions ---
    eligible = covered & np.isfinite(height) & (height > max(args.min_height, 0.0)) & (d_cat > 200.0) & (d_C > 200.0)
    rows, cols = np.nonzero(eligible)
    order = np.argsort(-height[rows, cols], kind="stable")
    rows, cols = rows[order], cols[order]
    n_list = [int(x) for x in args.n_add.split(",") if x.strip()]
    kr, kc = poisson_thin(rows, cols, C.copy(), max(n_list), PIX_MIN_DIST)
    print(f"eligible={eligible.sum()} thinned={len(kr)} ({time.time() - t0:.0f}s)")

    # --- scoring on the identical fold geometry ---
    truth_new = sgmc & footprint & (d_cat > 300.0)
    truth_raw = sgmc_raw & footprint & (d_cat > 300.0)

    def score(pred: np.ndarray) -> dict:
        out = {}
        for tname, truth in (("sgmc_newer_offcat", truth_new), ("sgmc_raw_offcat", truth_raw)):
            folds = {fn: score_fold(pred.astype(np.float64), truth, footprint, core) for fn, core in blocks.items()}
            out[tname] = {"mean_dti": float(np.mean([f["dti"] for f in folds.values()])),
                          "folds": {fn: float(f["dti"]) for fn, f in folds.items()}}
        return out

    report = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tag": args.tag,
              "inputs": {"base": str(args.base), "base_sha256": sha256_file(args.base), "scarp": str(args.scarp),
                         "scarp_sha256": sha256_file(args.scarp), "layer": args.layer, "cover_min": args.cover_min,
                         "min_height_m": args.min_height},
              "counts": {"C_dots": int(C.sum()), "covered_cells": int(covered.sum()), "eligible_cells": int(eligible.sum()),
                         "thinned_available": int(len(kr))},
              "detector_check": detector_check, "references": {}, "variants": {}}
    for name, pred in (("C_dotted_02778", C), ("prior_union_decision", C | tip), ("h49_yager_balanced", h49)):
        report["references"][name] = {"dots": int(pred.sum()), **score(pred)}
        print(name, report["references"][name]["sgmc_newer_offcat"]["mean_dti"])
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for n in n_list:
        n_eff = min(n, len(kr))
        add = np.zeros_like(C); add[kr[:n_eff], kc[:n_eff]] = True
        cand = C | add
        v = {"requested": n, "added": int(n_eff), "dots": int(cand.sum()),
             "min_height_added_m": float(height[kr[:n_eff], kc[:n_eff]].min()) if n_eff else None,
             "added_within_300m_of_catalogue": int((d_cat[kr[:n_eff], kc[:n_eff]] <= 300).sum()),
             **score(cand)}
        v["delta_vs_C_newer"] = v["sgmc_newer_offcat"]["mean_dti"] - report["references"]["C_dotted_02778"]["sgmc_newer_offcat"]["mean_dti"]
        v["delta_vs_h49_newer"] = v["sgmc_newer_offcat"]["mean_dti"] - report["references"]["h49_yager_balanced"]["sgmc_newer_offcat"]["mean_dti"]
        path = args.out_dir / f"h50_C_plus_{n_eff}{('_' + args.tag) if args.tag else ''}.tif"
        v["path"] = str(path.relative_to(ROOT)); v["sha256"] = write_candidate(path, cand, footprint, profile, nan_outside=True)
        report["variants"][str(n)] = v
        print(f"n={n_eff:5d} dots={v['dots']} newer={v['sgmc_newer_offcat']['mean_dti']:.6f} "
              f"(dC {v['delta_vs_C_newer']:+.6f}, dH49 {v['delta_vs_h49_newer']:+.6f}) raw={v['sgmc_raw_offcat']['mean_dti']:.6f} "
              f"folds={[round(x, 4) for x in v['sgmc_newer_offcat']['folds'].values()]}")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=1))
    print("wrote", args.report, f"({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
