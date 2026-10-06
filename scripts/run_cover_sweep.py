"""COVER-48: does controlling the *covering radius* instead of the *minimum spacing*
buy emitted mass for free?

Run:  python3 -u scripts/run_cover_sweep.py

Outputs evidence/cover_sweep.json and evidence/cover_pareto.json.

Method
------
1. Build the union support U of the two families (dotted 0.2708, tip/step-over)
   and the corridor R = dilate(U, 1 px).
2. Measure, for the *shipped* emissions, N and the covering-radius profile of R.
3. Build hexagonal covers of R at a ladder of spacings, each greedily completed
   and batched-pruned, and measure the same profile.
4. Score every candidate on three truth layers with the official metric at the
   candidate's own emitted mass, so mass and coverage are both visible.

The three truth layers are independent of each other and none of them is the
competition's hidden label set, so this file reports *coverage* comparisons, not
forecasts.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from gemsdoe48 import emit, families, grid as G, metric as M  # noqa: E402


def main() -> int:
    t0 = time.time()
    truth, footprint = G.load_truth_and_footprint()
    sgmc = G.read_mask(REPO / "data/official/derived_sgmc_faults_100m.tif")

    k_to_cat = M.max_kernel_to_truth(truth)
    sgmc_off = sgmc & (k_to_cat == 0.0)

    e_dot = families.load_family_mask("dotted_02708")
    e_tip = families.load_family_mask("tip_02632")
    union = e_dot | e_tip
    corridor = emit.dilate_mask(union, 1)

    truth_layers = {
        "catalogue_all": truth,
        "catalogue_in_corridor_r3": truth & emit.dilate_mask(corridor, 3),
        "sgmc_off_catalogue": sgmc_off,
    }
    kt = {name: M.max_kernel_to_truth(t) for name, t in truth_layers.items()}
    print(f"[{time.time()-t0:.0f}s] truth layers ready: "
          + ", ".join(f"{k}={int(v.sum())}" for k, v in truth_layers.items()), flush=True)

    def score(points: np.ndarray) -> dict:
        out = {
            "n": int(points.sum()),
            "cover_over_corridor": emit.coverage_profile(points, corridor),
        }
        p = points.astype(np.float64)
        for name, tmask in truth_layers.items():
            res = M.dti(p, tmask, footprint, precomputed_max_kernel=kt[name])
            out[name] = {
                "dti": res.dti,
                "tpw": res.tpw,
                "fpw": res.fpw,
                "mass": res.mass,
                "n_truth": res.n_truth,
                "coverage": res.coverage,
                "tpw_per_mass": res.tpw / max(res.mass, 1.0),
            }
        return out

    results: dict = {
        "generated_unix": int(time.time()),
        "truth_layer_px": {k: int(v.sum()) for k, v in truth_layers.items()},
        "shipped": {},
        "hex_covers": {},
        "notes": [
            "TPw is measured on three independent truth layers so that a gain cannot "
            "be an artefact of one proxy.",
            "The catalogue layers are the organizers' published catalogue; the hidden "
            "competition truth is a different, withheld population (see docs/research).",
        ],
    }

    candidates: list[tuple[str, str, np.ndarray]] = [
        ("shipped", "shipped_dotted_02708", e_dot),
        ("shipped", "shipped_tip_02632", e_tip),
        ("shipped", "shipped_union", union),
    ]
    for spacing in (2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.4, 4.8):
        r = emit.cover_region(corridor, spacing, keep_radius=1, prune=True)
        results.setdefault("hex_build", {})[f"hex_{spacing:.1f}"] = {
            "spacing": spacing,
            "target_radius": r["target_radius"],
            "measured_radius": r["measured_radius"],
        }
        candidates.append(("hex_covers", f"hex_{spacing:.1f}", r["points"]))
        print(f"[{time.time()-t0:.0f}s] built hex_{spacing:.1f} n={r['n']} "
              f"radius={r['measured_radius']:.3f}", flush=True)

    for group, name, pts in candidates:
        results[group][name] = score(pts)
        d = results[group][name]
        print(
            f"[{time.time()-t0:.0f}s] {name:<24} n={d['n']:>6} "
            f"r_max={d['cover_over_corridor']['max']:.2f} "
            f"r_mean={d['cover_over_corridor']['mean']:.3f} | "
            f"cat tpw={d['catalogue_all']['tpw']:>7.0f} dti={d['catalogue_all']['dti']:.4f} | "
            f"sgmc tpw={d['sgmc_off_catalogue']['tpw']:>7.0f} "
            f"dti={d['sgmc_off_catalogue']['dti']:.4f}",
            flush=True,
        )

    results["elapsed_s"] = time.time() - t0
    G.write_json(REPO / "evidence" / "cover_sweep.json", results)

    pareto = []
    for group in ("shipped", "hex_covers"):
        for name, r in results[group].items():
            pareto.append(
                {
                    "group": group,
                    "name": name,
                    "n": r["n"],
                    "max_radius_over_corridor": r["cover_over_corridor"]["max"],
                    "mean_radius_over_corridor": r["cover_over_corridor"]["mean"],
                    "tpw_catalogue": r["catalogue_all"]["tpw"],
                    "dti_catalogue": r["catalogue_all"]["dti"],
                    "tpw_sgmc_off": r["sgmc_off_catalogue"]["tpw"],
                    "dti_sgmc_off": r["sgmc_off_catalogue"]["dti"],
                }
            )
    pareto.sort(key=lambda d: d["n"])
    G.write_json(REPO / "evidence" / "cover_pareto.json", {"frontier": pareto})
    print(f"\n[{time.time()-t0:.0f}s] wrote evidence/cover_sweep.json + cover_pareto.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
