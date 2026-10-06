# Independent review passes — 2026-10-06 UTC

Five review passes were completed across the original candidate, main-branch reconciliation, and SGMC input follow-up. These are documented engineering reviews, not organizer sign-off.

## Pass 1 — scope, provenance, and official format

- Re-checked the official challenge page for the grid, score, and upload requirements: 3,730 × 3,292, EPSG:32611, 100 m, one float32 band, values in `[0,1]` in the valid area, and null/NaN outside. The public sample template uses NaN nodata.
- The output was independently reopened. Its finite-cell mask equals the separately derived sample-template footprint exactly: 5,167,373 inside cells; 7,111,787 outside cells; 60,988 positive catalogue labels; zero footprint-mask differences. The sample pixel values were never used as labels.
- Hash-pinned candidate inputs, label/template mirrors, and the SGMC proxy were rechecked. Third-party owner-mirror identity is kept distinct from organizer authentication; license status remains unverified.
- Corrected the leaderboard row interpretation: DARD's 0.3195 was #7, not the top score. The displayed 0.2778 row belonged to `extradr19`; no artifact-level association is claimed and no automated monitoring is implemented.

**Artifacts:** `docs/sources.md`, `docs/irregularities.md`, `evidence/source_audit.json`, `evidence/footprint_mask_receipt.json`, `evidence/submission_validation_20261006.json`.

## Pass 2 — formulas, edge cases, metric APIs, and leakage

- Re-derived the discounted masses and Dempster conflict expression. Tests cover agreement (`m(F)=0.75`), disagreement (`m(F)=1/3`, `m(Theta)=1/3`, `K=0.25`), source symmetry, total ignorance at zero reliability, and fail-closed total conflict.
- The distance-weighted Tversky implementation is compared with an independent brute-force oracle for the branch's core-plus-halo scorer. Compatibility tests also cover the prior upstream metric's offset/kernel, shift, component, brute-force, credit-bar, and footprint APIs.
- Revisited fold truth/domain semantics: only positive labels in each core quadrant count as truth; the 300 m halo admits nearby predictions for the distance kernel. Source surfaces were not rebuilt inside folds. The H33-2-B2 owner audit describes a full-catalogue proximity prune, so the results are conditional and potentially leaky.
- Confirmed `rho=0.5` was not retuned after observing results. The historical alpha=.99 model and binary union remain separate comparators.

**Artifacts:** `src/gemsdoe48/evidence.py`, `src/gemsdoe48/metric.py`, `scripts/run_spatial_holdout.py`, `tests/test_metric*.py`, `tests/test_yager_evidence.py`.

## Pass 3 — artifact bytes, output format, and original catalogue gate

- Rebuilt the primary GeoTIFF and two diagnostics from the hash-pinned source surfaces. The primary SHA-256 remains `818957c0cb69caf360d445c7f7a684578c37528f363b5d84f5ae3be832e7413f`; unassigned-mass and raw-conflict SHA-256s are `975c217ef803a45041077a219ba460134a8c84c8ea9f7ffc0414ddb47cb54ccd` and `5daa6eaf7ce78603896b0696df5be67d9a71971da936e030161c3157944b576b`.
- Local format audit passed: 3,730 × 3,292, EPSG:32611, 100 m, one float32 band; all 5,167,373 in-footprint cells are finite and within `[0,0.75]`; exactly 7,111,787 cells outside are NaN/nodata. This is not organizer acceptance.
- Proved the result is not arithmetic averaging: 47,905 in-footprint cells differ; union-only MAE is 0.22166091; maximum absolute difference is 0.25. Correlation is not used as the distinction test.
- Catalogue-proxy blocked mean DTI: fusion 0.03258776; tip/stepover 0.08682019; arithmetic mean 0.04640640; dotted 0.00683054. Fusion loses to tip and mean on all four folds and fails the preregistered gate.

**Artifacts:** `docs/downloads/GEMSDOE48-*.tif`, `evidence/build_receipt_20261006.json`, `evidence/submission_validation_20261006.json`, `evidence/holdout_20261006.json`.

## Pass 4 — main-branch reconciliation and SGMC paired re-evaluation

- Reviewed main's newer alpha=.99/union work, retained its receipts, source assets, scripts, and older site pages in an archive with a warning. Kept the branch's rho=.5 builder as the default, retained the earlier historical builder at `scripts/previous_main_build_submission.py`, and preserved the later PR #5 Dempster builder as `scripts/previous_main_build_submission_pr5.py.disabled`.
- Preserved the upstream metric APIs in the combined metric module and added the exact current main metric tests as `tests/test_metric_main.py`; kept the previous metric and Yager tests in separate compatibility files. The PR-head CI run passed its then-current 162-test suite; after the follow-up regression test and provenance changes, the complete local suite has 178 tests and passed (see Pass 5).
- Recomputed the prior alpha=.99 belief and binary union alongside dotted, tip, mean, and rho=.5 using the same four quadrants, held-out core, 300 m halo, and metric. The first run used the prior raw SGMC raster: 61,664 off-catalogue cells; rho=.5 mean 0.06857388 versus dotted 0.09450317, tip 0.09449144, arithmetic mean 0.08784120, and prior union 0.09595726, losing to each in 0/4 folds. This remains the separately reported raw-raster sensitivity.
- The historical pooled alpha=.99 tier sweep and its incompatible full-grid quadrant scores were not treated as the promotion gate.
- Updated current HTML/Markdown pages to remove stale slot-clear language; earlier pages are preserved in `docs/archive-main-pages/` and marked historical. Disabled the upstream six-hour leaderboard workflow (`.github/workflows/feed.yml.disabled`); its parser helper no longer has a network-fetch path. The stale root Markdown site builder is a no-op, and the DS48 sub-site builder inserts an explicit retirement banner. No weekly slot was used and no private-label or organizer score is claimed.
- After the workflow/page retirement and link repairs, reran `compileall` and all 162 tests successfully; a local-link audit found zero missing links across 41 HTML pages. Direct execution of the retired site builder is a no-op, and the parser exits with its disabled notice without making a request.

