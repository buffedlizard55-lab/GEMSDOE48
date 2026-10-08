"""Retired H55 score surrogate — INVALIDATED for metric inference and promotion.

The historical implementation tried to infer hidden truth from owner-reported
scores by substituting ``FPw = S - TPw`` (or an equivalent ``Q ≈ T`` assumption).
The official metric instead uses truth-centred ``TPw = T`` and prediction-centred
``FPw = S - Q``; these quantities are generally unequal. Therefore this module's
``hidden_truth_px``, inverted ``TPw``, fitted ``rho``, live-equivalent scores,
frontier/ceiling, and per-pixel thresholds are not private-label facts, metric
bounds, or promotion evidence.

The functions remain only to reproduce historical H55/H48 calculations under an
explicit forensic opt-in in their command-line tools. Do not use the results as
score estimates, candidate gates, or claims about organizer labels. See
``docs/research/metric-identity-erratum-20261007.md``.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np

from .metric import OFFSETS

# ---------------------------------------------------------------------------
# Owner-reported live scores (OWNER-REPORT class; not organizer-verified).
# `path` is repository-relative; `sha256` pins the restored mirror bytes.
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
MODEL_VALIDITY_STATUS = "INVALIDATED_FORENSIC_ONLY_DO_NOT_USE_FOR_PROMOTION"
MODEL_INVALIDATION_REASON = (
    "Historical calibration substitutes FPw=S-TPw (Q≈T), which is not a general "
    "identity under the official metric."
)


@dataclass(frozen=True)
class LiveArtifact:
    """One owner-reported live-scored emission on the competition grid."""

    key: str
    path: str
    live: float
    sha256: str
    note: str = ""


LIVE_ARTIFACTS: tuple[LiveArtifact, ...] = (
    LiveArtifact("h19_5_backbone", "data/raw/scored/h19_5_01922.tif", 0.1922,
                 "ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d",
                 "dense h19-5 corridor backbone, unthinned"),
    LiveArtifact("d1_5_dotted", "data/raw/scored/d15_02477.tif", 0.2477,
                 "68d0e2e4fcc594f9a23f56c44b885fee733d026d39be55e18ad2a07289525310",
                 "Poisson-disk d=1.5 px thinning of the backbone"),
    LiveArtifact("A_d2_8", "data/families/dotted_d2_8_02600.tif", 0.2600,
                 "3e78737f0da8dd2ca66cc6caac0ce8eeefcd6715707f8d1bd3091845cd9bcc30",
                 "Poisson-disk d=2.83 px thinning; rung A"),
    LiveArtifact("B_prune100", "data/families/dotted_d2_8_02708.tif", 0.2708,
                 "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73",
                 "rung A minus every dot within 100 m of the public catalogue"),
    LiveArtifact("C_prune200", "data/families/dotted_b2_prune_02778.tif", 0.2778,
                 "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
                 "LIVE BEST. rung B minus every dot 100-200 m from the catalogue"),
    # Both of these are restored from the GEMSDOE28 published mirrors so that the pin
    # is the published one.  They were verified pixel-identical (np.array_equal on the
    # boolean emission) to the tracked local twins data/raw/ref_h36_1_rung30.tif
    # (SHA-256 7c74270a...) and data/raw/tip_h32_1_prethin_tip_euler.tif
    # (SHA-256 26748e4b...), which differ only in outside-footprint encoding and tags.
    LiveArtifact("h36_rung30", "data/raw/scored/h36_rung30_02710.tif", 0.2710,
                 "5556aa1438fd67376b60d5ffc99228ec09dcc11a8408298a743ccb88d6163641",
                 "independent 37,660 px thinning of the same backbone"),
    LiveArtifact("h32_prethin_tip", "data/raw/scored/h32_prethin_tip_02649.tif", 0.2649,
                 "04d31922f5c1ea4016984fc470ab2b0ff8e266c615792f0e86020da3b940d3ff",
                 "tip/Euler variant, 42,294 px, subset of the backbone"),
    LiveArtifact("h33d_tip_step", "data/raw/tip_h33d_stepover.tif", 0.2632,
                 "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757",
                 "tip/step-over family best, 41,865 px (133 px off-backbone)"),
)

#: Out-of-family live artifact used only to bound the model's transfer error.
OUT_OF_FAMILY = LiveArtifact("sgmc_offcat_44k", "data/raw/scored/sgmc44k_00512.tif", 0.0512,
                             "9b83158bde01cd5d42e38229d70d01e67cecd2514eeb5fa8d1f3ab6851469dad",
                             "Poisson-disk emission on SGMC faults >300 m off-catalogue")

#: Nested triple used to identify |G| (strictly nested, verified pixel-wise).
NESTED_TRIPLE = ("A_d2_8", "B_prune100", "C_prune200")

CATALOGUE_BUFFER_M = 200.0
ALPHA = 0.2
BETA = 0.8


# ---------------------------------------------------------------------------
# kernel helpers
# ---------------------------------------------------------------------------

_OFF = tuple((int(dy), int(dx), float(w)) for dy, dx, w in OFFSETS)


def max_credit_field(mask: np.ndarray) -> np.ndarray:
    """``max_x k(d(x, y))`` for every cell ``y``, from a binary ``mask``."""
    values = np.asarray(mask)
    if values.ndim != 2:
        raise ValueError("mask must be 2-D")
    v = np.where(values, 1.0, 0.0)
    h, w = v.shape
    best = np.zeros(v.shape, dtype=np.float64)
    for dy, dx, wt in _OFF:
        r0, r1 = max(dy, 0), min(h, h + dy)
        c0, c1 = max(dx, 0), min(w, w + dx)
        if r0 >= r1 or c0 >= c1:
            continue
        np.maximum(best[r0:r1, c0:c1], v[r0 - dy:r1 - dy, c0 - dx:c1 - dx] * wt,
                   out=best[r0:r1, c0:c1])
    return best


def coverage(emission: np.ndarray, target: np.ndarray) -> float:
    """``Cov(X) = sum_{b in target} max_{x in X} k(d(x, b))``."""
    field = max_credit_field(emission)
    return float(field[np.asarray(target, dtype=bool)].sum())


def kernel_weight_sum() -> float:
    """Maximum coverage one isolated dot can add (= sum of all kernel weights)."""
    return float(sum(w for _, _, w in _OFF))


# ---------------------------------------------------------------------------
# calibration
# ---------------------------------------------------------------------------

def _require_legacy_audit_only(enabled: bool, operation: str) -> None:
    if not enabled:
        raise RuntimeError(
            f"{operation} is an invalidated FPw=S-TPw surrogate; pass legacy_audit_only=True "
            "only for forensic reproduction"
        )


def invert_truth(live: float, emitted: int, hidden_truth_px: float, *,
                 legacy_audit_only: bool = False) -> float:
    """FOR FORENSIC REPRODUCTION ONLY: solve the invalid historical surrogate for T."""
    _require_legacy_audit_only(legacy_audit_only, "invert_truth")
    return float(live * (ALPHA * emitted + BETA * hidden_truth_px))


def fit_hidden_truth(masses: Sequence[int], lives: Sequence[float],
                     lo: float = 4000.0, hi: float = 60000.0, *,
                     legacy_audit_only: bool = False) -> dict:
    """INVALIDATED forensic fit assuming the false ``FPw = S - TPw`` identity.

    Returned ``hidden_truth_px`` and shared ``T`` are historical surrogate values,
    not estimates of private/organizer labels or promotion inputs.
    """
    _require_legacy_audit_only(legacy_audit_only, "fit_hidden_truth")
    if len(masses) != len(lives) or len(masses) < 2:
        raise ValueError("need at least two (mass, live) pairs")
    masses = np.asarray(masses, dtype=np.float64)
    lives = np.asarray(lives, dtype=np.float64)

    def sse(g: float) -> float:
        t = lives * (ALPHA * masses + BETA * g)
        return float(((t - t.mean()) ** 2).sum())

    grid = np.arange(lo, hi, 1.0)
    coarse = grid[int(np.argmin([sse(g) for g in grid]))]
    fine = np.arange(coarse - 2.0, coarse + 2.0, 0.01)
    best = float(min(fine, key=sse))
    shared_t = float(np.mean(lives * (ALPHA * masses + BETA * best)))

    pairs = []
    for i in range(len(masses)):
        for j in range(i + 1, len(masses)):
            l1, s1 = lives[i], masses[i]
            l2, s2 = lives[j], masses[j]
            if l1 == l2:
                continue
            # l1 (0.2 s1 + 0.8 G) = l2 (0.2 s2 + 0.8 G)  =>  G closed form
            g = 0.25 * (l2 * s2 - l1 * s1) / (l1 - l2)
            pairs.append({"pair": [int(s1), int(s2)], "live": [float(l1), float(l2)],
                          "closed_form_G": float(g)})
    return {"validity_status": MODEL_VALIDITY_STATUS,
            "invalidation_reason": MODEL_INVALIDATION_REASON,
            "promotion_use": "NONE — historical surrogate values only.",
            "hidden_truth_px": best, "shared_tpw": shared_t, "sse": sse(best),
            "pairwise_closed_form": pairs}


def fit_rho(coverages: Sequence[float], masses: Sequence[int], lives: Sequence[float],
            hidden_truth_px: float, *, legacy_audit_only: bool = False) -> dict:
    """INVALIDATED least-squares ``rho`` fit for the historical surrogate."""
    _require_legacy_audit_only(legacy_audit_only, "fit_rho")
    xs = np.asarray(coverages, dtype=np.float64)
    ys = np.asarray([invert_truth(l, s, hidden_truth_px, legacy_audit_only=True)
                     for l, s in zip(lives, masses)])
    rho = float((xs * ys).sum() / (xs * xs).sum())
    denom = ALPHA * np.asarray(masses, dtype=np.float64) + BETA * hidden_truth_px
    pred = rho * xs / denom
    act = np.asarray(lives, dtype=np.float64)
    rel = (pred - act) / act
    return {
        "validity_status": MODEL_VALIDITY_STATUS,
        "invalidation_reason": MODEL_INVALIDATION_REASON,
        "promotion_use": "NONE — historical surrogate values only.",
        "rho": rho,
        "rms_relative_error_pct": float(100.0 * np.sqrt((rel ** 2).mean())),
        "max_abs_relative_error_pct": float(100.0 * np.abs(rel).max()),
        "per_artifact_relative_error_pct": [float(r) * 100.0 for r in rel],
        "inverted_tpw": [float(y) for y in ys],
        "predicted_dti": [float(p) for p in pred],
    }


@dataclass(frozen=True)
class ForwardModel:
    """Historical surrogate parameters; never an official-score predictor."""

    hidden_truth_px: float
    rho: float
    target_px: int
    legacy_audit_only: bool = False

    def __post_init__(self) -> None:
        _require_legacy_audit_only(self.legacy_audit_only, "ForwardModel")

    def tpw(self, cov: float) -> float:
        return self.rho * cov

    def dti(self, cov: float, emitted: int) -> float:
        return self.tpw(cov) / (ALPHA * emitted + BETA * self.hidden_truth_px)

    def break_even_credit(self, dti: float) -> float:
        """Return the invalid surrogate's historical threshold; not a live gate."""
        return ALPHA * dti

    def worst_case_dti(self, base_cov: float, base_emitted: int, added: int) -> float:
        """Score if every one of ``added`` new pixels earns exactly zero credit."""
        return self.tpw(base_cov) / (ALPHA * (base_emitted + added) + BETA * self.hidden_truth_px)

    def scenario_dti(self, base_cov: float, base_emitted: int, added: int,
                     credit_per_added: float) -> float:
        t = self.tpw(base_cov) + credit_per_added * added
        return t / (ALPHA * (base_emitted + added) + BETA * self.hidden_truth_px)

    def tpw_needed(self, dti_target: float, emitted: int) -> float:
        return dti_target * (ALPHA * emitted + BETA * self.hidden_truth_px)

    def to_json(self) -> dict:
        return {"validity_status": MODEL_VALIDITY_STATUS,
                "invalidation_reason": MODEL_INVALIDATION_REASON,
                "promotion_use": "NONE — historical surrogate values only.",
                "hidden_truth_px_invalidated": self.hidden_truth_px,
                "rho_invalidated": self.rho,
                "target_px": self.target_px,
                "break_even_credit_at_0_2778_invalidated": self.break_even_credit(0.2778),
                "max_coverage_one_isolated_dot": kernel_weight_sum()}


