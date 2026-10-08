#!/usr/bin/env python3
"""Build H58 — pignistic conflict-priced Dempster–Shafer fusion of B2 × H33-D.

Novel contribution (distinct from all prior GEMSDOE48 fusions):
  H48: raw binary × simple Dempster, ρ=0.5
  H49: Yager conflict-transfer
  H50: kernel-belief × Dempster with reliability discounts → Bel(F) normalized
  H56: open-world mass assignment → Bel(F)
  H56B: kernel-belief × Dempster ρ=0.5 → Bel(F)
  H57-RELIEF: kernel-belief × Dempster + lidar relief → Bel(F)
  **H58: kernel-belief × Dempster with reliability discounts → PIGNISTIC PROBABILITY
         weighted by conflict-price (1 − K). This carries the two-family disagreement
         directly INTO the submission surface, not just as a diagnostic.**

Theory (Smets 1990; Shafer 1976 sec. 6.2):
  The pignistic probability BetP(F) = Bel(F) + m(Θ)/2 is the unique coherent
  decision-theoretic transform from belief functions to probability for betting.
  Multiplying by (1 − K) prices the raw conjunctive conflict: where the two
  families actively contradict each other (one says fault, the other says not-fault),
  the surface is suppressed. This is the brief's requirement to "preserve disagreement
  instead of averaging it away" — the disagreement enters the SURFACE itself, not
  just a separate diagnostic.

Parents (SHA-256 pinned, verified on read):
  A  Dotted family H33-2-B2   37,654 px  owner-reported 0.2778
  B  Tip/step-over H33-D       41,865 px  owner-reported 0.2632
     (these are genuinely independent families built by different methods)

Output: single-band float32, EPSG:32611, 100 m, 3292×3730, all-finite, [0,1].
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gemsdoe48 import ds50
from gemsdoe48.geotiff import (
    assert_competition_grid,
    assert_same_grid,
    read_band,
)
from gemsdoe48.grid import EXPECTED, write_submission

ROOT = Path(__file__).resolve().parents[1]

# --- Pinned parents ---
PINNED_DOTTED = ROOT / "data/raw/dotted_h33_2_b2_zeros.tif"
PINNED_TIP = ROOT / "data/raw/tip_h33d_stepover.tif"
PINNED_TEMPLATE = ROOT / "data/raw/sample_submission_template.tif"

SHA_DOTTED = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
SHA_TIP = "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757"

# Owner-reported live scores (anchoring only, not receipts)
LIVE_DOTTED_B2 = 0.2778
LIVE_TIP_H33D = 0.2632

# Reliability ceiling
RHO_MAX = 0.95

DATESTAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
SUBMISSION_NAME = "GEMSDOE48-H58-PignisticConflictPriced-B2xH33D"
SUBMISSION_NOTE = (
    "GEMSDOE48 H58 | Pignistic BetP(F)*(1-K) of B2 dotted x H33-D tip/stepover; "
    "kernel-credit belief, reliability discounts; unique DS variant; UNSCORED."
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    if x.size < 2 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(np.corrcoef(x.ravel(), y.ravel())[0, 1])


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    from gemsdoe48.ds50 import spearman_rank_correlation
    return spearman_rank_correlation(x, y)


def main() -> int:
    print("=" * 70)
    print("H58 Pignistic Conflict-Priced DS Fusion: B2 × H33-D")
    print("=" * 70)

    # --- Verify SHA-256 ---
    for path, expected, label in [
        (PINNED_DOTTED, SHA_DOTTED, "dotted B2"),
        (PINNED_TIP, SHA_TIP, "tip/stepover H33-D"),
    ]:
        got = sha256_file(path)
        if got != expected:
            print(f"FATAL: {label} SHA-256 mismatch: {got} != {expected}")
            return 1
        print(f"  ✓ {label} SHA-256 verified")

    # --- Read parents ---
    dotted_raw, dotted_profile = read_band(PINNED_DOTTED)
    tip_raw, tip_profile = read_band(PINNED_TIP)
    assert_competition_grid(dotted_profile, path=PINNED_DOTTED)
    assert_competition_grid(tip_profile, path=PINNED_TIP)
    assert_same_grid(dotted_profile, tip_profile,
                     name_a=str(PINNED_DOTTED), name_b=str(PINNED_TIP))

    dotted = np.where(np.isfinite(dotted_raw), dotted_raw, 0.0).astype(np.float64)
    tip = np.where(np.isfinite(tip_raw), tip_raw, 0.0).astype(np.float64)

    if np.any((dotted < 0) | (dotted > 1)) or np.any((tip < 0) | (tip > 1)):
        print("FATAL: parent surfaces must lie in [0, 1]")
        return 1

    dotted_mask = dotted > 0
    tip_mask = tip > 0
    n_dotted = int(dotted_mask.sum())
    n_tip = int(tip_mask.sum())
    n_both = int((dotted_mask & tip_mask).sum())
    n_union = int((dotted_mask | tip_mask).sum())

    print(f"\n  B2 dotted: {n_dotted} positive pixels")
    print(f"  H33-D tip/stepover: {n_tip} positive pixels")
    print(f"  Overlap: {n_both} pixels")
    print(f"  Union: {n_union} pixels")
    print(f"  Jaccard: {n_both / n_union:.4f}")

    # --- Determine footprint from the sample template ---
    with rasterio.open(PINNED_TEMPLATE) as ds:
        tmpl = ds.read(1)
        footprint = np.isfinite(tmpl)  # valid cells are finite in the template
    n_footprint = int(footprint.sum())
    print(f"  Footprint: {n_footprint} valid pixels")

    # --- Build kernel-belief surfaces ---
    print("\n  Building kernel-belief surfaces (metric-geometry)...")
    belief_a = ds50.kernel_belief_surface(dotted_mask)
    belief_b = ds50.kernel_belief_surface(tip_mask)

    # --- Reliability-weighted discounts ---
    alpha_a = RHO_MAX  # dotted is the stronger family
    alpha_b = RHO_MAX * (LIVE_TIP_H33D / LIVE_DOTTED_B2)
    print(f"  Reliability: α_A (B2) = {alpha_a:.6f}")
    print(f"  Reliability: α_B (H33-D) = {alpha_b:.6f}")

    # --- Dempster combination ---
    print("  Running Dempster normalization...")
    fusion = ds50.dempster_fuse(belief_a, belief_b, alpha_a, alpha_b, footprint=footprint)

    # --- NOVEL: Pignistic probability weighted by conflict-price ---
    # BetP(F) = Bel(F) + m(Θ)/2
    betp = fusion.belief + fusion.unassigned / 2.0

    # Conflict-price: suppress where raw conflict K is high
    # K ranges from 0 to max possible; clip to [0, 1]
    k_clipped = np.clip(fusion.conflict, 0.0, 1.0)
    conflict_priced = betp * (1.0 - k_clipped)

    # Zero outside footprint
    conflict_priced = np.where(footprint, conflict_priced, 0.0)

    # Normalize the continuous surface for diagnostic purposes
    fp_max = float(conflict_priced[footprint].max())
    if fp_max > 0:
        continuous_surface = conflict_priced / fp_max
    else:
        continuous_surface = np.zeros_like(conflict_priced)
    continuous_surface = np.clip(continuous_surface, 0.0, 1.0)

    # --- Budget-constrained emission using the pignistic surface as RANKING ---
    # The DTI metric penalizes mass not covering truth: DTI = TPw / (TPw + 0.2*FPw + 0.8*FNw)
    # The best-performing families emit ~37K-42K pixels. We use the pignistic
    # conflict-priced surface to rank cells, then emit the top-K as binary 1.0.
    # This is the key novel step: the DS surface RANKS, the metric rewards sparsity.
    TARGET_BUDGET = 40000  # between the two parent family sizes

    # Rank cells within footprint by the continuous pignistic surface
    fp_values = continuous_surface[footprint]
    if TARGET_BUDGET >= len(fp_values):
        topk_mask_fp = np.ones(len(fp_values), dtype=bool)
    else:
        # Get the threshold for top-K
        threshold_idx = len(fp_values) - TARGET_BUDGET
        threshold = np.partition(fp_values, threshold_idx)[threshold_idx]
        topk_mask_fp = fp_values >= threshold
        # If ties push us over budget, trim to exactly TARGET_BUDGET
        if topk_mask_fp.sum() > TARGET_BUDGET:
            topk_indices = np.where(topk_mask_fp)[0]
            # Among tied cells, pick by highest value
            tied_vals = fp_values[topk_indices]
            sorted_tied = np.argsort(-tied_vals)
            keep = sorted_tied[:TARGET_BUDGET]
            topk_mask_fp = np.zeros(len(fp_values), dtype=bool)
            topk_mask_fp[topk_indices[keep]] = True

    # Reconstruct full-grid binary emission
    submission = np.zeros((EXPECTED["height"], EXPECTED["width"]), dtype=np.float64)
    submission[footprint] = topk_mask_fp.astype(np.float64)

    # Use the continuous surface as the actual graded values for the top-K cells
    # (cells outside top-K stay at 0; cells inside get their pignistic value)
    # This gives a graded submission where the ranking is the DS pignistic surface
    # but only the top-K cells are nonzero, preserving the metric-optimal sparsity
    graded = np.zeros_like(submission)
    graded[footprint] = continuous_surface[footprint] * topk_mask_fp.astype(np.float64)
    # Normalize graded to [0,1]
    graded_max = float(graded.max())
    if graded_max > 0:
        graded = graded / graded_max
    submission = np.clip(graded, 0.0, 1.0).astype(np.float32)

    # Ensure all-finite
    submission = np.where(np.isfinite(submission), submission, 0.0)

    n_emitted = int((submission > 0).sum())
    print(f"\n  Budget-constrained emission:")
    print(f"    Target budget: {TARGET_BUDGET} pixels")
    print(f"    Emitted pixels (>0): {n_emitted}")
    print(f"    Submission range: [{submission.min():.6f}, {submission.max():.6f}]")
    print(f"    All finite: {np.all(np.isfinite(submission))}")

    # Store the continuous surface for diagnostics
    continuous_out = continuous_surface.astype(np.float32)

    # --- Verify NOT the naive mean ---
    # Compare with a naive mean of the two parent surfaces (both sparse binary)
    naive_mean = 0.5 * (dotted + tip)  # average of the two raw parent surfaces
    naive_mean_fp = np.where(footprint, naive_mean, 0.0)
    naive_max = float(naive_mean_fp[footprint].max())
    if naive_max > 0:
        naive_norm = np.clip(naive_mean_fp / naive_max, 0.0, 1.0)
    else:
        naive_norm = np.zeros_like(naive_mean_fp)

    rho_pearson = pearson(submission.astype(np.float64), naive_norm.astype(np.float64))
    rho_spearman = spearman(submission.astype(np.float64), naive_norm.astype(np.float64))
    max_abs_diff = float(np.max(np.abs(submission.astype(np.float64) - naive_norm.astype(np.float64))))

    print(f"\n  Not-a-naive-mean check:")
    print(f"    Pearson ρ against naive mean: {rho_pearson:.6f}")
    print(f"    Spearman ρ against naive mean: {rho_spearman:.6f}")
    print(f"    Max |Δ| from naive mean: {max_abs_diff:.6f}")

    # --- Verify NOT identical to prior DS variants ---
    # Compare with raw Bel(F) from the same Dempster run (full grid, budget-emitted)
    bel_normalized = fusion.belief_normalized
    # Emit top-K from Bel(F) for fair comparison
    bel_fp_vals = bel_normalized[footprint]
    if TARGET_BUDGET >= len(bel_fp_vals):
        bel_topk_fp = np.ones(len(bel_fp_vals), dtype=bool)
    else:
        bel_thresh_idx = len(bel_fp_vals) - TARGET_BUDGET
        bel_thresh = np.partition(bel_fp_vals, bel_thresh_idx)[bel_thresh_idx]
        bel_topk_fp = bel_fp_vals >= bel_thresh
    bel_emitted = np.zeros((EXPECTED["height"], EXPECTED["width"]), dtype=np.float64)
    bel_emitted[footprint] = bel_topk_fp.astype(np.float64) * bel_fp_vals
    bel_em_max = float(bel_emitted.max())
    if bel_em_max > 0:
        bel_emitted = bel_emitted / bel_em_max
    bel_emitted = np.clip(bel_emitted, 0.0, 1.0).astype(np.float32)
    rho_vs_bel = pearson(submission.astype(np.float64), bel_emitted.astype(np.float64))
    print(f"    Pearson ρ against budget-emitted raw Bel(F): {rho_vs_bel:.6f}")

    # Compare with pignistic without conflict-pricing (budget-emitted)
    betp_clipped = np.clip(betp, 0.0, None)
    betp_fp_vals = betp_clipped[footprint]
    if TARGET_BUDGET >= len(betp_fp_vals):
        betp_topk_fp = np.ones(len(betp_fp_vals), dtype=bool)
    else:
        betp_thresh_idx = len(betp_fp_vals) - TARGET_BUDGET
        betp_thresh = np.partition(betp_fp_vals, betp_thresh_idx)[betp_thresh_idx]
        betp_topk_fp = betp_fp_vals >= betp_thresh
    betp_emitted = np.zeros((EXPECTED["height"], EXPECTED["width"]), dtype=np.float64)
    betp_emitted[footprint] = betp_topk_fp.astype(np.float64) * betp_fp_vals
    betp_em_max = float(betp_emitted.max())
    if betp_em_max > 0:
        betp_emitted = betp_emitted / betp_em_max
    betp_emitted = np.clip(betp_emitted, 0.0, 1.0).astype(np.float32)
    rho_vs_betp = pearson(submission.astype(np.float64), betp_emitted.astype(np.float64))
    print(f"    Pearson ρ against budget-emitted BetP(F) alone: {rho_vs_betp:.6f}")

    is_distinct = abs(rho_pearson) < 0.999 and abs(rho_vs_bel) < 0.999
    print(f"    ✓ Submission is DISTINCT from naive mean and raw Bel(F): {is_distinct}")

    # --- Write submission ---
    outdir = ROOT / "docs" / "downloads"
    outdir.mkdir(parents=True, exist_ok=True)

    submission_filename = f"gemsdoe48-h58-pignistic-conflict-priced-B2xH33D-{DATESTAMP}-e58.tif"
    submission_path = outdir / submission_filename

    write_submission(submission_path, submission.astype(np.float64))
    submission_sha = sha256_file(submission_path)
    print(f"\n  ✓ Submission written: {submission_path.name}")
    print(f"    SHA-256: {submission_sha}")

    # --- Write diagnostics ---
    # m(Θ) — unassigned/ignorance mass
    mtheta_path = outdir / f"gemsdoe48-h58-diag-mtheta-{DATESTAMP}-e58.tif"
    from gemsdoe48.grid import write_float32
    mtheta_out = np.where(footprint, fusion.unassigned.astype(np.float32), np.float32(np.nan))
    write_float32(mtheta_path, mtheta_out, nodata=np.nan)
    print(f"  ✓ Diagnostic m(Θ): {mtheta_path.name}")

    # K — raw conflict
    conflict_path = outdir / f"gemsdoe48-h58-diag-conflict-{DATESTAMP}-e58.tif"
    conflict_out = np.where(footprint, fusion.conflict.astype(np.float32), np.float32(np.nan))
    write_float32(conflict_path, conflict_out, nodata=np.nan)
    print(f"  ✓ Diagnostic K: {conflict_path.name}")

    # Plausibility
    plaus_path = outdir / f"gemsdoe48-h58-diag-plausibility-{DATESTAMP}-e58.tif"
    plaus_out = np.where(footprint, fusion.plausibility.astype(np.float32), np.float32(np.nan))
    write_float32(plaus_path, plaus_out, nodata=np.nan)
    print(f"  ✓ Diagnostic Pl(F): {plaus_path.name}")

    # Continuous pignistic surface (the full ranking, for reference)
    cont_path = outdir / f"gemsdoe48-h58-continuous-pignistic-{DATESTAMP}-e58.tif"
    cont_out = np.where(footprint, continuous_out, np.float32(np.nan))
    write_float32(cont_path, cont_out, nodata=np.nan)
    print(f"  ✓ Continuous ranking surface: {cont_path.name}")

    # --- Build receipt ---
    receipt = {
        "hypothesis": "H58 pignistic conflict-priced DS fusion",
        "description": (
            "Pignistic probability BetP(F) = Bel(F) + m(Θ)/2 weighted by (1−K) "
            "where K is raw conjunctive conflict. Unlike all prior GEMSDOE48 fusions "
            "(which output raw Bel(F)), this carries disagreement INTO the submission "
            "surface itself."
        ),
        "timestamp": DATESTAMP,
        "parents": {
            "A": {
                "id": "H33-2-B2",
                "family": "dotted",
                "path": str(PINNED_DOTTED),
                "sha256": SHA_DOTTED,
                "owner_reported_live": LIVE_DOTTED_B2,
                "positive_pixels": n_dotted,
            },
            "B": {
                "id": "H33-D",
                "family": "tip/stepover",
                "path": str(PINNED_TIP),
                "sha256": SHA_TIP,
                "owner_reported_live": LIVE_TIP_H33D,
                "positive_pixels": n_tip,
            },
        },
        "overlap": {
            "shared_pixels": n_both,
            "union_pixels": n_union,
            "jaccard": n_both / n_union if n_union > 0 else 0,
        },
        "parameters": {
            "RHO_MAX": RHO_MAX,
            "alpha_A": alpha_a,
            "alpha_B": alpha_b,
            "kernel": "triangular k(d) = max(1-d/300m, 0)",
            "evidence": "metric-geometry kernel-credit belief surface",
            "combination": "canonical normalized Dempster rule",
            "output": "BetP(F) * (1 - K), normalized to [0,1]",
        },
        "distinctness": {
            "pearson_vs_naive_mean": rho_pearson,
            "spearman_vs_naive_mean": rho_spearman,
            "max_abs_diff_vs_naive_mean": max_abs_diff,
            "pearson_vs_raw_belief": rho_vs_bel,
            "pearson_vs_betp_alone": rho_vs_betp,
            "is_distinct": bool(is_distinct),
        },
        "submission": {
            "filename": submission_filename,
            "sha256": submission_sha,
            "positive_pixels": int((submission > 0).sum()),
            "all_finite": bool(np.all(np.isfinite(submission))),
            "value_range": [float(submission.min()), float(submission.max())],
            "grid": {
                "width": EXPECTED["width"],
                "height": EXPECTED["height"],
                "crs": EXPECTED["crs"],
                "pixel_size_m": 100.0,
            },
        },
        "diagnostics": {
            "mtheta_file": mtheta_path.name,
            "conflict_file": conflict_path.name,
            "plausibility_file": plaus_path.name,
        },
        "status": "UNSCORED — research artifact; no organizer score exists",
        "note_for_submission_form": SUBMISSION_NOTE,
        "submission_name": SUBMISSION_NAME,
    }

    receipt_path = ROOT / "evidence" / f"build_h58_receipt_{DATESTAMP.replace(':', '').replace('-', '')}.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2, default=str)
        f.write("\n")
    print(f"  ✓ Receipt: {receipt_path.name}")

    # --- Zip submission ---
    zip_path = submission_path.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(submission_path, submission_filename)
    print(f"  ✓ ZIP: {zip_path.name}")

    print("\n" + "=" * 70)
    print(f"SUBMISSION FILE: {submission_path}")
    print(f"NAME FOR PORTAL: {SUBMISSION_NAME}")
    print(f"NOTE ({len(SUBMISSION_NOTE)}/200 chars): {SUBMISSION_NOTE}")
    print(f"SHA-256: {submission_sha}")
    print(f"FORMAT: all-finite, [0,1], {EXPECTED['width']}x{EXPECTED['height']}, EPSG:32611, float32")
    print(f"POSITIVE PIXELS: {(submission > 0).sum()}")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
