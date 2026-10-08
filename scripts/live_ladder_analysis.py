#!/usr/bin/env python3
"""Historical live-ladder calculation — INVALIDATED and forensic-only.

The legacy calculation substituted ``FPw=S-TPw`` and assumed that removed dots had
zero hidden-label credit, then inferred private truth quantities, ceilings, and
per-cell thresholds from owner-reported scores. Neither premise validates those
inferences, and no organizer receipt links the local TIFF bytes to the score rows.
The command refuses by default and writes forensic output only with
``--legacy-audit-only``. Results do not describe private labels or clear a slot.
See ``docs/research/metric-identity-erratum-20261007.md``.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gemsdoe48 import metric as M  # noqa: E402

ALPHA, BETA = 0.2, 0.8
LADDER = [  # (name, path, owner-reported live score)
    ("A_d2.8", "data/families/dotted_d2_8_02600.tif", 0.2600),
    ("B_B1", "data/families/dotted_d2_8_02708.tif", 0.2708),
    ("C_B2", "data/families/dotted_b2_prune_02778.tif", 0.2778),
]


def read_pos(path: str) -> np.ndarray:
    with rasterio.open(ROOT / path) as src:
        a = src.read(1)
    return np.isfinite(a) & (a > 0)


def invert_pair(s_big: float, n_big: int, s_small: float, n_small: int, f: float = 1.0) -> float:
    """T per pi, assuming the removed (n_big-n_small) dots carried zero credit and FP fraction f.

    1/s = D/T and D falls by 0.2*f*n when n empty dots are removed, so
    1/s_big - 1/s_small = 0.2*f*n/T.
    """
    return ALPHA * f * (n_big - n_small) / (1.0 / s_big - 1.0 / s_small)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-audit-only", action="store_true",
                        help="required opt-in for invalidated historical inversion")
    parser.add_argument("--output", type=pathlib.Path,
                        default=ROOT / "evidence" / "forensic" / "live_ladder_legacy_20261007.json")
    args = parser.parse_args()
    if not args.legacy_audit_only:
        parser.error("invalidated FPw=S-TPw inversion; pass --legacy-audit-only only for forensic reproduction")
    print("LEGACY AUDIT ONLY — INVALIDATED; NOT A TRUTH ESTIMATE OR PROMOTION GATE")
    masks = {name: read_pos(p) for name, p, _ in LADDER}
    a, b, c = masks["A_d2.8"], masks["B_B1"], masks["C_B2"]
    nested = bool((b & ~a).sum() == 0 and (c & ~b).sum() == 0)
    with rasterio.open(ROOT / "data/official/labels.tif") as src:
        lab = src.read(1)
    cat = lab == 1
    dcat = distance_transform_edt(~cat, sampling=(100.0, 100.0))
    out = {
        "validity_status": "INVALIDATED_FORENSIC_ONLY_DO_NOT_USE_FOR_PROMOTION",
        "invalidation_reason": "Historical hidden-truth inversion assumes FPw=S-TPw, which is not a general official-metric identity.",
        "nested_A_superset_B_superset_C": nested,
        "n": {"A": int(a.sum()), "B": int(b.sum()), "C": int(c.sum())},
        "removed": {
            "A_minus_B": {"n": int((a & ~b).sum()), "max_d_cat_m": float(dcat[a & ~b].max()),
                           "n_on_catalogue_d0": int(((a & ~b) & cat).sum())},
            "B_minus_C": {"n": int((b & ~c).sum()), "min_d_cat_m": float(dcat[b & ~c].min()),
                           "max_d_cat_m": float(dcat[b & ~c].max())},
        },
        "c_dots_within_300m_of_catalogue": int((dcat[c] <= 300).sum()),
    }
    sA, sB, sC = (x[2] for x in LADDER)
    nA, nB, nC = out["n"]["A"], out["n"]["B"], out["n"]["C"]
    # Masked (d=0) dots add neither FP nor mass; they are excluded from the removed count.
    nAB = out["removed"]["A_minus_B"]["n"] - out["removed"]["A_minus_B"]["n_on_catalogue_d0"]
    nBC = out["removed"]["B_minus_C"]["n"]
    T_ab = invert_pair(sA, nAB, sB, 0)
    T_bc = invert_pair(sB, nBC, sC, 0)
    T = 0.5 * (T_ab + T_bc)
    # D_C = T/sC = 0.2 T + 0.2 FP_C + 0.8 G ;  FP_C ≈ S_C - M_C with M_C ≈ T (dots that earn credit
    # sit at k≈1 of the truth), so  0.8 G ≈ T/sC - 0.2 S_C.
    G = (T / sC - ALPHA * nC) / BETA
    D_C = T / sC
    bar_add = ALPHA * sC  # a new unit-mass dot helps iff its realised credit > 0.2*DTI
    mean_credit_per_dot = T / nC
    out["inversion_S0"] = {
        "T_per_pi_from_AB": T_ab, "T_per_pi_from_BC": T_bc, "T_per_pi_mean": T,
        "pair_consistency_pct": 100 * abs(T_ab - T_bc) / T,
        "G_per_pi": G, "D_C_per_pi": D_C,
        "recall_weighted_T_over_G": T / G,
        "mean_credit_per_C_dot": mean_credit_per_dot,
        "addition_bar_credit_per_dot": bar_add,
        "addition_bar_as_fraction_of_mean_dot": bar_add / mean_credit_per_dot,
        "removal_rule": "removing n dots gains iff their total credit < 0.2*DTI*n, i.e. < "
                        f"{bar_add / mean_credit_per_dot:.2f} of the average C dot",
        "note": "per-pi = full-region-equivalent; the public-chunk fraction pi cancels",
    }
    # What it takes to reach the leaderboard top on the same mass, and with fewer dots.
    tops = {"xiaofanhu_0.3774": 0.3774, "alexoktaba_0.3345": 0.3345, "nchuzhoy_0.3262": 0.3262}
    out["ceiling"] = {}
    for k, s in tops.items():
        T_need_same_mass = s * (ALPHA * nC + BETA * G)
        out["ceiling"][k] = {
            "T_needed_at_37654_px": T_need_same_mass,
            "T_gain_pct_needed": 100 * (T_need_same_mass / T - 1),
            "recall_needed": T_need_same_mass / G,
        }
    # Pure-removal frontier: drop n dots whose hit-rate is h times the C average.
    frontier = []
    for n_drop in (5000, 10000, 15000, 20000):
        for rel in (0.0, 0.25, 0.38, 0.5, 1.0):
            dT = rel * mean_credit_per_dot * n_drop
            # removing a credit-earning dot removes ~1 from both S and M (no FP change);
            # removing an empty dot removes 1 FP unit.
            frac_hit = rel * mean_credit_per_dot / 2.2  # ~2.2 credit units per hit dot [DERIVED]
            dFP = -(1 - min(frac_hit, 1.0)) * n_drop
            Dn = D_C - ALPHA * dT + ALPHA * dFP
            frontier.append({"n_drop": n_drop, "removed_credit_rel_to_mean": rel,
                             "dti": (T - dT) / Dn})
    out["removal_frontier"] = frontier

    # --- synthetic verification of the algebra against the exact metric -----------------
    rng = np.random.default_rng(7)
    H, W = 400, 400
    truth = np.zeros((H, W), bool)
    for _ in range(12):  # random straight "fault" segments
        r0, c0 = rng.integers(20, H - 20), rng.integers(20, W - 20)
        ang = rng.uniform(0, np.pi); L = rng.integers(30, 120)
        for t in np.linspace(0, L, L * 2):
            r, cc = int(round(r0 + t * np.sin(ang))), int(round(c0 + t * np.cos(ang)))
            if 0 <= r < H and 0 <= cc < W:
                truth[r, cc] = True
    pred = np.zeros((H, W), float)
    near = M.dilate(truth, 2)
    hits = np.argwhere(near); far = np.argwhere(~M.dilate(truth, 6))
    for idx in rng.choice(len(hits), 150, replace=False):
        pred[tuple(hits[idx])] = 1.0
    far_idx = rng.choice(len(far), 600, replace=False)
    for idx in far_idx:
        pred[tuple(far[idx])] = 1.0
    r_full = M.dti(pred, truth)
    # identity check: DTI == T/(0.2T + 0.2FP + 0.8|G|)
    ident = r_full.tpw / (ALPHA * r_full.tpw + ALPHA * r_full.fpw + BETA * r_full.n_truth)
    # removal of empty (far) dots: predicted vs exact
    pred2 = pred.copy()
    for idx in far_idx[:300]:
        pred2[tuple(far[idx])] = 0.0
    r2 = M.dti(pred2, truth)
    pred_s2 = r_full.tpw / (ALPHA * r_full.tpw + ALPHA * (r_full.fpw - 300) + BETA * r_full.n_truth)
    # invert the synthetic pair exactly as the live ladder is inverted
    T_inv = invert_pair(r_full.dti, 300, r2.dti, 0)
    out["synthetic_check"] = {
        "exact_dti": r_full.dti, "identity_dti": ident, "identity_abs_err": abs(ident - r_full.dti),
        "after_removing_300_empty_dots_exact": r2.dti, "predicted": pred_s2,
        "removal_prediction_abs_err": abs(pred_s2 - r2.dti),
        "true_TPw": r_full.tpw, "inverted_TPw_from_pair": T_inv,
        "inversion_rel_err_pct": 100 * abs(T_inv - r_full.tpw) / r_full.tpw,
        "marginal_bar_check": {
            "bar": ALPHA * r_full.dti,
            "note": "adding a dot with realised credit k changes DTI with the sign of k - 0.2*DTI",
        },
    }
    # explicit marginal-bar check: add one dot at a truth-adjacent cell with credit k
    cand = np.argwhere(truth & (pred == 0) & (M.max_credit_field(pred) < 0.05))
    if len(cand):
        p3 = pred.copy(); p3[tuple(cand[0])] = 1.0
        r3 = M.dti(p3, truth)
        out["synthetic_check"]["marginal_bar_check"]["add_credit1_dot_delta"] = r3.dti - r_full.dti
    p5 = pred.copy(); p5[tuple(far[rng.choice(len(far))])] = 1.0
    out["synthetic_check"]["marginal_bar_check"]["add_credit0_dot_delta"] = M.dti(p5, truth).dti - r_full.dti

    dest = args.output if args.output.is_absolute() else ROOT / args.output
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2))
    print(json.dumps(out["inversion_S0"], indent=2))
    print(json.dumps(out["ceiling"], indent=2))
    print(json.dumps(out["synthetic_check"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
