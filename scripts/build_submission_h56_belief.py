#!/usr/bin/env python3
"""GEMSDOE48 H56B — a with-flank rebuild of the prior H56 D-S surface.

It re-creates a normalized Dempster-Shafer belief surface from the dotted and
actual tip/step-over families for reproducibility and format auditing. Its recipe
is the same as the earlier H56 zero-outside artifact; it is not a meaningfully new
submission candidate.

Prompt mandate (verbatim intent)
--------------------------------
"Combine your best dotted-family surface and best tip-family surface this way
[Dempster's rule of combination], and treat the resulting unassigned-belief mass
as its own diagnostic layer ... Normalize the combined belief to [0,1], write to
the required format, and verify the result isn't simply the average of the two
inputs (a quick correlation check against a naive mean will show this)."

Relationship to prior art — do not claim this build is a new candidate
-----------------------------------------------------------------------
The exact H56B with-flank recipe below matches the earlier H56 zero-outside
artifact's assumptions and is a reproducibility/format rebuild, not a meaningfully
new model. Direct comparison found the in-footprint surfaces differ by at most
1.788139343e-7, share the same positive support, and have top-37,654 Jaccard 1.0.
The separate H56B-NF script removes the catalogue-flank absence term as a
post-hoc mass-assignment ablation, not a new geological detector.

Prior repository work also includes H48/H53 Dempster diagnostics on related
parents. Therefore neither this rebuild nor the no-flank ablation is a claim of
new D-S theory, a new geological source family, or a validated probability model.
The source assignments use the competition's 300 m triangular kernel, heuristic
reliability discounts and absence weights; parent positive-cell overlap is
31,614 and statistical independence is not established. Normalized residual
m(Theta) is uncommitted/ignorance under those assumptions, not direct disagreement.
Raw pre-normalization conflict K and absolute support difference are exported
separately; normalized Dempster divides out K.

Recorded H56B recipe (not a preregistration; chronology is audited separately)
-----------------------------------------------------------------------------
Sources (sha256-pinned):
  dotted : data/families/dotted_b2_prune_02778.tif   owner-reported live 0.2778
  tip    : data/families/tip_stepover_r30_02632.tif  owner-reported live 0.2632
  backbone: data/raw/scored/h19_5_01922.tif (shared h19-5 ancestor, for absence)
BPA per source i at every footprint pixel x:
  s_i(x)     = k(d(x, D_i)),  k the official triangular kernel, R = 3 cells = 300 m
  m_i(F)     = r_i * s_i(x)
  m_i(N)     = r_i * (1 - s_i(x)) * a_i(x)
  m_i(Theta) = 1 - m_i(F) - m_i(N)
Heuristic discount factors (Shafer discounting form; not calibrated reliability):
  r_dot = 0.95
  r_tip = 0.95 * 0.2632 / 0.2778
Absence informativeness:
  a_i(x) = 0.5 within 100 m of the h19-5 backbone, 0.2 elsewhere,
  dotted source only: a_dot(x) = 1.0 where d(x, catalogue) <= 200 m
  (this catalogue-flank term is inferred from an owner-reported score rung;
   its transfer to this task's hidden truth is unvalidated).
Combination: Dempster's normalized rule (total conflict is an error, not patched).
Research surface: Bel(F) / max_footprint(Bel(F)) in [0,1], NaN outside the
finite footprint. Diagnostic layers (NOT submissions): residual m(Theta),
pre-normalization conflict K, plausibility Pl(F) = f + u, and |s_dot - s_tip|.

Decision note: the repository's metric algebra (knowledge/research_notes.md,
result (a)) shows the DTI objective's unconstrained ranking optimum is binary
{0,1}; a graded surface is a constructed belief/favorability raster, not a
claim that grading beats the 0.2778 owner-reported score. Its support proxies
were not persuasive in matched blocked holdout, so this build must not be
promoted to a weekly submission. Local file validation is not organizer acceptance.

Outputs
-------
  docs/downloads/GEMSDOE48-H56B-ds-belief-dotted-x-tip-20261007-<cid>-nan-outside.tif
  docs/downloads/diagnostics/gemsdoe48-h56b-mtheta-<cid>.tif
  docs/downloads/diagnostics/gemsdoe48-h56b-conflict-<cid>.tif
  docs/downloads/diagnostics/gemsdoe48-h56b-plausibility-<cid>.tif
  docs/downloads/diagnostics/gemsdoe48-h56b-support-difference-<cid>.tif
  evidence/build_h56b_belief_receipt_20261007.json

Deterministic: identical inputs -> identical bytes. This does not imply organizer
acceptance, a calibrated probability, or an expected score.
"""
from __future__ import annotations

import hashlib
import json
import sys
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
    "footprint_mask": {
        "path": ROOT / "data/source_mirrors/footprint-mask.tif",
        "sha256": "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f",
        "origin": "on-grid AOI mask derived from the official solution/sample footprint",
        "site": "https://www.drivendata.org/competitions/306/competition-doe-gems/data/",
    },
}

