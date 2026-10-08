#!/usr/bin/env python3
"""Regenerate the machine-readable and human-readable status feed.

The feed answers, without any manual inspection:

* which downloadable file is the **current primary submission candidate**;
* whether each downloadable file is **portal-safe** (single band, float32, all values
  finite, every value in [0, 1], no nodata tag, grid equal to the organizer template);
* which holdout receipts and build receipts back the current decision.

Outputs: ``docs/data/status.json`` (machine readable) and ``docs/status.html``.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / "docs/downloads"
TEMPLATE = ROOT / "data/raw/sample_submission_template.tif"
FEED_JSON = ROOT / "docs/data/status.json"
FEED_HTML = ROOT / "docs/status.html"


def portal_safety(path: Path, template_profile) -> dict:
    """Run the portal's own checks on one GeoTIFF."""
    with rasterio.open(path) as src:
        profile = src.profile.copy()
        band = src.read(1)
    finite = bool(np.isfinite(band).all())
    in_range = bool(np.all((band >= 0) & (band <= 1)))
    return {
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest(),
        "dtype": profile["dtype"],
        "bands": int(profile["count"]),
        "shape": [int(band.shape[0]), int(band.shape[1])],
        "crs": profile["crs"].to_string() if profile["crs"] else None,
        "transform_matches_template": tuple(profile["transform"])[:6]
        == tuple(template_profile["transform"])[:6],
        "crs_matches_template": profile["crs"] == template_profile["crs"],
        "nodata": profile.get("nodata"),
        "all_finite": finite,
        "min": float(np.nanmin(band)),
        "max": float(np.nanmax(band)),
        "positive_cells": int((band > 0).sum()),
        "portal_safe": bool(finite and in_range and profile["dtype"] == "float32"
                            and int(profile["count"]) == 1 and profile.get("nodata") is None
                            and tuple(profile["transform"])[:6]
                            == tuple(template_profile["transform"])[:6]),
    }


def newest(pattern: str) -> Path | None:
    hits = sorted(ROOT.glob(pattern))
    return hits[-1] if hits else None


