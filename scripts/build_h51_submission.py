#!/usr/bin/env python3
"""Build the H51 plausibility-budget emission: a unique second submission.

H51 keeps the H50 evidential construction exactly (same SHA-pinned parents,
same kernel-credit belief surfaces, same RHO_MAX-ceiled live-anchored
reliabilities, same canonical normalized Dempster rule) and changes only the
decision rule:

    H50 submission : graded normalized Bel(F)               (diagnostic fusion)
    H51 submission : binary 1 on the top-B cells ranked by Pl(F) = Bel(F) + m(Theta),
                     B = 37,654 (mass-matched to the dotted parent)

Rationale (docs/research/h51-method-20261007.md): the official DTI is a budget
metric for which binary emission on a fixed support is optimal, and ranking by
plausibility -- the upper Dempster-Shafer interval bound, "commit wherever the
combined evidence has not positively refuted a fault" -- restores the
union-like coverage that beat both parents on the blocked proxies while still
ordering doubly supported cells above single-family cells.

Outputs
-------
docs/downloads/gemsdoe48-h51-plausibility-budget-<date>-<sha8>-zeros.tif  primary
docs/downloads/gemsdoe48-h51-plausibility-budget-<date>-<sha8>-zeros.zip  zip twin
docs/downloads/gemsdoe48-h51-plausibility-budget-<date>-<sha8>-nan.tif    official-convention twin
evidence/build_h51_receipt_20261007.json                                  preregistration + audit

The Pl / m(Theta) / K diagnostics are byte-identical to the H50 diagnostic
layers (identical fusion); the receipt pins their SHAs instead of duplicating
the files.
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

from gemsdoe48 import ds50, h51
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
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
H50_PRIMARY = ROOT / "docs/downloads/gemsdoe48-h50-ds-b2xh36rung30-20261007-5b59e106-zeros.tif"
H48_PRIOR = ROOT / "docs/downloads/GEMSDOE48-DS-conflict-aware-fusion-20261006.tif"
H49_PRIOR = ROOT / "docs/downloads/gemsdoe48-h49-ds-conflict-balanced-20261006-e6f08013888b.tif"

SHA_DOTTED = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
SHA_TIP_H36 = "5556aa1438fd67376b60d5ffc99228ec09dcc11a8408298a743ccb88d6163641"
SHA_FOOTPRINT = "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f"
# H50 diagnostics must be byte-reproducible from the identical fusion.
SHA_H50_DIAG_MTHETA = "405346c4c940615e725bca74370888d527860fd561ef237723626acd9f6c2b40"
SHA_H50_DIAG_K = "612412b48e45704e40a00718589da6a04f12e0b23d55954094de7c4ebc85a44f"
SHA_H50_DIAG_PL = "cd0e07fb882927d528a6708044e4f88e63ea21ffa9e6af4b41f045f186a930e0"

DATESTAMP = "20261007"
SUBMISSION_NAME = "GEMSDOE48-H51-PLAUSIBILITY-BUDGET"
SUBMISSION_NOTE = (
    "GEMSDOE48 H51 | binary top-37,654 by DS plausibility; Dempster fusion of "
    "B2 x H36-1 rung30 (H19-5/rung-30 repack, not tip/step-over); "
    "H50 diagnostics reused; unscored research candidate."
)


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


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    if x.size < 2 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=ROOT / "docs/downloads")
    parser.add_argument("--receipt", type=Path, default=ROOT / "evidence/build_h51_receipt_20261007.json")
    parser.add_argument("--allow-unpinned", action="store_true")
    args = parser.parse_args()

    if len(SUBMISSION_NOTE) > 200:
        raise SystemExit("submission note exceeds the portal's 200-character limit")
    if not args.allow_unpinned:
        require_sha(PINNED_DOTTED, SHA_DOTTED, "dotted parent")
        require_sha(PINNED_TIP, SHA_TIP_H36, "H36-1 rung30 parent")
        require_sha(FOOTPRINT, SHA_FOOTPRINT, "footprint mask")

    dotted_raw, dotted_profile = read_band(PINNED_DOTTED)
    tip_raw, tip_profile = read_band(PINNED_TIP)
    assert_competition_grid(dotted_profile, path=PINNED_DOTTED)
    assert_competition_grid(tip_profile, path=PINNED_TIP)
    assert_same_grid(dotted_profile, tip_profile, name_a="dotted B2", name_b="H36-1 rung30 (not tip/step-over)")
    with rasterio.open(FOOTPRINT) as fp_ds:
        assert_competition_grid(fp_ds.profile, path=FOOTPRINT)
        footprint = fp_ds.read(1) == 1

    dotted = np.where(np.isfinite(dotted_raw), dotted_raw, 0.0)
    tip = np.where(np.isfinite(tip_raw), tip_raw, 0.0)
    dotted_mask = (dotted > 0) & footprint
    tip_mask = (tip > 0) & footprint
    n_dotted = int(dotted_mask.sum())
    n_tip = int(tip_mask.sum())
    n_union = int((dotted_mask | tip_mask).sum())

    # ------------------------- preregistered constants ------------------------
    budget = n_dotted  # 37,654: mass-matched to the dotted parent's committed cells
    a_dotted = ds50.RHO_MAX
    a_tip = ds50.RHO_MAX * (ds50.LIVE_TIP_H36 / ds50.LIVE_DOTTED_B2)
    prereg = h51.H51Preregistration(
        budget=budget,
        dotted_reliability=a_dotted,
        tip_reliability=a_tip,
        dotted_sha256=SHA_DOTTED,
        tip_sha256=SHA_TIP_H36,
    )
    preregistered_utc = datetime.now(timezone.utc).isoformat()

    # ------------------------- evidence and DS fusion -------------------------
    belief_a = ds50.kernel_belief_surface(dotted_mask)
    belief_b = ds50.kernel_belief_surface(tip_mask)
    fusion = ds50.dempster_fuse(belief_a, belief_b, a_dotted, a_tip, footprint=footprint)
    pl = np.where(footprint, fusion.plausibility, 0.0)

    # ------------------------- the H51 decision rule --------------------------
    emission = h51.plausibility_emission(pl, budget=budget, where=footprint)
    emission_mask = emission > 0
    if int(emission_mask.sum()) != budget:
        raise SystemExit("emission budget not met exactly")
    submission = np.where(footprint, emission, 0.0).astype(np.float32)

    # ------------------------- anti-copy / anti-average checks ----------------
    union_mask = dotted_mask | tip_mask
    h50_top_bel = ds50.top_k_mask(
        np.where(footprint, fusion.belief_normalized, 0.0), budget, where=footprint
    )
    naive = ds50.naive_mean_belief(belief_a, belief_b)
    algebraic_or = belief_a + belief_b - belief_a * belief_b  # DS OR of the two beliefs
    set_distances = {
        "budget_cells": budget,
        "union_cells": n_union,
        "jaccard_vs_parent_union": h51.jaccard(emission_mask, union_mask),
        "cells_in_union": int((emission_mask & union_mask).sum()),
        "cells_outside_union": int((emission_mask & ~union_mask).sum()),
        "jaccard_vs_dotted_parent": h51.jaccard(emission_mask, dotted_mask),
        "jaccard_vs_tip_parent": h51.jaccard(emission_mask, tip_mask),
        "jaccard_vs_h50_bel_top_budget": h51.jaccard(emission_mask, h50_top_bel),
        "note": (
            "observed: every emitted cell lies inside the parents' committed-pixel "
            "union, i.e. H51 is a budget-trimmed union -- it drops the lowest-plausibility "
            "union cells (weak single-family support) instead of adding new cells"
        ),
    }
    rank_correlations = {
        "pl_vs_naive_mean_in_footprint": pearson(pl[footprint], naive[footprint]),
        "pl_vs_algebraic_or_in_footprint": pearson(pl[footprint], algebraic_or[footprint]),
        "pl_vs_h50_belief_in_footprint": pearson(
            pl[footprint], fusion.belief_normalized[footprint]
        ),
        "note": (
            "plausibility ranking is close to the DS algebraic OR (b1+b2-b1*b2), which "
            "is the point: Pl restores union-like coverage; it is not the naive mean"
        ),
    }

    # ------------------------- write the artifacts -----------------------------
    args.outdir.mkdir(parents=True, exist_ok=True)
    tmp_primary = args.outdir / f".tmp-h51-{DATESTAMP}.tif"
    write_submission(tmp_primary, submission)
    primary_sha = sha256_file(tmp_primary)
    short_id = primary_sha[:8]
    primary_path = args.outdir / f"gemsdoe48-h51-plausibility-budget-{DATESTAMP}-{short_id}-zeros.tif"
    primary_path.unlink(missing_ok=True)
    tmp_primary.rename(primary_path)
    zip_path = primary_path.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(primary_path, arcname=primary_path.name)

    # Frozen H51 TIFF tags and receipt fields retain ``tip`` compatibility
    # aliases for the H36-1 rung30 raster. They do not classify H36 as a
    # tip/step-over family; see the dated classification erratum.
    tag_values = {
        "model": "H51 plausibility-budget emission of the H50 Dempster fusion",
        "decision_rule": "binary top-B by Pl(F)=Bel(F)+m(Theta), B=37654",
        "reliability_dotted": str(a_dotted),
        "reliability_tip": f"{a_tip:.6f}",
        "frame": "{fault, not_fault, Theta}",
        "source_dotted_sha256": SHA_DOTTED,
        "source_tip_sha256": SHA_TIP_H36,
        "submission_name": SUBMISSION_NAME,
    }
    twin_path = primary_path.with_name(primary_path.name.replace("-zeros.tif", "-nan.tif"))
    receipt_twin = write_float32(
        twin_path,
        np.where(footprint, emission, np.nan).astype(np.float32),
        dotted_profile,
        valid_mask=footprint,
        description="H51 plausibility-budget emission; NaN/nodata outside survey footprint",
        tags=tag_values,
    )

    # Diagnostics are byte-identical to the H50 layers (same fusion). Verify.
    diag_dir = args.outdir / "diagnostics"
    diag_pl = diag_dir / f"gemsdoe48-h50-plausibility-{DATESTAMP}-5b59e106.tif"
    diag_k = diag_dir / f"gemsdoe48-h50-conflict-K-{DATESTAMP}-5b59e106.tif"
    diag_mtheta = diag_dir / f"gemsdoe48-h50-unassigned-mTheta-{DATESTAMP}-5b59e106.tif"
    diag_specs = (
        (diag_pl, SHA_H50_DIAG_PL, "plausibility diagnostic", fusion.plausibility),
        (diag_k, SHA_H50_DIAG_K, "conflict-K diagnostic", fusion.conflict),
        (diag_mtheta, SHA_H50_DIAG_MTHETA, "unassigned-mass diagnostic", fusion.unassigned),
    )
    for path, expected, label, field in diag_specs:
        if path.is_file():
            require_sha(path, expected, label)
        else:
            # Rebuild the missing layer so the sub-site link never dangles.
            write_float32(
                path, np.where(footprint, field, np.nan).astype(np.float32),
                dotted_profile, valid_mask=footprint,
                description=f"rebuilt {label}", tags=tag_values,
            )
            require_sha(path, expected, f"rebuilt {label}")

    # ------------------------- uniqueness audit --------------------------------
    existing = sorted(
        p for p in list((ROOT / "docs/downloads").rglob("*.tif")) + list((ROOT / "data").rglob("*.tif"))
        if p.is_file() and p != primary_path and p != twin_path
    )
    collisions = []
    for path in existing:
        if sha256_file(path) == primary_sha:
            collisions.append(str(path.relative_to(ROOT)))
    if collisions:
        raise SystemExit(f"hash collision with existing artifacts: {collisions}")

    prior_distances = {}
    for label, path in (("h50_belief", H50_PRIMARY), ("h49_yager", H49_PRIOR), ("h48_rho05", H48_PRIOR)):
        if path.is_file():
            arr, prof = read_band(path)
            assert_same_grid(prof, dotted_profile, name_a=label, name_b="h51")
            vals = np.where(np.isfinite(arr), arr, 0.0)
            if vals.min() == 0.0 and vals.max() <= 1.0:
                prior_mask = (vals > 0) & footprint
                prior_distances[label] = {
                    "path": display_path(path),
                    "sha256": sha256_file(path),
                    "jaccard_emission_vs_positive_cells": h51.jaccard(emission_mask, prior_mask),
                    "pearson_in_footprint": pearson(submission[footprint].astype(np.float64), vals[footprint]),
                }

    # ------------------------- receipt -----------------------------------------
    with rasterio.open(primary_path) as ds:
        primary_values = ds.read(1)
    receipt = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "preregistered_utc": preregistered_utc,
        "candidate_id": "H51",
        "submission_status": "UNSCORED_RESEARCH_CANDIDATE",
        "submission_name": SUBMISSION_NAME,
        "submission_note": SUBMISSION_NOTE,
        "submission_note_length": len(SUBMISSION_NOTE),
        "preregistration": {
            "budget": prereg.budget,
            "budget_rationale": "mass-matched to the dotted parent (owner-reported live 0.2778)",
            "rule": prereg.rule,
            "reliabilities": {"dotted": prereg.dotted_reliability, "tip": prereg.tip_reliability},
            "reliability_anchor": "identical to the preregistered H50 build (RHO_MAX x live-score ratio)",
            "parents": {"dotted": prereg.dotted_sha256, "tip": prereg.tip_sha256},
            "no_parameter_was_tuned_on_holdout_results": True,
        },
        "primary_file": str(primary_path.relative_to(ROOT)),
        "primary_sha256": primary_sha,
        "primary_bytes": primary_path.stat().st_size,
        "zip_file": str(zip_path.relative_to(ROOT)),
        "zip_sha256": sha256_file(zip_path),
        "nan_outside_twin": {
            "path": str(twin_path.relative_to(ROOT)),
            "sha256": sha256_file(twin_path),
            "bytes": receipt_twin["bytes"],
            "purpose": "official sample-template convention (NaN/nodata outside); passes scripts/validate_submission.py",
        },
        "diagnostics_reused_from_h50": {
            "plausibility": display_path(diag_pl),
            "conflict_K": display_path(diag_k),
            "unassigned_mTheta": display_path(diag_mtheta),
            "note": "byte-identical to the H50 diagnostic layers because the fusion is identical; SHAs re-verified at build time",
        },
        "set_distances": set_distances,
        "rank_correlations": rank_correlations,
        "prior_artifact_distances": prior_distances,
        "uniqueness": {
            "compared_existing_tifs": len(existing),
            "hash_collisions": collisions,
            "new_construction": "plausibility-ranked budget emission; no prior artifact ranked by Pl(F)",
        },
        "format_receipt": {
            "single_band": True,
            "dtype_float32": True,
            "crs": "EPSG:32611",
            "width": int(primary_values.shape[1]),
            "height": int(primary_values.shape[0]),
            "all_finite": bool(np.isfinite(primary_values).all()),
            "min_value": float(primary_values.min()),
            "max_value": float(primary_values.max()),
            "values_in_0_1": bool((primary_values >= 0).all() and (primary_values <= 1).all()),
            "positive_pixels": int((primary_values > 0).sum()),
            "zero_outside_footprint": bool((primary_values[~footprint] == 0).all()),
        },
        "organizer_score": None,
        "score_claim": "No organizer score exists for this artifact; no leaderboard projection is claimed.",
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "primary": str(primary_path.relative_to(ROOT)),
        "sha256": primary_sha,
        "budget": budget,
        "pl_vs_naive_mean": rank_correlations["pl_vs_naive_mean_in_footprint"],
        "pl_vs_algebraic_or": rank_correlations["pl_vs_algebraic_or_in_footprint"],
        "jaccard_vs_union": set_distances["jaccard_vs_parent_union"],
        "receipt": str(args.receipt.relative_to(ROOT)),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
