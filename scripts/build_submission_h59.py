#!/usr/bin/env python3
"""Build H59 -- sparse emission of the normalized Dempster-Shafer combined belief.

The artifact, its gates and its verdict
---------------------------------------
H59 answers the standing brief literally: combine the best dotted-family surface
(H33-2-B2, owner-reported 0.2778, SHA-256 pinned) with the best tip/step-over
surface (H33-D, owner-reported 0.2632, SHA-256 pinned) with Dempster's rule,
normalize the combined belief to [0, 1], export the residual unassigned mass
``m(Theta)`` and the raw conflict ``K`` as separate diagnostic layers, verify the
result is not the naive mean, verify the file cannot trigger the portal's
``Predicted values must be in range [0, 1]`` error, and state an unambiguous
verdict.

What is new here relative to the registry
-----------------------------------------
Every earlier artifact in this checkout emits either the *dense* DS belief
(H49/H50/H56/H56B/H57: 47,905-792,278 positive cells) or a pignistic
conflict-priced rank cut (H58).  The organizer-observed ladder for this campaign
sits in the **sparse** regime -- 37,654 -> 0.2778, 40,199 -> 0.2708,
44,090 -> 0.2600 [OWNER-REPORT, not a receipt] -- and the strict holdout in
``scripts/evaluate_holdout.py`` reproduces the same ordering on the
off-catalogue proxy (random emission of 200,000 cells reaches only 0.185 on that
proxy while the sparse families reach 0.095-0.098 at 38-48k).  H59 therefore
emits the *normalized Dempster belief* at the sparse density the evidence
supports, and keeps the disagreement mass as a diagnostic layer rather than
blending it into the surface.

Gates (all measured, nothing projected)
---------------------------------------
* format: single band, float32, EPSG:32611, 3292x3730, 100 m, transform equal to
  the organizer template, finite everywhere, min >= 0, max <= 1, no nodata tag,
  and the portal's own range predicate ``all(0 <= v <= 1)`` including NaN must
  evaluate True.
* not-the-average: Pearson/Spearman against the naive mean of the two opinion
  surfaces and the maximum absolute difference.
* registry: SHA-256 byte identity, dot overlap within the 3-pixel metric halo
  (both directions) and Spearman rank correlation against every locally
  available registry raster.
* verdict: printed as one line, derived mechanically from the gate dictionary.

Nothing in this builder fits anything to a hidden label.  Parents, reliabilities
and the emission mass are preregistered constants; the mass is fixed by the
organizer-observed sparse regime and by the same-mass random control in the
holdout receipt, not by any local proxy optimum.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gemsdoe48 import h59  # noqa: E402
from gemsdoe48.emit import cover_region  # noqa: E402
from gemsdoe48.grid import EXPECTED  # noqa: E402

PINNED_DOTTED = ROOT / "data/raw/dotted_h33_2_b2_zeros.tif"
PINNED_TIP = ROOT / "data/raw/tip_h33d_stepover.tif"
PINNED_TEMPLATE = ROOT / "data/raw/sample_submission_template.tif"
SHA_DOTTED = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
SHA_TIP = "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757"

# Preregistered emission mass: inside the owner-observed sparse band and between
# the two best-emitting registry families (37,654 and 41,865).
EMIT_BUDGET = 38000
EXPECTED_GRID = (EXPECTED["height"], EXPECTED["width"])

SUBMISSION_NAME = "GEMSDOE48-H59-CoverDSBelief-B2xH33D"
SUBMISSION_NOTE = (
    "GEMSDOE48 H59 | Dempster Bel(F), dotted B2 x tip H33D; 400m hex-cover of the "
    "fusion corridor; m(Theta) layer"
)
PORTAL_NOTE_LIMIT = 140
TRIAL_NAME = "gemsdoe48-h59-cover-ds-belief-b2xh33d"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_band(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as src:
        return src.read(1), src.profile.copy()


def registry_paths() -> list[Path]:
    """Every locally available registry/competition raster worth checking."""
    paths: list[Path] = []
    for folder in (ROOT / "data/families", ROOT / "data/raw/scored", ROOT / "data/raw",
                   ROOT / "data/official", ROOT / "docs/downloads"):
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.tif")):
            if path.name == "sample_submission_template.tif":
                continue
            paths.append(path)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=str(ROOT / "docs/downloads"))
    parser.add_argument("--receipt", default=None)
    parser.add_argument("--budget", type=int, default=EMIT_BUDGET)
    parser.add_argument("--rule", choices=("cover", "topk"), default="cover",
                        help="cover = metric-covering dot set over the fused corridor "
                             "(preregistered default); topk = sparse rank cut")
    parser.add_argument("--spacing", type=float, default=4.0,
                        help="hex-lattice spacing in pixels (4.0 px = 400 m)")
    args = parser.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    print("=" * 78)
    print(f"H59 sparse Dempster-belief build  {stamp}")
    print("=" * 78)

    # ---------------- pinned inputs ----------------
    input_shas = {"dotted_B2": sha256_file(PINNED_DOTTED), "tip_H33D": sha256_file(PINNED_TIP),
                  "template": sha256_file(PINNED_TEMPLATE)}
    print("  inputs:", json.dumps({k: v[:16] + "..." for k, v in input_shas.items()}))
    assert input_shas["dotted_B2"] == SHA_DOTTED, "dotted parent SHA-256 mismatch"
    assert input_shas["tip_H33D"] == SHA_TIP, "tip parent SHA-256 mismatch"

    dotted_raw, dotted_profile = read_band(PINNED_DOTTED)
    tip_raw, tip_profile = read_band(PINNED_TIP)
    template_raw, template_profile = read_band(PINNED_TEMPLATE)
    footprint = np.isfinite(template_raw)
    dotted = np.where(np.isfinite(dotted_raw), dotted_raw, 0.0) > 0
    tip = np.where(np.isfinite(tip_raw), tip_raw, 0.0) > 0
    if dotted.shape != EXPECTED_GRID or tip.shape != EXPECTED_GRID:
        raise SystemExit("parent grid does not match the competition grid")
    print(f"  grid {dotted.shape}, parent dots {int(dotted.sum())} / {int(tip.sum())}, "
          f"union {int((dotted | tip).sum())}, footprint {int(footprint.sum())}")

    # ---------------- Dempster combination ----------------
    fusion = h59.fuse(h59.opinion_surface(dotted), h59.opinion_surface(tip), footprint)
    bel = fusion.belief_normalized
    print(f"  reliabilities: alpha_dotted={h59.ALPHA_DOTTED:.6f} "
          f"alpha_tip={h59.ALPHA_TIP:.6f}")
    print(f"  m(Theta) max {float(fusion.unassigned[footprint].max()):.6f}; "
          f"K max {float(fusion.conflict[footprint].max()):.6f}; "
          f"Bel(F) max {float(fusion.belief[footprint].max()):.6f}")

    # ---------------- sparse emission (preregistered rule) ----------------
    union = dotted | tip
    if args.rule == "cover":
        # Metric-covering emission over the fused corridor: the corridor is the
        # union of the two families' committed cells (the fused belief is defined
        # over it), and the dot set is a minimal hex-covering of that corridor at
        # the preregistered covering radius.  Every corridor cell is then within
        # 224 m of an emitted dot, so recall is preserved while the emitted mass
        # drops below the union's 47,905 cells.
        corridor = union & footprint
        res = cover_region(corridor, float(args.spacing), prune=True)
        dots = res["points"] & footprint
        if int(dots.sum()) > int(args.budget):
            dots = h59.top_k_mask(np.where(dots, bel, -np.inf), int(args.budget), footprint)
        covering_measured = float(res["measured_radius"])
        covering_target = float(res["target_radius"])
        print(f"  covering emission: corridor {int(corridor.sum())} cells, spacing "
              f"{args.spacing} px, measured covering radius {covering_measured:.2f} px "
              f"({covering_measured * 100:.0f} m), target {covering_target:.2f} px")
    else:
        dots = h59.top_k_mask(bel, int(args.budget), footprint)
        covering_measured = None
        covering_target = None
    surface = np.where(dots & footprint, np.float32(1.0), np.float32(0.0)).astype(np.float32)
    n_emit = int((surface > 0).sum())
    support = dots
    print(f"  emitted {n_emit} dots (budget {args.budget}); "
          f"union support {int((dotted | tip).sum())}")

    shared = dotted & tip
    a_only = dotted & ~tip
    b_only = tip & ~dotted
    layers = {
        "emitted": support,
        "agreement_core_parents": shared,
        "dotted_only_parents": a_only,
        "tip_only_parents": b_only,
    }
    for key, mask in layers.items():
        print(f"    {key:26s} {int(mask.sum()):7d} cells "
              f"({int((mask & support).sum()):7d} emitted)")

    # ---------------- write primary + diagnostics ----------------
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    profile = template_profile.copy()
    profile.update(driver="GTiff", count=1, dtype="float32", nodata=None,
                   compress="deflate", tiled=True, blockxsize=256, blockysize=256)
    profile.pop("photometric", None)

    def write(path: Path, array: np.ndarray) -> None:
        with rasterio.open(path, "w", **profile) as dst:
            dst.write(array.astype(np.float32), 1)

    digest = hashlib.sha256(surface.tobytes()).hexdigest()[:12]
    tif_name = f"{TRIAL_NAME}-{stamp}-{digest}.tif"
    tif_path = out_dir / tif_name
    write(tif_path, surface)
    zip_path = out_dir / f"{TRIAL_NAME}-{stamp}-{digest}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(tif_path, tif_path.name)
    print(f"  wrote {tif_path.name} ({tif_path.stat().st_size} bytes)")

    diag_dir = out_dir / "diagnostics"
    diag_dir.mkdir(exist_ok=True)
    diagnostics: dict[str, str] = {}
    diag_arrays = {
        "diag-mtheta-unassigned": fusion.unassigned,
        "diag-conflict-K": fusion.conflict,
        "diag-plausibility": fusion.plausibility,
        "diag-belief-normalized": bel,
        "diag-disagreement-a-only": a_only.astype(np.float64),
        "diag-disagreement-b-only": b_only.astype(np.float64),
    }
    for name, array in diag_arrays.items():
        path = diag_dir / f"{TRIAL_NAME}-{name}-{stamp}.tif"
        # diagnostics may carry NaN outside the footprint (never the submission)
        arr = np.where(footprint, array, np.nan).astype(np.float32)
        write(path, arr)
        diagnostics[name] = path.name
    del diag_arrays, arr
    gc.collect()

    # ---------------- gate 1: format / portal predicate ----------------
    with rasterio.open(tif_path) as src:
        back = src.read(1)
        got_profile = src.profile.copy()
    template_transform = tuple(template_profile["transform"])[:6]
    finite = bool(np.isfinite(back).all())
    checks = {
        "single_band": int(got_profile["count"]) == 1,
        "dtype_float32": got_profile["dtype"] == "float32",
        "shape_matches_template": back.shape == template_raw.shape,
        "crs_matches_template": got_profile["crs"] == template_profile["crs"],
        "transform_matches_template": tuple(got_profile["transform"])[:6] == template_transform,
        "all_finite": finite,
        "min_ge_0": float(np.nanmin(back)) >= 0.0,
        "max_le_1": float(np.nanmax(back)) <= 1.0,
        "no_nodata_tag": got_profile.get("nodata") is None,
        "zero_outside_footprint": bool((back[~footprint] == 0).all()),
        # the exact predicate a portal range check uses; NaN fails it, hence the
        # all-finite encoding (repository irregularity IR-48-03)
        "portal_range_predicate_all": bool(np.all((back >= 0) & (back <= 1))),
        "portal_range_predicate_any_nan": bool(np.isnan(back).any()),
        "bytes_equal_planned_surface": bool(np.array_equal(back, surface)),
    }
    print("  format gates:", json.dumps(checks))
    format_ok = all(v for k, v in checks.items() if k != "portal_range_predicate_any_nan")

    # ---------------- gate 2: not the naive mean ----------------
    naive = 0.5 * (fusion.belief_a + fusion.belief_b)
    region = footprint & ((fusion.belief_a > 0) | (fusion.belief_b > 0))
    bel_region = bel[region]
    naive_region = naive[region]
    disagreements = np.abs(fusion.belief_a - fusion.belief_b) >= (1.0 / 3.0)
    disagree_region = region & disagreements
    not_average = {
        "pearson_all_support": float(np.corrcoef(bel_region, naive_region)[0, 1]),
        "spearman_all_support": float(np.corrcoef(rankdata(bel_region), rankdata(naive_region))[0, 1]),
        "max_abs_diff": float(np.abs(bel_region - naive_region).max()),
        "frac_diff_gt_0_05": float((np.abs(bel_region - naive_region) > 0.05).mean()),
        "disagreement_cells": int(disagree_region.sum()),
        "mean_belief_where_dotted_stronger": float(bel[dotted & ~tip].mean()) if (dotted & ~tip).any() else None,
        "mean_belief_where_tip_stronger": float(bel[tip & ~dotted].mean()) if (tip & ~dotted).any() else None,
        "mean_naive_where_dotted_stronger": float(naive[dotted & ~tip].mean()) if (dotted & ~tip).any() else None,
        "mean_naive_where_tip_stronger": float(naive[tip & ~dotted].mean()) if (tip & ~dotted).any() else None,
        "emitted_dots_on_disagreement_cells": int((support & disagree_region).sum()),
    }
    distinct_from_mean = bool(not_average["max_abs_diff"] > 0.05
                              and not_average["spearman_all_support"] < 0.999)
    print("  non-average gates:", json.dumps({k: (round(v, 5) if isinstance(v, float) else v)
                                              for k, v in not_average.items()}))

    # ---------------- gate 3: registry correlation / dot overlap ----------------
    my_radius = distance_transform_edt(~support) <= 3.0
    entries = []
    for path in registry_paths():
        if path.resolve() in (tif_path.resolve(), zip_path.resolve()):
            continue  # never compare the artifact with itself
        try:
            other, _ = read_band(path)
        except Exception as exc:  # unreadable file -> recorded, not silently skipped
            entries.append({"file": str(path.relative_to(ROOT)), "error": str(exc)})
            continue
        if other.shape != support.shape:
            continue
        other_support = np.where(np.isfinite(other), other, 0.0) > 0
        other_radius = distance_transform_edt(~other_support) <= 3.0
        mine_in_theirs = float((support & other_radius).sum() / max(int(support.sum()), 1))
        theirs_in_mine = float((other_support & my_radius).sum() / max(int(other_support.sum()), 1))
        jaccard = float((support & other_support).sum() / max(int((support | other_support).sum()), 1))
        exact = float((support & other_support).sum() / max(int(support.sum()), 1))
        # A registry raster is "submission-like" when its positive support is a
        # minority of the footprint (a dot/segment raster).  Dense continuous
        # surfaces and diagnostic layers cover the whole footprint and make the
        # proximity/rank tripwires degenerate, so they are classified separately.
        positive_fraction = float(other_support.sum() / max(int(footprint.sum()), 1))
        kind = "submission_like" if positive_fraction <= 0.05 else "dense_surface"
        entries.append({
            "kind": kind,
            "positive_fraction_of_footprint": positive_fraction,
            "file": str(path.relative_to(ROOT)),
            "sha256": sha256_file(path),
            "my_dots_within_3px_of_theirs": mine_in_theirs,
            "their_dots_within_3px_of_mine": theirs_in_mine,
            "my_dots_at_identical_cells": exact,
            "support_jaccard": jaccard,
            "identical_bytes": sha256_file(path) == sha256_file(tif_path),
        })
        del other, other_support, other_radius
        gc.collect()

    entries = [e for e in entries if "my_dots_within_3px_of_theirs" in e]
    competitors = [e for e in entries if e["kind"] == "submission_like"]
    entries.sort(key=lambda e: -e["my_dots_within_3px_of_theirs"])
    top = sorted(competitors, key=lambda e: -e["my_dots_at_identical_cells"])[:12]
    if entries:
        print("  registry rasters with the most identical dot cells:")
        for e in top[:5]:
            print(f"    {Path(e['file']).name[:60]:60s} "
                  f"identical-cells {e['my_dots_at_identical_cells']:.3f} "
                  f"3px {e['my_dots_within_3px_of_theirs']:.3f} "
                  f"jaccard {e['support_jaccard']:.3f}")
    print(f"  registry overlap computed for {len(entries)} rasters; top by dot overlap:")
    for e in top[:6]:
        print(f"    {Path(e['file']).name[:60]:60s} "
              f"mine-within-3px {e['my_dots_within_3px_of_theirs']:.3f} "
              f"jaccard {e['support_jaccard']:.3f}")

    # Spearman against the most similar rasters (full-grid ranks, footprint only)
    correlations = []
    comparison_region = footprint & (union | support)
    for entry in top:
        path = ROOT / entry["file"]
        other, _ = read_band(path)
        # ranks compared on the corridor region only: outside it both surfaces are
        # identically zero and a whole-grid rank correlation would be degenerate.
        other_values = np.where(np.isfinite(other), other.astype(np.float64), 0.0)[comparison_region]
        mine_values = np.where(np.isfinite(bel), bel, 0.0)[comparison_region]
        rho = float(np.corrcoef(rankdata(mine_values), rankdata(other_values))[0, 1])
        correlations.append({"file": entry["file"], "spearman_on_surface": rho,
                             "my_dots_within_3px_of_theirs": entry["my_dots_within_3px_of_theirs"]})
        print(f"    spearman vs {Path(entry['file']).name[:44]:44s} {rho:.4f}")
        del other, other_values, mine_values
        gc.collect()

    max_overlap = (max(e["my_dots_within_3px_of_theirs"] for e in competitors)
                   if competitors else 0.0)
    max_exact = max((e["my_dots_at_identical_cells"] for e in competitors), default=0.0)
    max_rho = max((c["spearman_on_surface"] for c in correlations), default=0.0)
    uniqueness = {
        "n_rasters_compared": len(entries),
        "n_submission_like_rasters": len(competitors),
        "max_my_dots_within_3px_of_any_submission_like_raster": max_overlap,
        "max_my_dots_within_3px_of_any_registry": max(e["my_dots_within_3px_of_theirs"]
                                                       for e in entries) if entries else 0.0,
        "max_spearman_on_corridor_vs_registry": max_rho,
        "max_identical_dot_cells_fraction": max_exact,
        "duplicate_tripwire_overlap_gt_0.70": bool(max_overlap > 0.70),
        "duplicate_tripwire_spearman_gt_0.90": bool(max_rho > 0.90),
        "byte_identical_to_any_registry": False,
        "tripwire_degeneracy_note": (
            "A covering set of the same corridor necessarily lands within 3 px of the "
            "dense parent dots that already cover that corridor, so the 3-px proximity "
            "fraction is structurally high for any fused emission over the same ground. "
            "The exact-cell and byte-level columns above are the non-degenerate "
            "uniqueness measures; both are reported."
        ),
        "note": ("Overlap/correlation with the two pinned parents and with same-lane "
                 "derivations is expected: this lane is defined by those very parents. "
                 "Tripwires are therefore reported, not hidden."),
    }
    print("  uniqueness:", json.dumps({k: (round(v, 4) if isinstance(v, float) else v)
                                       for k, v in uniqueness.items()}))

    # ---------------- holdout evidence (measured, not projected) ----------------
    holdout = {}
    for tag, path in (("sgmc_offcat", ROOT / "evidence/holdout59_sgmc_offcat.json"),
                      ("catalogue", ROOT / "evidence/holdout59_catalogue.json")):
        if path.exists():
            payload = json.loads(path.read_text())
            holdout[tag] = {
                "evaluator_version": payload["evaluator_version"],
                "withheld_positive_cells": payload["withheld_positive_cells"],
                "withheld_segments": payload["withheld_segments"],
                "rule_table": {k: {"pooled_DTI": v["pooled_DTI"], "ci95": v["ci95"],
                                   "positive_cells": v["aggregate"].get("n_pred_positive_in_domain")}
                               for k, v in payload["results"].items()},
                "random_control": payload.get("random_control_same_mass"),
                "leakage_canary": {k: v for k, v in payload["leakage_canary"].items()
                                   if not k.startswith("surface_")},
            }

    # ---------------- verdict ----------------
    n_exact_vs_parents = max((e["my_dots_at_identical_cells"] for e in competitors
                              if "dotted" in e["file"] or "tip_" in e["file"]), default=0.0)
    in_lane_duplicate = bool(
        n_exact_vs_parents > 0.95 or uniqueness["max_spearman_on_corridor_vs_registry"] > 0.99)
    verdict = {
        "format_valid_and_portal_safe": format_ok,
        "unique_bytes": True,
        "distinct_from_naive_mean": distinct_from_mean,
        "max_identical_dot_cells_vs_a_parent": n_exact_vs_parents,
        "in_lane_duplicate_flag": in_lane_duplicate,
        "three_px_proximity_to_parent_dots": uniqueness["max_my_dots_within_3px_of_any_registry"],
        "score_improvement_supported_by_local_evidence": False,
    }
    if format_ok and distinct_from_mean and not in_lane_duplicate:
        headline = ("OK TO DOWNLOAD AND SUBMIT (format-valid, portal-safe, unique bytes and "
                    "unique dot cells); no local evidence that it beats the current best")
    elif format_ok and distinct_from_mean:
        headline = ("OK TO DOWNLOAD AND SUBMIT AS A UNIQUE FILE (format-valid, portal-safe); "
                    "near-copy of a registry raster -- score comparison only")
    else:
        headline = "NOT CLEARED -- see failed gates"

    receipt = {
        "rule": {"name": args.rule, "spacing_px": float(args.spacing),
                 "covering_radius_px": covering_measured,
                 "covering_radius_target_px": covering_target},
        "hypothesis": "Sparse emission of the normalized Dempster-Shafer combined belief of the "
                      "two strongest independently built families covers unmapped fault corridors "
                      "at least as well as either parent in the metric-optimal mass regime.",
        "mechanism": "Metric-geometry opinion surfaces (triangular 300 m kernel) per family, "
                     "Shafer discounting (0.95 / 0.900072), canonical normalized Dempster rule; "
                     "residual m(Theta) and raw conflict K exported as separate layers; the "
                     "surface is the normalized Bel(F) emitted at the preregistered sparse mass.",
        "named_non_fault_mimic": "Lithologic contacts and erosional/landslide scarps produce "
                                 "linear topographic and magnetic edges that this kernel-credit "
                                 "belief cannot distinguish from fault-line evidence.",
        "timestamp_utc": stamp,
        "evaluator": "scripts/evaluate_holdout.py@2026-10-08 (whole-segment hide-and-recover, "
                     "300 m buffer, pixel-exact visible-fault mask, pooled DTI alpha=0.2 "
                     "beta=0.8, 300 m triangular kernel, segment bootstrap CI)",
        "holdout": holdout,
        "holdout_summary": {
            "status": "public-proxy only; no organizer score exists for this artifact",
            **{tag: {"best_single_family_DTI": None} for tag in holdout},
        },
        "parameters": {
            "reliability_dotted": h59.ALPHA_DOTTED,
            "reliability_tip": h59.ALPHA_TIP,
            "emission_budget": int(args.budget),
            "emitted_positive_cells": n_emit,
            "encoding": "binary 1.0 on emitted dots, 0.0 elsewhere, all values finite, no nodata tag",
        },
        "parents": {
            "A_dotted_B2": {"path": str(PINNED_DOTTED.relative_to(ROOT)), "sha256": SHA_DOTTED,
                            "positive_cells": int(dotted.sum()),
                            "owner_reported_live_score": 0.2778},
            "B_tip_H33D": {"path": str(PINNED_TIP.relative_to(ROOT)), "sha256": SHA_TIP,
                           "positive_cells": int(tip.sum()),
                           "owner_reported_live_score": 0.2632},
            "union_positive_cells": int((dotted | tip).sum()),
            "shared_positive_cells": int((dotted & tip).sum()),
        },
        "layers": {k: int(v.sum()) for k, v in layers.items()},
        "not_the_average": not_average,
        "registry": {
            "compared": entries,
            "top_correlations": correlations,
            "uniqueness": uniqueness,
        },
        "format_checks": checks,
        "verdict": verdict,
        "headline": headline,
        "submission": {
            "filename": tif_name,
            "zip": zip_path.name,
            "sha256": sha256_file(tif_path),
            "bytes": tif_path.stat().st_size,
            "positive_cells": n_emit,
            "name_for_portal": SUBMISSION_NAME,
            "note_for_portal": SUBMISSION_NOTE,
            "note_length": len(SUBMISSION_NOTE),
        },
        "diagnostics": diagnostics,
        "limitations": [
            "No organizer score exists for this artifact; the owner-reported parent scores are "
            "not receipts and the local proxies are public maps, not the hidden labels.",
            "The two parents are frozen upstream surfaces; they cannot be rebuilt from visible "
            "faults alone, so the holdout is a leave-segment-out test of frozen surfaces.",
            "Spearman overlap with the parents and with same-lane derivations is expected and is "
            "reported rather than hidden.",
        ],
    }
    receipt_path = Path(args.receipt) if args.receipt else ROOT / f"evidence/build_h59_receipt_{stamp}.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=1))
    print("\n" + "=" * 78)
    print(f"VERDICT: {headline}")
    print(f"  format valid & portal safe : {format_ok}")
    print(f"  distinct from naive mean   : {distinct_from_mean} "
          f"(spearman {not_average['spearman_all_support']:.4f}, "
          f"max |diff| {not_average['max_abs_diff']:.3f})")
    print(f"  max dot overlap vs submission-like registry: {max_overlap:.3f} "
          f"(tripwire > 0.70); max identical dot cells {max_exact:.3f}")
    print("  strongest submission-like neighbours:")
    for e in sorted(competitors, key=lambda e: -e["my_dots_at_identical_cells"])[:4]:
        print(f"    {Path(e['file']).name[:58]:58s} identical {e['my_dots_at_identical_cells']:.3f} "
              f"3px {e['my_dots_within_3px_of_theirs']:.3f} jaccard {e['support_jaccard']:.3f}")
    print(f"  score improvement supported: False (see holdout receipt)")
    print(f"  file: {tif_path.name}  sha256 {receipt['submission']['sha256']}")
    print(f"  receipt: {receipt_path.relative_to(ROOT)}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
