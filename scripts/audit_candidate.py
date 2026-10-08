#!/usr/bin/env python3
"""RETIRED: historical GEMSDOE48-GATE-2 proxy audit; not valid for promotion.

The original protocol compared equal-mass surfaces and randomly thinned a public
SGMC proxy to ``LIVE_TRUTH_PX = 14,307``. That count came from an invalid
``FPw = S - TPw`` hidden-truth inversion. It also applied ``0.05556`` as a
universal live break-even bar, although that condition only follows under
restrictive assumptions about the increments to both truth-centred T and
prediction-centred Q. The metric-identity erratum invalidates the inferred
truth-density calibration and the general interpretation of this threshold.

The code is retained only to reproduce historical receipts. Its PASS/FAIL,
density-matched values and live-scaled threshold MUST NOT be used to promote a
candidate or claim private-label performance. A re-derived, independently
validated gate is required before a future promotion. Local format checks and
equal-mass public-proxy scores may still be inspected as historical diagnostics.

Usage for forensic reproduction only (requires an explicit opt-in):
    python scripts/audit_candidate.py CANDIDATE.tif --legacy-audit-only --receipt evidence/audit_x.json

See ``docs/research/metric-identity-erratum-20261007.md``.
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
from gems48.validation import score_dti_regions  # noqa: E402

RADIUS_M = 300.0
ALPHA = 0.2
BETA = 0.8
PIXEL_YX_M = (100.0, 100.0)
LIVE_TRUTH_PX = 14307  # HISTORICAL ONLY: invalid FPw=S-TPw inversion; do not use for promotion
INCUMBENT_LIVE_DTI = 0.2778  # owner-reported ladder value for the incumbent; not organizer-authenticated
EQUAL_MASS_TOLERANCE = -0.002  # subsample repeat-resolution of the equal-mass test
DEFAULT_INCUMBENT = ROOT / "data/raw/scored/b2_02778.tif"
DEFAULT_LABELS = ROOT / "data/official/labels.tif"
DEFAULT_SGMC = ROOT / "data/official/derived_sgmc_faults_100m.tif"
DEFAULT_FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
EXPECTED_GRID = (3730, 3292)
VALIDITY_STATUS = "INVALIDATED_FORENSIC_ONLY_DO_NOT_USE_FOR_PROMOTION"
INVALIDATION_REASON = (
    "The historical density match uses a hidden-truth count inferred through the invalid "
    "FPw=S-TPw substitution, and its 0.05556 threshold is not universal."
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_surface(path: Path) -> tuple[np.ndarray, dict]:
    path = path.resolve()
    with rasterio.open(path) as source:
        arr = source.read(1).astype(np.float64)
        profile = source.profile.copy()
        crs = str(source.crs)
        epsg = source.crs.to_epsg() if source.crs else None
        transform = tuple(source.transform)[:6]
        shape = tuple(source.shape)
        nodata = source.nodata
        count = source.count
        dtype = source.dtypes[0]
    return arr, {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "bands": count,
        "dtype": dtype,
        "crs": crs,
        "epsg": epsg,
        "shape": list(shape),
        "transform": list(transform),
        "nodata": nodata,
    }


def grid_ok(info: dict) -> bool:
    return (
        info["bands"] == 1
        and info["dtype"] == "float32"
        and info["epsg"] == 32611
        and tuple(info["shape"]) == EXPECTED_GRID
    )


def decide(*, format_ok: bool, identical: bool, equal_mass_delta: float, n_added: int,
           density_matched_credit: float, bar_live: float, bar_proxy: float,
           legacy_audit_only: bool = False) -> tuple[str, list[str]]:
    """Reproduce the retired Gate-2 verdict logic for forensic comparison only."""
    if not legacy_audit_only:
        raise RuntimeError("invalidated Gate-2 decision logic; explicit legacy_audit_only=True is required")
    reasons: list[str] = []
    if not format_ok:
        reasons.append("format_or_range_failed")
    if identical:
        reasons.append("identical_support_to_incumbent")
    elif equal_mass_delta < EQUAL_MASS_TOLERANCE:
        reasons.append(f"equal_mass_credit_density_below_incumbent ({equal_mass_delta:+.5f})")
    if n_added:
        if density_matched_credit < bar_live:
            reasons.append(
                "added_cells_below_live_break_even_bar "
                f"(density-matched {density_matched_credit:.4f} < {bar_live:.4f} per cell)")
        elif density_matched_credit < bar_proxy:
            reasons.append("added_cells_below_raw_proxy_bar")
    if identical:
        return "IDENTICAL_TO_INCUMBENT", reasons
    if not reasons:
        return "PASS_MASS_NEUTRAL", reasons
    return "FAIL_MASS_NEUTRAL", reasons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--legacy-audit-only", action="store_true",
                        help="required opt-in: reproduce the invalidated historical Gate-2 proxy diagnostic only")
    parser.add_argument("--incumbent", type=Path, default=DEFAULT_INCUMBENT)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--sgmc", type=Path, default=DEFAULT_SGMC)
    parser.add_argument("--footprint", type=Path, default=DEFAULT_FOOTPRINT)
    parser.add_argument("--equal-mass-seeds", type=int, default=3)
    parser.add_argument("--density-match-seeds", type=int, default=5)
    parser.add_argument("--live-truth-px", type=int, default=LIVE_TRUTH_PX,
                        help="historical inferred density (invalidated); retained for forensic reproduction")
    parser.add_argument("--incumbent-live-dti", type=float, default=INCUMBENT_LIVE_DTI,
                        help="owner-reported historical anchor; not organizer-authenticated")
    parser.add_argument("--support-threshold", type=float, default=0.0,
                        help="cells with candidate value > threshold count as emitted (use >0 for graded "
                             "candidates; the mass-neutral blocks assume a near-binary emission)")
    parser.add_argument("--random-control", action="store_true",
                        help="also score a uniform-random equal-mass control drawn from the allowed pool")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    if not args.legacy_audit_only:
        parser.error(
            "the historical Gate-2 calibration is invalidated; no current promotion audit is available. "
            "Use --legacy-audit-only only to reproduce old receipts."
        )

    cand, cand_info = read_surface(args.candidate)
    incumbent, inc_info = read_surface(args.incumbent)
    labels, _ = read_surface(args.labels)
    sgmc, _ = read_surface(args.sgmc)
    with rasterio.open(args.footprint) as source:
        footprint = source.read(1) == 1

    # ---------------------------------------------------------------- format
    finite = np.isfinite(cand)
    in_range = bool(np.all((cand[finite] >= 0.0) & (cand[finite] <= 1.0))) if finite.any() else False
    format_block = {
        "bands_dtype_crs_shape_ok": bool(grid_ok(cand_info)),
        "all_finite_in_footprint": bool(np.isfinite(cand[footprint]).all()),
        "finite_iff_footprint": bool(np.array_equal(finite & footprint, footprint)),
        "finite_outside_footprint_count": int((finite & ~footprint).sum()),
        "min": float(np.nanmin(np.where(finite, cand, np.nan))) if finite.any() else None,
        "max": float(np.nanmax(np.where(finite, cand, np.nan))) if finite.any() else None,
        "values_in_0_1": in_range,
        "positive_cells": int((cand[footprint] > 0).sum()),
        "total_mass": float(cand[footprint].sum()),
        "portal_range_ok": bool(np.isfinite(cand[footprint]).all() and in_range),
    }

    # ------------------------------------------------------------- the proxy
    known = labels == 1
    valid = footprint & ~known
    dist_known = distance_transform_edt(~known, sampling=PIXEL_YX_M)
    truth = (sgmc > 0) & footprint & (dist_known > RADIUS_M) & ~known
    height, width = footprint.shape
    regions = {"overall": valid.copy()}
    row_mid, col_mid = height // 2, width // 2
    for name, (ys, xs) in {
        "northwest": (slice(0, row_mid), slice(0, col_mid)),
        "northeast": (slice(0, row_mid), slice(col_mid, width)),
        "southwest": (slice(row_mid, height), slice(0, col_mid)),
        "southeast": (slice(row_mid, height), slice(col_mid, width)),
    }.items():
        region = np.zeros((height, width), dtype=bool)
        region[ys, xs] = True
        regions[name] = region
    folds = ("northwest", "northeast", "southwest", "southeast")

    def score(prediction: np.ndarray, truth_mask: np.ndarray = truth) -> dict:
        result = score_dti_regions(
            prediction.astype(np.float32), truth_mask, valid, regions,
            radius_m=RADIUS_M, pixel_size_yx_m=PIXEL_YX_M, alpha=ALPHA, beta=BETA,
        )
        fold_values = [result[name]["dti"] for name in folds]
        return {
            "overall": float(result["overall"]["dti"]),
            "mean4": float(np.mean(fold_values)),
            "folds": [float(v) for v in fold_values],
            "tp": float(result["overall"]["tp"]),
            "truth_pixels": int(result["overall"]["truth_pixels"]),
        }

    threshold = float(args.support_threshold)
    incumbent_support = np.isfinite(incumbent) & (incumbent > threshold)
    support = np.isfinite(cand) & (cand > threshold)
    incumbent_score = score(incumbent_support.astype(np.float64))
    candidate_score = score(support.astype(np.float64))
    n_incumbent = int(incumbent_support.sum())
    bar_proxy = float(0.2 * incumbent_score["overall"])          # for raw-proxy credit
    bar_live = float(0.2 * args.incumbent_live_dti)              # for density-matched credit

    # ------------------------------------------------------------ equal mass
    equal_mass = []
    rows, cols = np.nonzero(support)
    for seed in range(args.equal_mass_seeds):
        if len(rows) <= n_incumbent:
            subset = support
        else:
            pick = np.random.default_rng(10_000 + seed).choice(len(rows), size=n_incumbent, replace=False)
            subset = np.zeros_like(support)
            subset[rows[pick], cols[pick]] = True
        equal_mass.append(score(subset.astype(np.float64)))
    equal_mass_mean4 = float(np.mean([row["mean4"] for row in equal_mass]))
    equal_mass_delta = equal_mass_mean4 - incumbent_score["mean4"]
    if abs(equal_mass_delta) < 1e-12:
        # an identical support cannot have a non-zero credit-density delta; the
        # residual is fold-mean accumulation noise and must not read as a signal
        equal_mass_delta = 0.0

    # --------------------------------------------------- random mass control
    random_control: dict | None = None
    if args.random_control:
        pool = valid & (dist_known > RADIUS_M) & ~(distance_transform_edt(~incumbent_support) <= 3.0)
        pool_rows, pool_cols = np.nonzero(pool)
        pick = np.random.default_rng(30_000).choice(
            len(pool_rows), size=min(n_incumbent, len(pool_rows)), replace=False)
        control = np.zeros_like(pool)
        control[pool_rows[pick], pool_cols[pick]] = True
        control_score = score(control.astype(np.float64))
        random_control = {"pool_cells": int(len(pool_rows)), "sampled_cells": int(control.sum()), **control_score}
        random_control["delta_vs_incumbent"] = control_score["mean4"] - incumbent_score["mean4"]

    # ------------------------------------------------------------- additions
    added = support & ~incumbent_support
    n_added = int(added.sum())
    addition_block: dict = {"added_cells": n_added}
    if n_added == 0:
        addition_block.update({"marginal_credit_per_cell": 0.0, "density_matched_credit_per_cell": 0.0})
    else:
        full_credit = score((incumbent_support | added).astype(np.float64))["tp"] - incumbent_score["tp"]
        density_matched = []
        truth_idx = np.nonzero(truth.ravel())[0]
        target = min(args.live_truth_px, len(truth_idx))
        for seed in range(args.density_match_seeds):
            keep = np.random.default_rng(20_000 + seed).choice(len(truth_idx), size=target, replace=False)
            thin = np.zeros(truth.size, dtype=bool)
            thin[truth_idx[keep]] = True
            thin = thin.reshape(truth.shape)
            tp_base = score(incumbent_support.astype(np.float64), thin)["tp"]
            tp_union = score((incumbent_support | added).astype(np.float64), thin)["tp"]
            density_matched.append((tp_union - tp_base) / n_added)
        addition_block.update({
            "break_even_bar_raw_proxy": bar_proxy,
            "break_even_bar_live_scaled": bar_live,
            "marginal_credit_per_cell_raw_proxy": float(full_credit / n_added),
            "density_matched_credit_per_cell": float(np.mean(density_matched)),
            "density_matched_credit_per_cell_seeds": [float(v) for v in density_matched],
        })

    # --------------------------------------------------------------- verdict
    legacy_verdict, legacy_reasons = decide(
        format_ok=bool(format_block["bands_dtype_crs_shape_ok"] and format_block["portal_range_ok"]),
        identical=bool(np.array_equal(support, incumbent_support)),
        equal_mass_delta=equal_mass_delta,
        n_added=n_added,
        density_matched_credit=addition_block.get("density_matched_credit_per_cell", 0.0),
        bar_live=bar_live,
        bar_proxy=bar_proxy,
        legacy_audit_only=True,
    )

    report = {
        "schema": "GEMSDOE48-candidate-audit-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "protocol": "RETIRED historical GEMSDOE48-GATE-2 reproduction; equal-mass public proxy + "
                    "density-matched test using an invalid inferred live-truth count",
        "protocol_status": "INVALIDATED_DO_NOT_USE_FOR_PROMOTION",
        "validity_status": VALIDITY_STATUS,
        "invalidation_reason": INVALIDATION_REASON,
        "promotion_use": "NONE — historical forensic reproduction only.",
        "leaderboard_linkage": "No organizer receipt links owner-reported anchors to the local TIFF bytes.",
        "warning": "Forensic reproduction only. Public proxy, not private truth or an organizer score. "
                   "The density match uses an invalid FPw=S-TPw inversion and the 0.05556 threshold "
                   "is not a universal break-even rule. PASS/FAIL does not authorize or clear any upload.",
        "legacy_opt_in_required": True,
        "candidate": cand_info,
        "incumbent": inc_info,
        "counts": {
            "incumbent_cells": n_incumbent,
            "candidate_cells": int(support.sum()),
            "added_cells": n_added,
            "proxy_truth_pixels": int(truth.sum()),
            "density_matched_truth_pixels": int(args.live_truth_px),
            "break_even_bar_raw_proxy": bar_proxy,
            "break_even_bar_live_scaled": bar_live,
            "incumbent_live_dti_source": f"owner-reported ladder anchor {args.incumbent_live_dti} (not organizer-authenticated)",
        },
        "format": format_block,
        "proxy_scores": {"incumbent": incumbent_score, "candidate": candidate_score},
        "random_equal_mass_control": random_control,
        "equal_mass": {
            "seeds": args.equal_mass_seeds,
            "mean4": equal_mass_mean4,
            "delta_vs_incumbent": equal_mass_delta,
            "per_seed": equal_mass,
        },
        "additions": addition_block,
        "legacy_verdict": legacy_verdict,
        "legacy_reasons": legacy_reasons,
        "verdict": "INVALIDATED_FOR_FORENSIC_REPRODUCTION_ONLY",
        "reasons": ["Historical verdict is invalidated; see validity_status and invalidation_reason."],
    }
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(report, indent=2) + "\n")
    print("LEGACY AUDIT ONLY — INVALIDATED; DO NOT USE FOR PROMOTION")
    print(json.dumps({k: report[k] for k in ("verdict", "legacy_verdict", "reasons", "counts", "equal_mass", "additions")}, indent=2))
    print(f"\nincumbent proxy mean4={incumbent_score['mean4']:.6f}  candidate proxy mean4={candidate_score['mean4']:.6f}")
    print(f"historical equal-mass mean4={equal_mass_mean4:.6f} (delta {equal_mass_delta:+.6f}; not a gate)")
    if args.receipt:
        print(f"receipt -> {args.receipt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
