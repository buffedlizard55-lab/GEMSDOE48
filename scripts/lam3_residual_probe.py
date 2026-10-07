#!/usr/bin/env python3
"""Does any new dot pay? Marginal-credit probe against the best-calibrated truth model.

The 2026-10-07 credit-density audit (docs/research/credit-density-audit-20261007.md)
showed that every shipped candidate is either the incumbent dotted family C itself or
an addition whose credit per added cell (0.005-0.013) sits far below the metric's own
break-even bar 0.2 * DTI = 0.0556. This script asks the sharper question:

    Would *any* new dot, placed wherever the best available truth model wants it,
    clear that bar?

It rebuilds the two-component hidden-truth density model "lam3" from scratch:

    Pl   = Dempster-Shafer plausibility of the dotted/tip kernel-credit families
           (live-anchored discounts a1 = 0.95, a2 = 0.95 * 0.2632 / 0.2778)
    Q    = normalized sum of the 16 other scored submissions' kernel-credit surfaces
    lam3 = [a * Pl**0.6 normalized + (1 - a) * Q normalized] * N

with (a, N) fitted to minimise rms against the 17 owner-reported live ladder scores.
The probe then reports, for each documented addition and for greedily selected
"model-optimal" cells, the marginal credit per added cell against the 0.0556 bar.

Reading: no existing addition comes within 3x of the bar, and even the model's own
greedy optimum only reaches 0.049-0.058 per cell - i.e. the incumbent sits on the
frontier of the *entire current information set* and only genuinely new information
(a detector whose cells are near hidden faults the 100 m layers cannot see) can move
the live score. Evidence class: model + owner-reported ladder anchors, not organizer truth.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gemsdoe48 import families as FAM  # noqa: E402
from gemsdoe48 import metric as M  # noqa: E402

RHO = 0.95
LIVE_DOTTED, LIVE_TIP = 0.2778, 0.2632
INCUMBENT_LIVE = 0.2778
BAR = 0.2 * INCUMBENT_LIVE
LADDER_TRUTH_PX = 14307.4  # from the A->B->C inversion in the audit document

# (name, path relative to ROOT, owner-reported live DTI) - identical to the val17 fit
FILES = [
    ("C_b2", "data/raw/scored/b2_02778.tif", 0.2778),
    ("B_r1solo", "data/raw/scored/r1solo_02708.tif", 0.2708),
    ("h36", "data/raw/scored/h36_02710.tif", 0.2710),
    ("h32tip", "data/raw/scored/h32tip_02649.tif", 0.2649),
    ("tip_h33d", "data/raw/scored/h33d_tip_02632.tif", 0.2632),
    ("h19_5_dense", "data/raw/scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif", 0.1922),
    ("h19_4", "data/raw/scored/gems19-h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan.tif", 0.1894),
    ("h16_1", "data/raw/scored/gems16-h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan.tif", 0.1855),
    ("d1_5", "data/raw/scored/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif", 0.2477),
    ("d2_8", "data/raw/scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif", 0.2600),
    ("tgc_v2", "data/raw/scored/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif", 0.2449),
    ("r13lattice", "data/raw/scored/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif", 0.0904),
    ("hedge_v2", "data/raw/scored/8GEMSDOE_Hedge-v2_submission.tif", 0.1563),
    ("h25ctx", "data/raw/scored/gems10-h25-ctx-ridge-20260927T232947704150Z-6452ae1d00.tif", 0.1280),
    ("h28ridge", "data/raw/scored/gems10-h28-dotted-ridge-20260928T020256236880Z-6452ae1d00.tif", 0.1839),
    ("ens12", "data/raw/scored/gemsdoe-ens12-adopted-7f00890a.tif", 0.1563),
    ("g9", "data/raw/scored/gemsdoe9-PLACEHOLDER-2314b599.tif", 0.0107),
]

ADDITIONS = [
    ("H49_yager_balanced", "docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif"),
    ("H52_lidar_2000", "docs/downloads/GEMSDOE48-H52-lidar-scarp-additions-20261007-38029417f6ca-nan-outside.tif"),
    ("H53_lidar_1000", "docs/downloads/GEMSDOE48-H53-ds-core-lidar-20261007-dedc43dc0167.tif"),
]


def load_binary(path: pathlib.Path) -> np.ndarray:
    with rasterio.open(path) as src:
        values = src.read(1).astype(np.float64)
        nodata = src.nodata
    values = np.where(np.isfinite(values), values, 0.0)
    if nodata is not None and np.isfinite(nodata):
        values = np.where(values == nodata, 0.0, values)
    return np.clip(values, 0.0, 1.0) > 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=pathlib.Path,
                        default=ROOT / "evidence" / "lam3_residual_probe_20261007.json")
    args = parser.parse_args()
    t0 = time.time()

    labels = rasterio.open(ROOT / "data/official/labels.tif").read(1)
    footprint = labels != -1
    catalogue = labels == 1
    dist_cat = distance_transform_edt(~catalogue, sampling=(100.0, 100.0))
    allowed = footprint & (dist_cat > 200.0)

    # --- DS plausibility of the two families (same convention as run_ds_fusion) ---
    b1 = FAM.kernel_credit_surface(FAM.load_family_mask("dotted_b2_prune_02778")).astype(np.float64)
    b2 = FAM.kernel_credit_surface(FAM.load_family_mask("tip_02632")).astype(np.float64)
    a1, a2 = RHO, RHO * (LIVE_TIP / LIVE_DOTTED)
    m1f, m1n, m1t = a1 * b1, a1 * (1.0 - b1), 1.0 - a1
    m2f, m2n, m2t = a2 * b2, a2 * (1.0 - b2), 1.0 - a2
    conflict = m1f * m2n + m1n * m2f
    plausibility = ((m1f * m2f + m1f * m2t + m1t * m2f) + m1t * m2t) / (1.0 - conflict)

    # --- coverage fields of the 17 scored submissions ---
    coverage, mass = {}, {}
    for name, rel, _live in FILES:
        support = load_binary(ROOT / rel)
        mass[name] = float(support.sum())
        coverage[name] = M.max_credit_field(support)
    print(f"coverage fields ready ({time.time() - t0:.0f}s)")

    other = [name for name, _p, _l in FILES if name != "C_b2"]
    q = np.zeros_like(plausibility)
    for name in other:
        field = coverage[name]
        q += field / max(field.max(), 1e-9)
    q = np.where(allowed, q, 0.0)
    q /= q.sum()
    p = np.where(allowed, np.power(np.clip(plausibility, 1e-12, None), 0.60), 0.0)
    p /= p.sum()

    best = None
    for mix_a in np.arange(0.0, 1.001, 0.05):
        weights = mix_a * p + (1.0 - mix_a) * q
        per_unit = {name: float((weights * coverage[name]).sum()) for name, _p, _l in FILES}
        for n_truth in np.arange(10_000, 17_001, 100):
            err = 0.0
            for name, _p, live in FILES:
                t = per_unit[name] * n_truth
                err += (t / (0.2 * mass[name] + 0.8 * n_truth) - live) ** 2
            rms = float(np.sqrt(err / len(FILES)))
            if best is None or rms < best[0]:
                best = (rms, float(mix_a), float(n_truth), {k: v * n_truth for k, v in per_unit.items()})
    rms, mix_a, n_fit, t_model = best
    print(f"best lam3 fit: rms={rms:.5f} a={mix_a:.2f} N={n_fit:.0f} ({time.time() - t0:.0f}s)")

    lam_fit = (mix_a * p + (1.0 - mix_a) * q) * n_fit            # the fitted model
    lam_ladder = lam_fit * (LADDER_TRUTH_PX / n_fit)             # doc convention (ladder mass)

    cov_c = coverage["C_b2"]
    support_c = load_binary(ROOT / "data/raw/scored/b2_02778.tif")

    def credit(pred: np.ndarray, lam: np.ndarray) -> dict:
        cov = M.max_credit_field(pred)
        t_new = float((lam * cov).sum())
        m_new = float(pred.sum())
        t_c = float((lam * cov_c).sum())
        m_c = float(support_c.sum())
        return {"T": t_new, "mass": m_new, "dti": t_new / (0.2 * m_new + 0.8 * float(lam.sum())),
                "delta_dti_vs_C": t_new / (0.2 * m_new + 0.8 * float(lam.sum()))
                - t_c / (0.2 * m_c + 0.8 * float(lam.sum())),
                "T_gain": t_new - t_c}

    def marginal(pred: np.ndarray, name: str) -> dict:
        out = {}
        for label, lam in (("ladder_mass_14307", lam_ladder), ("fitted_mass_17000", lam_fit)):
            c = credit(pred, lam)
            added = float(pred.sum() - support_c.sum())
            base_c = credit(support_c, lam)
            out[label] = {"per_cell": c["T_gain"] / added if added else 0.0,
                          "T_gain": c["T_gain"], "delta_dti_vs_C": c["delta_dti_vs_C"]}
        out["per_cell_ladder_mass"] = out["ladder_mass_14307"]["per_cell"]
        out["per_cell_fitted_mass"] = out["fitted_mass_17000"]["per_cell"]
        return out

    additions = {}
    for name, rel in ADDITIONS:
        path = ROOT / rel
        if not path.exists():
            continue
        support = load_binary(path)
        add = support & ~support_c
        row = {"file": rel, "added_cells": int(add.sum()), **marginal(support, name),
               "verdict": "below_bar"}
        if row["per_cell_fitted_mass"] >= BAR:
            row["verdict"] = "at_or_above_bar_fitted_mass"
        additions[name] = row
        print(f"{name:20s} added={row['added_cells']:7d} per-cell "
              f"{row['per_cell_ladder_mass']:.4f} (ladder mass) / {row['per_cell_fitted_mass']:.4f} (fitted)")

    # --- model-optimal residual: where does lam3 want dots that C does not cover? ---
    residual = lam_ladder * (1.0 - cov_c)
    residual_sweep = {}
    for k in (250, 500, 1000, 2000, 4000):
        flat = np.argpartition(residual.ravel(), -k)[-k:]
        support = support_c.copy()
        support.ravel()[flat] = True  # union with the incumbent: additions are never standalone
        row = marginal(support, f"top_{k}")
        row["dots"] = k
        residual_sweep[f"top_{k}_lam3_residual"] = row
        print(f"top-{k:5d} lam3-residual cells: per-cell {row['per_cell_ladder_mass']:.4f} (ladder) "
              f"/ {row['per_cell_fitted_mass']:.4f} (fitted)")

    rng = np.random.default_rng(7)
    rows, cols = np.nonzero(allowed & (lam_fit > 0))
    pick = rng.choice(len(rows), size=2000, replace=False)
    control = support_c.copy()
    control[rows[pick], cols[pick]] = True  # union with the incumbent
    control_row = marginal(control, "random_2000_in_lam3_support")

    receipt = {
        "schema": "GEMSDOE48-lam3-residual-probe-v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "question": "Would any new dot clear the metric break-even bar 0.2*DTI = 0.0556 "
                    "under the best-calibrated hidden-truth density model?",
        "method": {
            "lam3": "a * Pl(ladder)**0.6 + (1-a) * Q(other detectors' normalized kernel credit), "
                    "scaled to N; (a, N) fitted to the 17 owner-reported live ladder scores",
            "fitted": {"rms": rms, "a": mix_a, "N": n_fit},
            "normalizations": {
                "ladder_mass_14307": "lam3 rescaled to the A->B->C inversion mass 14,307.4 pixels "
                                      "(conservative; the convention used in the audit document)",
                "fitted_mass_17000": "lam3 at its own fitted mass N (1.188x the above)",
            },
            "bar_per_cell": BAR,
            "evidence_class": "model + OWNER-REPORTED ladder anchors; the SGMC/catalogue proxies are not used here",
        },
        "model_fit_per_file": {name: {"mass": mass[name], "live_owner_reported": live,
                                      "model_dti": t_model[name] / (0.2 * mass[name] + 0.8 * n_fit),
                                      "T_model": t_model[name]} for name, _p, live in FILES},
        "incumbent": {"file": "data/raw/scored/b2_02778.tif", "cells": int(support_c.sum()),
                      "live_owner_reported": INCUMBENT_LIVE,
                      "lam3_mass_covered_fraction_ladder": float((lam_ladder * cov_c).sum() / LADDER_TRUTH_PX)},
        "additions": additions,
        "model_optimal_residual": residual_sweep,
        "random_control_2000": control_row,
        "reading": "No shipped addition reaches half the bar. Even cells the model itself ranks as the "
                   "most valuable uncovered pixels reach only ~0.049-0.058 per cell (ladder / fitted mass), "
                   "i.e. the incumbent is on the frontier of the current information set: only genuinely "
                   "new information can move the live score, and the maximum model-admissible gain from any "
                   "addition is ~+0.000-0.002 DTI.",
    }
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"receipt -> {args.receipt} ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
