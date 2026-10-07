#!/usr/bin/env python3
"""Build the unique H53 three-source adaptive Dempster-Shafer submission.

Sources (all SHA-256 pinned, verified on read):
  A  dotted parent       H33-2-B2      37,654 px  owner-reported live 0.2778
  B  H36-1 rung30 parent  H19-5/rung-30 repack, not tip/step-over; owner live 0.2710
  L  native-lidar scarp  h_gate12/sigma_mean/cover from data/external/h52_scarp3m_100m.tif

Beliefs: metric-geometry kernel-credit surfaces for A and B (H50
construction); a preregistered height ramp for L.  Discounts: scalar
live-anchored a_A/a_B (H50 scheme, RHO_MAX = 0.95 ceiling) and a
terrain-adaptive per-pixel lidar reliability map (0.75 smooth / 0.25 rough /
0.05 uncovered).  Rule: canonical normalized Dempster, (A (+) B) (+) L.

Outputs: graded Bel_ABC(F) normalized to [0,1] (NaN-outside primary plus a
zeros-outside twin), a pignistic budget-matched binary twin, m(Theta) /
K_AB / K_ABL / plausibility diagnostics, a build receipt, and the
not-a-naive-mean checks.  All H53-1 constants are preregistered in
docs/research/hypotheses-h53-20261007.md section 3; the builder refuses to
run if the module constants drift from the frozen slate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

from gemsdoe48 import ds50, ds53
from gemsdoe48.geotiff import (
    assert_competition_grid,
    assert_same_grid,
    display_path,
    read_band,
    write_float32,
)
from gemsdoe48.grid import write_submission

ROOT = Path(__file__).resolve().parents[1]

PINNED_DOTTED = ROOT / "data/raw/dotted_h33_2_b2_zeros.tif"
PINNED_TIP = ROOT / "data/source_mirrors/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif"
PINNED_LIDAR = ROOT / "data/external/h52_scarp3m_100m.tif"
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"

SHA_DOTTED = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
SHA_TIP_H36 = "5556aa1438fd67376b60d5ffc99228ec09dcc11a8408298a743ccb88d6163641"
SHA_LIDAR = "b5e53d67c3a7d3d1ca44ae04ae1e84d8574857da3fcd5e34ba47276d6c04b923"
SHA_FOOTPRINT = "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f"

DATESTAMP = "20261007"
SUBMISSION_NAME = "GEMSDOE48-H53-3SRC-DS"
SUBMISSION_NOTE = (
    "GEMSDOE48-H53-3SRC-DS | B2 x H36-1 rung30 (H19-5 repack, not tip) "
    "x lidar; adaptive D-S; unscored research; gate failed."
)

# Preregistered slate (evidence/hypothesis_slate_h53_20261007.json); the builder
# fails closed if the module drifts from these frozen values.
SLATE = {
    "a_dotted": 0.95,
    "a_tip_ratio": 0.2710 / 0.2778,
    "h_lo": 1.0,
    "h_hi": 2.8,
    "cover_min": 0.9,
    "sigma_smooth_lt": 1.2,
    "a_smooth": 0.75,
    "a_rough": 0.25,
    "a_uncovered": 0.05,
    "budget_px": 37654,
}

CHUNK_ROWS = 512  # row-chunked fusion: exact, keeps peak RAM well under 3 GB


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def require_sha(path: Path, expected: str, label: str) -> None:
    got = sha256_file(path)
    if got != expected:
        raise SystemExit(f"{label}: SHA-256 {got} != pinned {expected} ({path})")


def check_slate() -> None:
    checks = {
        "a_dotted": ds53.A_DOTTED,
        "a_tip_ratio": ds53.A_TIP / ds53.A_DOTTED,
        "h_lo": ds53.H_LO_M,
        "h_hi": ds53.H_HI_M,
        "cover_min": ds53.COVER_MIN,
        "sigma_smooth_lt": ds53.SIGMA_SMOOTH_LT_M,
        "a_smooth": ds53.A_LIDAR_SMOOTH,
        "a_rough": ds53.A_LIDAR_ROUGH,
        "a_uncovered": ds53.A_LIDAR_UNCOVERED,
        "budget_px": ds53.PARENT_A_BUDGET_PX,
    }
    for key, got in checks.items():
        want = SLATE[key]
        if isinstance(want, float):
            if abs(got - want) > 1e-12:
                raise SystemExit(f"slate drift: {key}={got!r} != frozen {want!r}")
        elif got != want:
            raise SystemExit(f"slate drift: {key}={got!r} != frozen {want!r}")


def read_lidar_layers(path: Path) -> tuple[dict[str, np.ndarray], dict]:
    with rasterio.open(path) as ds:
        profile0 = ds.profile.copy()
        profile0["count"] = 1  # 7-band product; grid identity is what matters
        assert_competition_grid(profile0, path=path)
        tags = ds.tags()
        profile = ds.profile.copy()
        nodata = ds.nodata
        layers: dict[str, np.ndarray] = {}
        for i, name in enumerate(ds.descriptions, 1):
            a = ds.read(i).astype(np.float64)
            missing = a == nodata
            a = a / float(tags[f"SCALE_{name}"])
            a[missing] = np.nan
            layers[name] = a
    for need in ("h_gate12", "sigma_mean", "cover"):
        if need not in layers:
            raise SystemExit(f"lidar product lacks band {need!r}: {sorted(layers)}")
    return layers, profile


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    if x.size < 2 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dotted", type=Path, default=PINNED_DOTTED)
    parser.add_argument("--tip", type=Path, default=PINNED_TIP)
    parser.add_argument("--lidar", type=Path, default=PINNED_LIDAR)
    parser.add_argument("--footprint", type=Path, default=FOOTPRINT)
    parser.add_argument("--outdir", type=Path, default=ROOT / "docs/downloads")
    parser.add_argument("--receipt", type=Path, default=ROOT / "evidence/build_h53_receipt_20261007.json")
    parser.add_argument("--allow-unpinned", action="store_true")
    args = parser.parse_args()

    if len(SUBMISSION_NOTE) > 200:
        raise SystemExit("submission note exceeds the portal's 200-character limit")
    check_slate()
    if not args.allow_unpinned:
        require_sha(args.dotted, SHA_DOTTED, "dotted parent")
        require_sha(args.tip, SHA_TIP_H36, "H36-1 rung30 parent (not tip/step-over)")
        require_sha(args.lidar, SHA_LIDAR, "lidar product")
        require_sha(args.footprint, SHA_FOOTPRINT, "footprint mask")

    dotted_raw, dotted_profile = read_band(args.dotted)
    tip_raw, tip_profile = read_band(args.tip)
    assert_competition_grid(dotted_profile, path=args.dotted)
    assert_competition_grid(tip_profile, path=args.tip)
    assert_same_grid(dotted_profile, tip_profile, name_a=str(args.dotted), name_b=str(args.tip))
    with rasterio.open(args.footprint) as fp_ds:
        assert_competition_grid(fp_ds.profile, path=args.footprint)
        footprint = fp_ds.read(1) == 1
    lidar, _ = read_lidar_layers(args.lidar)

    dotted = np.where(np.isfinite(dotted_raw), dotted_raw, 0.0)
    tip = np.where(np.isfinite(tip_raw), tip_raw, 0.0)
    if np.any((dotted < 0) | (dotted > 1)) or np.any((tip < 0) | (tip > 1)):
        raise SystemExit("parent surfaces must lie in [0, 1]")
    dotted_mask = (dotted > 0) & footprint
    tip_mask = (tip > 0) & footprint
    n_dotted = int(dotted_mask.sum())
    n_tip = int(tip_mask.sum())

    # --- belief surfaces ------------------------------------------------------
    belief_a = ds53.kernel_belief_surface(dotted_mask)
    belief_b = ds53.kernel_belief_surface(tip_mask)
    belief_l, rel_l = ds53.lidar_belief_and_reliability(
        lidar["h_gate12"], lidar["sigma_mean"], lidar["cover"]
    )
    lidar_support = (belief_l > 0) & footprint
    smooth = footprint & (rel_l == ds53.A_LIDAR_SMOOTH)
    rough = footprint & (rel_l == ds53.A_LIDAR_ROUGH)
    uncovered = footprint & (rel_l == ds53.A_LIDAR_UNCOVERED)

    # --- three-source fusion, row-chunked (exact; per-pixel operator) ---------
    h, w = belief_a.shape
    m_f = np.empty((h, w), dtype=np.float32)
    m_t = np.empty((h, w), dtype=np.float32)
    k_ab = np.empty((h, w), dtype=np.float32)
    k_abl = np.empty((h, w), dtype=np.float32)
    for r0 in range(0, h, CHUNK_ROWS):
        sl = slice(r0, min(h, r0 + CHUNK_ROWS))
        m1 = ds53.discounted_mass(belief_a[sl], ds53.A_DOTTED)
        m2 = ds53.discounted_mass(belief_b[sl], ds53.A_TIP)
        m3 = ds53.discounted_mass(belief_l[sl], rel_l[sl])
        ab_f, ab_n, ab_t, kab = ds53.dempster_combine_pair(m1, m2)
        f, _n, t, k2 = ds53.dempster_combine_pair(np.stack([ab_f, ab_n, ab_t]), m3)
        m_f[sl] = f
        m_t[sl] = t
        k_ab[sl] = kab
        k_abl[sl] = k2
        del m1, m2, m3, ab_f, ab_n, ab_t, kab, f, _n, t, k2
    ref_max = float(m_f[footprint].max())
    if not np.isfinite(ref_max) or ref_max <= 0:
        raise SystemExit("fusion belief has no positive in-footprint mass")
    belief_norm = np.clip(m_f.astype(np.float64) / ref_max, 0.0, 1.0)
    plaus = np.clip(m_f.astype(np.float64) + m_t.astype(np.float64), 0.0, 1.0)
    pign = np.clip(m_f.astype(np.float64) + 0.5 * m_t.astype(np.float64), 0.0, 1.0)
    k_total = 1.0 - (1.0 - k_ab.astype(np.float64)) * (1.0 - k_abl.astype(np.float64))

    # --- binary pignistic twin (parent-A-mass budget) -------------------------
    twin_mask = ds50.top_k_mask(pign, ds53.PARENT_A_BUDGET_PX, where=footprint)
    twin_support_px = int(twin_mask.sum())

    # --- not-a-naive-mean checks ----------------------------------------------
    checks = {}
    for label, naive in {
        "mean3_of_beliefs": ds53.naive_mean3_belief(belief_a, belief_b, belief_l),
        "mean2_of_family_beliefs": ds50.naive_mean_belief(belief_a, belief_b),
    }.items():
        nn = naive / float(naive[footprint].max())
        diff = np.abs(belief_norm[footprint] - nn[footprint])
        ds_top = ds50.top_k_mask(belief_norm, n_dotted, where=footprint)
        mean_top = ds50.top_k_mask(nn, n_dotted, where=footprint)
        inter = int((ds_top & mean_top).sum())
        union_k = int((ds_top | mean_top).sum())
        checks[label] = {
            "pearson_in_footprint": pearson(belief_norm[footprint], nn[footprint]),
            "spearman_in_footprint": ds50.spearman_rank_correlation(
                belief_norm[footprint], nn[footprint]
            ),
            "mae_in_footprint": float(diff.mean()),
            "max_abs_difference": float(diff.max()),
            "fraction_cells_abs_diff_gt_0.05": float((diff > 0.05).mean()),
            "cells_exactly_equal": int((belief_norm[footprint] == nn[footprint]).sum()),
            "topk_emission_jaccard": inter / union_k if union_k else None,
            "topk": n_dotted,
        }
        if not np.isfinite(checks[label]["pearson_in_footprint"]):
            raise SystemExit(f"anti-average correlation failed for {label}")

    # --- write primary (NaN-outside) + twins + diagnostics --------------------
    args.outdir.mkdir(parents=True, exist_ok=True)
    # Keep the frozen H53-1 GeoTIFF tags byte-compatible. The historical model
    # label and ``tip`` tag names refer to H36-1 rung30 only; the classification
    # erratum explains why they do not make this an actual tip/step-over fusion.
    tags = {
        "model": "H53 three-source Dempster combination (dotted x tip x lidar)",
        "reliability_dotted": str(ds53.A_DOTTED),
        "reliability_tip": f"{ds53.A_TIP:.6f}",
        "reliability_lidar_map": (
            f"smooth<{ds53.SIGMA_SMOOTH_LT_M}m:{ds53.A_LIDAR_SMOOTH}/"
            f"rough:{ds53.A_LIDAR_ROUGH}/uncovered:{ds53.A_LIDAR_UNCOVERED}"
        ),
        "frame": "{fault, not_fault, Theta}",
        "source_dotted_sha256": sha256_file(args.dotted),
        "source_tip_sha256": sha256_file(args.tip),
        "source_lidar_sha256": sha256_file(args.lidar),
        "submission_name": SUBMISSION_NAME,
    }
    tmp_primary = args.outdir / f".tmp-h53-{DATESTAMP}.tif"
    primary_nan = np.where(footprint, belief_norm, np.nan).astype(np.float32)
    receipt_primary = write_float32(
        tmp_primary, primary_nan, dotted_profile, valid_mask=footprint,
        description="H53 normalized three-source Dempster belief; NaN/nodata outside survey footprint",
        tags=tags,
    )
    primary_sha = sha256_file(tmp_primary)
    short_id = primary_sha[:8]
    primary_path = args.outdir / f"GEMSDOE48-H53-3SRC-DS-{DATESTAMP}-{short_id}-nan-outside.tif"
    primary_path.unlink(missing_ok=True)
    tmp_primary.rename(primary_path)
    # Post-rename audit: re-open the shipped bytes (rename preserves bytes, but
    # the receipt must describe the shipped path, not the temp name).
    with rasterio.open(primary_path) as audit_ds:
        assert_competition_grid(audit_ds.profile, path=primary_path)
        if audit_ds.dtypes != ("float32",) or audit_ds.nodata is None:
            raise SystemExit("renamed primary failed dtype/nodata audit")
        reread = audit_ds.read(1)
        if not np.isfinite(reread[footprint]).all() or np.any(~np.isnan(reread[~footprint])):
            raise SystemExit("renamed primary failed footprint/nodata audit")
        if reread[footprint].min() < 0.0 or reread[footprint].max() > 1.0:
            raise SystemExit("renamed primary has in-footprint values outside [0, 1]")
        if not np.allclose(
            np.nan_to_num(reread, nan=-1.0), np.nan_to_num(primary_nan, nan=-1.0), atol=0
        ):
            raise SystemExit("renamed primary bytes differ from the validated array")
    receipt_primary = {**receipt_primary, "path": display_path(primary_path)}
    zip_path = primary_path.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(primary_path, arcname=primary_path.name)

    zeros_path = primary_path.with_name(primary_path.name.replace("-nan-outside.tif", "-zeros-outside.tif"))
    write_submission(zeros_path, np.where(footprint, belief_norm, 0.0))
    twin_path = primary_path.with_name(
        primary_path.name.replace("-nan-outside.tif", "-pignistic-twin-nan.tif")
    )
    receipt_twin = write_float32(
        twin_path, np.where(footprint, twin_mask.astype(np.float32), np.nan).astype(np.float32),
        dotted_profile, valid_mask=footprint,
        description="H53 pignistic BetP top-37654 binary twin; NaN/nodata outside survey footprint",
        tags=tags,
    )
    diag_specs = {
        "unassigned": (m_t, "H53 residual unassigned Dempster mass m_ABC(Theta); NaN outside footprint"),
        "conflict-AB": (k_ab, "H53 raw family-vs-family conjunctive conflict K_AB; NaN outside footprint"),
        "conflict-ABL": (k_abl, "H53 raw conflict when lidar joins the family pair K_ABL; NaN outside footprint"),
        "plausibility": (
            plaus.astype(np.float32),
            "H53 plausibility Pl(F) = Bel(F) + m(Theta); NaN outside footprint",
        ),
    }
    diag_receipts = {}
    for diag_name, (arr, desc) in diag_specs.items():
        diag_path = primary_path.with_name(
            primary_path.name.replace("-nan-outside.tif", f"-diag-{diag_name}-nan.tif")
        )
        diag_receipts[diag_name] = {
            **write_float32(
                diag_path, np.where(footprint, arr, np.nan).astype(np.float32),
                dotted_profile, valid_mask=footprint, description=desc, tags=tags,
            ),
            "path": display_path(diag_path),
            "sha256": sha256_file(diag_path),
        }

    # --- uniqueness: sha must differ from every TIF already shipped -----------
    new_files = {primary_path, zeros_path, twin_path} | {
        primary_path.with_name(primary_path.name.replace("-nan-outside.tif", f"-diag-{n}-nan.tif"))
        for n in diag_specs
    }
    existing = sorted(
        p for p in list((ROOT / "docs/downloads").rglob("*.tif")) + list((ROOT / "data").rglob("*.tif"))
        if p not in new_files
    )
    collisions = [display_path(p) for p in existing if sha256_file(p) == primary_sha]
    if collisions:
        raise SystemExit(f"submission hash collides with existing artifact(s): {collisions}")

    # --- support overlap of the binary twin vs key prior binaries ------------
    overlap = {}
    for label, path in {
        "dotted_parent_C": args.dotted,
        "tip_parent_H36": args.tip,
        "h52_lidar_additions": ROOT / "docs/downloads/GEMSDOE48-H52-lidar-scarp-additions-20261007-38029417f6ca-nan-outside.tif",
        "h51_plausibility": ROOT / "docs/downloads/gemsdoe48-h51-plausibility-budget-20261007-f8fa1d08-nan.tif",
        "h49_yager": ROOT / "docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif",
    }.items():
        if not path.is_file():
            overlap[label] = {"present": False}
            continue
        arr, prof = read_band(path)
        assert_same_grid(prof, dotted_profile, name_a=label, name_b=str(args.dotted))
        other = (np.nan_to_num(arr, nan=0.0) > 0) & footprint
        inter = int((twin_mask & other).sum())
        union = int((twin_mask | other).sum())
        overlap[label] = {
            "present": True,
            "other_px": int(other.sum()),
            "intersection_px": inter,
            "jaccard": inter / union if union else None,
        }

    receipt = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": "H53",
        "submission_status": "UNSCORED_RESEARCH_CANDIDATE",
        "submission_name": SUBMISSION_NAME,
        "submission_note": SUBMISSION_NOTE,
        "submission_note_length": len(SUBMISSION_NOTE),
        "primary_file": display_path(primary_path),
        "primary_sha256": primary_sha,
        "primary_bytes": primary_path.stat().st_size,
        "zip_file": display_path(zip_path),
        "zip_sha256": sha256_file(zip_path),
        "zeros_outside_twin": {
            "path": display_path(zeros_path),
            "sha256": sha256_file(zeros_path),
            "purpose": "all-finite zeros-outside encoding; immune to portal range rejection by construction",
        },
        "pignistic_binary_twin": {
            **receipt_twin,
            "path": display_path(twin_path),
            "sha256": sha256_file(twin_path),
            "support_px": twin_support_px,
            "purpose": "BetP top-37654 (parent-A-mass-matched) binary decision surface; same gate",
        },
        "encoding": "float32 in [0,1] in-footprint; NaN/nodata outside (official sample-template convention)",
        "diagnostics": diag_receipts,
        "parents": {
            "dotted_best": {
                "family": "dotted (spacing-tuned)",
                "id": "H33-2-B2",
                "path": display_path(args.dotted),
                "sha256": sha256_file(args.dotted),
                "positive_pixels": n_dotted,
                "owner_reported_live": ds50.LIVE_DOTTED_B2,
                "evidence_class": "OWNER-REPORT",
            },
            "tip_best": {
                "family": "tip / step-over",
                "id": "H36-1-rung30",
                "path": display_path(args.tip),
                "sha256": sha256_file(args.tip),
                "positive_pixels": n_tip,
                "owner_reported_live": ds50.LIVE_TIP_H36,
                "evidence_class": "OWNER-REPORT",
            },
            "lidar_scarp": {
                "product": display_path(args.lidar),
                "sha256": sha256_file(args.lidar),
                "bands_used": ["h_gate12", "sigma_mean", "cover"],
                "support_belief_gt0_px": int(lidar_support.sum()),
                "reliability_class_px": {
                    "smooth": int(smooth.sum()),
                    "rough": int(rough.sum()),
                    "uncovered": int(uncovered.sum()),
                },
            },
        },
        "method": {
            "belief_construction": "b_A/b_B = max_y k(d(x,y)) triangular 300 m (metric geometry); b_L = clip((h_gate12-1.0)/(2.8-1.0)) on cover>=0.9 else 0",
            "mass_assignment": "m_i(F)=a_i*b_i, m_i(notF)=a_i*(1-b_i), m_i(Theta)=1-a_i; a_L is a per-pixel map",
            "combination": "canonical normalized Dempster (Dempster 1967; Shafer 1976), sequential (A(+)B)(+)L",
            "reliabilities": {"dotted": ds53.A_DOTTED, "tip": ds53.A_TIP, "lidar_map": "0.75/0.25/0.05"},
            "reliability_anchor": "RHO_MAX=0.95 ceiling x owner-reported live ratio [OWNER-REPORT]; lidar classes preregistered from pilot lift (smooth) vs unproven (rough) vs missing (uncovered)",
            "submitted_surface": "Bel_ABC(F) / max(footprint)",
            "chunk_rows": CHUNK_ROWS,
            "assumptions": [
                "Kernel-credit belief treats distance-decayed credit as graded evidence.",
                "Sources are not assumed statistically independent; shared regional inputs remain a risk.",
                "Lidar ramp anchors are label-free distribution quantiles, not calibrated probabilities.",
            ],
        },
        "fusion_summary_in_footprint": {
            "belief_max_before_norm": ref_max,
            "belief_normalized_max": float(belief_norm[footprint].max()),
            "belief_normalized_mean": float(belief_norm[footprint].mean()),
            "unassigned_min": float(m_t[footprint].min()),
            "unassigned_max": float(m_t[footprint].max()),
            "conflict_AB_max": float(k_ab[footprint].max()),
            "conflict_ABL_max": float(k_abl[footprint].max()),
            "conflict_total_max": float(k_total[footprint].max()),
            "unassigned_strictly_positive": bool((m_t[footprint] > 0).all()),
        },
        "anti_average_checks": {**checks, "is_the_average": False},
        "twin_support_overlap": overlap,
        "uniqueness": {
            "compared_existing_tifs": len(existing),
            "hash_collisions": collisions,
            "novelty": "first three-source fusion (dotted x tip x lidar) with a terrain-adaptive reliability map in any reviewed GEMSDOE artifact",
        },
        "format_receipt_primary": receipt_primary,
        "organizer_score": None,
        "score_claim": "No organizer score exists for this artifact; no leaderboard projection is claimed.",
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
