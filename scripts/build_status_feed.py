#!/usr/bin/env python3
"""Build a local artifact-audit feed; never infer organizer acceptance.

The feed records grid/dtype checks, in-footprint value checks, outside-footprint
encoding, and an unmasked whole-array [0, 1] predicate. Those are local byte
observations only. They do not emulate or establish DrivenData portal behavior.

Outputs: ``docs/data/status.json`` and ``docs/status.html``.
"""
from __future__ import annotations

import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / "docs/downloads"
TEMPLATE = ROOT / "data/raw/sample_submission_template.tif"
FEED_JSON = ROOT / "docs/data/status.json"
FEED_HTML = ROOT / "docs/status.html"
DECISION_PATH = ROOT / "evidence/submission_gate_reconciliation_20261008.json"


def local_file_audit(path: Path, template_profile, footprint: np.ndarray) -> dict:
    """Measure local raster properties without labeling the file portal-safe."""
    with rasterio.open(path) as src:
        profile = src.profile.copy()
        band = src.read(1)

    same_shape = tuple(band.shape) == tuple(footprint.shape)
    same_transform = tuple(profile["transform"])[:6] == tuple(template_profile["transform"])[:6]
    same_crs = profile["crs"] == template_profile["crs"]
    same_grid = bool(same_shape and same_transform and same_crs)

    if same_shape:
        inside = band[footprint]
        outside = band[~footprint]
        in_footprint_finite = bool(np.isfinite(inside).all())
        in_footprint_range = bool(np.isfinite(inside).all() and np.all((inside >= 0) & (inside <= 1)))
        outside_all_nan = bool(outside.size > 0 and np.isnan(outside).all())
        outside_all_zero = bool(outside.size > 0 and np.all(outside == 0))
    else:
        inside = band.ravel()
        in_footprint_finite = False
        in_footprint_range = False
        outside_all_nan = False
        outside_all_zero = False

    all_finite = bool(np.isfinite(band).all())
    all_range = bool(all_finite and np.all((band >= 0) & (band <= 1)))
    layout_ok = bool(
        profile["dtype"] == "float32"
        and int(profile["count"]) == 1
        and same_grid
    )
    local_published_format_checks = bool(
        layout_ok and in_footprint_finite and in_footprint_range and outside_all_nan
    )

    return {
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "dtype": profile["dtype"],
        "bands": int(profile["count"]),
        "shape": [int(band.shape[0]), int(band.shape[1])],
        "crs": profile["crs"].to_string() if profile["crs"] else None,
        "grid_matches_template": same_grid,
        "transform_matches_template": same_transform,
        "crs_matches_template": same_crs,
        "nodata": profile.get("nodata"),
        "in_footprint_all_finite": in_footprint_finite,
        "in_footprint_all_in_0_1": in_footprint_range,
        "outside_all_nan": outside_all_nan,
        "outside_all_zero": outside_all_zero,
        "whole_array_all_finite": all_finite,
        "whole_array_all_in_0_1": all_range,
        "min_whole_array": float(np.nanmin(band)) if band.size else None,
        "max_whole_array": float(np.nanmax(band)) if band.size else None,
        "positive_cells": int((band > 0).sum()),
        "local_layout_checks_pass": layout_ok,
        "local_published_format_checks_pass": local_published_format_checks,
        "organizer_portal_acceptance_tested": False,
    }


def newest(pattern: str) -> Path | None:
    hits = sorted(ROOT.glob(pattern))
    return hits[-1] if hits else None


