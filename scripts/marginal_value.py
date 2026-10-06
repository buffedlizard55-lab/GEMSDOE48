#!/usr/bin/env python3
"""Measure the MARGINAL proxy value of every candidate group, one group at a time.

Adding dots to an existing emission is not worth their *standalone* credit: the
published metric takes, for each truth pixel, the MAXIMUM over the kernel
support, so dots that shadow each other are partly redundant.  This script adds
one group at a time to a fixed base and reports the realised marginal credit per
emitted cell, which is the quantity the marginal-acceptance bar

        include a set iff  dT > alpha * DTI * dM

must be compared against.  Everything is [MEASURED] on the SGMC off-catalogue
proxy; the live bar is carried alongside in proxy credit units.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, uniform_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems48.evidence import (  # noqa: E402
    combine_yager,
    discounted_binary_mass,
    kernel_support,
    pignistic,
)
from gems48.metric import ALPHA, dti  # noqa: E402

R_DOTTED = 0.90
R_TIP = 0.90 * (0.11987588720357811 / 0.13446190223260976)

DOTTED = ROOT / "data/raw/dotted.tif"
TIP = ROOT / "data/raw/tip.tif"
TEMPLATE = ROOT / "data/raw/sample_submission.tif"
LABELS = ROOT / "data/raw/labels.tif"
SGMC = ROOT / "data/raw/external/derived_sgmc_faults_100m_u8.tif"

LIVE_DTI = 0.2778          # [ANCHOR] owner-reported, GEMSDOE32 H33-2-B2
LIVE_CREDIT_PER_DOT = 0.13446190223260976  # [MODEL] regime-A inversion of that anchor


def rd(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        return s.read(1)


def marginal(base: np.ndarray, group: np.ndarray, truth: np.ndarray) -> dict:
    b = dti(base.astype(np.float64), truth)
    both = np.maximum(base, group)
    g = dti(both.astype(np.float64), truth)
    n = float(group.sum())
    return {
        "added_cells": n,
        "base_tp": b.tp, "with_group_tp": g.tp,
        "marginal_tp": g.tp - b.tp,
        "marginal_per_cell": (g.tp - b.tp) / n if n else 0.0,
        "base_dti": b.dti, "with_group_dti": g.dti,
        "delta_dti": g.dti - b.dti,
    }


def main() -> None:
    dotted = (rd(DOTTED) > 0)
    tip = (rd(TIP) > 0)
    labels = rd(LABELS) > 0
    sgmc = rd(SGMC) > 0
    footprint = np.isfinite(rd(TEMPLATE))
    d_cat = distance_transform_edt(~labels)
    truth = sgmc & footprint & (d_cat >= 3.0)

    sup_d = kernel_support(dotted.astype(np.float64))
    sup_t = kernel_support(tip.astype(np.float64))
    a = discounted_binary_mass(sup_d, R_DOTTED)
    b = discounted_binary_mass(sup_t, R_TIP)
    bel, dis, u, k = combine_yager(a, b)
    betp = pignistic(bel, dis)

    inter = dotted & tip
    d_only = dotted & ~tip
    t_only = tip & ~dotted
    base = dotted.astype(np.float64)

    proxy_dti = dti(base, truth).dti
    # Convert the live acceptance bar into proxy credit units using the ratio of
    # the two instruments' mean credit per dot (live [MODEL] vs proxy [MEASURED]).
    proxy_credit_per_dot = dti(base, truth).tp / dotted.sum()
    scale = LIVE_CREDIT_PER_DOT / proxy_credit_per_dot
    live_bar_proxy_units = ALPHA * LIVE_DTI / scale

    out = {
        "schema": "GEMSDOE48-marginal-value-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "base": "dotted parent (GEMSDOE32 H33-2-B2)",
        "proxy_truth_pixels": int(truth.sum()),
        "proxy_dti_of_base": proxy_dti,
        "proxy_credit_per_dot_of_base": proxy_credit_per_dot,
        "live_to_proxy_credit_scale": scale,
        "acceptance_bars": {
            "live_bar_live_units": ALPHA * LIVE_DTI,
            "live_bar_in_proxy_units": live_bar_proxy_units,
            "proxy_native_bar": ALPHA * proxy_dti,
            "note": "[MODEL] the proxy's own bar is 3x more permissive than the live bar because the proxy truth set is ~5x denser than the hidden set; additions must be judged against the live bar expressed in proxy units.",
        },
    }

    # ------------------------------------------------- 1. tip-only, by corroboration
    rows = {}
    for lo, hi, tag in [(0.0, 0.0, "no_dotted_support_within_300m"),
                        (0.0, 1.0 / 3.0, "dotted_support_0_to_033"),
                        (1.0 / 3.0, 2.0 / 3.0, "dotted_support_033_to_066"),
                        (2.0 / 3.0, 1.01, "dotted_support_066_to_1")]:
        m = t_only & (sup_d >= lo) & (sup_d < hi)
        rows[f"tip_only__{tag}"] = marginal(base, m.astype(np.float64), truth)
    rows["tip_only__all"] = marginal(base, t_only.astype(np.float64), truth)
    # 2. tip-only by distance to the public catalogue
    for lo, hi, tag in [(0, 1, "dcat_lt_1px"), (1, 2, "dcat_1_2px"), (2, 3, "dcat_2_3px"), (3, 100, "dcat_ge_3px")]:
        m = t_only & (d_cat >= lo) & (d_cat < hi)
        rows[f"tip_only__{tag}"] = marginal(base, m.astype(np.float64), truth)
    # 3. non-dot "bridge" cells (no parent dot, both supports high)
    support_sum = sup_d + sup_t
    for lo, hi, tag in [(1.2, 1.5, "1.2_1.5"), (1.5, 2.1, "1.5_2.1")]:
        m = footprint & ~dotted & ~tip & (support_sum >= lo) & (support_sum < hi)
        rows[f"bridge_cells__sum_{lo}_{hi}"] = marginal(base, m.astype(np.float64), truth)
    # 4. candidate removal groups from the dotted parent itself (leave-out test)
    for lo, hi, tag in [(0.0, 0.40, "betp_lt_040"), (0.40, 0.80, "betp_040_080"), (0.80, 0.99, "betp_080_099")]:
        m = dotted & (betp >= lo) & (betp < hi)
        rows[f"dotted_remove__{tag}"] = {
            "cells": float(m.sum()),
            "dti_without_group": dti((dotted & ~m).astype(np.float64), truth).dti,
            "delta_dti_if_removed": dti((dotted & ~m).astype(np.float64), truth).dti - proxy_dti,
        }
    # 5. local geometric context of the dotted parent's dots vs realised credit
    from gems48.metric import credit_per_dot
    cred, _, _ = credit_per_dot(dotted.astype(np.float64), truth)
    dens3 = uniform_filter(dotted.astype(np.float64), size=7) * 49 - dotted  # neighbours in a 7x7 box
    feats = {}
    for nm, f in [("neighbour_count_7x7", dens3), ("dotted_support_neighbourhood", support_sum),
                  ("betp", betp), ("dist_to_catalogue", d_cat)]:
        q = np.quantile(f[dotted], np.linspace(0, 1, 6))
        bins = []
        for i in range(5):
            m = dotted & (f >= q[i]) & (f <= q[i + 1]) if i == 4 else dotted & (f >= q[i]) & (f < q[i + 1])
            n = int(m.sum())
            bins.append({"range": [float(q[i]), float(q[i + 1])], "dots": n,
                         "realised_credit_per_dot": float(cred[m].sum() / n) if n else 0.0,
                         "fraction_earning": float(((cred > 0) & m).sum() / n) if n else 0.0})
        feats[nm] = bins
    out["dotted_dot_quality_vs_feature"] = {
        "note": "[MEASURED] realised proxy credit per dot when the whole dotted parent is emitted, binned by a per-dot feature. Dots shadowed by a neighbour show zero realised credit and are the candidates for removal.",
        "features": feats}

    out["marginal_groups"] = rows
    for k, v in rows.items():
        if "marginal_per_cell" in v:
            v["above_live_bar"] = bool(v["marginal_per_cell"] > live_bar_proxy_units)
            v["safety_factor"] = v["marginal_per_cell"] / live_bar_proxy_units if live_bar_proxy_units else None
    (ROOT / "docs" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "data" / "h49-marginal-value.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ["proxy_dti_of_base", "live_to_proxy_credit_scale", "acceptance_bars"]}, indent=2))
    for k, v in rows.items():
        print(f"{k:44s}", {kk: (round(vv, 5) if isinstance(vv, float) else vv) for kk, vv in v.items()})


if __name__ == "__main__":
    main()
