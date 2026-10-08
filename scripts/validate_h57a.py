#!/usr/bin/env python3
"""Build and spatially score the frozen H57-A screen without creating a submission.

H57-A is preregistered in docs/research/hypotheses-h57-20261007.md. It fits a
robust K~Th line over valid GeoDAWN cells, requires a high positive residual and a
high gradient in TMI-up150, ranks by their product, and adds at most 2,000 cells
to the frozen H49 surface. A small same-pool random-addition control checks whether
the feature ranking carries proxy information beyond the conjunction itself.

The four-quadrant protocol and metric are shared with scripts/run_spatial_holdout.py.
This is a public-proxy diagnostic on frozen surfaces, not a private-label score,
not an organizer file-to-score link, and not a submission or slot-clearance tool.
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
for entry in (ROOT / "src", ROOT / "scripts"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from gemsdoe48.geotiff import assert_competition_grid, assert_same_grid  # noqa: E402
from gemsdoe48.h57a import (  # noqa: E402
    deterministic_top_k,
    fit_huber_line,
    magnetic_gradient_magnitude,
    make_addition_surface,
    robust_residual_z,
)
from gemsdoe48.metric import distance_weighted_tversky  # noqa: E402
from run_spatial_holdout import fold_domain, quadrants  # noqa: E402

RAD = ROOT / "data/source_mirrors/geodawn_rad_u8.tif"
EXT = ROOT / "data/raw/external/geodawn_extensions_u8.tif"
FOOTPRINT_PATH = ROOT / "data/source_mirrors/footprint-mask.tif"
LABELS = ROOT / "data/raw/labels_catalogue.tif"
SGMC = ROOT / "data/official/derived_sgmc_faults_100m.tif"
H49 = ROOT / "docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif"
H49_REFERENCE = ROOT / "evidence/holdout_h56_h49_reference_20261007.json"

PINS = {
    "radiometrics": "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682",
    "geodawn_extensions": "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b",
    "footprint": "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f",
    "catalogue_labels": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "sgmc": "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0",
    "h49_reference": "9f028289c364c071065245799d7ed131600e80e9f0d10602806b12ce34d7cae8",
}
BUDGET = 2_000
GRADIENT_QUANTILE = 75.0
RESIDUAL_Z_MIN = 2.0
RANDOM_SEED = 20261007


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_array(array: np.ndarray) -> str:
    """Hash a C-order little-endian canonical array representation."""
    canonical = np.asarray(array, dtype=np.dtype(array.dtype).newbyteorder("<"), order="C")
    return hashlib.sha256(canonical.tobytes(order="C")).hexdigest()


def read_raster(path: Path) -> tuple[np.ndarray, dict, tuple[str | None, ...]]:
    with rasterio.open(path) as dataset:
        values = dataset.read()
        return values, dataset.profile.copy(), dataset.descriptions


def read_one(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as dataset:
        assert_competition_grid(dataset.profile, path=path)
        if dataset.count != 1:
            raise SystemExit(f"expected one band in {path}, got {dataset.count}")
        return dataset.read(1), dataset.profile.copy()


def assert_grid_geometry(profile_a: dict, profile_b: dict, *, name_a: str, name_b: str) -> None:
    """Compare geometry only; source rasters may have different band counts."""
    a, b = profile_a.copy(), profile_b.copy()
    a["count"] = b["count"] = 1
    assert_same_grid(a, b, name_a=name_a, name_b=name_b)


def require_pin(path: Path, name: str) -> str:
    got = sha256_file(path)
    expected = PINS[name]
    if got != expected:
        raise SystemExit(f"{name} SHA-256 mismatch: {got} != {expected} ({path})")
    return got


def make_contexts(
    truths: dict[str, np.ndarray], footprint: np.ndarray, blocks: dict[str, np.ndarray]
) -> dict[str, list[dict]]:
    """Cache exactly the local arrays consumed by run_spatial_holdout.score_fold."""
    contexts: dict[str, list[dict]] = {}
    for truth_name, truth in truths.items():
        rows = []
        for fold_name, core in blocks.items():
            domain = fold_domain(core, footprint, radius_m=300.0)
            y, x = np.nonzero(domain)
            if y.size == 0:
                raise ValueError(f"empty spatial fold {fold_name}")
            sl = (
                slice(max(0, int(y.min())), min(domain.shape[0], int(y.max()) + 1)),
                slice(max(0, int(x.min())), min(domain.shape[1], int(x.max()) + 1)),
            )
            rows.append({
                "fold": fold_name,
                "slice": sl,
                "domain": domain[sl],
                "core": core[sl],
                "truth": truth[sl] & core[sl],
            })
        contexts[truth_name] = rows
    return contexts


def score_surface(prediction: np.ndarray, contexts: dict[str, list[dict]]) -> dict[str, dict]:
    """Score a full frozen surface on the shared four-fold proxy protocol."""
    result: dict[str, dict] = {}
    for truth_name, folds in contexts.items():
        per_fold = {}
        for context in folds:
            sl = context["slice"]
            local_domain = context["domain"]
            local_prediction = np.where(local_domain, prediction[sl], 0.0).astype(np.float64)
            scored = distance_weighted_tversky(
                local_prediction,
                context["truth"],
                valid=local_domain,
                radius_m=300.0,
                pixel_size_m=100.0,
                alpha=0.2,
                beta=0.8,
            )
            scored["prediction_mass"] = float(local_prediction[local_domain].sum(dtype=np.float64))
            scored["positive_cells"] = int(np.count_nonzero(local_prediction[local_domain] > 0.0))
            scored["valid_domain_cells"] = int(local_domain.sum())
            per_fold[context["fold"]] = scored
        per_fold["mean_dti"] = float(np.mean([per_fold[row["fold"]]["dti"] for row in folds]))
        result[truth_name] = per_fold
    return result


def compare_to_h49(candidate: dict[str, dict], baseline: dict[str, dict]) -> dict[str, dict]:
    comparisons: dict[str, dict] = {}
    for truth_name, candidate_result in candidate.items():
        baseline_result = baseline[truth_name]
        folds = [name for name in ("NW", "NE", "SW", "SE")]
        deltas = {
            name: float(candidate_result[name]["dti"] - baseline_result[name]["dti"])
            for name in folds
        }
        comparisons[truth_name] = {
            "fold_delta_dti_vs_h49": deltas,
            "mean_delta_dti_vs_h49": float(np.mean(list(deltas.values()))),
            "positive_folds": int(sum(delta > 0.0 for delta in deltas.values())),
            "passes_numeric_gate": bool(np.mean(list(deltas.values())) > 0.0 and sum(delta > 0.0 for delta in deltas.values()) >= 3),
        }
    return comparisons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "evidence/holdout_h57a_20261007.json",
    )
    parser.add_argument(
        "--random-controls", type=int, default=8,
        help="same-pool random additions to compare against feature ranking (default: 8)",
    )
    args = parser.parse_args()
    if args.random_controls < 0:
        raise SystemExit("--random-controls must be nonnegative")

    paths = {
        "radiometrics": RAD,
        "geodawn_extensions": EXT,
        "footprint": FOOTPRINT_PATH,
        "catalogue_labels": LABELS,
        "sgmc": SGMC,
        "h49_reference": H49,
    }
    for name, path in paths.items():
        if not path.exists():
            raise SystemExit(f"missing {name} input: {path}")
    hashes = {name: require_pin(path, name) for name, path in paths.items()}

    rad_bands, rad_profile, rad_names = read_raster(RAD)
    ext_bands, ext_profile, ext_names = read_raster(EXT)
    if len(rad_names) != 4 or not {"K", "Th"}.issubset(set(rad_names)):
        raise SystemExit(f"GeoDAWN radiometric descriptions lack K/Th: {rad_names}")
    if len(ext_names) != 4 or "TMI_up150" not in ext_names:
        raise SystemExit(f"GeoDAWN extension lacks TMI_up150: {ext_names}")
    assert_grid_geometry(rad_profile, ext_profile, name_a=str(RAD), name_b=str(EXT))
    k = rad_bands[rad_names.index("K")]
    th = rad_bands[rad_names.index("Th")]
    tmi = ext_bands[ext_names.index("TMI_up150")]

    footprint_raw, footprint_profile = read_one(FOOTPRINT_PATH)
    labels, labels_profile = read_one(LABELS)
    sgmc, sgmc_profile = read_one(SGMC)
    baseline_raw, baseline_profile = read_one(H49)
    for profile, path in (
        (footprint_profile, FOOTPRINT_PATH), (labels_profile, LABELS),
        (sgmc_profile, SGMC), (baseline_profile, H49),
    ):
        assert_grid_geometry(rad_profile, profile, name_a=str(RAD), name_b=str(path))

    footprint = footprint_raw == 1
    if not np.array_equal(footprint, labels != -1):
        raise SystemExit("footprint mask differs from label nodata support")
    catalogue = (labels == 1) & footprint
    if int(catalogue.sum()) != 60_988:
        raise SystemExit("pinned catalogue mask positive count changed")
    baseline = np.nan_to_num(baseline_raw.astype(np.float32), nan=0.0)
    if not np.isfinite(baseline).all() or np.any((baseline < 0.0) | (baseline > 1.0)):
        raise SystemExit("H49 reference must be finite in [0,1] after outside NaN fill")
    if np.any(baseline[~footprint] != 0.0):
        raise SystemExit("H49 reference has nonzero values outside the registered footprint")

    rad_valid = (k > 0) & (th > 0)
    tmi_valid = tmi > 0
    gradient, gradient_valid = magnetic_gradient_magnitude(tmi, tmi_valid, pixel_size_m=100.0)
    common_valid = footprint & rad_valid & gradient_valid
    if int(common_valid.sum()) < 100_000:
        raise SystemExit(f"too few common valid pixels for H57-A: {int(common_valid.sum())}")

    fit = fit_huber_line(th[common_valid], k[common_valid], max_iter=5, huber_c=1.345)
    residual_z = robust_residual_z(th, k, fit, common_valid)
    gradient_cut = float(np.percentile(gradient[common_valid], GRADIENT_QUANTILE))
    if not np.isfinite(gradient_cut) or gradient_cut < 0.0:
        raise SystemExit("invalid gradient p75 cutoff")

    candidate_pool = (
        common_valid
        & (residual_z >= RESIDUAL_Z_MIN)
        & (gradient > 0.0)
        & (gradient >= gradient_cut)
        & (baseline <= 0.0)
    )
    rank_score = residual_z * gradient
    additions = deterministic_top_k(rank_score, candidate_pool, BUDGET)
    candidate = make_addition_surface(baseline, additions, footprint)
    addition_count = int(additions.sum())
    if np.any(candidate[footprint & ~additions] != baseline[footprint & ~additions]):
        raise AssertionError("candidate changed baseline outside the selected additions")

    dcat = distance_transform_edt(~catalogue, sampling=(100.0, 100.0))
    catalogue_truth = catalogue
    sgmc_offcat_truth = (sgmc > 0) & footprint & (dcat > 300.0)
    truths = {
        "catalogue_proxy": catalogue_truth,
        "sgmc_off_catalogue_gt300m": sgmc_offcat_truth,
    }
    blocks = quadrants(*footprint.shape)
    contexts = make_contexts(truths, footprint, blocks)
    scored_baseline = score_surface(baseline.astype(np.float64), contexts)
    scored_candidate = score_surface(candidate.astype(np.float64), contexts)

    # Guard the implementation against fold, crop, kernel or metric drift.
    frozen_reference = json.loads(H49_REFERENCE.read_text(encoding="utf-8"))
    for truth_key, receipt_key in (("catalogue_proxy", "catalogue"), ("sgmc_off_catalogue_gt300m", "sgmc_off_catalogue_results")):
        stored = frozen_reference["results" if receipt_key == "catalogue" else receipt_key]["h49_balanced_same_protocol_reference"]
        for fold in ("NW", "NE", "SW", "SE"):
            expected = float(stored[fold]["dti"])
            actual = float(scored_baseline[truth_key][fold]["dti"])
            if not np.isclose(actual, expected, rtol=0.0, atol=1e-10):
                raise SystemExit(f"H49 baseline drift in {truth_key}/{fold}: {actual} != {expected}")

    paired = compare_to_h49(scored_candidate, scored_baseline)
    controls = []
    pool_indices = np.flatnonzero(candidate_pool.ravel())
    rng = np.random.default_rng(RANDOM_SEED)
    for control_i in range(args.random_controls):
        random_mask = np.zeros(candidate_pool.size, dtype=bool)
        if addition_count:
            if pool_indices.size < addition_count:
                raise AssertionError("random-control pool smaller than selected addition count")
            chosen = rng.choice(pool_indices, size=addition_count, replace=False)
            random_mask[chosen] = True
        random_mask = random_mask.reshape(candidate_pool.shape)
        random_candidate = make_addition_surface(baseline, random_mask, footprint)
        scored_random = score_surface(random_candidate.astype(np.float64), contexts)
        controls.append({
            "seed_index": control_i,
            "selected_mask_sha256": sha256_array(random_mask.astype(np.uint8)),
            "results": scored_random,
            "paired_vs_h49": compare_to_h49(scored_random, scored_baseline),
        })

    control_summary = {}
    for truth_name in truths:
        means = [row["results"][truth_name]["mean_dti"] for row in controls]
        feature_mean = scored_candidate[truth_name]["mean_dti"]
        control_summary[truth_name] = {
            "feature_rank_mean_dti": feature_mean,
            "random_same_pool_mean_dti": float(np.mean(means)) if means else None,
            "feature_minus_random_mean": float(feature_mean - np.mean(means)) if means else None,
            "random_draws_at_or_below_feature": int(sum(value <= feature_mean for value in means)),
            "random_draws": len(means),
            "warning": "small descriptive control sample; not a significance test",
        }

    report = {
        "schema_version": 1,
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PUBLIC_PROXY_HOLDOUT_ONLY_NOT_SLOT_CLEARED",
        "preregistration": "docs/research/hypotheses-h57-20261007.md#h57-a-preregistration--residual-k--tmi-up150-gradient",
        "candidate": {
            "name": "H57-A K-Th residual x TMI_up150 gradient, H49 + up to 2000 additions",
            "construction": "label-free K~Th residual and TMI-up150 gradient; fixed thresholds and budget from frozen H57 slate; H49 values are preserved; no candidate TIFF is written",
            "baseline_h49_sha256": hashes["h49_reference"],
            "baseline_logical_sha256": sha256_array(baseline.astype(np.float32)),
            "addition_mask_sha256": sha256_array(additions.astype(np.uint8)),
            "candidate_logical_sha256": sha256_array(candidate.astype(np.float32)),
            "addition_count": addition_count,
            "candidate_pool_count": int(candidate_pool.sum()),
            "positive_cells_in_footprint": int(np.count_nonzero(candidate[footprint] > 0.0)),
        },
        "inputs": {
            name: {"path": str(path.relative_to(ROOT)), "sha256": hashes[name]}
            for name, path in paths.items()
        },
        "feature_fit": {
            "k_band": rad_names.index("K") + 1,
            "th_band": rad_names.index("Th") + 1,
            "magnetic_band": ext_names.index("TMI_up150") + 1,
            "huber_intercept_quantized_units": fit.intercept,
            "huber_slope_quantized_units": fit.slope,
            "huber_iterations": fit.iterations,
            "fit_valid_pixels": int(common_valid.sum()),
            "residual_mad_scale": fit.residual_scale,
            "residual_z_threshold": RESIDUAL_Z_MIN,
            "gradient_p75_cutoff_quantized_units_per_m": gradient_cut,
            "gradient_p75": GRADIENT_QUANTILE,
            "candidate_budget": BUDGET,
            "rank_score": "positive_K_Th_residual_z * TMI_up150_gradient_magnitude; descending; ties row-major",
            "edge_nodata_handling": "3x3 erosion of TMI-valid mask before gradient cells are considered",
            "catalogue_mask_used_for_feature_selection": False,
            "holdout_truth_used_for_feature_selection": False,
        },
        "truth_sources": {
            "catalogue_proxy": {
                "path": str(LABELS.relative_to(ROOT)),
                "sha256": hashes["catalogue_labels"],
                "positive_pixels": int(catalogue_truth.sum()),
                "is_private_expert_truth": False,
            },
            "sgmc_off_catalogue_gt300m": {
                "path": str(SGMC.relative_to(ROOT)),
                "sha256": hashes["sgmc"],
                "positive_pixels": int(sgmc_offcat_truth.sum()),
                "definition": "SGMC positives inside footprint and >300 m Euclidean distance from any catalogue-positive cell",
                "is_private_expert_truth": False,
            },
        },
        "fold_protocol": {
            "source_implementation": "scripts/run_spatial_holdout.py:quadrants, fold_domain, official distance_weighted_tversky metric",
            "geometry": "four fixed NW/NE/SW/SE blocks split at the full raster row/column midpoint",
            "radius_m": 300,
            "pixel_size_m": 100,
            "alpha": 0.2,
            "beta": 0.8,
            "halo": "300 m around each held-out core, clipped to footprint; only core truth scored",
            "surface_retrained_within_folds": False,
        },
        "results": {
            "H49_reference": scored_baseline,
            "H57A_candidate": scored_candidate,
        },
        "paired_vs_current_comparable_best_H49": paired,
        "same_candidate_pool_random_controls": controls,
        "feature_ranking_control_summary": control_summary,
        "numeric_proxy_gate": {
            "rule": "mean paired delta > 0 and >=3/4 positive folds on both truth proxies",
            "passed_both_truths": bool(all(row["passes_numeric_gate"] for row in paired.values())),
        },
        "download_verdict": "NO H57-A TIFF generated; this is an evidence-only research test, not a download artifact",
        "submit_verdict": "NOT CLEARED / DO NOT SUBMIT",
        "slot_decision": {
            "cleared": False,
            "reason": "Public map proxies and frozen, potentially label-informed H49 surfaces cannot authorize a weekly slot or establish private expert-label performance; external mirror provenance/licence and portal acceptance also remain unresolved.",
        },
        "caveats": [
            "GeoDAWN inputs are hash-pinned third-party owner mirrors; hashes do not authenticate them with the organizer or verify sponsor-sharing rights.",
            "Radiometric and TMI extension bands are uint8 quantized relative signals, not calibrated physical units.",
            "The feature fit and p75 threshold use the full unlabeled feature grid, not a fold-local fit; no public target labels are used in H57-A feature selection.",
            "The H49 reference is a frozen upstream surface that used public catalogue-derived evidence; the holdout is conditional and not an independent end-to-end retraining test.",
            "Catalogue/SGMC targets are public-map proxies, not private expert labels or competition scores.",
            "No organizer receipt links a leaderboard row to the H49 or any H57-A TIFF bytes.",
            "The random-control sample is small and descriptive, not a statistical significance claim.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("H57-A mean DTI by truth:")
    for truth_name in truths:
        print(
            f"  {truth_name}: candidate={scored_candidate[truth_name]['mean_dti']:.6f} "
            f"H49={scored_baseline[truth_name]['mean_dti']:.6f} "
            f"delta={paired[truth_name]['mean_delta_dti_vs_h49']:+.6f} "
            f"wins={paired[truth_name]['positive_folds']}/4"
        )
    print("numeric proxy gate passed:", report["numeric_proxy_gate"]["passed_both_truths"])
    print("submit verdict:", report["submit_verdict"])
    print("receipt:", args.output.relative_to(ROOT) if args.output.is_relative_to(ROOT) else args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