def summarize_holdout(path: Path, tag: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    results = payload.get("results", {})
    # H59's candidate is recorded under one X_* key in each current receipt.
    # Never fall back to a different rule/candidate if that exact key is absent.
    candidate_keys = sorted(key for key in results if key.startswith("X_"))
    candidate = results[candidate_keys[0]] if len(candidate_keys) == 1 else None
    return {
        "truth_proxy": tag,
        "evaluator_version": payload.get("evaluator_version"),
        "withheld_positive_cells": payload.get("withheld_positive_cells"),
        "withheld_segments": payload.get("withheld_segments"),
        "candidate_key": candidate_keys[0] if len(candidate_keys) == 1 else None,
        "candidate_dti": candidate.get("pooled_DTI") if candidate else None,
        "candidate_ci95": candidate.get("ci95") if candidate else None,
        "candidate_score_available": candidate is not None,
    }


def main() -> int:
    with rasterio.open(TEMPLATE) as src:
        template_profile = src.profile.copy()
        template_band = src.read(1)
    footprint = np.isfinite(template_band)

    reconciliation = json.loads(DECISION_PATH.read_text(encoding="utf-8"))
    decision = reconciliation["decision"]
    artifact = reconciliation["current_inspection_artifact"]

    build_receipt_path = ROOT / artifact["build_receipt"]
    build_receipt = json.loads(build_receipt_path.read_text(encoding="utf-8"))
    candidate_path = ROOT / artifact["file"]
    candidate_filename = candidate_path.name
    local_candidate_audit = local_file_audit(candidate_path, template_profile, footprint)

    holdouts = []
    for tag, relpath in (
        ("catalogue", "evidence/holdout59_catalogue.json"),
        ("sgmc_offcat", "evidence/holdout59_sgmc_offcat.json"),
    ):
        path = ROOT / relpath
        if path.is_file():
            holdouts.append(summarize_holdout(path, tag))

    files = []
    for path in sorted(DOWNLOADS.glob("*.tif")):
        try:
            files.append(local_file_audit(path, template_profile, footprint))
        except Exception as exc:  # keep the feed complete if an archive is unreadable
            files.append({
                "file": path.name,
                "error": str(exc),
                "local_layout_checks_pass": False,
                "local_published_format_checks_pass": False,
                "organizer_portal_acceptance_tested": False,
            })

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "decision_evidence": str(DECISION_PATH.relative_to(ROOT)),
        "current_inspection_artifact": {
            "file": candidate_filename,
            "path": artifact["file"],
            "sha256": artifact["sha256"],
            "name_for_identification_only": artifact["name_for_identification_only"],
            "note_for_identification_only": artifact["note_for_identification_only"],
            "current_disposition": artifact["current_disposition"],
            "historic_build_receipt_wording": artifact["historic_build_receipt_wording"],
            "build_receipt": artifact["build_receipt"],
            "local_audit": local_candidate_audit,
        },
        "holdouts": holdouts,
        "downloadable_geotiff_count": len(files),
        "local_published_format_check_pass_count": sum(
            bool(row.get("local_published_format_checks_pass")) for row in files
        ),
        "files": files,
        "notes": [
            "All checks in this feed inspect local bytes only; none emulates or establishes organizer portal behavior or acceptance.",
            "The official problem description says out-of-footprint cells should be null/NaN. This feed reports that encoding separately from in-footprint values.",
            "The whole-array [0,1] predicate is a local diagnostic relevant to the reported portal error, not proof of its cause. No portal upload was made.",
            "H59 is available for inspection only. The project decision in the linked reconciliation explicitly clears no weekly submission slot.",
        ],
        "historical_build_verdict": build_receipt.get("headline"),
    }
    FEED_JSON.parent.mkdir(parents=True, exist_ok=True)
    FEED_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def check(value: bool | None) -> str:
        if value is None:
            return "not comparable"
        return "yes" if value else "no"

    table_rows = []
    for row in sorted(files, key=lambda item: item["file"]):
        name = html.escape(row["file"])
        if row.get("error"):
            grid = values = outside = raw_range = "audit error"
        else:
            grid = check(row.get("local_layout_checks_pass"))
            values = check(row.get("in_footprint_all_in_0_1"))
            outside = "all NaN" if row.get("outside_all_nan") else ("all zero" if row.get("outside_all_zero") else "mixed / other")
            raw_range = check(row.get("whole_array_all_in_0_1"))
        table_rows.append(
            "<tr>"
            f"<td class=\"mono\"><a href=\"downloads/{name}\">{name}</a></td>"
            f"<td>{grid}</td><td>{values}</td><td>{html.escape(outside)}</td>"
            f"<td>{raw_range}</td></tr>"
        )
    rows_html = "\n".join(table_rows)

    holdout_rows = []
    for item in holdouts:
        dti = item["candidate_dti"]
        ci = item["candidate_ci95"]
        if dti is None:
            result = "not present in receipt"
        else:
            result = f"{dti:.4f} [{ci[0]:.4f}, {ci[1]:.4f}]" if ci else f"{dti:.4f}"
        holdout_rows.append(
            f"<tr><td>{html.escape(item['truth_proxy'])}</td>"
            f"<td>{html.escape(str(item['evaluator_version']))}</td>"
            f"<td>{int(item['withheld_positive_cells']):,} / {int(item['withheld_segments']):,}</td>"
            f"<td>{result}</td></tr>"
        )
    holdout_rows_html = "\n".join(holdout_rows)

    file_link = "downloads/" + html.escape(candidate_filename)
    h59 = html.escape(candidate_filename)
    sha = html.escape(artifact["sha256"])
    html_doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="GEMSDOE48 local GeoTIFF audit and explicit no-slot submission decision.">
