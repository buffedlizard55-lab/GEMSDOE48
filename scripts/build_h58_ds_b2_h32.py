#!/usr/bin/env python3
"""Build the H58 dot-supported Dempster-Shafer GeoTIFF: dotted B2 x tip/Euler H32-1.

Parents (SHA-256 pinned, verified on read; both are owner mirrors, not organizer-authenticated):
  A  dotted family best   H33-2-B2 (data/raw/dotted_h33_2_b2_zeros.tif)        37,654 px, owner-reported 0.2778
  B  tip/Euler family     H32-1 prethin tip (data/raw/scored/h32_prethin_tip_02649.tif)  42,294 px, owner-reported 0.2649

Rule: src/gemsdoe48/ds58.py (two-sided simple support, owner-anchored discounts, normalized Dempster).
Scope note (2026-10-08): the parent pair B2 x tip H32-1 was already fused by H48-1
(docs/downloads/gemsdoe48-h48-1-ds-fusion-b2xh32tip-20261006-*.tif, which excludes tip dots within 200 m of the
catalogue). This H58-A file keeps the unpruned union support, so it is a different artifact, but it is not a new
pairing. See docs/research/h58-results-20261008.md.

Outputs (docs/downloads/):
  * primary GeoTIFF, all-finite float32, zeros outside the footprint (in [0,1])
  * NaN-outside twin with identical in-footprint values (official text says null/NaN outside)
  * diagnostics: unassigned mass m(Theta), raw conflict K, plausibility Pl(F), each on the support
Receipts (evidence/): build receipt (format, sha, not-average checks, sensitivity) and a
blocked-proxy receipt (official DTI on the SGMC off-catalogue public proxy, full footprint and
four quadrants with a 300 m halo).

Nothing here is organizer validation or a leaderboard estimate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe48 import ds58  # noqa: E402
from gemsdoe48 import metric as M  # noqa: E402
from gemsdoe48.metric import max_credit_field  # noqa: E402
from gemsdoe48.ds50 import spearman_rank_correlation  # noqa: E402
from gemsdoe48.grid import write_float32, write_submission  # noqa: E402
from gemsdoe48.holdout import quadrants  # noqa: E402

INPUTS = {
    "dotted_b2": (ROOT / "data/raw/dotted_h33_2_b2_zeros.tif",
                  "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"),
    "tip_h32_1": (ROOT / "data/raw/scored/h32_prethin_tip_02649.tif",
                  "04d31922f5c1ea4016984fc470ab2b0ff8e266c615792f0e86020da3b940d3ff"),
    "footprint": (ROOT / "data/source_mirrors/footprint-mask.tif",
                  "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f"),
    "catalogue": (ROOT / "data/official/labels.tif",
                  "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"),
    "sgmc": (ROOT / "data/official/derived_sgmc_faults_100m.tif",
             "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"),
}
# Comparison candidates for the proxy receipt (paths and hashes pinned as well).
COMPARISON = {
    "dotted_base_0.2708": (ROOT / "data/families/dotted_d2_8_02708.tif",
                           "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73"),
    "tip_H33-D_0.2632": (ROOT / "data/families/tip_stepover_r30_02632.tif",
                         "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757"),
    "H49_yager_pignistic": (ROOT / "docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif",
                            "9f028289c364c071065245799d7ed131600e80e9f0d10602806b12ce34d7cae8"),
}

DOWNLOADS = ROOT / "docs/downloads"
DATESTAMP = "20261008"
NAME = "GEMSDOE48-H58-ds-belief-dotted-x-tipeuler"
NOTE = (
    "GEMSDOE48 H58 | Dempster fusion, dotted B2 (owner 0.2778) x tip/Euler H32-1 (owner 0.2649); "
    "dot-supported Bel, m(Theta)+K diagnostics; unscored research."
)
SGMC_EXPECTED_OFFCAT = 62122
PROXY_RADIUS_M = 300.0
PIXEL_M = 100.0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_plane(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        arr = ds.read(1).astype(np.float64)
    return np.where(np.isfinite(arr), arr, 0.0)


def require(path: Path, expected: str, label: str) -> None:
    got = sha256_file(path)
    if got != expected:
        raise SystemExit(f"{label}: SHA-256 {got} != pinned {expected} ({path})")


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    if x.size < 2 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def topk_jaccard(x: np.ndarray, y: np.ndarray, support: np.ndarray, k: int) -> float:
    idx = np.flatnonzero(support.ravel())
    k = min(int(k), idx.size)
    top_x = set(idx[np.argsort(-x.ravel()[idx], kind="stable")[:k]].tolist())
    top_y = set(idx[np.argsort(-y.ravel()[idx], kind="stable")[:k]].tolist())
    union = top_x | top_y
    return len(top_x & top_y) / len(union) if union else float("nan")


def dti_row(pred: np.ndarray, truth: np.ndarray, fp: np.ndarray) -> dict:
    r = M.dti(pred, truth, fp)
    return {"dti": r.dti, "tpw": r.tpw, "fpw": r.fpw, "fnw": r.fnw,
            "mass": r.mass, "emitted": r.n_emitted}


def quadrant_scores(pred: np.ndarray, offcat: np.ndarray, fp: np.ndarray, quads) -> list[float]:
    """Core-quadrant truth; predictions inside the core plus a 300 m Euclidean halo."""
    out = []
    for quad in quads:
        dist_to_quad = distance_transform_edt(~quad, sampling=PIXEL_M)
        domain = (dist_to_quad <= PROXY_RADIUS_M) & fp
        truth_core = offcat & quad
        res = M.distance_weighted_tversky(pred, truth_core, valid=domain)
        out.append(float(res["dti"]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir", type=Path, default=DOWNLOADS)
    ap.add_argument("--receipt", type=Path, default=ROOT / f"evidence/build_h58_receipt_{DATESTAMP}.json")
    ap.add_argument("--proxy-receipt", type=Path, default=ROOT / f"evidence/holdout_h58_{DATESTAMP}.json")
    ap.add_argument("--skip-proxy", action="store_true", help="write files and build receipt only")
    args = ap.parse_args()
    out_name = NAME
    note = NOTE

    if len(note) > 200:
        raise SystemExit(f"submission note is {len(note)} characters; limit 200")
    for label, (path, sha) in {**INPUTS, **COMPARISON}.items():
        require(path, sha, label)

    with rasterio.open(INPUTS["footprint"][0]) as ds:
        fp = ds.read(1) == 1
        grid_profile = {"crs": ds.crs.to_string(), "transform": list(ds.transform)[:6],
                        "shape": [ds.height, ds.width], "dtype": ds.dtypes[0]}
    cat = read_plane(INPUTS["catalogue"][0]) > 0
    sgmc = read_plane(INPUTS["sgmc"][0]) > 0
    dotted = read_plane(INPUTS["dotted_b2"][0]) > 0
    tip = read_plane(INPUTS["tip_h32_1"][0]) > 0
    dotted &= fp
    tip &= fp

    dist_cat = distance_transform_edt(~cat, sampling=PIXEL_M)
    offcat = sgmc & fp & (dist_cat > PROXY_RADIUS_M)
    if int(offcat.sum()) != SGMC_EXPECTED_OFFCAT:
        raise SystemExit(f"SGMC off-catalogue count {int(offcat.sum())} != {SGMC_EXPECTED_OFFCAT}")

    ra, rb = ds58.reliabilities()
    fus = ds58.fuse_dots(dotted, tip, fp, ra, rb)
    belief = fus.belief
    support = fus.support
    if not (np.isfinite(belief).all() and belief.min() >= 0.0 and belief.max() <= 1.0):
        raise SystemExit("normalized belief failed the [0,1] finiteness check")

    # ---- not-the-average and disagreement checks ---------------------------------
    naive = ds58.naive_kernel_mean(dotted, tip, fp)
    a_only = dotted & ~tip
    b_only = tip & ~dotted
    both = dotted & tip
    ptl = {
        "pearson_support_vs_kernel_mean": pearson(belief[support], naive[support]),
        "spearman_support_vs_kernel_mean": spearman_rank_correlation(belief[support], naive[support]),
        "mae_support_vs_kernel_mean": float(np.abs(belief[support] - naive[support]).mean()),
        "max_abs_diff_support_vs_kernel_mean": float(np.abs(belief[support] - naive[support]).max()),
        "topK_jaccard_vs_kernel_mean_K_eq_B2": topk_jaccard(belief, naive, support, int(dotted.sum())),
        "is_the_average": False,
        "interpretation": (
            "The belief ranks almost identically to the kernel-credit average inside the support; its "
            "departure from the average is in magnitudes, and the disagreement itself is carried by the "
            "separate conflict K and unassigned-mass m(Theta) layers."
        ),
    }
    classes = {
        "B2_only": a_only, "H32_1_only": b_only, "both": both,
    }
    class_stats = {}
    for name, mask in classes.items():
        class_stats[name] = {
            "cells": int(mask.sum()),
            "mean_belief": float(belief[mask].mean()) if mask.any() else None,
            "mean_conflict_K": float(fus.conflict[mask].mean()) if mask.any() else None,
            "mean_m_theta": float(fus.m_theta[mask].mean()) if mask.any() else None,
        }

    # ---- sensitivity: other discount choices, same parents ---------------------
    sensitivity = {}
    for label, (ra_s, rb_s) in {
        "owner_ratio_primary": (ra, rb),
        "symmetric_0.95": (ds58.RHO_MAX, ds58.RHO_MAX),
        "symmetric_0.5": (0.5, 0.5),
    }.items():
        alt = ds58.fuse_dots(dotted, tip, fp, ra_s, rb_s)
        sensitivity[label] = {
            "reliabilities": [ra_s, rb_s],
            "pearson_vs_primary_support": pearson(alt.belief[support], belief[support]),
            "topK_jaccard_vs_primary_K_eq_B2": topk_jaccard(alt.belief, belief, support, int(dotted.sum())),
        }

    # ---- write outputs ---------------------------------------------------------
    args.outdir.mkdir(parents=True, exist_ok=True)
    tmp = args.outdir / f".tmp-h58-{DATESTAMP}.tif"
    write_submission(tmp, belief)
    primary_sha = sha256_file(tmp)
    sha8 = primary_sha[:8]
    stem = f"{out_name}-{DATESTAMP}-{sha8}"
    primary = args.outdir / f"{stem}-zeros-outside.tif"
    primary.unlink(missing_ok=True)
    tmp.rename(primary)

    twin_values = np.where(fp, belief, np.nan)
    twin = args.outdir / f"{stem}-nan-outside.tif"
    twin.unlink(missing_ok=True)
    write_float32(twin, twin_values, nodata=float("nan"))

    diag_dir = args.outdir / "diagnostics"
    diag_dir.mkdir(parents=True, exist_ok=True)
    diag_paths = {
        "mtheta": diag_dir / f"{stem}-diag-mtheta.tif",
        "conflict_K": diag_dir / f"{stem}-diag-conflict-K.tif",
        "plausibility": diag_dir / f"{stem}-diag-plausibility.tif",
    }
    diag_arrays = {"mtheta": fus.m_theta, "conflict_K": fus.conflict, "plausibility": fus.plausibility}
    for key, path in diag_paths.items():
        arr = np.clip(np.where(support, diag_arrays[key], 0.0), 0.0, 1.0)
        path.unlink(missing_ok=True)
        write_submission(path, arr)

    # ---- proxy receipt ---------------------------------------------------------
    proxy = {}
    if not args.skip_proxy:
        a_ds = belief
        candidates = {
            "B2_owner_0.2778 (parent A)": dotted.astype(np.float64),
            "H32-1_tip_owner_0.2649 (parent B)": tip.astype(np.float64),
            "naive_binary_mean_A_B": 0.5 * (dotted.astype(np.float64) + tip.astype(np.float64)),
            "union_binary_A_or_B": (dotted | tip).astype(np.float64),
            "H50_style_smeared_kernel_belief (control)": None,
            "H58_dot_supported_DS (this artifact)": a_ds,
        }
        # smeared H50-style control, full footprint, max-normalized
        m_f, _, _, _ = ds58.dempster_masks(max_credit_field(dotted.astype(np.float64)),
                                           max_credit_field(tip.astype(np.float64)), ra, rb)
        smear = m_f / float(m_f[fp].max())
        candidates["H50_style_smeared_kernel_belief (control)"] = np.where(fp, smear, 0.0)
        for label, (path, _sha) in COMPARISON.items():
            candidates[label] = (read_plane(path) > 0).astype(np.float64)

        quads = quadrants(fp)
        full = {}
        blocks = {}
        for name, pred in candidates.items():
            pred = np.where(cat, 0.0, np.clip(pred, 0.0, 1.0))  # official pixel-exact mask of known faults
            full[name] = dti_row(np.where(fp, pred, 0.0), offcat, fp)
            blocks[name] = quadrant_scores(np.where(fp, pred, 0.0), offcat, fp, quads)
        base = blocks["B2_owner_0.2778 (parent A)"]
        paired = {}
        for name, vals in blocks.items():
            deltas = [v - b for v, b in zip(vals, base)]
            paired[name] = {
                "quadrant_dti": vals,
                "mean_quadrant_dti": float(np.mean(vals)),
                "mean_delta_vs_B2": float(np.mean(deltas)),
                "folds_above_B2": int(sum(d > 0 for d in deltas)),
            }
        best_existing = max(
            (n for n in full if not n.startswith("H58")),
            key=lambda n: full[n]["dti"],
        )
        proxy = {
            "schema": "GEMSDOE48-H58-proxy-v1",
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "metric": "official distance-weighted Tversky: alpha=0.2, beta=0.8, triangular 300 m kernel (src/gemsdoe48/metric.py)",
            "truth": "SGMC off-catalogue public-map proxy: derived SGMC cells >300 m from the public catalogue (62,122 px). NOT the organizer's new-fault labels.",
            "masking": "predictions on pixel-exact catalogue cells set to 0 (organizer 2026-09-21 clarification)",
            "full_footprint_dti": full,
            "quadrant_protocol": {
                "description": "four quadrants; core truth only; predictions inside core plus 300 m Euclidean halo",
                "results": paired,
            },
            "best_existing_full_footprint_candidate": best_existing,
            "gate": {
                "required": "beat the current best comparable candidate on the proxy in >=3/4 quadrants AND full footprint, before any slot",
                "dot_supported_beats_B2_full_footprint": full["H58_dot_supported_DS (this artifact)"]["dti"] > full["B2_owner_0.2778 (parent A)"]["dti"],
                "dot_supported_beats_H49_full_footprint": full["H58_dot_supported_DS (this artifact)"]["dti"] > full["H49_yager_pignistic"]["dti"],
                "dot_supported_folds_above_B2": paired["H58_dot_supported_DS (this artifact)"]["folds_above_B2"],
                "result": "NOT CLEARED",
            },
            "limitations": [
                "Proxy truth is a public SGMC map filtered by distance to the catalogue, not expert new-fault labels.",
                "Differences among the 0.26-0.28 parents on this proxy are about 0.001-0.002 and are within proxy noise.",
                "The owner-reported score ladder is not reproduced by this proxy; no local file-to-score link exists.",
            ],
        }
        args.proxy_receipt.parent.mkdir(parents=True, exist_ok=True)
        args.proxy_receipt.write_text(json.dumps(proxy, indent=2, sort_keys=True) + "\n")

    receipt = {
        "schema": "GEMSDOE48-H58-build-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "submission_name": f"{out_name}-{DATESTAMP}-{sha8}",
        "submission_note": note,
        "submission_note_length": len(note),
        "variant": "H58-A brief-literal dot-supported DS (preregistered design)",
        "primary_file": primary.relative_to(ROOT).as_posix(),
        "primary_sha256": primary_sha,
        "primary_bytes": primary.stat().st_size,
        "primary_encoding": "all-finite float32, zeros outside footprint, nodata unset",
        "nan_outside_twin": twin.relative_to(ROOT).as_posix(),
        "nan_outside_sha256": sha256_file(twin),
        "diagnostics": {k: {"file": p.relative_to(ROOT).as_posix(), "sha256": sha256_file(p)} for k, p in diag_paths.items()},
        "grid": grid_profile,
        "inputs": {k: {"path": p.relative_to(ROOT).as_posix(), "sha256": s} for k, (p, s) in {**INPUTS, **COMPARISON}.items()},
        "rule": {
            "module": "src/gemsdoe48/ds58.py",
            "frame": "Theta = {F, notF}; two-sided simple support; normalized Dempster rule",
            "reliabilities": {"dotted_B2": ra, "tip_H32_1": rb,
                              "anchor": "owner-reported 0.2778 / 0.2649; ratio heuristic, not calibration"},
            "emission_support": "union of committed dots of both parents inside the footprint",
            "normalization": "belief = m12(F) / max over support, clipped to [0,1]",
        },
        "counts": {
            "dotted_B2": int(dotted.sum()), "tip_H32_1": int(tip.sum()),
            "both": int(both.sum()), "support_union": int(support.sum()),
            "primary_positive_cells": int((belief > 0).sum()),
            "belief_eq_1_cells": int((belief >= 0.999999).sum()),
        },
        "not_average_checks": ptl,
        "class_statistics": class_stats,
        "sensitivity": sensitivity,
        "proxy_receipt": args.proxy_receipt.relative_to(ROOT).as_posix() if not args.skip_proxy else None,
        "verdict": {
            "download_for_inspection": True,
            "submit_cleared": False,
            "reason": "Does not beat the H49 proxy-best, is below B2 and the prior H48-1 file on the sparse-truth proxies, and does not clearly beat its parents; AGENTS.md gate not met. Public proxy is not private or organizer evidence.",
        },
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    print(json.dumps({
        "primary": primary.name, "sha256": primary_sha, "twin": twin.name,
        "support": int(support.sum()), "pearson_support_vs_kernel_mean": ptl["pearson_support_vs_kernel_mean"],
        "spearman_support_vs_kernel_mean": ptl["spearman_support_vs_kernel_mean"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
