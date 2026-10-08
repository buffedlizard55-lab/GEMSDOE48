#!/usr/bin/env python3
"""Retired H54 candidate builder — invalidated live-density gate; no default writes.

The historical H54 risk/bracket and addition selection cite an inversion-derived
truth density and a universal 0.0556 per-cell bar. Those are invalid as score or
promotion evidence under the corrected metric. Existing H54 artifacts are archival
research only. This builder refuses by default; ``--legacy-audit-only`` is an
explicit forensic opt-in. Local checks do not establish portal acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import sys
import time
import zipfile

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gemsdoe48 import ds as DS  # noqa: E402
from gemsdoe48 import families as FAM  # noqa: E402

MAX_DOTS = 1000
PIX_MIN_DIST = 3.0
RHO = 0.95
LIVE_DOTTED = 0.2778
LIVE_TIP = 0.2632
STEM = "GEMSDOE48-H54-ds-core-lidar-20261007"


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_h52_builder():
    """Reuse the frozen H52 selection machinery (ranking + Poisson thinning)."""
    spec = importlib.util.spec_from_file_location(
        "h52_builder", ROOT / "scripts" / "build_submission_h52.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-add", type=int, default=MAX_DOTS)
    forensic_root = ROOT / "evidence" / "forensic" / "h54-build"
    parser.add_argument("--out-dir", type=pathlib.Path, default=forensic_root / "artifacts")
    parser.add_argument("--diag-dir", type=pathlib.Path, default=forensic_root / "diagnostics")
    parser.add_argument("--receipt", type=pathlib.Path,
                        default=forensic_root / "build_h54_receipt_20261007.json")
    parser.add_argument("--legacy-audit-only", action="store_true",
                        help="required opt-in; uses invalidated H54 score-risk assumptions")
    args = parser.parse_args()
    if not args.legacy_audit_only:
        parser.error("retired H54 builder uses invalidated Gate-2 assumptions; no writes without --legacy-audit-only")
    print("LEGACY H54 BUILD ONLY — INVALIDATED; NOT CLEARED TO SUBMIT")
    t0 = time.time()

    h52 = load_h52_builder()
    dotted = FAM.load_family_mask("dotted_b2_prune_02778")
    tip = FAM.load_family_mask("tip_02632")
    footprint = h52.read_band(ROOT / "data/source_mirrors/footprint-mask.tif")[0] == 1
    labels = h52.read_band(ROOT / "data/raw/labels_catalogue.tif")[0]
    catalogue = (labels > 0) & footprint
    template_profile = rasterio.open(ROOT / "data/raw/sample_submission_template.tif").profile.copy()

    # ---------------------------------------------------------------- additions
    d_cat = distance_transform_edt(~catalogue, sampling=(100.0, 100.0))
    d_dot = distance_transform_edt(~(dotted & footprint), sampling=(100.0, 100.0))
    layers = h52.scarp_layers(ROOT / "data/external/h52_scarp3m_100m.tif")
    height = layers["h_gate12"]
    covered = footprint & np.isfinite(layers["cover"]) & (layers["cover"] >= 0.9)
    eligible = covered & (d_cat > 200.0) & (d_dot > 200.0)
    rows, cols = np.nonzero(eligible)
    order = np.argsort(-height[rows, cols], kind="stable")
    rows, cols = rows[order], cols[order]
    kr, kc = h52.poisson_thin(rows, cols, dotted.copy(), max(1, args.n_add), PIX_MIN_DIST)
    add = np.zeros_like(dotted)
    add[kr[:args.n_add], kc[:args.n_add]] = True
    support = dotted | add

    # -------------------------------------------------------------- DS evidence
    b1 = FAM.kernel_credit_surface(dotted)
    b2 = FAM.kernel_credit_surface(tip)
    a1 = RHO
    a2 = RHO * (LIVE_TIP / LIVE_DOTTED)
    combined = DS.combine_pair(b1, b2, a1, a2)
    bel = np.asarray(combined.bel_F, dtype=np.float64)
    m_theta = np.asarray(combined.m_theta, dtype=np.float64)
    conflict = np.asarray(combined.conflict, dtype=np.float64)
    bel_norm = np.zeros_like(bel, dtype=np.float32)
    active = footprint & (bel > 0)
    lo, hi = float(bel[active].min()), float(bel[active].max())
    bel_norm[active] = ((bel[active] - lo) / (hi - lo)).astype(np.float32)
    naive = 0.5 * (b1.astype(np.float64) + b2.astype(np.float64))

    # ------------------------------------------------------------------ outputs
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.diag_dir.mkdir(parents=True, exist_ok=True)
    emission = np.full(support.shape, np.nan, dtype=np.float32)
    emission[footprint] = 0.0
    emission[support & footprint] = 1.0
    profile = template_profile
    profile.update(count=1, dtype="float32", nodata=float("nan"))
    tmp = args.out_dir / f"{STEM}.tmp.tif"
    with rasterio.open(tmp, "w", **profile) as sink:
        sink.write(emission, 1)
    ident = sha256_file(tmp)[:12]
    primary = args.out_dir / f"{STEM}-{ident}.tif"
    tmp.rename(primary)
    zeros = args.out_dir / f"{STEM}-{ident}-zeros-nan-outside.tif"
    zero_emission = np.where(np.isfinite(emission), emission, 0.0).astype(np.float32)
    with rasterio.open(zeros, "w", **{**profile, "nodata": None}) as sink:
        sink.write(zero_emission, 1)
    zip_path = args.out_dir / f"{STEM}-{ident}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        info = zipfile.ZipInfo(primary.name, date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, primary.read_bytes())
    diag = {}
    for name, array in (("belief-normalized", bel_norm), ("unassigned-mtheta", m_theta.astype(np.float32)),
                        ("conflict-K", conflict.astype(np.float32))):
        path = args.diag_dir / f"gemsdoe48-h54-{name}-{ident}.tif"
        out = np.where(footprint, np.clip(array, 0.0, 1.0), 0.0).astype(np.float32)
        with rasterio.open(path, "w", **{**profile, "nodata": None}) as sink:
            sink.write(out, 1)
        diag[name] = {"file": str(path.relative_to(ROOT)), "sha256": sha256_file(path),
                      "min": float(out[footprint].min()), "max": float(out[footprint].max())}

    # ------------------------------------------------------- independent re-read
    with rasterio.open(primary) as check:
        reread = check.read(1)
        tags = {"bands": check.count, "dtype": check.dtypes[0], "epsg": check.crs.to_epsg(),
                "shape": list(check.shape), "transform": list(check.transform)[:6],
                "nodata": check.nodata, "compress": check.profile.get("compress")}
    finite = np.isfinite(reread)
    pearson = float(np.corrcoef(bel_norm[footprint].astype(np.float64), naive[footprint])[0, 1])
    max_abs_ds_vs_naive = float(np.max(np.abs(bel_norm[footprint].astype(np.float64) - naive[footprint])))
    pixel_identical_ds_vs_naive = bool(np.array_equal(
        bel_norm[footprint].astype(np.float32), naive[footprint].astype(np.float32)))
    identical_parents = {
        "identical_to_dotted_parent": bool(np.array_equal(support, dotted & footprint)),
        "identical_to_tip_parent": bool(np.array_equal(support, tip & footprint)),
        "identical_to_union": bool(np.array_equal(support, (dotted | tip) & footprint)),
    }
    composition = {
        "cells": int(support.sum()),
        "core_dotted_cells": int((support & dotted).sum()),
        "added_lidar_cells": int((support & ~dotted).sum()),
        "added_within_200m_of_catalogue": int((d_cat[kr[:args.n_add], kc[:args.n_add]] <= 200).sum()),
        "added_min_height_m": float(height[kr[:args.n_add], kc[:args.n_add]].min()),
    }

    # minimal local score block on the frozen blocked proxy for the record
    sgmc = h52.read_band(ROOT / "data/official/derived_sgmc_faults_100m.tif")[0] > 0
    truth = sgmc & footprint & (d_cat > 300.0)

    def proxy_mean4(pred: np.ndarray) -> float:
        blocks = h52.quadrants(*labels.shape)
        return float(np.mean([h52.score_fold(pred.astype(np.float64), truth, footprint, core)["dti"]
                              for core in blocks.values()]))

    proxy = {"C_dotted": proxy_mean4(dotted), "H54": proxy_mean4(support)}

    receipt = {
        "schema": "GEMSDOE48-h54-build-v1",
        "validity_status": "INVALIDATED_FORENSIC_ONLY_DO_NOT_USE_FOR_PROMOTION",
        "invalidation_reason": "The historical Gate-2 status used an invalid FPw=S-TPw inferred truth density and a non-universal 0.0556 threshold.",
        "submission_decision": "NOT CLEARED TO SUBMIT; public-proxy comparisons do not establish private-label performance.",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "artifact": {"file": str(primary.relative_to(ROOT)), "sha256": sha256_file(primary),
                     "bytes": primary.stat().st_size, **tags,
                     "zeros_nan_outside_twin": str(zeros.relative_to(ROOT)),
                     "zip": str(zip_path.relative_to(ROOT))},
        "diagnostics": diag,
        "preregistered_constants": {"max_additions": args.n_add, "poisson_min_dist_px": PIX_MIN_DIST,
                                    "rho": RHO, "live_dotted": LIVE_DOTTED, "live_tip": LIVE_TIP,
                                    "a1": a1, "a2": a2},
        "composition": composition,
        "format_checks": {
            **tags,
            "all_finite_in_footprint": bool(np.isfinite(reread[footprint]).all()),
            "nan_outside_footprint": bool(np.isnan(reread[~footprint]).all()),
            "min_in_footprint": float(reread[footprint].min()),
            "max_in_footprint": float(reread[footprint].max()),
            "portal_range_ok": bool(np.isfinite(reread[footprint]).all()
                                    and reread[footprint].min() >= 0.0
                                    and reread[footprint].max() <= 1.0),
        },
        "ds_diagnostics": {
            "bel_raw_min": lo, "bel_raw_max": hi, "m_theta_range": [float(m_theta.min()), float(m_theta.max())],
            "conflict_range": [float(conflict.min()), float(conflict.max())],
            "bel_at_both_families_mean": float(bel[dotted & tip].mean()),
            "bel_at_dotted_only_mean": float(bel[dotted & ~tip].mean()) if (dotted & ~tip).any() else None,
            "bel_at_lidar_additions_mean": float(bel[support & ~dotted].mean()),
            "uncertainty_preserved_note": "m(Theta) is exported separately and never merged into the emission",
        },
        "not_the_average_check": {
            "pearson_ds_normalized_belief_vs_naive_mean": pearson,
            "max_abs_difference_ds_belief_vs_naive_mean": max_abs_ds_vs_naive,
            "pixel_identical_ds_belief_to_naive_mean": pixel_identical_ds_vs_naive,
            "max_abs_difference_binary_support_vs_naive_mean": float(
                np.max(np.abs(support.astype(np.float64) - naive))),
            **identical_parents,
            "pass": bool(not pixel_identical_ds_vs_naive and max_abs_ds_vs_naive > 0.0
                         and not any(identical_parents.values())),
        },
        "blocked_proxy_diagnostic": proxy,
        "status": "INVALIDATED_FORENSIC_ONLY_NOT_CLEARED_TO_SUBMIT",
        "status_basis": "Historical Gate-2 verdict withdrawn: its density match used an invalid FPw=S-TPw inversion and universal 0.0556 threshold. See docs/research/credit-density-audit-20261007.md.",
        "evidence_class": {"measured": "format_checks, composition, ds_diagnostics, not_the_average_check, "
                                       "blocked_proxy_diagnostic",
                           "owner_reported": "live anchors 0.2778 / 0.2632 (registry/live_scores.json)",
                           "proxy": "SGMC > 300 m off-catalogue, four fixed quadrants; not the private truth"},
    }
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: receipt[k] for k in ("artifact", "composition", "format_checks",
                                              "not_the_average_check", "blocked_proxy_diagnostic", "status")},
                     indent=2))
    print(f"({time.time() - t0:.0f}s) receipt -> {args.receipt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
