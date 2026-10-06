#!/usr/bin/env python3
"""Forensic decomposition of the two parent families and live-anchored projection.

Everything written to ``docs/data/h49-parent-decomposition.json`` is either

* ``[MEASURED]``  - computed here from hash-pinned inputs with the published metric,
* ``[ANCHOR]``    - an owner-reported leaderboard score used as an input, or
* ``[MODEL]``     - a stated modelling assumption whose sensitivity is swept.

No cell of the report is allowed to present a modelled number as a measurement.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems48.evidence import kernel_support  # noqa: E402
from gems48.metric import ALPHA, BETA, credit_per_dot, dti  # noqa: E402

# ---------------------------------------------------------------- inputs
DOTTED = ROOT / "data/raw/dotted.tif"          # GEMSDOE32 H33-2-B2  (owner-reported 0.2778)
TIP = ROOT / "data/raw/tip.tif"                # GEMSDOE33 H33-D tip/step-over (owner-reported 0.2632)
TEMPLATE = ROOT / "data/raw/sample_submission.tif"
LABELS = ROOT / "data/raw/labels.tif"
SGMC = ROOT / "data/raw/external/derived_sgmc_faults_100m_u8.tif"

# ------------------------------------------------- owner-reported live anchors
LIVE = {
    "dotted": {"mass": 37654, "dti": 0.2778},
    "tip": {"mass": 41865, "dti": 0.2632},
}
# GEMSDOE32's measured pair: the same emission before/after removing 3,891 dots
# that sat within 100 m of the public catalogue (the "zero-credit" pair).
PAIR = {"before": {"mass": 44090, "dti": 0.2600}, "after": {"mass": 40199, "dti": 0.2708}}


def rd(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        return s.read(1)


def main() -> None:
    dotted = rd(DOTTED) > 0
    tip = rd(TIP) > 0
    labels = rd(LABELS) > 0
    sgmc = rd(SGMC) > 0
    template = rd(TEMPLATE)
    footprint = np.isfinite(template)

    inter = dotted & tip
    d_only = dotted & ~tip
    t_only = tip & ~dotted
    union = dotted | tip

    # ------------------------------------------------------------ proxy truth
    d_cat = distance_transform_edt(~labels)
    truth_off = sgmc & footprint & (d_cat >= 3.0)     # >= 300 m from the public catalogue
    truth_all = sgmc & footprint

    report: dict = {
        "schema": "GEMSDOE48-parent-decomposition-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "classes": {
            "intersection": int(inter.sum()),
            "dotted_only": int(d_only.sum()),
            "tip_only": int(t_only.sum()),
            "union": int(union.sum()),
            "dotted": int(dotted.sum()),
            "tip": int(tip.sum()),
            "jaccard": float(inter.sum() / union.sum()),
        },
        "proxy_truth": {
            "name": "USGS SGMC-derived faults, >=300 m from the public catalogue, inside the template footprint",
            "pixels_off_catalogue": int(truth_off.sum()),
            "pixels_all_sgmc": int(truth_all.sum()),
            "public_catalogue_pixels": int(labels.sum()),
            "warning": "[MODEL] the SGMC compilation is a stand-in for the hidden expert labels; it is not the test set.",
        },
    }

    # ------------------------------------------- proxy DTI with the published metric
    proxy = {}
    for name, arr in [
        ("dotted", dotted.astype(np.float64)),
        ("tip", tip.astype(np.float64)),
        ("union_binary", union.astype(np.float64)),
        ("intersection", inter.astype(np.float64)),
        ("naive_mean", 0.5 * (dotted.astype(np.float64) + tip.astype(np.float64))),
    ]:
        r = dti(arr, truth_off)
        proxy[name] = {**r.as_dict(), "emitted_dots": int((arr > 0).sum())}
    report["proxy_off_catalogue_dti"] = proxy

    # ------------------------------------- per-dot credit decomposition (proxy)
    cred_d, cnt_d, _ = credit_per_dot(dotted.astype(np.float64), truth_off)
    cred_t, cnt_t, _ = credit_per_dot(tip.astype(np.float64), truth_off)
    cred_u, _, _ = credit_per_dot(union.astype(np.float64), truth_off)

    def class_rates(cred, mask_of_file):
        out = {}
        for nm, m in [("intersection", inter), ("dotted_only", d_only), ("tip_only", t_only)]:
            sel = m & mask_of_file
            n = int(sel.sum())
            if n == 0:
                out[nm] = {"dots": 0, "credit": 0.0, "credit_per_dot": 0.0}
                continue
            c = float(cred[sel].sum())
            out[nm] = {"dots": n, "credit": c, "credit_per_dot": c / n}
        return out

    report["proxy_credit_by_class"] = {
        "dotted_file": class_rates(cred_d, dotted),
        "tip_file": class_rates(cred_t, tip),
        "union_file": class_rates(cred_u, union),
        "note": "[MEASURED] TP_w attributed to the predicted cell that realised each truth pixel's maximum; totals equal TP_w exactly.",
    }
    # how many dots earn any proxy credit at all
    for nm, cred, mask in [("dotted", cred_d, dotted), ("tip", cred_t, tip), ("union", cred_u, union)]:
        n = int(mask.sum())
        report["proxy_credit_by_class"].setdefault("coverage", {})[nm] = {
            "dots": n,
            "dots_with_credit": int(((cred > 0) & mask).sum()),
            "fraction_with_credit": float(((cred > 0) & mask).sum() / max(n, 1)),
        }

    # ------------------------------------------------- live-anchored inversion
    m0, s0 = PAIR["before"]["mass"], PAIR["before"]["dti"]
    m1, s1 = PAIR["after"]["mass"], PAIR["after"]["dti"]
    dm = m0 - m1
    # Removing dm dots that realise no credit leaves T unchanged while the
    # denominator falls by exactly alpha*dm:  1/s_after - 1/s_before = -alpha*dm/T
    t_pair = ALPHA * dm / (1.0 / s1 - 1.0 / s0) * -1.0 * -1.0
    t_pair = ALPHA * dm / (1.0 / s0 - 1.0 / s1)

    def regime_a_K(T, mass, s):
        """1/s = (alpha*M + beta*K)/T  (assumes F = M - T: no two dots share a truth pixel)."""
        return (T / s - ALPHA * mass) / BETA

    def regime_b_K(T, mass, s):
        """1/s = (alpha*T + alpha*M + beta*K)/T  (assumes F = M: every dot is essentially wasted)."""
        return (T / s - ALPHA * T - ALPHA * mass) / BETA

    reg = {}
    for tag, kfun, tfun in [
        ("A_no_sharing", regime_a_K, lambda mass, s, K: s * (ALPHA * mass + BETA * K)),
        ("B_all_wasted", regime_b_K, lambda mass, s, K: s * (ALPHA * mass + BETA * K) / (1 - ALPHA * s)),
    ]:
        K = kfun(t_pair, m1, s1)
        T = {
            "dotted": tfun(LIVE["dotted"]["mass"], LIVE["dotted"]["dti"], K),
            "tip": tfun(LIVE["tip"]["mass"], LIVE["tip"]["dti"], K),
        }
        reg[tag] = {
            "assumption": {"A_no_sharing": "F = M - T", "B_all_wasted": "F = M"}[tag],
            "hidden_truth_pixels_K": K,
            "weighted_tp_T": T,
            "credit_per_dot": {k: T[k] / LIVE[k]["mass"] for k in T},
            "weighted_recall": {k: T[k] / K for k in T},
        }
    report["live_anchor_inversion"] = {
        "inputs": {"pair_before": PAIR["before"], "pair_after": PAIR["after"],
                   "removed_dots": dm, "zero_credit_assumption": "[MODEL] owner-reported; the removed dots sat within 100 m of the masked public catalogue"},
        "weighted_tp_of_pair": t_pair,
        "regimes": reg,
        "provenance": "[ANCHOR] owner-reported leaderboard scores; [MODEL] regime assumptions; not organizer-confirmed.",
    }

    # ------------- relative credit rates by class, transferred onto the live scale
    # Proxy rates are *relative*; the live scale is fixed by the two live anchors.
    I, DO, TO = int(inter.sum()), int(d_only.sum()), int(t_only.sum())
    proj = {}
    for tag, regtag in [("A_no_sharing", "A_no_sharing"), ("B_all_wasted", "B_all_wasted")]:
        T_d = reg[regtag]["weighted_tp_T"]["dotted"]
        T_t = reg[regtag]["weighted_tp_T"]["tip"]
        # proxy shape: fraction of each file's proxy credit that sits in each class
        sd = report["proxy_credit_by_class"]["dotted_file"]
        st = report["proxy_credit_by_class"]["tip_file"]
        tot_d = sd["intersection"]["credit"] + sd["dotted_only"]["credit"]
        tot_t = st["intersection"]["credit"] + st["tip_only"]["credit"]
        f_I_d = sd["intersection"]["credit"] / tot_d if tot_d else 0.0
        f_I_t = st["intersection"]["credit"] / tot_t if tot_t else 0.0
        f_I = 0.5 * (f_I_d + f_I_t)
        e_I = T_d * f_I / I
        e_DO = T_d * (1 - f_I) / DO
        e_TO = (T_t - I * e_I) / TO
        bar = ALPHA * LIVE["dotted"]["dti"]
        # candidate emissions
        cands = {
            "dotted_parent": (I * e_I + DO * e_DO, LIVE["dotted"]["mass"]),
            "tip_parent": (I * e_I + TO * e_TO, LIVE["tip"]["mass"]),
            "union": (I * e_I + DO * e_DO + TO * e_TO, LIVE["dotted"]["mass"] + TO),
            "intersection_only": (I * e_I, I),
            "dotted_plus_tip_only": (I * e_I + DO * e_DO + TO * e_TO, LIVE["dotted"]["mass"] + TO),
        }
        out = {}
        for nm, (T, M) in cands.items():
            if tag == "A_no_sharing":
                sc = T / (ALPHA * M + BETA * reg[regtag]["hidden_truth_pixels_K"])
            else:
                sc = T / (ALPHA * T + ALPHA * M + BETA * reg[regtag]["hidden_truth_pixels_K"])
            out[nm] = {"weighted_tp": T, "mass": M, "projected_dti": sc,
                       "delta_vs_dotted_parent": sc - LIVE["dotted"]["dti"]}
        proj[tag] = {
            "proxy_credit_fraction_in_intersection": f_I,
            "credit_per_dot": {"intersection": e_I, "dotted_only": e_DO, "tip_only": e_TO},
            "marginal_bar_alpha_times_dti": bar,
            "tip_only_above_bar": bool(e_TO > bar),
            "candidates": out,
        }
    report["live_projection_by_class"] = {
        "method": "[MODEL] proxy-measured *relative* credit split between the three dot classes, rescaled so each parent reproduces its owner-reported live score; both extreme regimes are reported.",
        "regimes": proj,
    }

    # ------------------------------------------------- kernel support geometry
    sup_d = kernel_support(dotted.astype(np.float64))
    sup_t = kernel_support(tip.astype(np.float64))
    report["kernel_support_fields"] = {
        "dotted": {"cells_gt0": int((sup_d > 0).sum()), "mean": float(sup_d.mean())},
        "tip": {"cells_gt0": int((sup_t > 0).sum()), "mean": float(sup_t.mean())},
        "correlation_on_union": float(np.corrcoef(sup_d[union], sup_t[union])[0, 1]),
    }

    outp = ROOT / "docs" / "data" / "h49-parent-decomposition.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
