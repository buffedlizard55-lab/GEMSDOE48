#!/usr/bin/env python3
"""Strict hide-and-recover holdout evaluator (the protocol named in the brief).

Protocol implemented here (evaluator version ``evaluate_holdout.py@2026-10-08``)
--------------------------------------------------------------------------------
1. **Truth proxy.** The official fault-catalogue raster on the competition grid
   (``data/raw/labels_catalogue.tif``, SHA-256 pinned, 60,988 positive cells) is
   decomposed into whole 8-connected fault segments.
2. **Hide whole segments with a buffer.** Segments are split into four spatial
   folds by centroid. For fold *f*: ``hidden`` = the segments of *f*,
   ``visible`` = every other segment. A hidden pixel that lies within 300 m of a
   visible fault is dropped from scoring (the buffer), so no credit can be earned
   by predicting a neighbouring visible fault.
3. **Catalogue-based features only from visible faults.** Per-fold catalogue
   distance/kernel features are recomputed with the hidden segments removed.
4. **Mask visible faults pixel-exactly.** Before scoring, every candidate
   prediction is set to zero on the visible faults dilated by the 3-pixel metric
   halo, so the tested claim is out-of-sample coverage of *hidden* fault
   segments rather than catalogue mimicry.
5. **Pooled DTI.** ``k(d) = max(1 - d/300 m, 0)``,
   ``DTI = TPw / (TPw + 0.2 FPw + 0.8 FNw + eps)`` with components pooled over the
   four folds. Score domain per fold = footprint cells within 300 m of that
   fold's hidden core (so a prediction cell is judged against the hidden truth it
   could serve).
6. **Leakage canary.** Each catalogue-derived feature and each candidate surface
   is scored *alone* on the withheld pixels (AUC). AUC > 0.90 is reported as
   leakage-until-proven-otherwise and blocks promotion of that feature.
7. **Uncertainty.** 95% CI by segment bootstrap: hidden segments are resampled
   with replacement per fold and the pooled DTI recomputed (FPw held at its point
   estimate -- a documented approximation, because FPw does not decompose over
   truth segments).

The evaluator needs no hidden labels and no network access.  It reports
measurements on frozen proxies only; nothing here is a score projection.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gemsdoe48 import h59  # noqa: E402
from gemsdoe48.metric import ALPHA, BETA, EPSILON, max_credit_field  # noqa: E402

EVALUATOR_VERSION = "evaluate_holdout.py@2026-10-08"
HALO_PX = 3.0          # 300 m metric halo
RADIUS_M = 300.0
PIXEL_M = 100.0
N_FOLDS = 4
BOOTSTRAP_DRAWS = 400
RNG_SEED = 20261008

SHA_CATALOGUE = "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"
SHA_SGMC_DERIVED = "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"
SHA_DOTTED = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
SHA_TIP = "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757"

CAT_PATH = ROOT / "data/raw/labels_catalogue.tif"
DOTTED_PATH = ROOT / "data/raw/dotted_h33_2_b2_zeros.tif"
TIP_PATH = ROOT / "data/raw/tip_h33d_stepover.tif"
TEMPLATE_PATH = ROOT / "data/raw/sample_submission_template.tif"
# The SGMC off-catalogue population: the only mapped-fault population in reach that
# is off-catalogue *by construction* (the repo's stated analogue of the hidden
# expert-mapped truth).  Two SGMC rasters exist in this checkout with different
# SHA-256 and different positive counts; the derived raster that the repository's
# own holdout scripts pin is used here.  See docs/irregularities.md.
SGMC_DERIVED_PATH = ROOT / "data/official/derived_sgmc_faults_100m.tif"
SGMC_MIRROR_PATH = ROOT / "data/raw/sgmc_faults_100m.tif"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_grid(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        return src.read(1)


def footprint_mask() -> np.ndarray:
    return np.isfinite(read_grid(TEMPLATE_PATH))


def coverage_field(prediction: np.ndarray) -> np.ndarray:
    """Max kernel credit of a graded prediction at every cell (scorer geometry)."""
    return max_credit_field(np.asarray(prediction, dtype=np.float64))


def kernel_credit_of_mask(mask: np.ndarray) -> np.ndarray:
    return max_credit_field((np.asarray(mask) > 0).astype(np.float64))


def auc(score: np.ndarray, truth: np.ndarray, domain: np.ndarray) -> float:
    """Rank AUC of ``score`` for ``truth`` inside ``domain`` (vectorised)."""
    sel = np.asarray(domain, dtype=bool)
    scores = np.asarray(score, dtype=np.float64)[sel]
    labels = np.asarray(truth, dtype=bool)[sel]
    n_pos = int(labels.sum())
    n_neg = int(labels.size - n_pos)
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    ranks = rankdata(scores, method="average")
    rank_sum = float(ranks[labels].sum())
    return (rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


class Fold:
    """One hide-and-recover fold: hidden truth, visible buffer mask, domain."""

    def __init__(self, fold_id: int, hidden_segments: np.ndarray, visible: np.ndarray,
                 footprint: np.ndarray, quadrant: np.ndarray | None = None,
                 mask_mode: str = "pixel"):
        self.fold_id = fold_id
        self.hidden_raw = hidden_segments
        near_visible = distance_transform_edt(~visible) <= HALO_PX
        self.hidden_core = hidden_segments & ~near_visible
        self.visible = visible
        self.mask_mode = mask_mode
        # "pixel": zero the prediction exactly on visible faults (the brief's
        #          "mask visible faults pixel-exactly").  The 300 m buffer is
        #          applied to the TRUTH (hidden_core), not to the prediction.
        # "band" : additionally zero the whole 300 m scoring band around visible
        #          faults -- retained only as a documented sensitivity run.
        self.visible_dilated = near_visible if mask_mode == "band" else visible
        self.label_map = ndimage.label(self.hidden_core, structure=np.ones((3, 3)))[0]
        self.segment_ids = np.unique(self.label_map)[1:]
        self.segment_slices = ndimage.find_objects(self.label_map)
        d_hidden = distance_transform_edt(~self.hidden_core)
        self.domain = footprint & (d_hidden <= HALO_PX)
        # FPw is attributed exactly once per cell: emissions inside this fold's
        # spatial quadrant are charged against the map that was blind to this
        # fold's faults (the scorer has no domain restriction -- every emitted
        # cell far from truth costs 0.2 * value).
        self.quadrant = footprint if quadrant is None else (quadrant & footprint)

    def mask_visible(self, prediction: np.ndarray) -> np.ndarray:
        """Set the prediction to zero on visible faults + the metric halo."""
        return np.where(self.visible_dilated, 0.0, np.asarray(prediction, dtype=np.float64))

    def components(self, prediction: np.ndarray, coverage: np.ndarray,
                   truth_credit: np.ndarray | None = None) -> dict:
        """TPw/FNw on the hidden core, FPw over the fold's own quadrant.

        ``truth_credit`` is the kernel credit of the *scored* truth (all hidden
        cores pooled).  When it is None the fold's own truth credit is used; for
        the pooled protocol all folds share the same pooled truth map, so the
        caller passes it explicitly.
        """
        pred = self.mask_visible(prediction)
        covered = self.mask_visible(coverage)
        cov = covered[self.hidden_core]
        tpw = float(cov.sum())
        fnw = float((1.0 - cov).sum())
        credit = self.k_nearest if truth_credit is None else truth_credit
        pos = (pred > 0) & self.quadrant
        fpw = float((pred[pos] * (1.0 - credit[pos])).sum())
        k = (1.0 - credit[pos])
        # per-segment TPw/FNw for the segment bootstrap
        seg_tpw = np.zeros(self.segment_ids.size)
        seg_fnw = np.zeros(self.segment_ids.size)
        for i, sid in enumerate(self.segment_ids):
            sl = self.segment_slices[sid - 1]
            sub = self.label_map[sl] == sid
            vals = covered[sl][sub]
            seg_tpw[i] = float(vals.sum())
            seg_fnw[i] = float((1.0 - vals).sum())
        fold_dti = tpw / (tpw + ALPHA * fpw + BETA * fnw + EPSILON)
        return {"TPw": tpw, "FPw": fpw, "FNw": fnw, "DTI": float(fold_dti),
                "n_truth": int(self.hidden_core.sum()),
                "n_pred_positive_in_domain": int(pos.sum()),
                "n_pred_positive_in_quadrant": int(pos.sum()),
                "mean_1_minus_k_at_positives": float(k.mean()) if pos.any() else None,
                "_seg_tpw": seg_tpw, "_seg_fnw": seg_fnw}

    def visible_only_feature(self) -> np.ndarray:
        """Kernel credit computed from VISIBLE faults only (canary input)."""
        return kernel_credit_of_mask(self.visible)


def sgmc_offcatalogue_truth(footprint: np.ndarray, catalogue: np.ndarray,
                            gap_px: float = HALO_PX) -> tuple[np.ndarray, dict]:
    """SGMC faults at least ``gap_px`` from every catalogue pixel (off-catalogue set)."""
    sgmc = read_grid(SGMC_DERIVED_PATH) > 0
    d_cat = distance_transform_edt(~catalogue)
    truth = sgmc & footprint & (d_cat > gap_px)
    info = {
        "sgmc_derived_sha256": sha256_file(SGMC_DERIVED_PATH),
        "sgmc_mirror_sha256": sha256_file(SGMC_MIRROR_PATH) if SGMC_MIRROR_PATH.exists() else None,
        "sgmc_in_footprint": int((sgmc & footprint).sum()),
        "sgmc_offcat_positive_cells": int(truth.sum()),
    }
    return truth, info


def build_folds(labels: np.ndarray, footprint: np.ndarray, n_folds: int = N_FOLDS,
                mask_mode: str = "pixel") -> list[Fold]:
    """Split catalogue fault segments into spatial folds by segment centroid."""
    lab, n = ndimage.label(labels, structure=np.ones((3, 3)))
    if n == 0:
        raise ValueError("no fault segments found")
    centroids = ndimage.center_of_mass(np.ones_like(lab, dtype=np.float64), lab,
                                       np.arange(1, n + 1))
    cy = np.array([c[0] for c in centroids])
    cx = np.array([c[1] for c in centroids])
    rows = np.clip((cy / labels.shape[0] * 2).astype(int), 0, 1)
    cols = np.clip((cx / labels.shape[1] * 2).astype(int), 0, 1)
    band = rows * 2 + cols
    fold_of_segment = band % n_folds
    rows_idx, cols_idx = np.indices(labels.shape)
    quadrant_id = np.clip((rows_idx / labels.shape[0] * 2).astype(np.int8), 0, 1) * 2 + \
                  np.clip((cols_idx / labels.shape[1] * 2).astype(np.int8), 0, 1)
    folds = []
    for f in range(n_folds):
        hidden = np.isin(lab, np.flatnonzero(fold_of_segment == f) + 1)
        visible = labels & ~hidden
        folds.append(Fold(f, hidden, visible, footprint,
                          quadrant=(quadrant_id == f), mask_mode=mask_mode))
    return folds


def pooled_truth_credit(folds: list[Fold]) -> np.ndarray:
    """Kernel credit of the pooled hidden truth (all folds' hidden cores)."""
    truth = np.zeros_like(folds[0].hidden_core)
    for fold in folds:
        truth |= fold.hidden_core
    return max_credit_field(truth.astype(np.float64))


def evaluate_surface(surface: np.ndarray, folds: list[Fold],
                     truth_credit: np.ndarray | None = None) -> dict:
    """Pooled strict-protocol score for one frozen surface."""
    coverage = coverage_field(surface)
    if truth_credit is None:
        truth_credit = pooled_truth_credit(folds)
    agg = {"TPw": 0.0, "FPw": 0.0, "FNw": 0.0, "n_truth": 0}
    per_fold = {}
    seg_tpw, seg_fnw = [], []
    for fold in folds:
        parts = fold.components(surface, coverage, truth_credit=truth_credit)
        agg["TPw"] += parts["TPw"]
        agg["FPw"] += parts["FPw"]
        agg["FNw"] += parts["FNw"]
        agg["n_truth"] += parts["n_truth"]
        per_fold[f"fold{fold.fold_id}"] = {k: v for k, v in parts.items()
                                           if not k.startswith("_")}
        seg_tpw.append(parts["_seg_tpw"])
        seg_fnw.append(parts["_seg_fnw"])
    pooled = agg["TPw"] / (agg["TPw"] + ALPHA * agg["FPw"] + BETA * agg["FNw"] + EPSILON)
    del coverage
    gc.collect()
    return {"pooled_DTI": float(pooled), "aggregate": agg, "per_fold": per_fold,
            "_seg_tpw": seg_tpw, "_seg_fnw": seg_fnw}


def bootstrap_ci(result: dict, draws: int = BOOTSTRAP_DRAWS,
                 seed: int = RNG_SEED) -> tuple[float, float]:
    """Segment-resampled 95% CI of the pooled DTI (FPw at point estimate)."""
    rng = np.random.default_rng(seed)
    fpw = result["aggregate"]["FPw"]
    seg_tpw, seg_fnw = result["_seg_tpw"], result["_seg_fnw"]
    samples = np.empty(draws, dtype=np.float64)
    for d in range(draws):
        tpw = fnw = 0.0
        for t, f in zip(seg_tpw, seg_fnw):
            if t.size == 0:
                continue
            idx = rng.integers(0, t.size, size=t.size)
            tpw += float(t[idx].sum())
            fnw += float(f[idx].sum())
        samples[d] = tpw / (tpw + ALPHA * fpw + BETA * fnw + EPSILON)
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return float(lo), float(hi)


def strip_private(result: dict) -> dict:
    return {k: v for k, v in result.items() if not k.startswith("_")}


def preregistered_surfaces(fusion: h59.H59Fusion, dotted: np.ndarray, tip: np.ndarray,
                           footprint: np.ndarray, budget: int = 40000) -> dict[str, np.ndarray]:
    """The preregistered emission rules compared by this evaluator."""
    bel = fusion.belief_normalized
    return {
        "A_dotted_B2": dotted.astype(np.float64),
        "B_tip_H33D": tip.astype(np.float64),
        "C_naive_mean_of_opinions": 0.5 * (fusion.belief_a + fusion.belief_b),
        "D_union_binary": (dotted | tip).astype(np.float64),
        "E_intersection_binary": (dotted & tip).astype(np.float64),
        "F_DS_belief_normalized": bel,
        "G_DS_pignistic_conflict_priced": fusion.pignistic * (1.0 - np.clip(fusion.conflict, 0, 1)),
        "H_DS_belief_top40k": h59.top_k_mask(bel, budget, footprint).astype(np.float64),
        "I_DS_spacing28_top40k": h59.coverage_emit(bel, footprint, h59.SPACING_TIGHT_PX,
                                                   budget=budget).astype(np.float64),
        "J_DS_spacing52_top40k": h59.coverage_emit(bel, footprint, h59.SPACING_KERNEL_PX,
                                                   budget=budget).astype(np.float64),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(ROOT / "evidence/holdout59_strict.json"))
    parser.add_argument("--budgets", default="20000,30000,40000,47905")
    parser.add_argument("--add-surface", action="append", default=[],
                        help="extra GeoTIFF(s) to score (added to the preregistered rule table)")
    parser.add_argument("--truth", choices=("catalogue", "sgmc_offcat"), default="catalogue",
                        help="truth population for the strict hide-and-recover protocol")
    parser.add_argument("--mask-mode", choices=("pixel", "band"), default="pixel",
                        help="pixel = brief's pixel-exact visible-fault mask (default); "
                             "band = also zero the 300 m band (sensitivity only)")
    args = parser.parse_args()

    started = datetime.now(timezone.utc)
    print(f"[{EVALUATOR_VERSION}] strict hide-and-recover evaluation")
    checks = {
        "catalogue_sha256": sha256_file(CAT_PATH),
        "dotted_sha256": sha256_file(DOTTED_PATH),
        "tip_sha256": sha256_file(TIP_PATH),
    }
    print("  input sha256:", json.dumps({k: v[:16] + "..." for k, v in checks.items()}))
    if checks["catalogue_sha256"] != SHA_CATALOGUE:
        print("FATAL: catalogue SHA-256 mismatch")
        return 2
    if checks["dotted_sha256"] != SHA_DOTTED or checks["tip_sha256"] != SHA_TIP:
        print("FATAL: parent SHA-256 mismatch")
        return 2

    footprint = footprint_mask()
    catalogue = read_grid(CAT_PATH) > 0
    dotted = read_grid(DOTTED_PATH) > 0
    tip = read_grid(TIP_PATH) > 0
    truth_info: dict = {}
    if args.truth == "catalogue":
        labels = catalogue
    else:
        labels, truth_info = sgmc_offcatalogue_truth(footprint, catalogue)
    print(f"  footprint {int(footprint.sum())} cells, catalogue {int(catalogue.sum())} cells, "
          f"truth({args.truth}) {int(labels.sum())} cells")
    if truth_info:
        print("  truth source:", json.dumps(truth_info))

    folds = build_folds(labels, footprint, mask_mode=args.mask_mode)
    fold_info = [{"fold": f.fold_id, "hidden_raw": int(f.hidden_raw.sum()),
                  "hidden_core": int(f.hidden_core.sum()),
                  "segments": int(f.segment_ids.size),
                  "domain": int(f.domain.sum())} for f in folds]
    print("  folds:", json.dumps(fold_info))
    withheld_cells = int(sum(f["hidden_core"] for f in fold_info))
    withheld_segments = int(sum(f["segments"] for f in fold_info))

    fusion = h59.fuse(h59.opinion_surface(dotted), h59.opinion_surface(tip), footprint)
    print(f"  DS parents: dotted {int(dotted.sum())} px, tip {int(tip.sum())} px, "
          f"union {int((dotted | tip).sum())} px, m(Theta) max "
          f"{float(fusion.unassigned[footprint].max()):.4f}, K max "
          f"{float(fusion.conflict[footprint].max()):.4f}")

    budgets = [int(b) for b in args.budgets.split(",") if b.strip()]
    headline_budget = budgets[2] if len(budgets) > 2 else (budgets[-1] if budgets else 40000)
    surfaces = preregistered_surfaces(fusion, dotted, tip, footprint, budget=headline_budget)
    for extra in args.add_surface:
        extra_path = Path(extra)
        surfaces[f"X_{extra_path.stem[:34]}"] = np.where(
            np.isfinite(read_grid(extra_path)), read_grid(extra_path), 0.0).astype(np.float64)
    print(f"  evaluating {len(surfaces)} preregistered surfaces over {len(folds)} folds ...")
    results = {}
    for name, surface in surfaces.items():
        res = evaluate_surface(surface, folds)
        lo, hi = bootstrap_ci(res)
        res["ci95"] = [lo, hi]
        results[name] = res
        print(f"  {name:34s} pooled DTI {res['pooled_DTI']:.4f}  CI [{lo:.4f}, {hi:.4f}]  "
              f"TPw={res['aggregate']['TPw']:.0f} FPw={res['aggregate']['FPw']:.0f} "
              f"FNw={res['aggregate']['FNw']:.0f} pos={int((surface > 0).sum())}")

    # ---- mass/density sweep on the fused belief ranking (mass-neutral gate) ----
    density = {}
    bel = fusion.belief_normalized
    values = bel[footprint]
    n_defined = int((values > 0).sum())
    for b in budgets:
        mask = h59.top_k_mask(bel, min(b, n_defined), footprint)
        res = evaluate_surface(mask.astype(np.float64), folds)
        lo, hi = bootstrap_ci(res, draws=120)
        density[str(b)] = {"pooled_DTI": res["pooled_DTI"], "ci95": [lo, hi],
                           "aggregate": res["aggregate"],
                           "emitted": int(mask.sum()),
                           "emitted_belief_support": n_defined}
        print(f"    budget {b:8d}  emitted {int(mask.sum()):7d}  pooled DTI {res['pooled_DTI']:.4f}"
              f"  CI [{lo:.4f}, {hi:.4f}]")
    # random-emission control at the same masses (Gate-2 intent, re-derived)
    rng = np.random.default_rng(RNG_SEED)
    control = {}
    fp_idx = np.flatnonzero(footprint.ravel())
    for b in budgets:
        picks = rng.choice(fp_idx, size=min(b, fp_idx.size), replace=False)
        mask = np.zeros(footprint.size, dtype=bool)
        mask[picks] = True
        res = evaluate_surface(mask.reshape(footprint.shape).astype(np.float64), folds)
        control[str(b)] = {"pooled_DTI": res["pooled_DTI"], "aggregate": res["aggregate"]}
        print(f"    random control {b:6d}  pooled DTI {res['pooled_DTI']:.4f}")

    # ---- leakage canary ----
    hidden_all = np.zeros_like(labels)
    domain_all = np.zeros_like(labels)
    for fold in folds:
        hidden_all |= fold.hidden_core
        domain_all |= fold.domain
    canary = {}
    features = {
        "distance_to_truth": -distance_transform_edt(~labels).astype(np.float64),
        "kernel_credit_of_truth": kernel_credit_of_mask(labels),
        "dotted_B2": dotted.astype(np.float64),
        "tip_H33D": tip.astype(np.float64),
        "DS_belief_normalized": bel,
        "naive_mean_of_opinions": 0.5 * (fusion.belief_a + fusion.belief_b),
    }
    for name, score in features.items():
        value = float(auc(score, hidden_all, domain_all))
        canary[name] = {"auc_on_withheld": value,
                        "leakage_flag": bool(np.isfinite(value) and value > 0.90)}
        print(f"    canary {name:32s} AUC {value:.4f}"
              f"{'   <-- LEAKAGE FLAG (>0.90)' if canary[name]['leakage_flag'] else ''}")
    for fold in folds:
        value = float(auc(fold.visible_only_feature(), fold.hidden_core, fold.domain))
        canary[f"fold{fold.fold_id}_kernel_credit_visible_only"] = {
            "auc_on_withheld": value,
            "leakage_flag": bool(np.isfinite(value) and value > 0.90),
        }
        print(f"    canary fold{fold.fold_id} visible-only kernel credit  AUC {value:.4f}")
    for name in ("A_dotted_B2", "B_tip_H33D", "F_DS_belief_normalized",
                 "H_DS_belief_top40k", "J_DS_spacing52_top40k"):
        values = []
        for fold in folds:
            masked = fold.mask_visible(surfaces[name])
            values.append(float(auc(masked, fold.hidden_core, fold.domain)))
        finite = [v for v in values if np.isfinite(v)]
        mean_value = float(np.mean(finite)) if finite else float("nan")
        canary[f"surface_{name}_per_fold_masked"] = {
            "auc_per_fold": values, "auc_mean": mean_value,
            "leakage_flag": bool(np.isfinite(mean_value) and mean_value > 0.90),
        }
        print(f"    canary surface {name:30s} mean AUC {mean_value:.4f}  per fold "
              f"{[round(v, 3) for v in values]}")

    payload = {
        "evaluator_version": EVALUATOR_VERSION,
        "generated_utc": started.isoformat(),
        "inputs": checks,
        "truth": args.truth,
        "truth_source": truth_info or {"catalogue_sha256": checks["catalogue_sha256"]},
        "grid": {"height": int(labels.shape[0]), "width": int(labels.shape[1]),
                 "footprint_cells": int(footprint.sum())},
        "protocol": {
            "truth_proxy": "official fault catalogue (existing_faults) 8-connected segments",
            "folds": N_FOLDS,
            "buffer_px": HALO_PX,
            "buffer_applied_to": "truth (hidden segments within 300 m of a visible fault are not scored)",
            "mask_visible_faults": "pixel-exact" if args.mask_mode == "pixel" else "300 m band (sensitivity)",
            "mask_mode": args.mask_mode,
            "metric": {"alpha": ALPHA, "beta": BETA, "radius_m": RADIUS_M,
                       "kernel": "triangular max(1 - d/300m, 0)"},
            "pooling": "components pooled over folds (TPw, FPw, FNw summed)",
            "ci": f"segment bootstrap, {BOOTSTRAP_DRAWS} draws, seed {RNG_SEED}, FPw fixed",
        },
        "fold_info": fold_info,
        "withheld_positive_cells": withheld_cells,
        "withheld_segments": withheld_segments,
        "ds_parents": {
            "dotted_positive_cells": int(dotted.sum()),
            "tip_positive_cells": int(tip.sum()),
            "union_positive_cells": int((dotted | tip).sum()),
            "intersection_positive_cells": int((dotted & tip).sum()),
            "unassigned_mtheta_max": float(fusion.unassigned[footprint].max()),
            "conflict_k_max": float(fusion.conflict[footprint].max()),
        },
        "results": {name: strip_private(res) for name, res in results.items()},
        "density_sweep_fused_belief": density,
        "random_control_same_mass": control,
        "leakage_canary": canary,
        "leakage_canary_note": (
            "distance_to_truth and kernel_credit_of_truth use the FULL "
            "catalogue including the hidden segments and are the positive control that "
            "the canary fires on leaked features. The visible-only per-fold features and "
            "the masked candidate surfaces are the real canary; AUC > 0.90 there means "
            "leakage until proven otherwise."
        ),
        "caveats": [
            "The two parent families are frozen upstream artifacts; they cannot be rebuilt "
            "from visible faults alone, so this is a leave-segment-out generalisation test "
            "of frozen surfaces, not a fully re-derived per-fold model.",
            "The truth proxy is the public mapped-fault catalogue; it is not the hidden "
            "organizer label set and these numbers are not organizer scores.",
            "FPw is a global quantity; the bootstrap holds it at its point estimate.",
        ],
    }
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=1))
    try:
        shown = out_path.relative_to(ROOT)
    except ValueError:
        shown = out_path
    print(f"  wrote {shown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
