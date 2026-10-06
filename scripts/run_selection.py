"""SELECT-48: choose the submission by a frozen rule, on measurements.

Run:  python3 -u scripts/run_selection.py

The rule, frozen before the run:

  R1 (contested removal, from Dempster-Shafer)
      A pixel committed by one family survives only if the *other* family also
      commits evidence within the metric's own kernel geometry -- i.e. only if
      its Dempster-Shafer belief exceeds the value reached by a single source
      alone.  Pixels where the two families disagree are removed.

  R2 (covering-optimal re-emission)
      The surviving corridor is re-covered by a hexagonal lattice at a ladder of
      spacings; each cover is greedily completed and batched-pruned, so the
      guarantee "every corridor pixel is within `rho` of a dot" holds by
      construction and `rho` is re-measured exactly afterwards.

  R3 (promotion gate -- must hold for a candidate to be shipped)
      (a) the emitted mass is <= the live-best artifact it must beat;
      (b) TPw on BOTH independent truth layers is >= 95 % of the live-best
          artifact's at that same mass;
      (c) the live-anchored credit-loss budget is not overspent
          (safety factor >= 2.0, computed in live_anchor.py).

Nothing here is a forecast of an organizer score.  Every number is a local
measurement and is written to evidence/selection.json.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from gemsdoe48 import ds, emit, families, grid as G, metric as M  # noqa: E402
from gemsdoe48.live_anchor import LiveAnchor  # noqa: E402

A_DOTTED = 0.60
A_TIP = 0.60
LIVE_BEST_PX = 37654  # the 0.2778 artifact, the best live result the group has


def main() -> int:
    t0 = time.time()
    truth, footprint = G.load_truth_and_footprint()
    sgmc = G.read_mask(REPO / "data/official/derived_sgmc_faults_100m.tif")
    k_to_cat = M.max_kernel_to_truth(truth)
    sgmc_off = sgmc & (k_to_cat == 0.0)

    e_dot = families.load_family_mask("dotted_02708")
    e_tip = families.load_family_mask("tip_02632")
    union = e_dot | e_tip

    b1 = families.kernel_credit_surface(e_dot)
    b2 = families.kernel_credit_surface(e_tip)
    r = ds.combine_pair(b1, b2, A_DOTTED, A_TIP)
    bel = r.bel_F
    single_source_bel = float(
        ds.combine_pair(np.ones((1, 1)), np.zeros((1, 1)), A_DOTTED, A_TIP).bel_F[0, 0]
    )
    print(f"[{time.time()-t0:.0f}s] DS layers built; single-source belief = {single_source_bel:.4f}")

    truth_layers = {
        "catalogue_all": truth,
        "catalogue_in_corridor_r3": truth & emit.dilate_mask(emit.dilate_mask(union, 1), 3),
        "sgmc_off_catalogue": sgmc_off,
    }
    kt = {k: M.max_kernel_to_truth(v) for k, v in truth_layers.items()}

    def score(points: np.ndarray) -> dict:
        p = points.astype(np.float64)
        out = {"n": int(points.sum())}
        for name, tmask in truth_layers.items():
            res = M.dti(p, tmask, footprint, precomputed_max_kernel=kt[name])
            out[name] = {
                "dti": res.dti, "tpw": res.tpw, "fpw": res.fpw,
                "mass": res.mass, "n_truth": res.n_truth,
                "coverage": res.coverage,
                "tpw_per_mass": res.tpw / max(res.mass, 1.0),
            }
        return out

    results: dict = {"stages": {}, "candidates": {}}

    # ---- baselines ----------------------------------------------------------
    baselines = {
        "live_best_02778": families.load_family_mask("dotted_b2_prune_02778"),
        "shipped_dotted_02708": e_dot,
        "shipped_union": union,
    }
    for name, pts in baselines.items():
        results["candidates"][name] = {"kind": "baseline", **score(pts)}
        d = results["candidates"][name]
        print(f"[{time.time()-t0:.0f}s] BASE {name:<22} n={d['n']:>6} "
              f"catTPw={d['catalogue_all']['tpw']:>8.0f} "
              f"corrTPw={d['catalogue_in_corridor_r3']['tpw']:>7.0f} "
              f"sgmcTPw={d['sgmc_off_catalogue']['tpw']:>8.0f}", flush=True)

    # ---- R1: DS contested removal -------------------------------------------
    corroborated = (e_dot & (b2 >= single_source_bel)) | (e_tip & (b1 >= single_source_bel))
    results["stages"]["R1_ds_filter"] = {
        "rule": "keep a family's pixel iff the other family's belief at that pixel "
                ">= the single-source Dempster belief",
        "single_source_bel": single_source_bel,
        "n": int(corroborated.sum()),
        "from_dotted": int((e_dot & (b2 >= single_source_bel)).sum()),
        "from_tip": int((e_tip & (b1 >= single_source_bel)).sum()),
    }
    results["candidates"]["R1_ds_filtered_union"] = {"kind": "R1", **score(corroborated)}
    d = results["candidates"]["R1_ds_filtered_union"]
    print(f"[{time.time()-t0:.0f}s] R1   ds_filtered_union  n={d['n']:>6} "
          f"catTPw={d['catalogue_all']['tpw']:>8.0f} "
          f"corrTPw={d['catalogue_in_corridor_r3']['tpw']:>7.0f} "
          f"sgmcTPw={d['sgmc_off_catalogue']['tpw']:>8.0f}", flush=True)

    # ---- R2: covering-optimal re-emission -----------------------------------
    corridor = emit.dilate_mask(corroborated, 1)
    hex_rows = {}
    for spacing in (1.6, 2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.4, 4.8, 5.6, 6.4):
        cov = emit.cover_region(corridor, spacing, prune=True)
        key = f"R2_hex_{spacing:.1f}"
        results["candidates"][key] = {
            "kind": "R2",
            "spacing": spacing,
            "target_radius": cov["target_radius"],
            "measured_radius": cov["measured_radius"],
            **score(cov["points"]),
        }
        d = results["candidates"][key]
        hex_rows[key] = d
        print(f"[{time.time()-t0:.0f}s] R2   {key:<18} n={d['n']:>6} r={cov['measured_radius']:.3f} "
              f"catTPw={d['catalogue_all']['tpw']:>8.0f} "
              f"corrTPw={d['catalogue_in_corridor_r3']['tpw']:>7.0f} "
              f"sgmcTPw={d['sgmc_off_catalogue']['tpw']:>8.0f}", flush=True)
        np.save(REPO / "evidence" / "ds_layers" / f"{key}.npy", cov["points"])

    # ---- R3: promotion gate -------------------------------------------------
    base = results["candidates"]["live_best_02778"]
    anchor = LiveAnchor()
    gate_rows = {}
    for name, d in results["candidates"].items():
        if d.get("kind") == "baseline":
            continue
        mass = d["n"]
        corridor_loss = max(
            0.0, base["catalogue_in_corridor_r3"]["tpw"] - d["catalogue_in_corridor_r3"]["tpw"]
        )
        sgmc_loss = max(
            0.0, base["sgmc_off_catalogue"]["tpw"] - d["sgmc_off_catalogue"]["tpw"]
        )
        measured_loss = max(corridor_loss, sgmc_loss)
        rows = {
            "n": mass,
            "mass_ok": mass <= LIVE_BEST_PX,
            "catalogue_all_tpw_ratio": d["catalogue_all"]["tpw"] / base["catalogue_all"]["tpw"],
            "corridor_tpw_ratio": d["catalogue_in_corridor_r3"]["tpw"] / base["catalogue_in_corridor_r3"]["tpw"],
            "sgmc_tpw_ratio": d["sgmc_off_catalogue"]["tpw"] / base["sgmc_off_catalogue"]["tpw"],
            "measured_credit_loss_corridor": corridor_loss,
            "measured_credit_loss_sgmc": sgmc_loss,
            "anchor": anchor.assess_removal(
                n_removed=max(0, LIVE_BEST_PX - mass), measured_credit_loss=measured_loss
            ),
        }
        rows["passes"] = bool(
            rows["mass_ok"]
            and rows["catalogue_all_tpw_ratio"] >= 0.95
            and rows["corridor_tpw_ratio"] >= 0.95
            and rows["sgmc_tpw_ratio"] >= 0.95
            and rows["anchor"]["safety"] >= 2.0
        )
        gate_rows[name] = rows
        print(f"[{time.time()-t0:.0f}s] GATE {name:<18} n={mass:>6} "
              f"cat={rows['catalogue_all_tpw_ratio']:.3f} corr={rows['corridor_tpw_ratio']:.3f} "
              f"sgmc={rows['sgmc_tpw_ratio']:.3f} safety={rows['anchor']['safety']:.2f} "
              f"-> {'PASS' if rows['passes'] else 'fail'}", flush=True)

    passing = sorted(
        [n for n, v in gate_rows.items() if v["passes"]], key=lambda n: gate_rows[n]["n"]
    )
    # ---- the frozen rule's own defects, recorded with the rule -----------------
    # R3 is kept for the record, NOT as a promotion instrument.  Two of its three
    # conditions are degenerate on this base, and saying so in the receipt is the
    # difference between "a gate passed" and "a gate could not fail":
    #
    #   (a) catalogue_all / corridor TPw ratios divide by the live-best base's own
    #       catalogue credit, which is 378.0 -- the base was pruned to sit off the
    #       published catalogue, so the denominator is ~0 and ANY candidate that
    #       puts mass back near the catalogue shows a double-digit ratio.  The
    #       catalogue instrument is separately known to be anti-monotone with the
    #       live ladder (Spearman -1.0 on n = 4, irregularity IR-48-04), so this
    #       term is uninformative in both directions.
    #   (b) the safety factor divides the removal budget by the measured credit
    #       loss.  A candidate that COVERS the same SGMC pixels as the base loses
    #       nothing measurable, so the safety saturates at its 99.0 ceiling and
    #       the >= 2.0 test cannot fail.
    #
    # Consequence: `eligible` below lists candidates that cleared a gate which
    # could not fail.  Nothing in this file promotes a candidate.  The shipped
    # artifact comes from scripts/build_submission.py; see
    # registry/submission_build.json -> headline_negative_result.
    results["gate"] = gate_rows
    results["eligible"] = passing
    results["chosen"] = passing[0] if passing else None
    results["gate_caveat"] = {
        "status": "degenerate, not a promotion instrument",
        "catalogue_term": "uninformative: divides by the base's own catalogue credit "
                          "(378.0), and the catalogue layer is anti-monotone with the "
                          "live ladder (IR-48-04)",
        "safety_term": "saturates at the 99.0 ceiling whenever the measured SGMC credit "
                       "loss is 0.0, so 'safety >= 2.0' cannot fail",
        "action": "treat `eligible` and `chosen` as descriptive only; no candidate is "
                  "promoted by this script",
        "shipped_artifact_built_by": "scripts/build_submission.py",
    }
    results["elapsed_s"] = time.time() - t0
    G.write_json(REPO / "evidence" / "selection.json", results)
    print(f"\n[{time.time()-t0:.0f}s] eligible: {passing}")
    print(f"[{time.time()-t0:.0f}s] chosen  : {results['chosen']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
