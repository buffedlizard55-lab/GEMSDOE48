# Executive summary — downloads, decision, and submission procedure

## Current decision: no weekly slot is cleared

The requested Yager conflict-transfer candidate is available for research, but the corrected spatial SGMC proxy gate failed. The H48-1 Dempster candidate from the prior session also did not beat its corrected holdout best; its owner-built LSI estimate cannot resolve this difference. PR #6 added an unscored DS48 re-emission, whose SGMC off-catalogue proxy is below the dotted baseline; its separate catalogue-based proxy is anti-monotone with the known live ladder. **Do not upload any of these files now.** No private score or portal acceptance was observed.

### Requested Yager candidate

**[Download Yager TIFF](downloads/gemsdoe48-h48-ds-yager-conflict-20261006.tif)** ·
[download single-file ZIP](downloads/gemsdoe48-h48-ds-yager-conflict-20261006.zip) ·
[build audit](downloads/gemsdoe48-h48-ds-yager-conflict-20261006-audit.json) ·
[unassigned-belief diagnostic — do not submit](downloads/gemsdoe48-h48-ds-yager-conflict-20261006-unassigned-diagnostic.tif)

- **Name (research only):** `GEMSDOE48-H48-DS-CONFLICT`
- **Suggested short note:** `H48 dotted+tip Yager fusion; distinct in bounded scan; SGMC proxy gate failed; do not spend slot`
- **SHA-256:** `fe68ae6f57be013e26d20006551b43cd84bb5fe4a0b07d1d10ce4725c90fd16c`
- **Corrected public proxy DTI:** Yager 0.08407; tip 0.09709; dotted 0.09613; naïve mean 0.09030. Yager loses in all four quadrants.
- **Format caveat:** the candidate is one-band float32, EPSG:32611, 100 m, 3730×3292, and every pixel is finite in [0,1] by local byte audit. This does not establish the cause of the earlier portal error or demonstrate acceptance. Finite zeros outside the footprint do not meet the official null/NaN-outside wording; the portal was not tested.

### Prior H48-1 Dempster candidate (comparison only)

**[Download H48-1 TIFF](downloads/{{TIF}})** ·
[ZIP](downloads/{{ZIP}}) · [receipt](downloads/{{RECEIPT}})

| field | historical value; not a submit recommendation |
|---|---|
| file | `{{TIF}}` |
| name | `{{UNIQUE}}` |
| note | `{{NOTE}}` |
| SHA-256 prefix / bytes | `{{SHA16}}…` / {{BYTES}} |
| result | did not beat b2 on the reported SGMC quadrants (2/4); LSI’s 0.26336 vs 0.26351 is too close for that instrument’s top-family rank power |

### PR #6 DS48 emission (comparison only; not cleared)

[Download `gemsdoe48-ds48-emission.tif`](downloads/gemsdoe48-ds48-emission.tif) ·
[build receipt](../registry/submission_build.json) · [research subsite](ds48-fusion/index.html)

The main-branch PR #6 emission has 37,654 positive pixels and passes that builder's single-band, grid, finite, and [0,1] checks. Its recorded SGMC off-catalogue DTI is 0.09068 versus 0.09613 for the dotted baseline (about 5.7% lower). A separate catalogue-proximity proxy is anti-monotone with the four known live anchors (Spearman −1, n=4) and cannot clear a slot. The emission is all-finite with zeros outside, so the official null/NaN-outside caveat remains; no portal acceptance or organizer score exists. **Research artifact only—do not upload.**

## Why the proxy result and 0.2778 are not organizer scores

The correction multiplies prediction confidence into each TP maximum and computes full-scene distance neighborhoods before fold accumulation. The earlier v1 apparent pass is **retracted** because it omitted confidence and cropped each quadrant before calculating distances. See the [v2 fold receipt](data/proxy-validation.json) and [v1 retraction](data/proxy-validation-v1-retracted.json).

The official metric weights false negatives four times as heavily as false positives (α=0.2, β=0.8), within a 300 m triangular kernel. Removing redundant off-target mass can plausibly improve DTI while preserving near-trace coverage, but that does not prove why a particular participant received 0.2778 or that a local file is the scored artifact. In the observed 2026-10-06 public snapshot, 0.2778 was rank 13; leaderboard rows are not linked to local TIFF hashes.

## Submission form procedure (use only after a candidate clears validation)

When a future candidate has passed the slot gate and format checks:

1. Sign in at the [DOE GEMS DrivenData competition](https://www.drivendata.org/competitions/306/competition-doe-gems/).
2. Open **Submissions → Submit**.
3. Upload exactly one single-band GeoTIFF, or a ZIP containing exactly one GeoTIFF.
4. Paste that candidate’s distinct name and concise note into the optional note field.
5. Submit only after checking its raster receipt, then record the returned score and artifact hash in `registry/live_scores.json`.

The Yager file above is **not cleared**. Do not treat the procedure as a recommendation to submit it.

## Diagnostic layers (not for submission)

| layer | meaning |
|---|---|
| [H48-1 normalized Dempster belief](downloads/diagnostics/gemsdoe48-h48-1-belief_dempster_mF_norm01.tif) | previous graded belief surface |
| [H48-1 conflict K](downloads/diagnostics/gemsdoe48-h48-1-conflict_K.tif) | disagreement between the two source families |
| [H48-1 Yager unassigned mass](downloads/diagnostics/gemsdoe48-h48-1-unassigned_yager_mTheta_incl_conflict.tif) | unassigned belief including conflict |
| [H48-1 Dempster unassigned mass](downloads/diagnostics/gemsdoe48-h48-1-unassigned_dempster_mTheta.tif) | residual mass after classical normalization |

The Yager candidate’s own unassigned-belief raster is linked above. All diagnostic layers are for scientific review only.