# ---------------------------------------------------------------------------
# reproducible calibration driver
# ---------------------------------------------------------------------------

def load_binary(path: str | Path) -> np.ndarray:
    """Read band 1 of a raster as a boolean mask (NaN -> False)."""
    import rasterio

    with rasterio.open(Path(path)) as ds:
        return np.nan_to_num(ds.read(1).astype(np.float64), nan=0.0) > 0.5


def calibrate(backbone: np.ndarray, catalogue_distance_m: np.ndarray,
              artifacts: Iterable[LiveArtifact] = LIVE_ARTIFACTS,
              buffer_m: float = CATALOGUE_BUFFER_M, *,
              legacy_audit_only: bool = False) -> dict:
    """Recreate an invalidated H55 surrogate receipt for forensic comparison only."""
    _require_legacy_audit_only(legacy_audit_only, "calibrate")
    artifacts = tuple(artifacts)
    eligible = np.asarray(backbone, dtype=bool) & (np.asarray(catalogue_distance_m) > buffer_m)
    masses, lives, covs, keys = [], [], [], []
    for art in artifacts:
        mask = load_binary(ROOT / art.path)
        masses.append(int(mask.sum()))
        lives.append(art.live)
        covs.append(coverage(mask, eligible))
        keys.append(art.key)

    nested = [i for i, a in enumerate(artifacts) if a.key in NESTED_TRIPLE]
    if len(nested) != 3:
        raise ValueError(f"nested triple not fully present: {[keys[i] for i in nested]}")
    gfit = fit_hidden_truth([masses[i] for i in nested], [lives[i] for i in nested],
                            legacy_audit_only=True)
    rfit = fit_rho(covs, masses, lives, gfit["hidden_truth_px"], legacy_audit_only=True)

    model = ForwardModel(gfit["hidden_truth_px"], rfit["rho"], int(eligible.sum()),
                         legacy_audit_only=True)
    oof = None
    try:
        oof_mask = load_binary(ROOT / OUT_OF_FAMILY.path)
        oof_cov = coverage(oof_mask, eligible)
        oof_s = int(oof_mask.sum())
        oof_t = invert_truth(OUT_OF_FAMILY.live, oof_s, model.hidden_truth_px,
                             legacy_audit_only=True)
        oof = {
            "key": OUT_OF_FAMILY.key, "live": OUT_OF_FAMILY.live, "emitted": oof_s,
            "cov_eligible_backbone": oof_cov, "inverted_tpw": oof_t,
            "implied_rho": oof_t / oof_cov if oof_cov else None,
            "predicted_dti_with_family_rho": model.dti(oof_cov, oof_s),
            "relative_transfer_error_pct": 100.0 * (model.dti(oof_cov, oof_s) - OUT_OF_FAMILY.live)
            / OUT_OF_FAMILY.live,
        }
    except FileNotFoundError:  # pragma: no cover - mirror not restored
        oof = {"key": OUT_OF_FAMILY.key, "status": "mirror not restored; transfer error not measured"}

    return {
        "validity_status": MODEL_VALIDITY_STATUS,
        "invalidation_reason": MODEL_INVALIDATION_REASON,
        "promotion_use": "NONE — historical surrogate values only.",
        "eligible_backbone_px": int(eligible.sum()),
        "catalogue_buffer_m": buffer_m,
        "artifacts": [{"key": k, "emitted": s, "live": l, "cov_eligible_backbone": c}
                      for k, s, l, c in zip(keys, masses, lives, covs)],
        "hidden_truth_fit": gfit,
        "rho_fit": rfit,
        "model": model.to_json(),
        "out_of_family_transfer_check": oof,
    }


def write_receipt(receipt: dict, path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return out
