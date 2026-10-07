# H56 implementation and release review — three passes

Date: 2026-10-07 UTC. This records code, data/validation, and release/claim review separately; it is not an organizer review or approval.

## Pass 1 — code and mathematical correctness

- Reviewed `src/gemsdoe48/h56.py`: open-world BPA entries are nonnegative and sum to one; the normalized Dempster formula, denominator, and pre-normalization conflict `K` are explicit; the canonical residual `m(Theta)` excludes `K`; the primary normalization is max-relative, not probability calibration.
- Reviewed `scripts/build_submission_h56.py`: it SHA-checks the two family parents and footprint, verifies one-band float32/grid/counts, derives the metric-kernel support surfaces, emits separate Bel, m(Theta), K, plausibility, and direct support-disagreement diagnostics, and checks the mass-sum invariant before writing.
- Reviewed `scripts/build_h56_strain_ridge_probe.py` against the machine-readable frozen H56-A transform: bands 4/7/8; median-absolute log transform; Hessian responses at 3/6/9 px; per-channel/scale P99.5 scaling; 0.1 earthquake-density term; deterministic 37,654-cell budget. We found a mismatch: the original Markdown slate also mentions structure-tensor coherence, while the explicit machine `frozen_test` does not specify it. The original frozen files were preserved; the builder follows the machine test and omits coherence. A post-score erratum now limits the result to that Hessian-only screen; the coherence-augmented prose idea remains untested. No transform or threshold was tuned after seeing labels.
- Added tests for open-world ignorance, weak absence evidence, Dempster symmetry/conflict, invalid BPA rejection, max normalization, Hessian response, robust clipping, and deterministic ties. `tests/test_h56.py`: 8 passed.
- Initial build exposed a mistaken expected valid-cell count in the new builder. An independent mask audit found 5,164,312 cells in the footprint-and-stack-valid intersection, 3,061 feature nodata cells inside the footprint, and 1,540 stack-valid cells outside it. The script was corrected to use and record the measured intersection; candidate ranking never uses the outside-footprint cells. The probe was rebuilt and its SHA recorded.

## Pass 2 — data, novelty, and comparable validation

- Rechecked all H56-DS parent/footprint hashes against their pinned values. H56-A stack SHA-256 matches the stored third-party-mirror digest, but this is not organizer authentication or license clearance.
- Re-ran H49 with the same `scripts/run_spatial_holdout.py` executable, fold geometry, masks, truth sources, and scoring parameters used for H56. The comparisons are kept separate by proxy and are not called leaderboard scores.
- H56-DS vs H49: catalogue mean DTI 0.054242 vs 0.095353 (Δ −0.041111; 0/4 folds positive); SGMC off-catalogue mean 0.066070 vs 0.100751 (Δ −0.034681; 0/4). H56-A: 0.014282 vs 0.095353 (Δ −0.081071; 0/4); SGMC off-catalogue 0.006531 vs 0.100751 (Δ −0.094220; 0/4). Both fail; no slot is cleared.
- Reviewed H53 and H55 prior art before making novelty claims. H53 already has the exact B2 × H33-D two-family D-S diagnostic. The H56 mass assignment is distinct (`alpha=0.60`, `q=0.10` open-world absence vs H53's `alpha=0.50` simple-support assignment), but the evidence parents and concept are not new. Local uniqueness audit compared 85 prior same-grid, one-band rasters and found no SHA or pixelwise duplicate; H56 remains highly correlated with H53 D-S and its top-37,654 rank set is identical to both H53's two-family diagnostic and the arithmetic mean (Jaccard 1.0). The report explicitly limits the claim to a distinct parameterization/output.
- The primary differs numerically from the arithmetic mean (Pearson 0.99668; MAE 0.01126; max absolute difference 0.19650; 12.52% of footprint cells differ by >0.05), but is not described as a materially different ranking at the matched budget.
- The 0.2778 attribution is worded as owner-reported and algebraically consistent with catalogue-distance pruning, not as verified for local B2 bytes; local `UNSCORED` and missing organizer file-to-score receipt are stated.

## Pass 3 — file acceptance, site copy, and release safety

- Re-opened the H56 primary independently with `scripts/validate_submission.py --encoding zeros`: one-band float32, EPSG:32611, 100 m, 3,730 × 3,292, whole raster finite and in `[0,1]`, zero-outside, `nodata` unset; local format audit passes. This is not organizer portal acceptance. The official null/NaN-outside wording remains a visible caveat.
- Re-opened all five diagnostic rasters: all finite float32, same grid, within `[0,1]`, zero outside. Verified `primary=Bel/max(Bel)`, `Pl=Bel+m(Theta)`, and that `m(Theta)` is not a copy of raw `K`.
- Updated README, H56 report, index, executive summary, submission guide, method, hypotheses, validation, irregularities, sources, research index, and next steps. Current pages say “download yes, submit no”; the H55 walkthrough is labeled historical. Local links are checked by the test suite.
- A first full-suite run found two site-test issues: `docs/research.html` linked to this review file before it existed, and the legacy test expected H55 to remain the current first download. Added this review record and updated the assertion to select H56 as current while retaining H55 receipt tests. Final rerun after the documentation/provenance erratum: `.venv/bin/python -m pytest -q` passed in 25.5 s; three tests were skipped. `py_compile` also passed for all six H56 modules/scripts.
- The PR/merge step is still pending. No external submission, leaderboard claim, or weekly slot is authorized.

## Release conclusion

**H56 is a downloadable local research artifact, not an approved submission.** The only defensible current action is to preserve the negative result and proceed only with separately preregistered, provenance-reviewed work. No H56 candidate beats the current blocked best, and public proxies are not private-label evidence.
