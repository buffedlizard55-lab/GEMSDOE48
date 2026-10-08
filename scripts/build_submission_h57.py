#!/usr/bin/env python3
"""H57-RELIEF — reproduce a historical Dempster-Shafer/lidar research artifact.

This builder preserves the recorded A/B/C construction and emits local format and
Dempster diagnostics. It does NOT calculate a live score, hidden-truth count,
per-dot break-even, candidate ceiling, or submission recommendation. The previous
surrogate projection used the invalid identity FPw = S - TPw; see
``docs/research/h57-relief-metric-erratum-20261007.md``. The artifact remains OK
for inspection only and is NOT CLEARED TO SUBMIT.

Namespace: this built H57-RELIEF artifact is separate from the two same-day
H57-A planning slates. Parent-score values and the catalogue-flank rationale are
owner-reported planning assumptions, not verified local-file attribution or
calibrated reliabilities.

The builder writes a normalized Bel(F) surface and separate residual m(Theta),
raw conflict K, and plausibility diagnostics. m(Theta) is unassigned/ignorance
mass, not conflict or direct family disagreement. A separate historical binary
emission is retained for reproducibility; its existence is not a metric-optimality
claim or a weekly-slot clearance. Local range and uniqueness checks are not
organizer portal acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

import numpy as np
import rasterio
from affine import Affine
from scipy import ndimage as ndi

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems48.ds import bpa, dempster, pignistic  # noqa: E402
from gemsdoe48 import metric as M  # noqa: E402

GRID_TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
GRID_SHAPE = (3730, 3292)
CRS = "EPSG:32611"
RHO_MAX = 0.95
SIGMA_CM = 200          # 2.0 m mean context roughness (band is in centimetres)
COVER_MIN = 50          # 50 % of the 100 m cell covered by valid 3 m samples
NMS_CELLS = 3
CATALOGUE_FLANK_CELLS = 2.0
R_B = 0.2632 / 0.2778


def read1(path: pathlib.Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        return ds.read(1)


def binary(path: pathlib.Path) -> np.ndarray:
    a = np.nan_to_num(read1(path).astype(np.float32), nan=0.0)
    return a > 0


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def nms(score: np.ndarray, mask: np.ndarray, spacing: int) -> np.ndarray:
    """Non-maximum suppression: local peaks only, then strongest-first exclusion disc.

    Byte-identical to the rule validated in the spatially-blocked holdout; do not
    "simplify" it (dropping the peak filter changes the dot set and the validated credit).
    """
    cand = mask & (score > 0)
    peak = ndi.maximum_filter(score, size=2 * spacing + 1, mode="constant", cval=-1.0)
    ys, xs = np.nonzero(cand & (score >= peak))
    order = np.argsort(-score[ys, xs], kind="stable")
    taken = np.zeros(score.shape, dtype=bool)
    ky: list[int] = []
    kx: list[int] = []
    h, w = score.shape
    for i in order:
        y, x = int(ys[i]), int(xs[i])
        if taken[y, x]:
            continue
        ky.append(y)
        kx.append(x)
        taken[max(0, y - spacing):min(h, y + spacing + 1),
              max(0, x - spacing):min(w, x + spacing + 1)] = True
    out = np.zeros(score.shape, dtype=bool)
    if ky:
        out[np.asarray(ky), np.asarray(kx)] = True
    return out


def write_tif(path: pathlib.Path, arr: np.ndarray, *, nodata, dtype="float32") -> None:
    profile = {
        "driver": "GTiff", "height": arr.shape[0], "width": arr.shape[1], "count": 1,
        "dtype": dtype, "crs": CRS, "transform": GRID_TRANSFORM,
        "compress": "deflate", "predictor": 2, "tiled": True, "nodata": nodata,
    }
    with rasterio.open(path, "w", **profile) as ds:
        ds.write(arr.astype(dtype), 1)
        ds.set_band_description(1, "prediction")


def main() -> int:
    ap = argparse.ArgumentParser()
    # Keep rebuilds out of the tracked download/evidence archive by default. The
    # dated build receipt contains the former projection under forensic-only
    # fields; a scratch rebuild must not silently replace that archival record.
    scratch_dir = ROOT / "scratch" / "h57-relief-rebuild"
    ap.add_argument("--out-dir", default=str(scratch_dir))
    ap.add_argument("--receipt", default=str(scratch_dir / "build_h57_receipt.json"))
    ap.add_argument("--id", default=None)
    args = ap.parse_args()
    out = pathlib.Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)

    lab = read1(ROOT / "data" / "official" / "labels.tif")
    footprint = lab != -1
    catalogue = lab == 1
    dcat = ndi.distance_transform_edt(~catalogue)

    A = binary(ROOT / "data" / "families" / "dotted_b2_prune_02778.tif")
    B = binary(ROOT / "data" / "families" / "tip_stepover_r30_02632.tif")
    if A.shape != GRID_SHAPE or B.shape != GRID_SHAPE:
        raise SystemExit("parent family grid mismatch")

    # ---- lidar relief evidence ---------------------------------------------
    with rasterio.open(ROOT / "data" / "external" / "h52_scarp3m_100m.tif") as ds:
        names = list(ds.descriptions)
        raw_sig = ds.read(names.index("sigma_mean") + 1)
        raw_cov = ds.read(names.index("cover") + 1)
    sigma = np.where(raw_sig == -32768, 0, raw_sig).astype(np.float32)
    cover = np.where(raw_cov == -32768, 0, raw_cov).astype(np.float32)

    # ---- basic probability assignments and Dempster combination ------------
    absence = np.ones(GRID_SHAPE, dtype=np.float32)
    absence[dcat <= CATALOGUE_FLANK_CELLS] = 0.0
    mA = bpa(A, 1.0, absence)[:3]
    mB = bpa(B, float(R_B), absence)[:3]
    fAB, nAB, uAB, KAB = dempster(mA, mB)

    supportAB = M.max_kernel_to_truth((A | B))
    blank = (supportAB <= 0.0) & footprint & (dcat > CATALOGUE_FLANK_CELLS)
    relief = (sigma >= SIGMA_CM) & (cover >= COVER_MIN)
    L = nms(sigma, blank & relief, NMS_CELLS)
    rC = RHO_MAX
    mC = bpa(L, rC, absence)[:3]
    f, n_, u, K = dempster((fAB, nAB, uAB), mC)

    bel = np.clip(f, 0.0, 1.0).astype(np.float32)
    pl = np.clip(f + u, 0.0, 1.0).astype(np.float32)
    mtheta = np.clip(u, 0.0, 1.0).astype(np.float32)
    kconf = np.clip(K, 0.0, 1.0).astype(np.float32)
    mx = float(bel.max())
    if mx > 0:
        bel = (bel / mx).astype(np.float32)
    bel = np.clip(bel, 0.0, 1.0).astype(np.float32)
    pl = np.clip(pl / max(float(pl.max()), 1e-9), 0.0, 1.0).astype(np.float32)

    # ---- recorded historical binary emission -------------------------------
    # This reproduces the prior A-plus-lidar recipe. It is not called metric-optimal:
    # the old live-score/break-even model is invalidated and no slot is cleared.
    decision = ((A | (A & B) | L) & footprint).astype(np.float32)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    digest_src = json.dumps({
        "A": int(A.sum()), "B": int(B.sum()), "L": int(L.sum()),
        "sigma_cm": SIGMA_CM, "cover_min": COVER_MIN, "nms": NMS_CELLS,
        "rB": round(float(R_B), 6), "rC": rC,
    }, sort_keys=True).encode()
    cid = args.id or hashlib.sha256(digest_src).hexdigest()[:12]
    # Every companion of this artefact must start with the primary's stem so that
    # scripts/check_candidate_uniqueness.py classifies it as the same artefact.
    stem = f"GEMSDOE48-H57-ds-relief-augmented-{stamp}-{cid}"

    files: dict[str, str] = {}
    primary = out / f"{stem}.tif"
    write_tif(primary, decision, nodata=None)
    files["primary_zeros_outside"] = str(primary)
    nan_twin = out / f"{stem}-nan-outside.tif"
    nan_arr = decision.copy()
    nan_arr[~footprint] = np.nan
    write_tif(nan_twin, nan_arr, nodata=float("nan"))
    files["nan_outside_twin"] = str(nan_twin)
    zpath = out / f"{stem}.zip"
    import zipfile
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(primary, arcname=primary.name)
    files["primary_zip"] = str(zpath)
    for tag, arr in (("belief", bel), ("mtheta", mtheta), ("conflict-k", kconf), ("plausibility", pl)):
        p = out / "diagnostics" / f"{stem}-diag-{tag}.tif"
        p.parent.mkdir(parents=True, exist_ok=True)
        write_tif(p, arr, nodata=None)
        files[f"diag_{tag}"] = str(p)

    # ---- checks -------------------------------------------------------------
    with rasterio.open(primary) as ds:
        chk = ds.read(1)
        prof = dict(ds.profile)
    all_finite = bool(np.isfinite(chk).all())
    in_range = bool(chk.min() >= 0.0 and chk.max() <= 1.0)
    naive = 0.5 * A.astype(np.float32) + 0.5 * B.astype(np.float32)
    x, y = bel.ravel(), naive.ravel()
    pearson = float(np.corrcoef(x, y)[0, 1])
    rx = np.argsort(np.argsort(x)); ry = np.argsort(np.argsort(y))
    spearman = float(np.corrcoef(rx, ry)[0, 1])
    resid = float(np.abs(bel - naive).mean())
    pos = bel > 0
    resid_pos = float(np.abs(bel - naive)[pos].mean())
    pearson_pos = float(np.corrcoef(bel[pos], naive[pos])[0, 1])
    kernel_mean = 0.5 * M.max_kernel_to_truth(A) + 0.5 * M.max_kernel_to_truth(B)
    km = float(kernel_mean.max())
    affine_resid = float(np.abs(bel - (kernel_mean / km if km else kernel_mean)).mean())
    top = int(A.sum())
    def topset(a):
        idx = np.argsort(-a.ravel(), kind="stable")[:top]
        m = np.zeros(a.size, bool); m[idx] = True
        return m.reshape(a.shape)
    jac = float((topset(bel) & A).sum() / (topset(bel) | A).sum())

    receipt = {
        "candidate_id": "H57-RELIEF",
        "namespace_note": "Distinct from both same-day H57-A planning slates; see the H57-RELIEF metric-identity erratum.",
        "slug": stem,
        "content_digest12": cid,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "brief": "historical Dempster-Shafer two-family fusion + lidar-relief research artifact; not slot-cleared",
        "parents": {
            "A_dotted": {"file": "data/families/dotted_b2_prune_02778.tif",
                         "sha256": sha256(ROOT / "data" / "families" / "dotted_b2_prune_02778.tif"),
                         "dots": int(A.sum()), "owner_reported_score_claim_unverified": 0.2778, "discount": 1.0},
            "B_tip_stepover": {"file": "data/families/tip_stepover_r30_02632.tif",
                               "sha256": sha256(ROOT / "data" / "families" / "tip_stepover_r30_02632.tif"),
                               "dots": int(B.sum()), "owner_reported_score_claim_unverified": 0.2632,
                               "discount": round(float(R_B), 6)},
            "C_lidar_relief": {"file": "data/external/h52_scarp3m_100m.tif",
                               "band": "sigma_mean", "threshold_cm": SIGMA_CM,
                               "threshold_m": SIGMA_CM / 100.0,
                               "cover_min": COVER_MIN, "nms_cells": NMS_CELLS,
                               "dots": int(L.sum()), "discount": rC},
        },
        "emission": {
            "dots": int(decision.sum()),
            "from_A_only": int((A & ~B & ~L).sum()),
            "from_A_and_B": int((A & B).sum()),
            "from_C_lidar": int((L & ~A).sum()),
            "B_only_rejected": int((B & ~A).sum()),
            "footprint_cells": int(footprint.sum()),
            "emitted_fraction": float(decision.sum() / footprint.sum()),
            "on_catalogue_pixels": int(((decision > 0) & catalogue).sum()),
            "min_dcat_cells": float(dcat[decision > 0].min()),
        },
        "dempster": {
            "bel_max": float(bel.max()), "bel_positive_cells": int((bel > 0).sum()),
            "mtheta_mean": float(mtheta.mean()), "mtheta_max": float(mtheta.max()),
            "mtheta_sum": float(mtheta.sum()),
            "conflict_K_mean": float(kconf.mean()), "conflict_K_max": float(kconf.max()),
        },
        "not_the_naive_mean": {
            "pearson_bel_vs_binary_mean": pearson,
            "spearman_bel_vs_binary_mean": spearman,
            "pearson_on_positive_cells": pearson_pos,
            "mean_abs_diff_vs_binary_mean": resid,
            "mean_abs_diff_on_positive_cells": resid_pos,
            "max_abs_diff_vs_binary_mean": float(np.abs(bel - naive).max()),
            "mean_abs_affine_residual_vs_kernel_mean": affine_resid,
            "top_rank_set_jaccard_vs_A": jac,
        },
        "format_checks": {
            "single_band": prof.get("count") == 1,
            "dtype_float32": prof.get("dtype") == "float32",
            "shape": [chk.shape[0], chk.shape[1]],
            "crs": str(prof.get("crs")),
            "transform": list(GRID_TRANSFORM)[:6],
            "all_cells_finite": all_finite,
            "min": float(chk.min()), "max": float(chk.max()),
            "values_in_0_1": in_range,
            "nodata": prof.get("nodata"),
            "portal_range_error_immune": all_finite and in_range,
            "organizer_acceptance_tested": False,
            "local_only_note": "Range/grid checks only; portal acceptance is not tested.",
        },
        "files": {k: {"path": str(pathlib.Path(v).relative_to(ROOT)),
                      "bytes": pathlib.Path(v).stat().st_size,
                      "sha256": sha256(pathlib.Path(v))} for k, v in files.items()},
        "verdict": {
            "download": "OK FOR INSPECTION",
            "submit": "NOT CLEARED TO SUBMIT",
            "basis": "The previous live-score projection and per-dot threshold were invalidated by the metric-identity correction; this record does not establish a comparable blocked-H49 win or organizer acceptance.",
        },
        "dempster_semantics": "m(Theta) is residual unassigned/ignorance mass; raw K is the separate pre-normalization conflict diagnostic; neither is a calibrated probability or literal family-disagreement map.",
        "metric_projection_status": {
            "status": "INVALIDATED_METRIC_IDENTITY_DO_NOT_USE",
            "reason": "This builder intentionally does not regenerate live-equivalent DTI, hidden-truth density, per-dot break-even, ceiling, floor, or sensitivity estimates based on FPw = S - TPw.",
            "superseding_erratum": "docs/research/h57-relief-metric-erratum-20261007.md",
            "recomputed_by_current_builder": False,
        },
    }
    pathlib.Path(args.receipt).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(args.receipt).write_text(json.dumps(receipt, indent=2))
    print(json.dumps({k: receipt[k] for k in ("candidate_id", "slug", "emission",
                                              "not_the_naive_mean", "format_checks")}, indent=2))
    print("\nprimary:", files["primary_zeros_outside"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
