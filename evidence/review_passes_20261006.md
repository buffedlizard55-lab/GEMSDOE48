# Independent review passes — 2026-10-06 UTC

Four review passes were completed across the original candidate and the later main-branch reconciliation. These are documented engineering reviews, not organizer sign-off.

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

- Reviewed main's newer alpha=.99/union work, retained its receipts, source assets, scripts, and older site pages in an archive with a warning. Kept the branch's rho=.5 builder as the default, retained an earlier historical builder snapshot, and copied the exact latest main builder to `scripts/previous_main_build_submission.py`.
- Preserved the upstream metric APIs in the combined metric module and added the exact current main metric tests as `tests/test_metric_main.py`; kept the previous metric and Yager tests in separate compatibility files. The complete suite now has 162 tests and passed after the reconciliation.
- Recomputed the prior alpha=.99 belief and binary union alongside dotted, tip, mean, and rho=.5 using the same four quadrants, held-out core, 300 m halo, and metric for both targets. SGMC off-catalogue truth is 61,664 raster cells, defined as SGMC positives more than 300 m from catalogue positives.
- On SGMC folds the rho=.5 fusion mean is 0.06857388, below dotted 0.09450317, tip 0.09449144, arithmetic mean 0.08784120, and prior union 0.09595726; it loses to each comparator in 0/4 folds. The historical pooled alpha=.99 tier sweep and its incompatible full-grid quadrant scores are not treated as the promotion gate.
- Updated current HTML/Markdown pages to remove stale slot-clear language; earlier pages are preserved in `docs/archive-main-pages/` and marked historical. Disabled the upstream six-hour leaderboard workflow (`.github/workflows/feed.yml.disabled`); its parser helper no longer has a network-fetch path. The stale root Markdown site builder is a no-op, and the DS48 sub-site builder inserts an explicit retirement banner. No weekly slot was used and no private-label or organizer score is claimed.
- After the workflow/page retirement and link repairs, reran `compileall` and all 162 tests successfully; a local-link audit found zero missing links across 41 HTML pages. Direct execution of the retired site builder is a no-op, and the parser exits with its disabled notice without making a request.

**Artifacts:** `evidence/holdout_20261006.json`, `docs/research/holdout-results-20261006.md`, `docs/validation.html`, `docs/archive-main-pages/`, `scripts/previous_main_build_submission.py`, `tests/test_metric_main.py`.

## Re-review triggers

Repeat the affected reviews if an input or label hash changes, an official rule changes, the footprint is rebuilt from a different template, a fusion weight or mapping changes, the metric implementation changes, a new holdout target is introduced, a source is rebuilt within folds, or anyone proposes clearing a submission slot.
