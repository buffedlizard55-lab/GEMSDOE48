#!/usr/bin/env python3
"""Build a post-hoc H56B ablation without catalogue-flank absence evidence.

This is a Dempster-Shafer evidence-assignment sensitivity experiment, not a new
geological detector, preregistered candidate, calibrated probability, or slot-cleared
submission. It removes the prior H56 recipe's catalogue-derived absence term to
reduce direct target-proxy leakage; parent surfaces remain frozen and may themselves
encode catalogue-based pruning.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]

# Reuse only low-level input-pin, grid, kernel-support, BPA, Dempster, and GeoTIFF
# helpers. The independent audit below recomputes the combined output separately.
spec = importlib.util.spec_from_file_location(
    "h56b_base_builder", ROOT / "scripts/build_submission_h56_belief.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("could not load pinned H56B helper implementation")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def main() -> int:
    inputs = base.INPUTS
    receipt = {
        "session": "H56B-NF exploratory ablation",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "POST_HOC_ABLATION_NOT_PREREGISTERED_NOT_SLOT_CLEARED",
        "recipe": {
            "variant": "remove dotted-only catalogue-flank absence term",
            "relation_to_prior": "post-hoc sensitivity ablation of H56B; not a new geological detector",
            "kernel": "official triangular k(d)=max(1-d/300m,0), R=3 cells",
            "r_dotted": base.R_DOT,
            "r_tip": base.R_TIP,
            "discount_interpretation": "heuristic, partly informed by owner-reported values; not calibrated source reliability",
            "absence_on_backbone": base.A_ON,
            "absence_off_backbone": base.A_OFF,
            "catalogue_flank_absence": "disabled in this variant",
            "rule": "normalized Dempster combination; fail on total/numerical conflict",
            "surface": "relative Bel(F), divided by footprint maximum, float32, NaN outside footprint",
            "m_theta": "residual uncommitted/ignorance mass after normalization; not a direct disagreement map",
            "conflict_K": "pre-normalization conflict, divided out by normalized Dempster and exported separately",
            "support_difference": "absolute difference between 300 m kernel-support surfaces; not a D-S mass",
            "independence": "not established; parent positive-cell overlap is reported",
            "submission_recommendation": "do not submit; same-protocol blocked public-proxy comparison required and cannot establish private-label performance",
        },
        "inputs": {},
    }
    for key, metadata in inputs.items():
        path = Path(metadata["path"])
        actual = base.sha256_file(path)
        if actual != metadata["sha256"]:
            raise SystemExit(f"input pin mismatch for {key}: {actual}")
        receipt["inputs"][key] = {
            **metadata,
            "path": path.relative_to(ROOT).as_posix(),
            "sha256_verified": True,
        }

    template, profile = base.read_band(inputs["template"]["path"])
    labels, _ = base.read_band(inputs["catalogue_labels"]["path"])
    footprint_band, _ = base.read_band(inputs["footprint_mask"]["path"])
    footprint = labels != -1
    template_footprint = np.isfinite(template) if template.dtype.kind == "f" else template >= 0
    if not np.array_equal(template_footprint, footprint):
        raise SystemExit("template and catalogue-label footprints differ")
    if not np.array_equal(footprint, footprint_band == 1):
        raise SystemExit("catalogue-label and pinned AOI footprints differ")
    for key in ("dotted_c", "tip_h33d", "backbone_h19_5"):
        with rasterio.open(inputs[key]["path"]) as src:
            if src.transform != profile["transform"] or src.crs != profile["crs"]:
                raise SystemExit(f"{key} is not on the competition grid")

    dotted = (base.read_band(inputs["dotted_c"]["path"])[0] > 0) & footprint
    tip = (base.read_band(inputs["tip_h33d"]["path"])[0] > 0) & footprint
    backbone = np.nan_to_num(
        base.read_band(inputs["backbone_h19_5"]["path"])[0].astype(np.float32), nan=0.0
    ) > 0
    on_backbone = ndi.distance_transform_edt(~backbone) <= 1.0
    absence = np.where(on_backbone, base.A_ON, base.A_OFF).astype(np.float32)
    support_dotted = base.kernel_support(dotted)
    support_tip = base.kernel_support(tip)
    m_dotted = base.bpa(support_dotted, base.R_DOT, absence)
    m_tip = base.bpa(support_tip, base.R_TIP, absence)
    belief, not_fault, theta, conflict = base.dempster(m_dotted, m_tip)
    mass_error = float(np.max(np.abs(belief[footprint] + not_fault[footprint] + theta[footprint] - 1.0)))
    if mass_error > 2e-6:
        raise SystemExit(f"combined masses do not sum to one: {mass_error}")
    belief_max = float(belief[footprint].max())
    normalized = np.where(footprint, belief / belief_max, 0.0).astype(np.float32)
    if np.any((normalized[footprint] < 0.0) | (normalized[footprint] > 1.0)):
        raise SystemExit("normalized belief is out of range")

    mean_binary = 0.5 * (dotted.astype(np.float64) + tip.astype(np.float64))
    mean_kernel_raw = 0.5 * (support_dotted.astype(np.float64) + support_tip.astype(np.float64))
    mean_kernel = mean_kernel_raw / float(mean_kernel_raw[footprint].max())
    primary64 = normalized.astype(np.float64)
    support_union = (dotted | tip) & footprint

    def compare_mean(reference: np.ndarray) -> dict:
        delta = np.abs(primary64[footprint] - reference[footprint])
        return {
            "pearson_r_footprint": float(np.corrcoef(primary64[footprint], reference[footprint])[0, 1]),
            "mae_footprint": float(delta.mean()),
            "max_abs_diff_footprint": float(delta.max()),
            "frac_footprint_diff_gt_0.05": float((delta > 0.05).mean()),
            "is_pixel_identical": bool(np.array_equal(primary64[footprint], reference[footprint])),
        }

    receipt["counts"] = {
        "dotted_positive": int(dotted.sum()),
        "tip_positive": int(tip.sum()),
        "intersection": int((dotted & tip).sum()),
        "union": int((dotted | tip).sum()),
        "dotted_only": int((dotted & ~tip).sum()),
        "tip_only": int((tip & ~dotted).sum()),
    }
    receipt["ds"] = {
        "raw_belief_max": belief_max,
        "normalized_belief_mass_S": float(normalized[footprint].sum(dtype=np.float64)),
        "mtheta_min_footprint": float(theta[footprint].min()),
        "mtheta_max_footprint": float(theta[footprint].max()),
        "mtheta_mean_footprint": float(theta[footprint].mean()),
        "conflict_K_max_footprint": float(conflict[footprint].max()),
        "mass_sum_max_abs_error": mass_error,
    }
    support_difference = np.abs(support_dotted - support_tip).astype(np.float32)
    receipt["support_difference"] = {
        "definition": "abs(s_dot-s_tip) with each support from the 300 m triangular kernel",
        "interpretation": "direct support-difference diagnostic; not m(Theta), K, or a probability",
        "mean_footprint": float(support_difference[footprint].mean()),
        "max_footprint": float(support_difference[footprint].max()),
        "pixels_gt_0_05": int(((support_difference > 0.05) & footprint).sum()),
    }
    receipt["not_the_arithmetic_mean"] = {
        "vs_binary_mean": {"definition": "0.5*(1[dotted]+1[tip])", **compare_mean(mean_binary)},
        "vs_normalized_kernel_mean": {
            "definition": "normalize(0.5*(s_dot+s_tip)) by its footprint maximum",
            **compare_mean(mean_kernel),
        },
        "is_identical_to_either_mean": bool(
            np.array_equal(primary64[footprint], mean_binary[footprint])
            or np.array_equal(primary64[footprint], mean_kernel[footprint])
        ),
    }

    nan_arr = np.where(footprint, normalized, np.nan).astype(np.float32)
    content_id = hashlib.sha256(nan_arr.tobytes()).hexdigest()[:12]
    base_name = f"GEMSDOE48-H56B-NF-DS-dotted-x-tip-20261007-{content_id}"
    downloads = ROOT / "docs/downloads"
    diagnostic_dir = downloads / "diagnostics"
    diagnostic_dir.mkdir(parents=True, exist_ok=True)
    primary = downloads / f"{base_name}-nan-outside.tif"
    base.write_float32(primary, nan_arr, profile, nodata=np.nan)

    diagnostics = {}
    for tag, values in {
        "mtheta": theta,
        "conflict": conflict,
        "plausibility": belief + theta,
        "support_difference": support_difference,
    }.items():
        path = diagnostic_dir / f"gemsdoe48-h56b-noflank-{tag}-{content_id}.tif"
        layer = np.where(footprint, values, np.nan).astype(np.float32)
        base.write_float32(path, layer, profile, nodata=np.nan)
        diagnostics[tag] = {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": base.sha256_file(path),
            "outside": "NaN",
            "is_submission": False,
        }
    receipt["artifacts"] = {
        "primary": {
            "path": primary.relative_to(ROOT).as_posix(),
            "sha256": base.sha256_file(primary),
            "content_id": content_id,
            "dtype": "float32",
            "crs": str(profile["crs"]),
            "nodata": "NaN outside footprint",
            "unique_byte_artifact": True,
            "meaningful_novelty": "not claimed; this is a post-hoc D-S mass-assignment ablation",
            "submission_recommendation": "do not submit",
        },
        "diagnostics": diagnostics,
        "diagnostics_are_submissions": False,
    }
    out = ROOT / "evidence/build_h56b_noflank_receipt_20261007.json"
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "primary": receipt["artifacts"]["primary"],
        "counts": receipt["counts"],
        "not_the_arithmetic_mean": receipt["not_the_arithmetic_mean"],
        "receipt": out.relative_to(ROOT).as_posix(),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
