# GEMSDOE48 — DOE GEMS Prize fault-discovery system

<div class="dl">
<h2>⬇ Yager conflict-fusion research TIFF (click to download; NOT CLEARED FOR SUBMISSION)</h2>
<p><a class="btn" href="downloads/gemsdoe48-h48-ds-yager-conflict-20261006.tif">Download Yager candidate .tif</a>
<a class="btn" href="downloads/gemsdoe48-h48-ds-yager-conflict-20261006.zip">Download single-file .zip</a></p>
<p>SHA-256 <code>fe68ae6f57be013e26d20006551b43cd84bb5fe4a0b07d1d10ce4725c90fd16c</code> · single-band float32 · EPSG:32611 · 100 m · 3730 × 3292 · all finite in [0,1].</p>
<p><b>Decision: DO NOT SPEND A WEEKLY SLOT.</b> Corrected public SGMC proxy DTI is 0.08407 vs 0.09709 tip, 0.09613 dotted, and 0.09030 naïve mean; it loses in all four quadrants. This is a public-derived proxy, not private expert truth or a DrivenData score.</p>
<p><b>Suggested name:</b> <code>GEMSDOE48-H48-DS-CONFLICT</code><br>
<b>Suggested short note:</b> <code>H48 dotted+tip Yager fusion; distinct in bounded scan; SGMC proxy gate failed; do not spend slot</code></p>
<p><a href="downloads/gemsdoe48-h48-ds-yager-conflict-20261006-unassigned-diagnostic.tif">Unassigned-belief diagnostic (do not submit)</a> · <a href="data/proxy-validation.json">Corrected proxy receipt</a> · <a href="data/proxy-validation-v1-retracted.json">v1 retraction</a></p>
<p><b>Format caveat:</b> finite zeros are stored outside the footprint to keep every value in [0,1]; this conflicts with the official null/NaN-outside wording. Portal acceptance was not tested.</p>
</div>

## Later-main DS48 re-emission — also not slot-cleared

A separate Dempster-ranked, mass-matched emission was added by PR #6. Its receipt reports SGMC off-catalogue DTI 0.09068 versus 0.09613 for the dotted baseline (about 5.7% lower); its catalogue-based proxy is anti-monotone with the known live ladder. It is **unscored and not cleared for a slot**. The [PR #6 research subsite](ds48-fusion/index.html) preserves its method and diagnostic layers; it is not an upload recommendation.

## Previous H48-1 file — available for comparison, not a slot recommendation

<div class="dl">
<h2>H48-1 Dempster candidate (historical; do not upload without a new passing gate)</h2>
<p><a class="btn" href="downloads/{{TIF}}">Download {{TIF}}</a></p>
<p>{{BYTES}} bytes · sha256 <code>{{SHA16}}…</code> · {{NPX}} dots · all-finite float32 in [0, 1] · EPSG:32611 · 3730 × 3292 · all {{NCHK}} checks passed in the file receipt · <a href="downloads/{{ZIP}}">.zip</a> · <a href="downloads/{{RECEIPT}}">receipt</a></p>
<p><b>Historical artifact name:</b> <code>{{UNIQUE}}</code><br><b>Historical note:</b> <code>{{NOTE}}</code></p>
<p><a href="executive-summary.html">→ Read the submission instructions and current no-go decision</a></p>
</div>

## Decision receipt

The corrected metric implementation multiplies prediction confidence into every TP maximum and computes distance neighborhoods on the full scene before accumulating block terms. The earlier v1 report omitted confidence and truncated quadrants; its apparent pass is **retracted**. See the [v2 receipt](data/proxy-validation.json) and [retraction record](data/proxy-validation-v1-retracted.json).

| Surface | Corrected public SGMC proxy DTI | Result |
|---|---:|---|
| Tip parent | **0.09709** | strongest baseline |
| Dotted parent | 0.09613 | baseline |
| Naïve mean | 0.09030 | baseline |
| Yager conflict-transfer belief | 0.08407 | fails vs all three; loses in four quadrants |

The SGMC layer is an owner-derived proxy from public state-map data, not hidden expert truth. No score improvement is claimed. No DrivenData upload or private score was observed.

## Why the reported 0.2778 is plausible—but not attributed to a local file

The official distance-weighted Tversky metric uses α=0.2, β=0.8 and a 300 m triangular kernel. False negatives carry four times the coefficient of false positives, so removing redundant off-target mass while preserving near-trace coverage can improve score. That is a plausible metric mechanism, not proof that thinning caused this participant's result or that the local raster bytes match it. The 0.2778 public row was rank 13 in the 2026-10-06 snapshot; no TIFF hash links it to a local file.

## Leaderboard snapshot and refresh

The [public snapshot](leaderboard.html) was observed 2026-10-06: leader 0.3774, rank 7 at 0.3195, and rank 13 at 0.2778. The scheduled workflow in `.github/workflows/feed.yml` attempts a refresh from GitHub Actions and commits the static feed/site to the legacy `main:/` Pages source. A local live HTTP fetch failed during TLS negotiation, so live-parser success has not yet been established; fixture tests pass. See the [feed data](data/leaderboard.json) and [official board](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).

## Next experiments — none slot-cleared

The earlier TMI-only cross-scale persistence arm was already screened in GEMSDOE47 and lost to its fixed-seed random control. Five prospective geological hypotheses and their source/coverage caveats are in [hypotheses](hypotheses.html). None has been spatially validated here. Do not use a weekly slot until a candidate beats the corrected holdout best and passes the format gate.

> **Core values.** *Maximize P(Win)* by rejecting a measured loss rather than spending an unvalidated slot. *Own the Outcome* by preserving the file, diagnostic, correction, and uncertainty together. See [irregularities](irregularities.html) and [sources](sources.html).
