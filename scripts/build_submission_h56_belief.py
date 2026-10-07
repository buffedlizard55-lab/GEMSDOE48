#!/usr/bin/env python3
"""GEMSDOE48 H56 — the session's unique submission: the normalized Dempster-Shafer
combined BELIEF surface of the two strongest independently-built families.

Prompt mandate (verbatim intent)
--------------------------------
"Combine your best dotted-family surface and best tip-family surface this way
[Dempster's rule of combination], and treat the resulting unassigned-belief mass
as its own diagnostic layer ... Normalize the combined belief to [0,1], write to
the required format, and verify the result isn't simply the average of the two
inputs (a quick correlation check against a naive mean will show this)."

What makes H56 unique (not a copy of any prior GEMSDOE submission)
-------------------------------------------------------------------
Prior DS work in this repository used Dempster's rule to GATE binary dots:
  * PR1/PR2 2026-10-06 (previous_build_submission.py): DS on RAW BINARY dot maps,
    symmetric alpha=0.99, no kernel, no absence evidence -> tiered union;
    its decision emission was the plain union (priced -0.0140 by the live model).
  * H48-1 (build_ds.py): kernel BPA, but emitted an NMS-selected {0,1} mask.
  * H49/H53/H54/H55: DS used as a gate; every shipped artifact is {0,1} and
    additive on top of the dotted core.
H56 ships the LITERAL normalized combined belief Bel(F) in [0,1] as the
submission surface — the graded evidential quantity Shafer's theory defines —
built from a basic probability assignment that (i) uses the competition's OWN
300 m triangular kernel as evidence support, (ii) discounts each source by its
live-anchored reliability, and (iii) carries informative ABSENCE evidence
(on-backbone decline + the live-validated catalogue-flank rejection of the
dotted family). The unassigned mass m(Theta) — where the two families actively
disagree — ships as a separate diagnostic layer, not blended away.

Frozen recipe (pre-registered below, before any scoring is read)
----------------------------------------------------------------
Sources (sha256-pinned):
  dotted : data/families/dotted_b2_prune_02778.tif   owner-reported live 0.2778
  tip    : data/families/tip_stepover_r30_02632.tif  owner-reported live 0.2632
  backbone: data/raw/scored/h19_5_01922.tif (shared h19-5 ancestor, for absence)
BPA per source i at every footprint pixel x:
  s_i(x)     = k(d(x, D_i)),  k the official triangular kernel, R = 3 cells = 300 m
  m_i(F)     = r_i * s_i(x)
  m_i(N)     = r_i * (1 - s_i(x)) * a_i(x)
  m_i(Theta) = 1 - m_i(F) - m_i(N)
Reliability (Shafer discounting, live-anchored as in the H54 session):
  r_dot = 0.95
  r_tip = 0.95 * 0.2632 / 0.2778
Absence informativeness:
  a_i(x) = 0.5 within 100 m of the h19-5 backbone, 0.2 elsewhere,
  dotted source only: a_dot(x) = 1.0 where d(x, catalogue) <= 200 m
  (the catalogue-flank rejection is the live-validated 0.2708 -> 0.2778 rung;
   it is NOT applied to the tip source, for which it was never validated).
Combination: Dempster's normalized rule.
Submission surface: Bel(F) / max_footprint(Bel(F)) in [0,1], zeros outside the
finite footprint (range-error-immune). Diagnostic layers (NOT submissions):
m(Theta), raw conflict K, plausibility Pl(F) = f + u.

Honesty note, computed and displayed on the site: the repository's metric
algebra (knowledge/research_notes.md, result (a)) shows the DTI-optimal
submission is binary {0,1}; a graded surface is a scientific measurement of
where the two families disagree, not an assertion that grading beats the
0.2778 core. The site banner is set by pre-registered gates, never by
optimism.

Outputs
-------
  docs/downloads/GEMSDOE48-H56-ds-belief-dotted-x-tip-20261007-<cid>-zeros-outside.tif
  docs/downloads/GEMSDOE48-H56-ds-belief-dotted-x-tip-20261007-<cid>-zeros-outside.zip
  docs/downloads/GEMSDOE48-H56-ds-belief-dotted-x-tip-20261007-<cid>-nan-outside.tif
  docs/downloads/diagnostics/gemsdoe48-h56-mtheta-<cid>.tif     (unassigned mass)
  docs/downloads/diagnostics/gemsdoe48-h56-conflict-<cid>.tif   (raw K)
  docs/downloads/diagnostics/gemsdoe48-h56-plausibility-<cid>.tif
  evidence/build_h56_belief_receipt_20261007.json
  evidence/h56_format_audit_20261007.json
  evidence/h56_uniqueness_20261007.json
  evidence/holdout_h56_spatial_20261007.json
  evidence/h56_live_model_projection_20261007.json

Deterministic: identical inputs -> identical bytes.
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
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems48.metric import kernel  # noqa: E402

# --------------------------------------------------------------------------- pins
INPUTS = {
    "dotted_c": {
        "path": ROOT / "data/families/dotted_b2_prune_02778.tif",
        "sha256": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
        "origin": "GEMSDOE32 h33-h33-2-b2 (spacing-tuned dotted family)",
        "owner_reported_live": 0.2778,
        "site": "https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html",
    },
    "tip_h33d": {
        "path": ROOT / "data/families/tip_stepover_r30_02632.tif",
        "sha256": "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757",
        "origin": "GEMSDOE33 h33d analog tip-stepover r30 (tip/step-over family)",
        "owner_reported_live": 0.2632,
        "site": "https://buffedlizard55-lab.github.io/GEMSDOE33/",
    },
    "backbone_h19_5": {
        "path": ROOT / "data/raw/scored/h19_5_01922.tif",
        "sha256": "ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d",
        "origin": "GEMSDOE19 h19-5 power-law budget backbone (shared ancestor)",
        "owner_reported_live": 0.1922,
        "site": "https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html",
    },
    "template": {
        "path": ROOT / "data/raw/sample_submission_template.tif",
        "sha256": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
        "origin": "owner mirror of the official sample_submission.tif grid",
        "site": "https://www.drivendata.org/competitions/306/competition-doe-gems/data/",
    },
    "catalogue_labels": {
        "path": ROOT / "data/raw/labels_catalogue.tif",
        "sha256": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
        "origin": "owner mirror of existing_faults.tif (USGS/INGENIOUS catalogue labels)",
        "site": "https://www.drivendata.org/competitions/306/competition-doe-gems/data/",
    },
    "sgmc_offcat_truth": {
        "path": ROOT / "data/official/derived_sgmc_faults_100m.tif",
        "sha256": "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0",
        "origin": "owner-mirror on-grid rasterization of USGS SGMC fault traces",
        "site": "https://mrdata.usgs.gov/geology/state/",
    },
}

# ------------------------------------------------------- frozen hyper-parameters
R_CELLS = 3.0            # official metric support: 300 m at 100 m cells
R_TOP = 0.95             # live-anchored reliability cap (H54 convention)
LIVE_DOT, LIVE_TIP = 0.2778, 0.2632
A_ON, A_OFF = 0.5, 0.2   # absence informativeness on / off the h19-5 backbone
FLANK_PX = 2.0           # catalogue-flank band, 200 m (live-validated rung)
MIN_D_SGMC = 3.0         # holdout SGMC truth: > 300 m off-catalogue

R_DOT = R_TOP
R_TIP = R_TOP * LIVE_TIP / LIVE_DOT


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_band(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as s:
        return s.read(1), dict(s.profile)


def write_float32(path: Path, arr: np.ndarray, profile: dict, nodata=None) -> None:
    prof = dict(profile)
    prof.update(dtype="float32", count=1, compress="deflate", nodata=nodata)
    with rasterio.open(path, "w", **prof) as s:
        s.write(arr.astype(np.float32), 1)


def kernel_support(dots: np.ndarray) -> np.ndarray:
    """s(x) = k(d(x, dots)) with the official triangular kernel, R = 3 cells."""
    d = ndi.distance_transform_edt(~dots)
    return kernel(d).astype(np.float32)


def bpa(support: np.ndarray, r: float, absence: np.ndarray):
    f = r * support
    n = r * (1.0 - support) * absence
    u = 1.0 - f - n
    assert (u >= -1e-9).all(), "BPA inconsistency: m(Theta) < 0"
    return f.astype(np.float32), n.astype(np.float32), np.maximum(u, 0.0).astype(np.float32)


def dempster(m1, m2):
    f1, n1, u1 = m1
    f2, n2, u2 = m2
    K = f1 * n2 + n1 * f2
    z = np.maximum(1.0 - K, 1e-9)
    f = (f1 * f2 + f1 * u2 + u1 * f2) / z
    n = (n1 * n2 + n1 * u2 + u1 * n2) / z
    u = (u1 * u2) / z
    return f.astype(np.float32), n.astype(np.float32), u.astype(np.float32), K.astype(np.float32)


def main() -> int:
    now = datetime.now(timezone.utc)
    receipt = {
        "session": "H56",
        "generated_utc": now.isoformat(),
        "recipe": {
            "kernel": "official triangular k(d)=max(1-d/300m,0), R=3 cells",
            "r_dotted": R_DOT,
            "r_tip": R_TIP,
            "absence_on_backbone": A_ON,
            "absence_off_backbone": A_OFF,
            "flank_absence_dotted_only_px": FLANK_PX,
            "rule": "Dempster normalized combination",
            "submission_surface": "Bel(F) normalized by footprint max, zeros outside footprint",
        },
        "inputs": {},
    }

    # ---- verify pins -------------------------------------------------------
    for k, meta in INPUTS.items():
        p = Path(meta["path"])
        if not p.exists():
            print(f"FATAL missing input {p}", file=sys.stderr)
            return 2
        got = sha256_file(p)
        assert got == meta["sha256"], f"pin mismatch for {k}: {got}"
        receipt["inputs"][k] = {**meta, "path": str(p), "sha256_verified": True}
        print(f"[pin] {k} {got[:16]}")

    # ---- load grid ----------------------------------------------------------
    tmpl, prof = read_band(INPUTS["template"]["path"])
    footprint = np.isfinite(tmpl) if tmpl.dtype.kind == "f" else (tmpl >= 0)
    # the sample template is all-finite 0/1; footprint comes from labels != -1
    lab, _ = read_band(INPUTS["catalogue_labels"]["path"])
    footprint = lab != -1
    catalogue = lab == 1
    dcat = ndi.distance_transform_edt(~catalogue)
    H, W = footprint.shape
    print(f"[grid] {H} x {W}, footprint cells {int(footprint.sum())}")

    dots_d = (read_band(INPUTS["dotted_c"]["path"])[0] > 0) & footprint
    dots_t = (read_band(INPUTS["tip_h33d"]["path"])[0] > 0) & footprint
    bb = np.nan_to_num(read_band(INPUTS["backbone_h19_5"]["path"])[0].astype(np.float32), nan=0.0) > 0
    onbb = ndi.distance_transform_edt(~bb) <= 1.0

    counts = {
        "dotted_positive": int(dots_d.sum()),
        "tip_positive": int(dots_t.sum()),
        "intersection": int((dots_d & dots_t).sum()),
        "union": int((dots_d | dots_t).sum()),
        "dotted_only": int((dots_d & ~dots_t).sum()),
        "tip_only": int((dots_t & ~dots_d).sum()),
    }
    receipt["counts"] = counts
    print(f"[counts] {json.dumps(counts)}")

    # ---- BPA + Dempster ------------------------------------------------------
    absence = np.where(onbb, A_ON, A_OFF).astype(np.float32)
    absence_d = absence.copy()
    absence_d[(dcat <= FLANK_PX) & footprint] = 1.0  # live-validated flank rejection

    s_d = kernel_support(dots_d)
    s_t = kernel_support(dots_t)
    m_d = bpa(s_d, R_DOT, absence_d)
    m_t = bpa(s_t, R_TIP, absence)
    f, n, u, K = dempster(m_d, m_t)

    bel_raw = f.copy()
    mx = float(bel_raw[footprint].max())
    bel = np.where(footprint, bel_raw / mx, 0.0).astype(np.float32)
    assert bel.min() >= 0.0 and bel.max() <= 1.0 + 1e-9
    receipt["ds"] = {
        "raw_belief_max": mx,
        "belief_mass_S": float(bel[footprint].sum()),
        "mtheta_min_footprint": float(u[footprint].min()),
        "mtheta_max_footprint": float(u[footprint].max()),
        "conflict_K_max": float(K[footprint].max()),
        "conflict_px_gt_0.3": int((K > 0.3).sum()),
        "conflict_share_of_footprint": float((K > 0.3)[footprint].mean()),
    }
    print(f"[ds] {json.dumps(receipt['ds'], indent=1)}")

    # ---- not-the-naive-mean checks -------------------------------------------
    naive_bin = 0.5 * (dots_d.astype(np.float64) + dots_t.astype(np.float64))
    naive_ker_raw = 0.5 * (s_d.astype(np.float64) + s_t.astype(np.float64))
    naive_ker = naive_ker_raw / naive_ker_raw[footprint].max()
    bel64 = bel.astype(np.float64)

    def affine_residual(x: np.ndarray, y: np.ndarray) -> dict:
        """Best affine fit y ~ c0 + c1 x on the footprint; report residual stats."""
        A = np.vstack([np.ones_like(x), x]).T
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        res = y - (coef[0] + coef[1] * x)
        return {"c0": float(coef[0]), "c1": float(coef[1]),
                "mean_abs_residual": float(np.abs(res).mean()),
                "max_abs_residual": float(np.abs(res).max())}

    fp = footprint
    sup = (naive_bin > 0) & fp
    nb64, nk64 = naive_bin, naive_ker
    notnaive = {
        "vs_binary_mean": {
            "definition": "0.5*(1[dotted] + 1[tip])",
            "pearson_r_footprint": float(np.corrcoef(bel64[fp], nb64[fp])[0, 1]),
            "pearson_r_support": float(np.corrcoef(bel64[sup], nb64[sup])[0, 1]),
            "mae_footprint": float(np.abs(bel64 - nb64)[fp].mean()),
            "max_abs_diff": float(np.abs(bel64 - nb64).max()),
            "affine_fit": affine_residual(nb64[fp], bel64[fp]),
        },
        "vs_kernel_mean": {
            "definition": "0.5*(s_dot + s_tip), same normalization as the submission",
            "pearson_r_footprint": float(np.corrcoef(bel64[fp], nk64[fp])[0, 1]),
            "pearson_r_support": float(np.corrcoef(bel64[sup], nk64[sup])[0, 1]),
            "mae_footprint": float(np.abs(bel64 - nk64)[fp].mean()),
            "max_abs_diff": float(np.abs(bel64 - nk64).max()),
            "affine_fit": affine_residual(nk64[fp], bel64[fp]),
            "frac_footprint_diff_gt_0.05": float((np.abs(bel64 - nk64) > 0.05)[fp].mean()),
        },
        "is_identical_to_either_mean": bool(
            np.array_equal(bel64, nb64) or np.allclose(bel64, nk64, atol=1e-6)),
    }
    receipt["not_the_naive_mean"] = notnaive
    print("[not-naive-mean] binary r:", notnaive["vs_binary_mean"]["pearson_r_footprint"],
          "kernel r:", notnaive["vs_kernel_mean"]["pearson_r_footprint"])

    # ---- write artifacts -------------------------------------------------------
    cid = hashlib.sha256(bel.astype(np.float32).tobytes()).hexdigest()[:12]
    base = f"GEMSDOE48-H56-ds-belief-dotted-x-tip-20261007-{cid}"
    dl = ROOT / "docs/downloads"
    dl.mkdir(parents=True, exist_ok=True)
    diag = dl / "diagnostics"
    diag.mkdir(exist_ok=True)

    zeros_path = dl / f"{base}-zeros-outside.tif"
    nan_path = dl / f"{base}-nan-outside.tif"
    write_float32(zeros_path, bel, prof, nodata=None)
    nan_arr = np.where(footprint, bel, np.nan).astype(np.float32)
    write_float32(nan_path, nan_arr, prof, nodata=None)
    with zipfile.ZipFile(dl / f"{base}-zeros-outside.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.write(zeros_path, arcname=zeros_path.name)

    diag_paths = {}
    for tag, arr in [("mtheta", u), ("conflict", K), ("plausibility", (f + u))]:
        p = diag / f"gemsdoe48-h56-{tag}-{cid}.tif"
        out = np.where(footprint, arr, 0.0).astype(np.float32)
        write_float32(p, out, prof, nodata=None)
        diag_paths[tag] = str(p.relative_to(ROOT))
    receipt["artifacts"] = {
        "base": base,
        "content_id": cid,
        "primary_zeros": str(zeros_path.relative_to(ROOT)),
        "nan_twin": str(nan_path.relative_to(ROOT)),
        "zip": str((dl / f"{base}-zeros-outside.zip").relative_to(ROOT)),
        "diagnostics": diag_paths,
        "diagnostics_are_submissions": False,
    }
    print(f"[write] {zeros_path.name} cid={cid}")

    (ROOT / "evidence/build_h56_belief_receipt_20261007.json").write_text(json.dumps(receipt, indent=1))
    print("[evidence] evidence/build_h56_belief_receipt_20261007.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