**Artifacts:** `evidence/holdout_20261006.json`, `docs/research/holdout-results-20261006.md`, `docs/validation.html`, `docs/archive-main-pages/`, `scripts/previous_main_build_submission.py`, `tests/test_metric_main.py`.

## Pass 5 — newer SGMC derivative and sensitivity review

- Compared the prior raw SGMC raster with the newer manifest-pinned derived raster (`643cbe…`). Spatial dimensions, CRS, and affine transform match; nodata metadata differs, and the positive masks differ at 1,450 cells (1,446 newer-only and 4 raw-only). The derivation discrepancy remains unresolved; neither raster is organizer-authenticated. The audit is `evidence/sgmc_raster_comparison_20261006.json`.
- Re-ran `scripts/run_spatial_holdout.py` against the newer derivative with the same >300 m target filter, fixed folds, held-out cores, 300 m halos, and official metric; the registered off-catalogue target has 62,122 cells. On this target, rho=.5 Dempster mean DTI is 0.06926131 and loses to dotted, tip, arithmetic mean, and prior union in 0/4 paired folds. The historical Yager alternative scores 0.08289145, beats Dempster in 4/4, but loses to dotted, tip, arithmetic mean, and prior union in 0/4. Neither clears a slot.
- Preserved the older raw-raster holdout separately (61,664 cells; Dempster 0.06857388; Yager 0.08206068) rather than pooling it with the primary derivative. The older PR #5 full-scene/≥300 m evaluator (63,121 cells) remains a separate historical protocol.
- Updated the README and current validation, source, method, executive-summary, and irregularities pages; synchronized `evidence/holdout_run.log` with the primary JSON report. The full-scene PR #5 proxy report was regenerated against the newer derivative (63,121 cells at >=300 m; gate false) and remains explicitly separate from the current fold protocol.
- Final checks passed: 178 pytest tests, Python compileall, local GeoTIFF format audit, and JSON/hash/log-sync checks. A link audit found zero missing local references across 300 HTML and 45 Markdown links. Direct leaderboard-script execution exits with its explicit no-network/disabled notice.
- Results remain public-map proxy diagnostics, not private-label or organizer scores.

**Artifacts:** `evidence/sgmc_raster_comparison_20261006.json`, `evidence/holdout_20261006.json`, `evidence/holdout_raw_sgmc_20261006.json`, `docs/research/holdout-results-20261006.md`.

## Pass 6 — latest-main H49 integration and slot-gate re-review

- Fetched and integrated the newer `origin/main` tip `0eaae0b` (PR #7) while staying on the Arena branch. Preserved its H49 code, tests, candidate outputs, audit receipts, and sub-site; kept H48 as a separate method/result rather than silently replacing its data or claims.
- Added a candidate label to the existing spatial-holdout runner and evaluated H49 using the exact H48 four-quadrant/core-plus-300 m-halo protocol, >300 m SGMC target, and DTI parameters. On the newer SGMC derivative, H49 mean DTI is 0.100751188 vs 0.096991657 for the prior-union best (+0.003759531, 4/4); on the separate older raw raster it is 0.099768355 vs 0.095957265 (+0.003811091, 4/4). Reports are separate and machine-readable.
- Explicitly reviewed the H49 result as post-selection on related public proxy evidence, not an independent blind holdout. Its +0.00376 delta is below the live instrument's roughly 0.005 resolution, and the live-anchored change bracket is −0.010 to +0.005. The slot gate remains closed despite the numeric proxy win.
- Preserved the upstream H49 TIFF unchanged and created a separate format-only copy that sets outside-footprint cells to NaN/nodata, preserving all 5,167,373 in-footprint values exactly. Local validation passes (one-band float32, EPSG:32611, 100 m, 3,730 × 3,292, in-footprint `[0,1]`); organizer acceptance remains untested.
- Reconciled root README, current landing/validation/executive/next-steps pages, H49 sub-site, and archived mainline pages. H49 sources/rights are described cautiously. Six-hour leaderboard references are clearly historical; the current workflow remains disabled and the parser remains offline-only.
- Final local checks: 216 pytest tests passed, 3 skipped (219 collected); compileall passed; 252 active HTML references and 61 active Markdown links checked with zero missing; JSON receipts parsed; H48 holdout JSON/log remain byte-identical; no conflict markers or whitespace errors.

**Artifacts:** `docs/research/holdout-h49-results-20261006.md`, `evidence/holdout_h49_spatial_comparison_20261006.json`, `evidence/holdout_h49_raw_sgmc_sensitivity_20261006.json`, `evidence/h49_submission_validation_20261006.json`, `docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif`.

## Re-review triggers

Repeat the affected reviews if an input or label hash changes, an official rule changes, the footprint is rebuilt from a different template, a fusion weight or mapping changes, the metric implementation changes, a new holdout target is introduced, a source is rebuilt within folds, or anyone proposes clearing a submission slot.