def main() -> int:
    with rasterio.open(TEMPLATE) as src:
        template_profile = src.profile.copy()

    build_receipt = newest("evidence/build_h59_receipt_*.json")
    holdouts = {}
    for tag, path in (("catalogue", ROOT / "evidence/holdout59_catalogue.json"),
                      ("sgmc_offcat", ROOT / "evidence/holdout59_sgmc_offcat.json")):
        if path.exists():
            payload = json.loads(path.read_text())
            holdouts[tag] = {
                "evaluator_version": payload["evaluator_version"],
                "withheld_positive_cells": payload["withheld_positive_cells"],
                "withheld_segments": payload["withheld_segments"],
                "results": {k: {"pooled_DTI": v["pooled_DTI"], "ci95": v["ci95"]}
                            for k, v in payload["results"].items()},
                "random_control_same_mass": payload.get("random_control_same_mass"),
            }

    primary = None
    receipt_payload = None
    if build_receipt and build_receipt.exists():
        receipt_payload = json.loads(build_receipt.read_text())
        primary_name = receipt_payload["submission"]["filename"]
        primary = {
            "file": primary_name,
            "sha256": receipt_payload["submission"]["sha256"],
            "positive_cells": receipt_payload["submission"]["positive_cells"],
            "name_for_portal": receipt_payload["submission"]["name_for_portal"],
            "note_for_portal": receipt_payload["submission"]["note_for_portal"],
            "headline": receipt_payload["headline"],
            "verdict": receipt_payload["verdict"],
            "receipt": str(build_receipt.relative_to(ROOT)),
            "built_utc": receipt_payload["timestamp_utc"],
            "rule": receipt_payload.get("rule"),
        }

    files = []
    for path in sorted(DOWNLOADS.glob("*.tif")):
        try:
            files.append(portal_safety(path, template_profile))
        except Exception as exc:  # keep the feed complete even if a file is unreadable
            files.append({"file": path.name, "error": str(exc), "portal_safe": False})
    safe = [f for f in files if f.get("portal_safe")]
    unsafe = [f for f in files if not f.get("portal_safe")]

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "primary": primary,
        "holdouts": holdouts,
        "downloadable_files": len(files),
        "portal_safe_files": len(safe),
        "portal_unsafe_files": len(unsafe),
        "files": files,
        "notes": [
            "portal_safe = single band, float32, all values finite, every value in [0,1], "
            "no nodata tag, transform equal to the organizer template.",
            "Files with NaN outside the footprint fail `all(0 <= v <= 1)` and are the "
            "documented cause of the portal error 'Predicted values must be in range [0, 1]'.",
            "Only the primary listed above is a current submission candidate; every other "
            "file is retained for traceability and is not cleared.",
        ],
    }
    FEED_JSON.parent.mkdir(parents=True, exist_ok=True)
    FEED_JSON.write_text(json.dumps(payload, indent=1))

    rows = "\n".join(
        f"<tr><td class='mono'>{f['file']}</td>"
        f"<td>{f.get('positive_cells', '')}</td>"
        f"<td>{'✅ safe' if f.get('portal_safe') else '❌ not portal-safe'}</td>"
        f"<td>{'' if f.get('all_finite', True) else 'NaN present'}</td>"
        f"<td>{f.get('min', '')} … {f.get('max', '')}</td></tr>"
        for f in sorted(files, key=lambda f: (not f.get("portal_safe"), f["file"]))
    )
    holdout_rows = "".join(
        f"<tr><td>{tag}</td><td>{h['evaluator_version']}</td>"
        f"<td>{h['withheld_positive_cells']:,} cells / {h['withheld_segments']:,} segments</td>"
        f"<td>{h['results'].get('X_cand_cover_q0.0_s4.0', h['results'].get('H_DS_belief_top40k', {})).get('pooled_DTI', float('nan')):.4f}</td></tr>"
        for tag, h in holdouts.items()
    )
    primary_block = "no build receipt found"
    if primary:
        primary_block = (
            f"<p><b>Primary candidate:</b> <code>{primary['file']}</code><br>"
            f"SHA-256 <code>{primary['sha256']}</code><br>"
            f"{primary['positive_cells']:,} positive cells · rule "
            f"{primary.get('rule')}<br><b>{primary['headline']}</b></p>"
            f"<p>Portal name: <code>{primary['name_for_portal']}</code><br>"
            f"Portal note: <code>{primary['note_for_portal']}</code></p>"
        )
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GEMSDOE48 — status feed</title><link rel="stylesheet" href="style.css">
<style>
table{{border-collapse:collapse;width:100%;margin:12px 0;font-size:.85rem}}
th,td{{border:1px solid #d1d5db;padding:6px 8px;text-align:left;vertical-align:top}}
th{{background:#f3f4f6}} .mono{{font-family:ui-monospace,Menlo,Consolas,monospace;word-break:break-all}}
.card{{background:#f8f9fa;border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin:14px 0}}
</style></head><body>
<header><div class="wrap"><p>GEMSDOE48 · automatically regenerated status feed</p>
<h1>Current feed — what is downloadable and what is portal-safe</h1></div></header>
<nav><div class="wrap"><a href="index.html">Overview</a><a href="executive-summary.html">Executive summary</a>
<a href="submission-guide.html">Submission guide</a><a href="method.html">Method</a>
<a href="hypotheses.html">Hypotheses</a><a href="validation.html">Validation</a>
<a href="status.html">Status feed</a><a href="irregularities.html">Irregularities</a>
<a href="next-steps.html">Next steps</a></div></nav>
<main class="wrap">
<p>Generated {payload['generated_utc']} by <code>scripts/build_status_feed.py</code>.
Rebuild with <code>python3 scripts/build_status_feed.py</code>. Machine-readable twin:
<a href="data/status.json">docs/data/status.json</a>.</p>
<div class="card">{primary_block}</div>
<h2>Strict holdout receipts backing the decision</h2>
<table><tr><th>Truth proxy</th><th>Evaluator</th><th>Withheld</th><th>H59 pooled DTI</th></tr>{holdout_rows}</table>
<h2>Every downloadable GeoTIFF ({len(files)} files, {len(safe)} portal-safe)</h2>
<p>{len(unsafe)} file(s) are <b>not</b> portal-safe (NaN outside the footprint or other
format deviation). They are kept for traceability and are not submission candidates.</p>
<table><tr><th>File</th><th>Positive cells</th><th>Portal check</th><th>NaN</th><th>Range</th></tr>{rows}</table>
</main>
<footer><div class="wrap">GEMSDOE48 · status feed · regenerated automatically</div></footer>
</body></html>
"""
    FEED_HTML.write_text(html)
    print(f"wrote {FEED_JSON.relative_to(ROOT)} and {FEED_HTML.relative_to(ROOT)}")
    print(f"  primary: {primary['file'] if primary else None}")
    print(f"  downloadable files: {len(files)} ({len(safe)} portal-safe, {len(unsafe)} not)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