<title>GEMSDOE48 — local status and format audit</title><link rel="stylesheet" href="style.css">
<style>
table{{border-collapse:collapse;width:100%;margin:12px 0;font-size:.9rem}}
th,td{{border:1px solid #d1d5db;padding:7px 9px;text-align:left;vertical-align:top}}
th{{background:#f3f4f6}} .mono{{font-family:ui-monospace,Menlo,Consolas,monospace;word-break:break-all}}
.card{{background:#f8f9fa;border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin:14px 0}}
.stop{{border:3px solid #b91c1c;background:#fff0ed;padding:16px;border-radius:12px}}
</style></head><body>
<header><div class="wrap"><p>GEMSDOE48 · automatically regenerated local audit</p>
<h1>Downloadable files, local checks, and submission decision</h1></div></header>
<nav><div class="wrap"><a href="index.html">Overview</a><a href="executive-summary.html">Executive summary</a>
<a href="submission-guide.html">Submission guide</a><a href="method.html">Method</a>
<a href="hypotheses.html">Hypotheses</a><a href="validation.html">Validation</a>
<a href="status.html">Status feed</a><a href="irregularities.html">Irregularities</a>
<a href="next-steps.html">Next steps</a></div></nav>
<main class="wrap">
<p>Generated {html.escape(payload['generated_utc'])} by <code>scripts/build_status_feed.py</code>.
Machine-readable record: <a href="data/status.json">docs/data/status.json</a> ·
current decision receipt: <a href="../{html.escape(str(DECISION_PATH.relative_to(ROOT)))}">{html.escape(str(DECISION_PATH.relative_to(ROOT)))}</a>.</p>
<div class="stop"><strong>NO WEEKLY SUBMISSION SLOT IS CLEARED.</strong>
Downloading a file is not submission authorization. No submission was made and no portal upload or acceptance test was performed.
The reported three-per-week limit and zero slots used are user-reported.</div>
<section class="card"><h2>Latest inspection artifact — H59</h2>
<p><a href="{file_link}" download>{h59}</a><br>SHA-256 <code>{sha}</code><br>
<strong>{html.escape(artifact['current_disposition'])}</strong></p>
<p>The older build receipt uses superseded wording that implied submission clearance. It is kept as a historical build record only; the current slot decision is documented in the reconciliation receipt above.</p>
<p>Local H59 observation: one float32 band, EPSG:32611 template grid, in-footprint values finite and in [0,1], zeros outside. This does not establish portal acceptance; zero outside differs from the official null/NaN outside wording.</p></section>
<h2>H59 spatial holdout (public proxies only)</h2>
<table><tr><th>Proxy</th><th>Evaluator</th><th>Withheld cells / segments</th><th>H59 pooled DTI (95% CI)</th></tr>{holdout_rows_html}</table>
<p>H59 is not a matched H49 gate result. Its SGMC off-catalogue result (0.0917) is below both parents (0.0954 / 0.0957) and their union (0.0975); no weekly slot is cleared.</p>
<h2>What this local format feed measures</h2>
<p>“Layout checks” mean one float32 band and the same shape, CRS, and transform as the local template. “In-footprint values” are checked for finiteness and range [0,1]. “Outside encoding” is reported separately; the official problem page describes outside cells as null/NaN. “Whole-array [0,1]” is a raw NumPy-style diagnostic relevant to the reported error, not a confirmed portal rule. The reported error's cause is unknown.</p>
<p><b>These are local byte checks only.</b> They do not emulate the organizer portal, guarantee acceptance, prove a score, or clear a submission slot.</p>
<table><tr><th>Download</th><th>Local layout</th><th>In-footprint [0,1]</th><th>Outside encoding</th><th>Whole-array [0,1]</th></tr>{rows_html}</table>
</main><footer><div class="wrap">GEMSDOE48 · local artifact audit · no organizer acceptance inferred</div></footer>
</body></html>
"""
    FEED_HTML.write_text(html_doc, encoding="utf-8")
    print(f"wrote {FEED_JSON.relative_to(ROOT)} and {FEED_HTML.relative_to(ROOT)}")
    print(f"  current disposition: {artifact['current_disposition']}")
    print(f"  downloadable GeoTIFFs audited: {len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