# ------------------------------------------------------- frozen hyper-parameters
R_CELLS = 3.0            # official metric support: 300 m at 100 m cells
R_TOP = 0.95             # live-anchored reliability cap (H54 convention)
LIVE_DOT, LIVE_TIP = 0.2778, 0.2632
A_ON, A_OFF = 0.5, 0.2   # absence informativeness on / off the h19-5 backbone
FLANK_PX = 2.0           # catalogue-flank band, 200 m (owner-score-informed heuristic)

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
    """Construct one two-source BPA; reject malformed data rather than hide it."""
    support = np.asarray(support, dtype=np.float64)
    absence = np.asarray(absence, dtype=np.float64)
    if support.shape != absence.shape:
        raise ValueError("support and absence arrays must have identical shapes")
    if not (0.0 < r <= 1.0):
        raise ValueError("discount factor must be in (0, 1]")
    if not np.isfinite(support).all() or not np.isfinite(absence).all():
        raise ValueError("support and absence arrays must be finite")
    if np.any((support < 0.0) | (support > 1.0)):
        raise ValueError("support must be in [0, 1]")
    if np.any((absence < 0.0) | (absence > 1.0)):
        raise ValueError("absence informativeness must be in [0, 1]")
    f = r * support
    n = r * (1.0 - support) * absence
    u = 1.0 - f - n
    if np.any(u < -1e-12):
        raise ValueError("invalid BPA: m(Theta) < 0")
    return f.astype(np.float32), n.astype(np.float32), np.maximum(u, 0.0).astype(np.float32)


def dempster(m1, m2):
    """Pixelwise normalized Dempster combination; reject total conflict.

    K is returned as a separate pre-normalization diagnostic. Dempster's rule
    normalizes it away, so the resulting m(Theta) is residual uncommitted mass,
    not K and not a direct support-difference map.
    """
    if len(m1) != 3 or len(m2) != 3:
        raise ValueError("each mass function must contain F, not-F, and Theta arrays")
    if any(np.asarray(x).shape != np.asarray(m1[0]).shape for x in m1 + m2):
        raise ValueError("all mass arrays must have identical shapes")
    f1, n1, u1 = (np.asarray(x, dtype=np.float64) for x in m1)
    f2, n2, u2 = (np.asarray(x, dtype=np.float64) for x in m2)
    K = f1 * n2 + n1 * f2
    z = 1.0 - K
    if not np.isfinite(z).all() or np.any(z <= 1e-12):
        raise ValueError("Dempster normalization is undefined at total conflict")
    f = (f1 * f2 + f1 * u2 + u1 * f2) / z
    n = (n1 * n2 + n1 * u2 + u1 * n2) / z
    u = (u1 * u2) / z
    if np.any(np.abs(f + n + u - 1.0) > 2e-6):
        raise ValueError("combined masses failed the unit-sum invariant")
    return f.astype(np.float32), n.astype(np.float32), u.astype(np.float32), K.astype(np.float32)


