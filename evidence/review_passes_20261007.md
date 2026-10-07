# H50-1 review passes — 2026-10-07 UTC

These are sequential review passes by the coding agent, not independent human or organizer reviews. They preserve the pre-build slate, implementation corrections, local audits, proxy result and remaining limitations.

## Pass 1 — brief, prior art, sources, and preregistration

- Re-read the full owner brief in `README.md`, the existing executive site, H48/H49 records, and the bounded campaign history relevant to thermal, seismic, Landsat, and alteration methods.
- Froze four ranked hypotheses and bbox-level source-availability claims in `docs/research/hypotheses-20261007.md` and `evidence/hypothesis_slate_20261007.json` at **2026-10-07 02:05:46 UTC**, before candidate construction and holdout scoring.
- Explicitly treated broad thermal targeting as prior art: H18-5/H49-1 already proposed related geothermal/probe ideas. H50-1 is a narrow, unexecuted repeated-date leave-one-station-out persistence operator; no global novelty claim is made.
- Checked official source landing/catalog pages. Landsat, ComCat, and Sentinel counts are broad-bbox metadata only, not exact footprint or usable-pixel coverage. No H50-2/3/4 payload was downloaded.

## Pass 2 — static code review and deterministic v1 candidate build

- Static inspection found an erroneous coordinate-conversion expression in the unexecuted builder; it was removed in favor of explicit paired x/y arrays. A syntax error in the range-check expression was also fixed before candidate construction. `py_compile` then passed.
- Copied the 1,080,530-byte probe archive into `data/external/` and verified SHA-256 `1301f70d230058e616ea5d34d1c7a32fabf7d49198172f376c59c89bd652eca3` against the pinned owner-mirror commit. GDR bytes were not downloaded directly; the local source is identified as an owner mirror.
- Built v1 from the frozen rule, then rebuilt from the persistent archive. Both emitted the same TIFF SHA-256, `1997316a0102909135dfa12d48e86dbc1fbe567b4d4ba3884c53ce981b2bc50c`.
- V1's source audit counted 3,800 DBF rows, 2,782 raw point records in finite footprint cells, 10 duplicate same-row station/date groups aggregated, 31 repeat-persistent rows, 1,410 fallback-positive rows, and 1,441 selected rows total. A first source-only correction changed the exploratory count from 26 to 31 before v1 holdout scoring. A later review found this did not collapse duplicate rows at the same physical location; see Pass 7. The v1 receipt and candidate are retained separately.
- V1 support contained 29,661 positive cells; it was binary 0/1 inside the footprint and NaN outside.

## Pass 3 — separate v1 format and bounded uniqueness audits

- `scripts/validate_submission.py` reopened v1 and passed single-band float32, EPSG:32611, 100 m, 3,730 × 3,292 dimensions, template transform, in-footprint `[0,1]` values, and NaN/nodata outside. The current v2 file was later revalidated separately.
- The v1 uniqueness run compared against 35 other local same-grid TIFFs and found no exact prediction or support match; its maximum support Jaccard to historic inputs was 0.006205. The corrected v2 audit has 36 comparators because it includes v1: v2 has no exact match, but is highly similar to v1 (Jaccard 0.998179, with v2 removing 54 positive cells).
- Both checks are intentionally local/bounded; neither proves global cross-repository uniqueness or organizer-side acceptance.

## Pass 4 — v1 frozen spatial validation and promotion decision

- Scored after the slate was frozen, with the repository's four fixed quadrants, official DTI equations, core truth and 300 m halo. Primary target: pinned newer SGMC off-catalogue public-map proxy. Separate sensitivity: older raw SGMC raster. Neither is private expert truth or organizer-authenticated.
- V1 H50-1 primary mean DTI: **0.003922077**. H49 same-protocol mean: **0.100751188**. Paired difference: **−0.096829111**, with **0/4** positive folds.
- V1 older raw-SGMC means: H50-1 **0.003930375**, H49 **0.099768355**; paired difference: **−0.095837980**, **0/4** positive folds.
- The preregistered H50 promotion gate required at least +0.005 mean over H49, ≥3/4 positive primary folds, and positive direction on the older raster. V1 failed every numeric condition. **No weekly slot is cleared.** A public proxy pass would not by itself have cleared the slot either.
- V1 receipts: `evidence/holdout_h50_probe_v1_preduplicate_correction_20261007.json`, `evidence/holdout_h50_probe_raw_sgmc_v1_preduplicate_correction_20261007.json`; paired gate: `evidence/h50_probe_vs_h49_v1_preduplicate_correction_20261007.json`.

