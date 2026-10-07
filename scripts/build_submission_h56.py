#!/usr/bin/env python3
"""Build the unique H56 open-world Dempster-Shafer B2 × H33-D candidate.

The primary is an all-finite, zeros-outside, one-band float32 GeoTIFF on the
competition grid. Residual m(Theta), raw Dempster conflict K, plausibility,
raw Bel(F), and absolute source disagreement are separate diagnostic GeoTIFFs.
All inputs are SHA-pinned. This is a research candidate, not a slot clearance.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.stats import pearsonr, spearmanr

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gemsdoe48.geotiff import (assert_competition_grid, display_path,
                               write_float32_zeros_outside)
from gemsdoe48.h56 import (combine_open_world_dempster, deterministic_top_k,
                           normalize_belief, sparse_open_world_bpa)
from gemsdoe48.live_model import max_credit_field

DOTTED = ROOT / "data/families/dotted_b2_prune_02778.tif"
TIP = ROOT / "data/raw/tip_h33d_stepover.tif"
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
DOWNLOADS = ROOT / "docs/downloads"
DIAGNOSTICS = DOWNLOADS / "diagnostics"
RECEIPT = ROOT / "evidence/build_h56_receipt_20261007.json"

EXPECTED_SHA = {
    DOTTED: "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    TIP: "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757",
    FOOTPRINT: "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f",
}
ALPHA_DOTTED = 0.60
ALPHA_TIP = 0.60
ABSENCE_INFORMATIVENESS = 0.10
TOP_K_REFERENCE = 37_654
BUILD_DATE = "20261007"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_pinned_inputs() -> dict:
    results = {}
    for path, expected in EXPECTED_SHA.items():
        if not path.exists():
            raise SystemExit(f"missing pinned source {display_path(path)}")
        actual = sha256_file(path)
        if actual != expected:
            raise SystemExit(
                f"SHA-256 mismatch for {display_path(path)}: expected {expected}, got {actual}"
            )
        results[path.name] = {
            "path": display_path(path),
            "sha256": actual,
            "bytes": path.stat().st_size,
            "pin_matched": True,
        }
    return results


def read_one_band(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as src:
        assert_competition_grid(src.profile, path=path)
        if src.count != 1 or src.dtypes != ("float32",):
            raise SystemExit(f"{display_path(path)} must be a one-band float32 surface")
        values = src.read(1)
        profile = src.profile.copy()
        nodata = src.nodata
    if nodata is not None and np.isnan(nodata):
        values = np.where(np.isfinite(values), values, 0.0)
    elif nodata is not None:
        values = np.where(values == nodata, 0.0, values)
    if not np.isfinite(values).all() or np.any((values < 0.0) | (values > 1.0)):
        raise SystemExit(f"{display_path(path)} contains nonfinite or out-of-range values")
    return values.astype(np.float32, copy=False), profile


def correlation_stats(prediction: np.ndarray, mean_surface: np.ndarray, valid: np.ndarray) -> dict:
    p = np.asarray(prediction[valid], dtype=np.float64)
    m = np.asarray(mean_surface[valid], dtype=np.float64)
    difference = np.abs(p - m)
    if p.size < 2 or p.std() == 0 or m.std() == 0:
        raise ValueError("cannot compare constant surfaces")
    sample_step = max(1, int(np.ceil(p.size / 100_000)))
    sampled_spearman = spearmanr(p[::sample_step], m[::sample_step]).statistic
    slope, intercept = np.polyfit(m, p, 1)
    residual = np.abs(p - (slope * m + intercept))
    p_top = deterministic_top_k(prediction, valid, TOP_K_REFERENCE)
    m_top = deterministic_top_k(mean_surface, valid, TOP_K_REFERENCE)
    intersection = int((p_top & m_top).sum())
    union = int((p_top | m_top).sum())
    return {
        "comparison_domain": "valid competition footprint cells",
        "pearson_bel_vs_naive_mean": float(pearsonr(p, m).statistic),
        "spearman_bel_vs_naive_mean_deterministic_sample": float(sampled_spearman),
        "spearman_sample_cells": int(p[::sample_step].size),
        "mean_absolute_difference": float(difference.mean()),
        "median_absolute_difference": float(np.median(difference)),
        "max_absolute_difference": float(difference.max()),
        "fraction_abs_difference_gt_0p05": float((difference > 0.05).mean()),
        "exactly_equal_cells": int(np.count_nonzero(p == m)),
        "best_affine_fit": {
            "slope": float(slope),
            "intercept": float(intercept),
            "mean_absolute_residual": float(residual.mean()),
        },
        "top_37654_budget_jaccard": float(intersection / union) if union else None,
        "is_pixelwise_equal": bool(np.array_equal(p, m)),
    }


def main() -> int:
    print("[1/7] verify SHA-pinned parents and competition footprint")
    inputs = require_pinned_inputs()
    dotted_raw, dotted_profile = read_one_band(DOTTED)
    tip_raw, tip_profile = read_one_band(TIP)
    if dotted_profile != tip_profile:
        # Dict equality is exact for the metadata used here; report a friendly error.
        for key in ("width", "height", "crs", "transform", "count", "dtype"):
            if dotted_profile.get(key) != tip_profile.get(key):
                raise SystemExit(f"grid/profile mismatch on {key}: dotted != tip")
    with rasterio.open(FOOTPRINT) as ds:
        assert_competition_grid(ds.profile, path=FOOTPRINT)
        if ds.dtypes != ("uint8",):
            raise SystemExit("footprint mask must be uint8")
        footprint = ds.read(1) == 1
        footprint_profile = ds.profile.copy()
    if int(footprint.sum()) != 5_167_373:
        raise SystemExit(f"unexpected footprint size: {int(footprint.sum())}")

    dotted_mask = (dotted_raw > 0.0) & footprint
    tip_mask = (tip_raw > 0.0) & footprint
    n_dotted, n_tip = int(dotted_mask.sum()), int(tip_mask.sum())
    if n_dotted != 37_654 or n_tip != 41_865:
        raise SystemExit(f"unexpected family masks: dotted={n_dotted}, tip={n_tip}")
    if np.any((dotted_raw > 0.0) & ~footprint) or np.any((tip_raw > 0.0) & ~footprint):
        raise SystemExit("family parent contains a positive cell outside the registered footprint")

    print("[2/7] derive the official 300 m triangular maximum-credit fields")
    b1 = np.clip(max_credit_field(dotted_mask), 0.0, 1.0).astype(np.float64)
    b2 = np.clip(max_credit_field(tip_mask), 0.0, 1.0).astype(np.float64)
    b1[~footprint] = 0.0
    b2[~footprint] = 0.0
    if float(b1[footprint].max()) != 1.0 or float(b2[footprint].max()) != 1.0:
        raise ArithmeticError("family support surfaces must each reach unit support")

    print("[3/7] apply the preregistered open-world discounted BPA and Dempster rule")
    bpa_dotted = sparse_open_world_bpa(
        b1, reliability=ALPHA_DOTTED,
        absence_informativeness=ABSENCE_INFORMATIVENESS,
    )
    bpa_tip = sparse_open_world_bpa(
        b2, reliability=ALPHA_TIP,
        absence_informativeness=ABSENCE_INFORMATIVENESS,
    )
    combined = combine_open_world_dempster(bpa_dotted, bpa_tip)
    bel = combined.fault
    unassigned = combined.ignorance
    conflict = combined.conflict
    plausibility = np.clip(bel + unassigned, 0.0, 1.0)
    bel_norm = normalize_belief(bel, footprint)
    naive_mean = 0.5 * (b1 + b2)
    if float(naive_mean[footprint].max()) > 0:
        naive_mean /= float(naive_mean[footprint].max())
    naive_mean[~footprint] = 0.0
    comparison = correlation_stats(bel_norm, naive_mean, footprint)
    if comparison["is_pixelwise_equal"] or comparison["best_affine_fit"]["mean_absolute_residual"] < 1e-8:
        raise SystemExit("D-S belief unexpectedly collapsed to an affine copy of the naive mean")

    # Numerical invariants over the valid domain, checked independently of file I/O.
    mass_total = combined.fault + combined.not_fault + combined.ignorance
    if not np.allclose(mass_total[footprint], 1.0, rtol=0.0, atol=2e-8):
        raise ArithmeticError("combined masses fail the in-footprint sum-to-one check")
    if not all(np.isfinite(field).all() for field in (bel, unassigned, conflict, plausibility)):
        raise ArithmeticError("nonfinite Dempster layer before writing")

    print("[4/7] write the primary all-finite zeros-outside competition GeoTIFF")
    temporary = DOWNLOADS / ".h56-primary-unhashed.tif"
    primary_tags = {
        "candidate_id": "GEMSDOE48-H56-OWDS-B2xH33D",
        "model": "Open-world discounted Dempster-Shafer combination",
        "source_dotted_sha256": EXPECTED_SHA[DOTTED],
        "source_tip_sha256": EXPECTED_SHA[TIP],
        "support_surface": "300 m triangular max-credit field",
        "reliability_alpha_dotted": str(ALPHA_DOTTED),
        "reliability_alpha_tip": str(ALPHA_TIP),
        "absence_informativeness_q": str(ABSENCE_INFORMATIVENESS),
        "belief_normalization": "Bel(F) divided by in-footprint maximum; relative favorability, not calibrated probability",
        "outside_encoding": "finite zero; nodata unset; all cells are in [0,1]",
        "status": "research_only_no_weekly_slot_cleared",
    }
    temporary_receipt = write_float32_zeros_outside(
        temporary,
        bel_norm,
        dotted_profile,
        valid_mask=footprint,
        description="H56 open-world Dempster-Shafer Bel(F), max-normalized relative favorability",
        tags=primary_tags,
    )
    primary_sha = sha256_file(temporary)
    content_id = primary_sha[:12]
    base = f"GEMSDOE48-H56-OWDS-B2xH33D-{BUILD_DATE}-{content_id}"
    primary_path = DOWNLOADS / f"{base}-zeros-outside.tif"
    if primary_path.exists():
        if sha256_file(primary_path) != primary_sha:
            raise SystemExit(f"refusing to overwrite a different existing artifact: {primary_path}")
        temporary.unlink()
    else:
        temporary.replace(primary_path)
    primary_record = dict(temporary_receipt)
    primary_record.update({
        "path": display_path(primary_path),
        "sha256": primary_sha,
        "bytes": primary_path.stat().st_size,
        "content_id": content_id,
    })

    print("[5/7] write separate belief, ignorance, conflict, plausibility, and disagreement diagnostics")
    diagnostic_specs = {
        "belief_raw": (bel, "canonical Dempster Bel(F) before max normalization"),
        "unassigned_mtheta": (unassigned, "canonical Dempster residual m(Theta); does not include conflict K"),
        "conflict_k": (conflict, "raw conjunctive Dempster conflict K before normalization"),
        "plausibility": (plausibility, "Dempster plausibility Pl(F)=Bel(F)+m(Theta)"),
        "support_disagreement": (np.abs(b1 - b2), "absolute difference between the two metric-kernel support surfaces; not a Dempster mass"),
    }
    diagnostics = {}
    for key, (array, description) in diagnostic_specs.items():
        path = DIAGNOSTICS / f"{base}-{key.replace('_', '-')}.tif"
        record = write_float32_zeros_outside(
            path,
            np.where(footprint, array, 0.0),
            dotted_profile,
            valid_mask=footprint,
            description=description,
            tags={**primary_tags, "layer": key, "role": "diagnostic_not_submission"},
        )
        record["sha256"] = sha256_file(path)
        diagnostics[key] = record

    print("[6/7] calculate parent overlap, output range, and non-mean diagnostics")
    overlap = int((dotted_mask & tip_mask).sum())
    union = int((dotted_mask | tip_mask).sum())
    in_bel = bel[footprint]
    in_theta = unassigned[footprint]
    in_k = conflict[footprint]
    in_prediction = bel_norm[footprint]
    portal_name = f"GEMSDOE48-H56-OWDS-B2xH33D-{content_id}"
    portal_note = (
        f"{portal_name} | q=0.10 open-world absence, alpha=0.60, metric-kernel B2 x H33-D; "
        "Bel normalized; mTheta/K separate; unscored research only, not slot-cleared."
    )
    if len(portal_note) > 200:
        raise SystemExit(f"portal note length {len(portal_note)} exceeds 200 characters")

    build_receipt = {
        "schema_version": 1,
        "status": "BUILT_RESEARCH_CANDIDATE_NOT_SLOT_CLEARED",
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "candidate": {
            "id": "H56-DS",
            "unique_name": portal_name,
            "primary": primary_record,
            "portal_note_draft_do_not_submit_without_gate": portal_note,
            "portal_note_characters": len(portal_note),
            "weekly_slot_cleared": False,
            "organizer_score_exists": False,
        },
        "inputs": inputs,
        "parents": {
            "dotted_b2": {"path": display_path(DOTTED), "positive_cells": n_dotted,
                          "owner_reported_live": 0.2778, "exact_file_score_receipt": False},
            "tip_stepover_h33d": {"path": display_path(TIP), "positive_cells": n_tip,
                                   "owner_reported_live": 0.2632, "exact_file_score_receipt": False},
            "footprint_cells": int(footprint.sum()),
            "overlap_cells": overlap,
            "union_cells": union,
            "jaccard": overlap / union,
            "b2_share_in_overlap": overlap / n_dotted,
            "h33d_share_in_overlap": overlap / n_tip,
        },
        "method": {
            "source_model": "Each binary sparse mask is transformed to the official 300 m triangular max-credit field.",
            "frame": "Theta = {fault, not fault}",
            "mass_assignment": "m(F)=alpha*b; m(notF)=alpha*q*(1-b); m(Theta)=1-m(F)-m(notF)",
            "reliability_alpha": {"dotted": ALPHA_DOTTED, "tip_stepover": ALPHA_TIP},
            "absence_informativeness_q": ABSENCE_INFORMATIVENESS,
            "q_interpretation": "Only 10% of a source's lack-of-support mass is assigned to not-fault; 90% remains uncommitted. This is a preregistered open-world assumption, not learned or calibrated.",
            "combination": "Canonical normalized Dempster orthogonal sum, pixelwise.",
            "conflict_semantics": "K is pre-normalization conflict and is not included in canonical residual m(Theta). Both are exported separately.",
            "primary": "Bel(F) divided by its maximum inside the valid footprint, then float32; relative favorability, not calibrated probability.",
            "outside_encoding": "all finite float32 zeros, nodata unset; selected to avoid nonfinite values in a portal-wide [0,1] check. The official problem description also documents null/NaN outside the data footprint; exact portal acceptance of this file remains untested.",
        },
        "layers": {
            "raw_belief_range": [float(in_bel.min()), float(in_bel.max())],
            "normalized_belief_range": [float(in_prediction.min()), float(in_prediction.max())],
            "mtheta_range": [float(in_theta.min()), float(in_theta.max())],
            "conflict_k_range": [float(in_k.min()), float(in_k.max())],
            "support_disagreement_range": [float(np.abs(b1[footprint] - b2[footprint]).min()),
                                           float(np.abs(b1[footprint] - b2[footprint]).max())],
            "diagnostics": diagnostics,
        },
        "not_the_naive_mean": comparison,
        "holdout": {
            "status": "NOT_YET_RUN",
            "protocol": "scripts/run_spatial_holdout.py; four fixed quadrants, held-out core plus 300 m Euclidean halo, catalogue and >300 m off-catalogue SGMC proxies separately",
            "slot_decision": "No submission slot will be used in this session; candidate must beat the comparable current proxy-best before any future slot discussion.",
        },
        "limitations": [
            "The local family TIFFs are public owner mirrors; the reported 0.2778 and 0.2632 values are owner-reported and not organizer receipts for these exact bytes.",
            "The family surfaces overlap heavily; separate construction pipelines do not establish statistical independence.",
            "The q=0.10 absence assumption and alpha=0.60 discounts are explicit but not estimated from private truth.",
            "The final max-normalized Bel surface is relative favorability and no longer a literal normalized BPA layer; raw Bel and m(Theta) are retained separately.",
            "A local format audit is not organizer acceptance. The primary uses finite zeros outside although the official challenge page describes null/NaN outside; the matching-grid template and live-best encoding provide precedent, not acceptance proof.",
        ],
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(build_receipt, indent=2) + "\n", encoding="utf-8")
    print("[7/7] receipt written")
    print(json.dumps({
        "candidate": portal_name,
        "primary": primary_record,
        "portal_note": portal_note,
        "primary_values_all_finite_0_1": primary_record["all_cells_in_range_0_1"],
        "not_naive_mean": comparison,
        "diagnostic_layers": {name: record["path"] for name, record in diagnostics.items()},
        "receipt": display_path(RECEIPT),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
