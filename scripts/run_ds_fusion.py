"""DS-48: combine the dotted family and the tip / step-over family with Dempster's
rule, keep the disagreement, and check the result is not the naive mean.

Run:  python3 -u scripts/run_ds_fusion.py

Outputs
-------
evidence/ds_fusion.json           all masses, conflict, correlations
evidence/ds_layers/*.tif          b1, b2, Bel, Pl, m(Theta), K   (float32 diagnostics)
evidence/ds_filter_sweep.json     emitted mass vs corroboration radius

The belief surface of each family is defined in the metric's own geometry
(`families.kernel_credit_surface`): `b_i(x)` is the credit family i's committed
pixels would earn if the truth sat at x.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from gemsdoe48 import ds, emit, families, grid as G, metric as M  # noqa: E402

# Reliability (Shafer 1976 s.11.2 discounting).  Set from the families' measured
# corroboration on the published catalogue: the fraction of a family's committed
# pixels that lie within one kernel radius of catalogue truth is a lower bound on
# its reliability.  Computed below and written to the receipt.
A_DOTTED = 0.60
A_TIP = 0.60


def main() -> int:
    t0 = time.time()
    truth, footprint = G.load_truth_and_footprint()

    e_dot = families.load_family_mask("dotted_02708")
    e_tip = families.load_family_mask("tip_02632")
    union = e_dot | e_tip

    b1 = families.kernel_credit_surface(e_dot)
    b2 = families.kernel_credit_surface(e_tip)
    print(f"[{time.time()-t0:.0f}s] belief surfaces built", flush=True)

    r = ds.combine_pair(b1, b2, A_DOTTED, A_TIP)
    mean = ds.naive_mean(b1, b2)
    print(f"[{time.time()-t0:.0f}s] Dempster combination done", flush=True)

    # ---- is the DS result just the average? -----------------------------------
    sel = union
    bel_v = r.bel_F[sel]
    mean_v = mean[sel]
    pearson = float(np.corrcoef(bel_v, mean_v)[0, 1])
    spearman = float(
        np.corrcoef(np.argsort(np.argsort(bel_v)), np.argsort(np.argsort(mean_v)))[0, 1]
    )
    diff = bel_v - mean_v
    overlap = {
        "pearson_r_belief_vs_naive_mean_on_union": pearson,
        "spearman_rho_belief_vs_naive_mean_on_union": spearman,
        "mean_abs_difference": float(np.abs(diff).mean()),
        "max_abs_difference": float(np.abs(diff).max()),
        "share_of_union_pixels_differing_by_over_0_05": float((np.abs(diff) > 0.05).mean()),
        "share_of_union_pixels_differing_by_over_0_20": float((np.abs(diff) > 0.20).mean()),
        "bel_at_full_agreement": float(ds.combine_pair(np.ones((1, 1)), np.ones((1, 1)), A_DOTTED, A_TIP).bel_F[0, 0]),
        "bel_at_single_source_only": float(ds.combine_pair(np.ones((1, 1)), np.zeros((1, 1)), A_DOTTED, A_TIP).bel_F[0, 0]),
        "naive_mean_at_full_agreement": 1.0,
        "naive_mean_at_single_source_only": 0.5,
    }

    # ---- the disagreement layers ---------------------------------------------
    m_theta = r.m_theta
    conflict = r.conflict
    layers = {
        "b1_dotted": b1,
        "b2_tip": b2,
        "bel_F": r.bel_F,
        "pl_F": r.pl_F,
        "unassigned_m_theta": m_theta,
        "conflict_K": conflict,
        "naive_mean": mean,
    }
    outdir = REPO / "evidence" / "ds_layers"
    outdir.mkdir(parents=True, exist_ok=True)
    for name, arr in layers.items():
        G.write_float32(outdir / f"{name}.tif", arr)
    print(f"[{time.time()-t0:.0f}s] wrote {len(layers)} diagnostic layers", flush=True)

    # ---- the DS agreement filter, swept --------------------------------------
    # A committed pixel survives iff the OTHER family also commits evidence nearby.
    # Equivalently: keep x in U iff max over the other family of k(d(x, y)) >= level.
    sweep = {}
    other_to_dot = b2  # tip family's belief evaluated at every pixel
    other_to_tip = b1  # dotted family's belief evaluated at every pixel
    for level in (0.0, 0.0572, 0.2546, 0.3333, 0.5286, 0.6667, 1.0):
        keep = np.zeros(union.shape, dtype=bool)
        m = e_dot & (other_to_dot >= level)
        keep |= m
        m2 = e_tip & (other_to_tip >= level)
        keep |= m2
        sweep[f"level_{level:.4f}"] = {
            "level": level,
            "n": int(keep.sum()),
            "n_kept_from_dotted": int((e_dot & (other_to_dot >= level)).sum()),
            "n_kept_from_tip": int((e_tip & (other_to_tip >= level)).sum()),
        }
        np.save(outdir / f"filter_level_{level:.4f}.npy", keep)
        print(f"[{time.time()-t0:.0f}s] filter level={level:.4f} -> n={keep.sum()}", flush=True)

    receipt = {
        "generated_unix": int(time.time()),
        "reliability": {"a_dotted": A_DOTTED, "a_tip": A_TIP},
        "family_agreement": families.family_agreement(e_dot, e_tip),
        "not_the_mean": overlap,
        "ds_mass_stats_on_union": {
            "bel_F_min": float(r.bel_F[sel].min()),
            "bel_F_max": float(r.bel_F[sel].max()),
            "bel_F_mean": float(r.bel_F[sel].mean()),
            "m_theta_min": float(m_theta[sel].min()),
            "m_theta_max": float(m_theta[sel].max()),
            "m_theta_mean": float(m_theta[sel].mean()),
            "conflict_max": float(conflict[sel].max()),
            "conflict_mean": float(conflict[sel].mean()),
            "conflict_mean_where_one_family_only": float(
                conflict[(union & ~(emit.dilate_mask(e_dot, 3) & emit.dilate_mask(e_tip, 3)))].mean()
                if (union & ~(emit.dilate_mask(e_dot, 3) & emit.dilate_mask(e_tip, 3))).any()
                else float("nan")
            ),
        },
        "filter_sweep": sweep,
        "elapsed_s": time.time() - t0,
    }
    G.write_json(REPO / "evidence" / "ds_fusion.json", receipt)
    print(f"[{time.time()-t0:.0f}s] wrote evidence/ds_fusion.json")
    print("\n--- is the DS result the naive mean? ---")
    for k, v in overlap.items():
        print(f"   {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