def main() -> int:
    now = datetime.now(timezone.utc)
    receipt = {
        "session": "H56B",
        "generated_utc": now.isoformat(),
        "recipe": {
            "kernel": "official triangular k(d)=max(1-d/300m,0), R=3 cells",
            "r_dotted": R_DOT,
            "r_tip": R_TIP,
            "discount_interpretation": "heuristics partly derived from owner-reported scores; not calibrated source reliability",
            "absence_on_backbone": A_ON,
            "absence_off_backbone": A_OFF,
            "flank_absence_dotted_only_px": FLANK_PX,
            "flank_term_interpretation": "owner-score-informed heuristic; off-catalogue transfer is unvalidated",
            "rule": "Dempster normalized combination; fail on total conflict",
            "surface": "relative Bel(F), divided by footprint maximum, float32, NaN outside footprint",
            "m_theta": "residual uncommitted/ignorance mass after normalization; not a direct disagreement map",
            "conflict_K": "pre-normalization conflict, separately exported and normalized away by Dempster's rule",
            "support_difference": "absolute difference between the two source support surfaces; not a Dempster-Shafer mass",
            "independence": "not established; positive-cell overlap is measured in the receipt",
            "submission_recommendation": "do not submit; matched blocked holdout loses to H49 on all folds for both truth sets",
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
    template_footprint = np.isfinite(tmpl) if tmpl.dtype.kind == "f" else (tmpl >= 0)
    with rasterio.open(INPUTS["catalogue_labels"]["path"]) as src:
        lab = src.read(1)
        if src.transform != prof["transform"] or src.crs != prof["crs"]:
            raise ValueError("catalogue labels and sample template grids differ")
    with rasterio.open(INPUTS["footprint_mask"]["path"]) as src:
        footprint_band = src.read(1)
        if src.transform != prof["transform"] or src.crs != prof["crs"]:
            raise ValueError("AOI footprint mask and sample template grids differ")
    footprint = lab != -1
    if not np.array_equal(template_footprint, footprint):
        raise ValueError("sample-template and catalogue-label footprint masks differ")
    if not np.array_equal(footprint, footprint_band == 1):
        raise ValueError("catalogue-label and pinned AOI footprint masks differ")
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
    absence_d[(dcat <= FLANK_PX) & footprint] = 1.0  # owner-score-informed heuristic; not independently validated

    s_d = kernel_support(dots_d)
    s_t = kernel_support(dots_t)
    support_difference = np.abs(s_d - s_t).astype(np.float32)
    m_d = bpa(s_d, R_DOT, absence_d)
    m_t = bpa(s_t, R_TIP, absence)
    f, n, u, K = dempster(m_d, m_t)
    mass_sum_error = float(np.max(np.abs(f[footprint] + n[footprint] + u[footprint] - 1.0)))
    if mass_sum_error > 2e-6:
        raise ValueError(f"combined BPA mass sum error {mass_sum_error} exceeds tolerance")

    bel_raw = f.copy()
    mx = float(bel_raw[footprint].max())
    bel = np.where(footprint, bel_raw / mx, 0.0).astype(np.float32)
    assert bel.min() >= 0.0 and bel.max() <= 1.0 + 1e-9
    receipt["ds"] = {
        "raw_belief_max": mx,
        "belief_mass_S": float(bel[footprint].sum()),
        "mtheta_min_footprint": float(u[footprint].min()),
        "mtheta_max_footprint": float(u[footprint].max()),
        "mtheta_mean_footprint": float(u[footprint].mean()),
        "conflict_K_max": float(K[footprint].max()),
        "conflict_px_gt_0.3": int(((K > 0.3) & footprint).sum()),
        "conflict_share_of_footprint": float((K > 0.3)[footprint].mean()),
        "mass_sum_max_abs_error": mass_sum_error,
    }
    receipt["support_difference"] = {
        "definition": "abs(s_dot - s_tip), with both supports from the 300 m triangular kernel",
        "interpretation": "direct diagnostic of source-support separation; not m(Theta), K, or a probability",
        "mean_footprint": float(support_difference[footprint].mean()),
        "max_footprint": float(support_difference[footprint].max()),
        "pixels_gt_0_05": int(((support_difference > 0.05) & footprint).sum()),
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
            "max_abs_diff_footprint": float(np.abs(bel64 - nb64)[fp].max()),
            "affine_fit": affine_residual(nb64[fp], bel64[fp]),
        },
        "vs_kernel_mean": {
            "definition": "0.5*(s_dot + s_tip), same normalization as the submission",
            "pearson_r_footprint": float(np.corrcoef(bel64[fp], nk64[fp])[0, 1]),
            "pearson_r_support": float(np.corrcoef(bel64[sup], nk64[sup])[0, 1]),
            "mae_footprint": float(np.abs(bel64 - nk64)[fp].mean()),
            "max_abs_diff_footprint": float(np.abs(bel64 - nk64)[fp].max()),
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
    nan_arr = np.where(footprint, bel, np.nan).astype(np.float32)
    cid = hashlib.sha256(nan_arr.tobytes()).hexdigest()[:12]
    base = f"GEMSDOE48-H56B-ds-belief-dotted-x-tip-20261007-{cid}"
    dl = ROOT / "docs/downloads"
    dl.mkdir(parents=True, exist_ok=True)
    diag = dl / "diagnostics"
    diag.mkdir(exist_ok=True)

    primary_path = dl / f"{base}-nan-outside.tif"
    write_float32(primary_path, nan_arr, prof, nodata=np.nan)

    diag_paths = {}
    diagnostic_arrays = {
        "mtheta": u,
        "conflict": K,
        "plausibility": f + u,
        "support_difference": support_difference,
    }
    for tag, arr in diagnostic_arrays.items():
        p = diag / f"gemsdoe48-h56b-{tag}-{cid}.tif"
        out = np.where(footprint, arr, np.nan).astype(np.float32)
        write_float32(p, out, prof, nodata=np.nan)
        diag_paths[tag] = {
            "path": str(p.relative_to(ROOT)),
            "sha256": sha256_file(p),
            "outside": "NaN",
            "is_submission": False,
        }
    receipt["artifacts"] = {
        "primary": {
            "path": str(primary_path.relative_to(ROOT)),
            "sha256": sha256_file(primary_path),
            "content_id": cid,
            "dtype": "float32",
            "crs": str(prof["crs"]),
            "nodata": "NaN outside footprint",
            "unique_byte_artifact": True,
            "materially_novel_candidate": False,
            "relationship_to_prior": "reproducibility/encoding rebuild of prior H56 recipe; not a new candidate",
            "submission_recommendation": "do not submit",
        },
        "diagnostics": diag_paths,
        "diagnostics_are_submissions": False,
    }
    print(f"[write] {primary_path.name} cid={cid}")

    receipt_path = ROOT / "evidence/build_h56b_belief_receipt_20261007.json"
    receipt_path.write_text(json.dumps(receipt, indent=1))
    print(f"[evidence] {receipt_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
