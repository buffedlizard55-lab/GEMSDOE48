"""Retired SELECT-48 gate — forensic reproduction only.

The historical rule combined public-proxy comparisons with an invalidated
live-anchor removal budget (``FPw=S-TPw``). The gate's ``passes``, ``eligible``,
and ``chosen`` values are not promotion evidence and do not predict organizer
scores. The live-best 0.2778 attribution is owner-reported and not linked to local
bytes by an organizer receipt. This script refuses by default; explicit
``--legacy-audit-only`` reproduces old diagnostics under ``evidence/forensic/selection-legacy/`` by default.
"""

from __future__ import annotations

import argparse
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
LIVE_BEST_PX = 37654  # owner-reported 0.2778 attribution; local-file linkage unverified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-audit-only", action="store_true",
                        help="required opt-in to reproduce the invalidated historical gate")
    parser.add_argument("--output-dir", type=Path,
                        default=REPO / "evidence/forensic/selection-legacy",
                        help="forensic output directory; never writes active download or registry paths")
    args = parser.parse_args()
    if not args.legacy_audit_only:
        parser.error("retired gate relies on invalidated live-anchor inversion; pass --legacy-audit-only only for forensic reproduction")
    print("FORENSIC REPRODUCTION ONLY — INVALIDATED LIVE GATE; NO PROMOTION DECISION")
    output_dir = args.output_dir if args.output_dir.is_absolute() else REPO / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "ds_layers").mkdir(parents=True, exist_ok=True)
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

    results: dict = {
        "validity_status": "INVALIDATED_FORENSIC_ONLY_DO_NOT_USE_FOR_PROMOTION",
        "invalidation_reason": "The live-anchor removal budget assumes the invalid FPw=S-TPw substitution; local-file-to-leaderboard linkage is also unverified.",
        "proxy_measurement_scope": "Public-proxy metrics are local diagnostics only; they are not private-label scores.",
        "stages": {},
        "candidates": {},
    }

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
        np.save(output_dir / "ds_layers" / f"{key}.npy", cov["points"])

    # ---- R3: promotion gate -------------------------------------------------
    base = results["candidates"]["live_best_02778"]
    anchor = LiveAnchor(legacy_audit_only=True)
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
        rows["legacy_rule_passes_not_promotion"] = bool(
            rows["mass_ok"]
            and rows["catalogue_all_tpw_ratio"] >= 0.95
            and rows["corridor_tpw_ratio"] >= 0.95
            and rows["sgmc_tpw_ratio"] >= 0.95
            and rows["anchor"]["safety_invalidated"] >= 2.0
        )
        gate_rows[name] = rows
        print(f"[{time.time()-t0:.0f}s] LEGACY GATE {name:<18} n={mass:>6} "
              f"cat={rows['catalogue_all_tpw_ratio']:.3f} corr={rows['corridor_tpw_ratio']:.3f} "
              f"sgmc={rows['sgmc_tpw_ratio']:.3f} safety={rows['anchor']['safety_invalidated']:.2f} "
              f"-> {'HISTORICALLY PASS' if rows['legacy_rule_passes_not_promotion'] else 'historically fail'} (NOT PROMOTION)", flush=True)

    passing = sorted(
        [n for n, v in gate_rows.items() if v["legacy_rule_passes_not_promotion"]],
        key=lambda n: gate_rows[n]["n"]
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
    results["legacy_gate_diagnostics"] = gate_rows
    results["legacy_passed_candidates_not_promotion"] = passing
    results["legacy_first_candidate_not_promotion"] = passing[0] if passing else None
    results["gate_caveat"] = {
        "status": "invalidated, degenerate, and not a promotion instrument",
        "calibration": "the live-anchor safety budget depends on FPw=S-TPw, an invalid general substitution",
        "catalogue_term": "uninformative: divides by the base's own catalogue credit (378.0); the catalogue layer is anti-monotone with the live ladder (IR-48-04)",
        "safety_term": "historical safety saturates at 99.0 when measured proxy loss is 0.0; it is not a private-label bound",
        "action": "no candidate is promoted or selected by this forensic script",
        "shipped_artifact_built_by": "scripts/build_submission.py (historical reference only)",
    }
    results["elapsed_s"] = time.time() - t0
    results["forensic_output_dir"] = str(output_dir)
    G.write_json(output_dir / "selection_legacy.json", results)
    print(f"\n[{time.time()-t0:.0f}s] historical gate candidates (NOT promotion evidence): {passing}")
    print(f"[{time.time()-t0:.0f}s] historical first candidate (NOT selected): {results['legacy_first_candidate_not_promotion']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
