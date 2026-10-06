#!/usr/bin/env python3
"""Build, independently re-read, and audit the GEMSDOE48 H49 submission.

H49 = Dempster-Shafer fusion of the two strongest independently built families,
emitted through a mass-budgeted, spatially balanced allocation.

Pipeline (every constant preregistered before the proxy screen)
---------------------------------------------------------------
1.  Parents (SHA-256 pinned)
      dotted : GEMSDOE32 H33-2-B2   37,654 cells, owner-reported live 0.2778
      tip    : GEMSDOE33 H33-D tip / step-over, 41,865 cells, owner-reported live 0.2632
2.  Evidence.  Each sparse family is turned into the graded field
    s(x) = max over its cells of the competition's own triangular kernel
    k(d) = max(1 - d/300m, 0), so s is "the credit this cell would realise if a
    truth pixel sat on it" -- the natural currency of the published metric.
3.  Masses.  Shafer discounting of each source's categorical opinion:
    m(F) = r*s, m(N) = r*(1-s), m(Theta) = 1-r, with r_dotted = 0.90 and
    r_tip = 0.90 x (measured live credit-per-dot ratio of the two parents).
4.  Combination.  Conjunctive rule; the empty-set mass K is the conflict.
    Yager's modified Dempster rule transfers K to m(Theta) so the disagreement
    survives as unassigned mass (classical Dempster normalisation deletes it).
    Dempster-normalised belief is computed too, for the documented comparison.
5.  Emission.  Cells are admitted in descending pignistic probability
    BetP = Bel + m(Theta)/2, subject to a minimum separation of 2.5 cells (the
    spacing regime that won live: d = 2.8 px beat d = 1.5 px), until the budget
    is reached.  Admitted cells are emitted at p = 1, which is optimal because
    both credit and cost are linear in p while credit per truth pixel is capped.
6.  Diagnostics.  The unassigned mass (m(Theta) + K) is written as its own
    GeoTIFF, together with the normalised combined belief field.

Outputs
-------
docs/downloads/<name>.tif                      primary submission
docs/downloads/<name>-unassigned-diagnostic.tif disagreement / uncertainty layer
docs/downloads/<name>-belief-field.tif         normalised combined belief (diagnostic)
docs/downloads/<name>.zip                      single-member ZIP of the primary
docs/downloads/<name>-audit.json               independent byte re-read + checks
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems48.evidence import (  # noqa: E402
    combine_dempster,
    combine_yager,
    discounted_binary_mass,
    kernel_support,
    pignistic,
)
from gems48.emission import poisson_sample  # noqa: E402
from gems48.metric import ALPHA, dti  # noqa: E402

STEM = "gemsdoe48-h49-ds-conflict-balanced-20261006"
OUTDIR = ROOT / "docs" / "downloads"

INPUTS = {
    "dotted": (ROOT / "data/raw/dotted.tif", "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"),
    "tip": (ROOT / "data/raw/tip.tif", "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757"),
    "template": (ROOT / "data/raw/sample_submission.tif", "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"),
    "labels": (ROOT / "data/raw/labels.tif", "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"),
    "sgmc": (ROOT / "data/raw/external/derived_sgmc_faults_100m_u8.tif", "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"),
}

# ------------------------------------------------------- preregistered constants
LIVE_DOTTED, LIVE_TIP = 0.2778, 0.2632          # [ANCHOR] owner-reported
R_DOTTED = 0.90
EFFICIENCY = 0.11987588720357811 / 0.13446190223260976
R_TIP = 0.90 * EFFICIENCY
SPACING = 2.5                                    # cells (250 m)
BUDGET = 47905                                   # = |dotted U tip|: both families fully represented
NB = 4                                           # 4x4 = 16 spatial blocks


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_checked(path: Path, expected: str):
    got = sha(path)
    if got != expected:
        raise SystemExit(f"hash mismatch: {path}: {got} != {expected}")
    with rasterio.open(path) as src:
        return src.read(1), src.profile.copy(), src.transform, src.crs


def write_tif(path: Path, data: np.ndarray, profile: dict) -> None:
    p = dict(profile)
    p.update(count=1, dtype="float32", nodata=None, compress="deflate", predictor=3,
             tiled=True, blockxsize=256, blockysize=256)
    with rasterio.open(path, "w", **p) as dst:
        dst.write(data.astype("float32"), 1)


def blocks(shape, n=NB):
    h, w = shape
    return [(slice(i * h // n, (i + 1) * h // n), slice(j * w // n, (j + 1) * w // n))
            for i in range(n) for j in range(n)]


def main() -> None:
    dotted_a, prof_d, tr_d, crs_d = read_checked(*INPUTS["dotted"])
    tip_a, prof_t, tr_t, crs_t = read_checked(*INPUTS["tip"])
    tpl, prof_p, tr_p, crs_p = read_checked(*INPUTS["template"])
    labels_a, *_ = read_checked(*INPUTS["labels"])
    sgmc_a, *_ = read_checked(*INPUTS["sgmc"])
    if not (dotted_a.shape == tip_a.shape == tpl.shape):
        raise SystemExit("input grids differ in shape")
    if not (tr_d == tr_t == tr_p and crs_d == crs_t == crs_p):
        raise SystemExit("input grids differ in geotransform or CRS")

    dotted = dotted_a > 0
    tip = tip_a > 0
    labels = labels_a > 0
    sgmc = sgmc_a > 0
    footprint = np.isfinite(tpl)

    # ------------------------------------------------------------ evidence + DS
    sup_d = kernel_support(dotted.astype(np.float64))
    sup_t = kernel_support(tip.astype(np.float64))
    a = discounted_binary_mass(sup_d, R_DOTTED)
    b = discounted_binary_mass(sup_t, R_TIP)
    bel, dis, unassigned, conflict = combine_yager(a, b)
    bel_dem, dis_dem, _ = combine_dempster(a, b)
    betp = pignistic(bel, dis)

    allowed = footprint & ((sup_d > 0) | (sup_t > 0))
    support = poisson_sample(betp, SPACING, BUDGET, allowed)
    emission = np.zeros(betp.shape, dtype=np.float32)
    emission[support] = 1.0
    emission[~footprint] = 0.0

    # ------------------------------------------------------------- diagnostics
    belief_norm = np.zeros(betp.shape, dtype=np.float32)
    m = footprint & (betp > 0)
    lo, hi = float(betp[m].min()), float(betp[m].max())
    belief_norm[m] = ((betp[m] - lo) / (hi - lo)).astype(np.float32)
    diag = np.zeros(betp.shape, dtype=np.float32)
    diag[footprint] = np.clip(unassigned[footprint], 0.0, 1.0).astype(np.float32)

    # ----------------------------------------------------------------- outputs
    OUTDIR.mkdir(parents=True, exist_ok=True)
    tmp = OUTDIR / f"{STEM}.tmp.tif"
    out_tif = OUTDIR / f"{STEM}.tif"
    unc_tif = OUTDIR / f"{STEM}-unassigned-diagnostic.tif"
    bel_tif = OUTDIR / f"{STEM}-belief-field.tif"
    zip_path = OUTDIR / f"{STEM}.zip"
    audit_path = OUTDIR / f"{STEM}-audit.json"

    write_tif(tmp, emission, prof_p)
    digest = sha(tmp)
    ident = digest[:12]
    final = OUTDIR / f"{STEM}-{ident}.tif"
    tmp.rename(final)
    write_tif(unc_tif, diag, prof_p)
    write_tif(bel_tif, belief_norm, prof_p)
    # Deterministic ZIP: a fixed member timestamp keeps the archive byte-identical
    # across rebuilds, so the published SHA-256 is reproducible rather than a
    # function of the wall clock.
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        info = zipfile.ZipInfo(final.name, date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        with open(final, "rb") as fh:
            z.writestr(info, fh.read())

    # ------------------------------------------------- independent byte re-read
    with rasterio.open(final) as chk:
        reread = chk.read(1)
        tags = {"bands": chk.count, "dtype": chk.dtypes[0], "crs": str(chk.crs), "epsg": chk.crs.to_epsg(),
                "shape": list(chk.shape), "transform": list(chk.transform)[:6], "resolution": list(chk.res),
                "nodata": chk.nodata, "compress": chk.profile.get("compress")}

    # ------------------------------------------------------------ validations
    dc = distance_transform_edt(~labels)
    truths = {"sgmc_off300m": sgmc & footprint & (dc >= 3.0), "sgmc_off100m": sgmc & footprint & (dc >= 1.0)}
    cands = {
        "dotted_parent": dotted.astype(np.float64),
        "tip_parent": tip.astype(np.float64),
        "union_binary": (dotted | tip).astype(np.float64),
        "intersection_only": (dotted & tip).astype(np.float64),
        "naive_mean_0.5_0.5": (0.5 * dotted + 0.5 * tip).astype(np.float64),
        "weighted_mean_0.64_0.36": (0.64 * dotted + 0.36 * tip).astype(np.float64),
        "H49_submission": emission.astype(np.float64),
    }
    blks = blocks(truths["sgmc_off300m"].shape)
    validation = {}
    for tname, truth in truths.items():
        rows = {}
        for cname, arr in cands.items():
            r = dti(arr, truth)
            per = [dti(arr[ys, xs], truth[ys, xs]).dti for ys, xs in blks if truth[ys, xs].sum() >= 50]
            rows[cname] = {**r.as_dict(), "emitted_cells": float((arr > 0).sum()),
                           "block_dti_mean": float(np.mean(per)),
                           "blocks_vs_dotted": int(np.sum(np.array(per) >
                                                          np.array([dti(dotted.astype(np.float64)[ys, xs], truth[ys, xs]).dti
                                                                    for ys, xs in blks if truth[ys, xs].sum() >= 50]))),
                           "blocks_scored": len(per)}
        base = rows["dotted_parent"]["dti"]
        for v in rows.values():
            v["delta_vs_dotted_parent"] = v["dti"] - base
        validation[tname] = {"truth_pixels": int(truth.sum()), "candidates": rows}

    # ------------------------------------------------- is it the naive average?
    naive = 0.5 * (dotted.astype(np.float64) + tip.astype(np.float64))
    act = footprint
    corr = float(np.corrcoef(emission[act], naive[act])[0, 1])
    corr_d = float(np.corrcoef(emission[act], dotted.astype(np.float64)[act])[0, 1])
    corr_t = float(np.corrcoef(emission[act], tip.astype(np.float64)[act])[0, 1])
    maxdiff = float(np.max(np.abs(emission[act] - naive[act])))
    identical = bool(np.array_equal(emission[act], naive[act].astype(np.float32)))
    identical_parents = {
        "identical_to_dotted_parent": bool(np.array_equal(support, dotted & footprint)),
        "identical_to_tip_parent": bool(np.array_equal(support, tip & footprint)),
        "identical_to_union": bool(np.array_equal(support, (dotted | tip) & footprint)),
    }
    composition = {
        "cells_selected": int(support.sum()),
        "from_intersection": int((support & dotted & tip).sum()),
        "from_dotted_only": int((support & dotted & ~tip).sum()),
        "from_tip_only": int((support & tip & ~dotted).sum()),
        "new_cells_not_in_either_parent": int((support & ~dotted & ~tip).sum()),
        "jaccard_with_dotted_parent": float((support & dotted).sum() / (support | dotted).sum()),
        "jaccard_with_union": float((support & (dotted | tip)).sum() / (support | (dotted | tip)).sum()),
    }

    audit = {
        "schema": "GEMSDOE48-audit-v2",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "submission_name": f"GEMSDOE48-H49-DS-CONFLICT-BALANCED-{ident}",
        "method": ("kernel-support evidence fields; Shafer reliability discounting; conjunctive combination; "
                   "Yager transfer of conflict K to Theta; pignistic ranking; mass-budgeted spatially balanced "
                   "emission at p=1 on the admitted support"),
        "scientific_note": ("Classical normalised Dempster's rule renormalises conflict away by dividing by 1-K. "
                            "Yager's modified Dempster rule is used because the deliverable must keep the two "
                            "families' disagreement visible as unassigned mass."),
        "preregistered_constants": {"r_dotted": R_DOTTED, "r_tip": R_TIP, "efficiency_ratio": EFFICIENCY,
                                    "spacing_cells": SPACING, "budget_cells": BUDGET,
                                    "live_anchor_dotted": LIVE_DOTTED, "live_anchor_tip": LIVE_TIP},
        "inputs": {k: {"file": str(v[0].relative_to(ROOT)), "sha256": v[1]} for k, v in INPUTS.items()},
        "outputs": {
            "primary_tif": {"file": str(final.relative_to(ROOT)), "sha256": sha(final), "bytes": final.stat().st_size, **tags},
            "zip": {"file": str(zip_path.relative_to(ROOT)), "sha256": sha(zip_path), "bytes": zip_path.stat().st_size},
            "unassigned_diagnostic": {"file": str(unc_tif.relative_to(ROOT)), "sha256": sha(unc_tif)},
            "belief_field_diagnostic": {"file": str(bel_tif.relative_to(ROOT)), "sha256": sha(bel_tif)},
        },
        "emission_composition": composition,
        "ds_field_statistics": {
            "belief_yager": {"min": float(bel.min()), "max": float(bel.max())},
            "unassigned_mass": {"min": float(unassigned.min()), "max": float(unassigned.max()),
                                "mean": float(unassigned.mean())},
            "conflict_K": {"max": float(conflict.max()), "cells_gt0": int((conflict > 1e-9).sum())},
            "pignistic": {"min": float(betp.min()), "max": float(betp.max())},
            "dempster_normalised_belief_max": float(np.nanmax(bel_dem)),
            "mass_conservation_max_abs_error": float(np.max(np.abs(bel + dis + unassigned - 1.0))),
        },
        "format_checks": {
            **tags,
            "all_finite": bool(np.isfinite(reread).all()),
            "min": float(reread.min()), "max": float(reread.max()),
            "out_of_range_count": int(((reread < 0) | (reread > 1)).sum()),
            "outside_footprint_all_zero": bool(np.all(reread[~footprint] == 0)),
            "positive_cells": int((reread > 0).sum()),
            "total_mass": float(reread.sum()),
            "portal_range_ok": bool(np.isfinite(reread).all() and reread.min() >= 0 and reread.max() <= 1),
        },
        "not_the_average_check": {
            "pearson_vs_naive_mean": corr,
            "pearson_vs_dotted_parent": corr_d,
            "pearson_vs_tip_parent": corr_t,
            "max_abs_difference_vs_naive_mean": maxdiff,
            "pixel_identical_to_naive_mean": identical,
            **identical_parents,
            "pass": bool(not identical and maxdiff > 0 and not any(identical_parents.values())),
        },
        "blocked_holdout": validation,
        "evidence_class": {
            "measured": "everything under emission_composition, ds_field_statistics, format_checks, blocked_holdout, not_the_average_check",
            "owner_reported_anchor": "live_anchor_dotted 0.2778 (GEMSDOE32), live_anchor_tip 0.2632 (GEMSDOE33); neither is organizer-authenticated",
            "proxy": "SGMC-derived faults inside the template footprint, >=300 m / >=100 m from the public catalogue. Not the hidden expert labels.",
        },
    }
    audit["format_pass"] = bool(
        tags["bands"] == 1 and tags["dtype"] == "float32" and tags["epsg"] == 32611
        and tags["shape"] == [3730, 3292] and audit["format_checks"]["portal_range_ok"]
        and tags["nodata"] is None and audit["not_the_average_check"]["pass"])
    audit_path.write_text(json.dumps(audit, indent=2) + "\n")

    print(json.dumps({k: audit[k] for k in ["submission_name", "emission_composition", "format_checks",
                                            "not_the_average_check", "format_pass"]}, indent=2))
    for tn, v in validation.items():
        print("\n--", tn, "truth px", v["truth_pixels"])
        for cn, r in sorted(v["candidates"].items(), key=lambda kv: -kv[1]["dti"]):
            print(f"   {cn:26s} dti={r['dti']:.6f} d={r['delta_vs_dotted_parent']:+.6f} "
                  f"blk={r['block_dti_mean']:.6f} mass={r['emitted_mass']:9.1f} won={r['blocks_vs_dotted']}/{r['blocks_scored']}")


if __name__ == "__main__":
    main()