## Pass 5 — user-facing workflow and scientific framing

- Put the corrected H50 v2 download first in `docs/index.html` and marked it clearly as **research only / do not upload**. Added a short candidate-tracking comment without implying slot approval.
- Added `docs/submission-guide.html` with explicit DrivenData upload steps, exact local format checks, the current no-slot decision, and the distinction between local validation and organizer acceptance.
- Updated the README executive block, current and superseded artifacts, reproducible H50 commands, proxy results, source/license caveats, and both source-count/identity corrections without altering the frozen preregistration JSON.

## Pass 6 — unit, integration, and link review

- Added three focused tests for exact-coordinate/date aggregation and leave-one-location-out residuals, repeat-vs-fallback selection, and exact Euclidean buffer clipping. Updated the cell-centre affine operation to avoid a pending deprecation warning.
- Full suite command: `./.venv/bin/python -m pytest -q -ra` completed with exit code 0; 3 pipeline tests were skipped because raw competition inputs are not restored. No hidden labels were fetched.
- `py_compile` and `git diff --check` passed. Final local link validation found no missing file links in `docs/index.html` (44 links checked) or `docs/submission-guide.html` (18 links checked).

## Pass 7 — second-review source-identity correction and v2 sensitivity

- After v1 scoring, reviewed the source DBF station labels and exact point geometry. Display station labels repeat across distinct coordinates; 13 exact-coordinate groups contain multiple source rows (16 rows beyond the first). Fourteen same-location/same-date groups have 18 additional readings; the v2 builder aggregates those by median. The exact coordinate key is a source-only clarification, with no change to thresholds. It remains a post-v1-score correction and is fully disclosed in `evidence/h50_implementation_errata_20261007.json`.
- V2 source counts: 3,800 rows; 3,784 exact coordinate locations; 2,782 raw records but 2,768 point locations on finite footprint cells; 28 repeat-persistent locations; 1,404 fallback-positive locations; 1,432 selected locations; 29,607 positive raster cells.
- V2 spatial proxy sensitivity: primary mean **0.003922712** vs H49 **0.100751188**, delta **−0.096828476**, 0/4 positive folds. Older raw-SGMC mean **0.003931016** vs H49 **0.099768355**, delta **−0.095837340**, 0/4. This fails the preregistered numerical gate and, because v1 results were already observed, does not constitute confirmatory validation. The weekly slot remains closed.
- Current output SHA-256 is `f12e5391bb9cd2709ae7331699bb0876cc4bf3c443f96ea8a5456c858eb67908`; local format validation passes. A 36-artifact same-grid comparison found no exact match, with superseded v1 as nearest (Jaccard 0.998179); no global or organizer uniqueness is claimed.

## Pass 8 — final packaging and reproducibility review

- Reviewed staged-artifact scope and found that the selected-location CSVs used CRLF line endings, which `git diff --check` reports as trailing whitespace. Standardized both exports to LF without changing any field values or row order; retained each original build-time CSV hash alongside the normalized-file hash and timestamp in its receipt. Updated the builder to emit LF on future runs.
- Re-ran the complete suite with a clean local environment: `python -m pytest -q -ra` passed; three raw-input pipeline cases skipped because the source mirrors are not restored. `compileall`, `git diff --check`, local HTML-link checks, current TIFF format validation against the official sample-template footprint, and a fresh bounded uniqueness audit passed.
- Confirmed the TIFF hash remains `f12e5391bb9cd2709ae7331699bb0876cc4bf3c443f96ea8a5456c858eb67908`, local uniqueness remains bounded (36 comparisons; no exact match; v1 Jaccard 0.998179), and no results justify using a weekly slot.

## Remaining blockers

No authenticated DrivenData training/private labels, no organizer-side file acceptance or artifact-to-score attribution, no fold-independent reconstruction of upstream surfaces, and no independent human or organizer review. Public-proxy evidence is not a leaderboard score. The H50-1 proxy result is weak; do not spend a competition slot.
