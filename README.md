# GEMSDOE48 — auditable Dempster-Shafer fault-surface research

> **Decision: no weekly submission slot is cleared.** Under one consistent four-block/core-plus-halo evaluator, the `rho=0.5` candidate improves over dotted-only on the catalogue proxy but loses to tip/stepover, the arithmetic mean, and the prior full-union decision. On SGMC off-catalogue faults it loses to both parents, the mean, and the prior union in every block. The old main-branch report used different quadrant semantics; the prior union is rescored alongside the candidate below. No result is private-label or organizer score.

## Executive summary and downloads

GEMSDOE48 combines the public owner-mirror dotted and tip/step-over candidate families with reliability-discounted Dempster-Shafer mass assignments. It exports a graded belief raster plus separate residual-ignorance and raw-conflict diagnostics. A prior main-branch implementation also explored a full-confidence union decision surface; that historical result is retained and discussed below, not silently treated as a cleared submission.

- **Current research artifact:** `GEMSDOE48-DS-FUSION-20261006`
- **One-click candidate:** [`GEMSDOE48-DS-conflict-aware-fusion-20261006.tif`](docs/downloads/GEMSDOE48-DS-conflict-aware-fusion-20261006.tif)
- **Current diagnostics:** [`unassigned mass m(Theta)`](docs/downloads/GEMSDOE48-unassigned-mass-20261006.tif) · [`raw conflict K`](docs/downloads/GEMSDOE48-raw-conflict-K-20261006.tif)
- **Executive site:** [`docs/index.html`](docs/index.html)
- **Build receipt / SHA-256s:** [`evidence/build_receipt_20261006.json`](evidence/build_receipt_20261006.json)
- **Independent local format audit:** [`evidence/submission_validation_20261006.json`](evidence/submission_validation_20261006.json)
- **Catalogue + SGMC-proxy blocked diagnostics, with identical fold semantics:** [`evidence/holdout_20261006.json`](evidence/holdout_20261006.json)
- **Previous main-branch union artifact:** linked from the [historical result record](docs/validation.html); it is not the current candidate.

**Paste-ready note (129 characters):**

`GEMSDOE48 DS fusion | H33-2-B2 dotted + H33-D tip/step-over; rho=0.5; conflict/ignorance diagnostic; unscored research candidate.`

The current TIFF uses one `float32` band, EPSG:32611, 100 m pixels, the documented 3,730 × 3,292 grid, finite in-footprint values in `[0,1]`, and NaN/nodata outside the valid footprint. The output was re-opened and audited locally; organizer portal acceptance has not been tested. The earlier alpha=.99 decision file encodes zeros outside, which is all-finite but does not follow the challenge page's explicit null/NaN-outside wording as closely as this file.

## Starting prompt and project requirements

The starting brief is to autonomously build an auditable GEMS competition project; review the repository and prior work; combine the dotted-family and fault-tip/stepover surfaces with an evidence method that preserves disagreement; and generate a unique, downloadable competition-grid GeoTIFF plus separate uncertainty/disagreement diagnostics. Before any weekly submission, preregister three to five geological hypotheses with layers, physical signatures, off-catalogue rationale, differences from prior methods, ranked expected DTI/cost, verified free-data availability, and spatially blocked validation of the leading candidate. Include a project brief and repeat-use instructions, executive summary and one-click download, a unique name and paste-ready note, cited sources/limitations, at least three review passes, and a PR merged to `main` if feasible. Do not use a weekly submission slot unless a candidate beats the current spatially blocked best. Work autonomously, verify carefully, flag irregularities, and do not overstate uncertain evidence.

This is a faithful restatement of the requirements retained in this session, not a claim that the paragraph reproduces the original prompt word-for-word. The frozen H48 slate is in [`docs/research/hypotheses-20261006.md`](docs/research/hypotheses-20261006.md) and [`evidence/hypothesis_slate_20261006.json`](evidence/hypothesis_slate_20261006.json). The earlier main branch also contained a separate H49 agenda, preserved in [`docs/archive-main-pages/hypotheses-main-20261006.html`](docs/archive-main-pages/hypotheses-main-20261006.html); those candidates remain proposals, not validated results.

## Validation results and slot decision

### Current `rho=0.5` candidate (four fixed quadrants, catalogue-label proxy)

| Candidate | NW | NE | SW | SE | Mean DTI |
|---|---:|---:|---:|---:|---:|
| Dotted input | 0.006140 | 0.008567 | 0.007524 | 0.005091 | 0.006831 |
| Tip/stepover input | 0.082720 | 0.102030 | 0.089601 | 0.072930 | **0.086820** |
| Arithmetic mean | 0.0439999 | 0.054671 | 0.048245 | 0.038710 | 0.046406 |
| Discounted Dempster belief | 0.030871 | 0.038664 | 0.033773 | 0.027043 | 0.032588 |

The fusion improves on dotted-only (+0.025757 mean, 4/4 folds) but loses to tip/stepover (−0.054232, 0/4) and arithmetic mean (−0.013819, 0/4). It **fails the preregistered gate**.

### Second proxy: SGMC off-catalogue faults under the same blocked protocol

The SGMC owner-mirror raster supplies 61,664 positive cells after excluding SGMC cells within 300 m of a positive public-catalogue cell. The very same quadrants, 300 m score halo, core-only truth, metric, and frozen candidate surfaces are used for each method:

| Candidate | NW | NE | SW | SE | Mean DTI |
|---|---:|---:|---:|---:|---:|
| Dotted input | 0.101822 | 0.095184 | 0.107461 | 0.073546 | 0.094503 |
| Tip/stepover input | 0.101429 | 0.096184 | 0.106455 | 0.073898 | 0.094491 |
| Arithmetic mean | 0.096056 | 0.088763 | 0.097484 | 0.069061 | 0.087841 |
| Prior full-union decision | 0.102528 | 0.098529 | 0.106520 | 0.076252 | **0.095957** |
| `rho=0.5` discounted Dempster belief | 0.074815 | 0.067592 | 0.079382 | 0.052506 | 0.068574 |

The fusion's paired mean delta is −0.025929 vs dotted (0/4 positive), −0.025918 vs tip/stepover (0/4), −0.019267 vs arithmetic mean (0/4), and −0.027383 vs the prior union decision (0/4). This second conditional proxy also rejects the fusion for promotion. The SGMC surface is a public-map proxy, not private expert truth; the candidate source rasters remain frozen upstream products and were not independently reconstructed per fold.

See [`docs/research/holdout-results-20261006.md`](docs/research/holdout-results-20261006.md) for exact fold semantics, the full candidate set, and limitations.

### Previously merged `alpha=0.99` work (historical pooled experiment)

The previous main-branch experiment tested an `alpha=0.99` normalized DS belief and a binary full-union decision on SGMC faults more than 300 m from the catalogue. Its pooled tier sweep reported 0.096047 for the union/full-confidence tier versus 0.093965 dotted and 0.094245 tip; its normalized-belief gate is explicitly `PASS_offcat_blocked: false`. The earlier quadrant evaluator masked truth to one quadrant but retained full-grid predictions, so its fold scores are not comparable to the current core-plus-halo scores and must not be used as an independent holdout. This implementation rescored the same union decision, its normalized alpha=.99 belief, both parents, the arithmetic mean, and the rho=.5 candidate with identical current fold semantics. On SGMC off-catalogue truth, union mean DTI is 0.095957; the rho=.5 candidate is 0.068574 and loses to union in all four folds (mean paired delta −0.027383). The previous tier sweep and outputs remain preserved in [`evidence/round2_tier_sweep.json`](evidence/round2_tier_sweep.json), [`evidence/holdout_validation.json`](evidence/holdout_validation.json), and [`evidence/build_submission.json`](evidence/build_submission.json). No weekly slot is cleared.

### Interpretation limits

- The current holdout uses two public-map proxies: a third-party mirror of existing public catalogue labels and the SGMC raster filtered to cells more than 300 m from that catalogue. Neither is the private expert-labelled competition target.
- Both source families are frozen upstream artifacts and were not rebuilt independently per fold. The H33-2-B2 owner audit describes a full-catalogue proximity prune; spatial-block results are therefore conditional and potentially leaky.
- The owner mirrors are not organizer-authenticated and their reusable license terms have not been verified. Hash pinning establishes byte identity only; confirm rights before external submission or redistribution.
- No organizer score, hidden-test score, or projected leaderboard score is claimed.

## Leaderboard and attribution irregularities

The official page was read once on **2026-10-06 UTC**. It showed `xiaofanhu` at 0.3774 (#1), `alexoktaba` at 0.3345 (#2), `nchuzhoy` at 0.3262 (#3), and DARD at 0.3195 (#7)—not 0.3195 as the highest. The displayed 0.2778 row belonged to `extradr19` (#13, 10 submissions). The local H33-2-B2 receipt says “UNSCORED”; no organizer evidence links it to that 0.2778 row. The H33-D 0.2632 value is an owner-reported claim, not an authenticated file-level score. See [`docs/irregularities.md`](docs/irregularities.md). This branch disables the upstream six-hour feed and preserves it as `.github/workflows/feed.yml.disabled`; the retained parser cannot fetch the page.

## Method and assumptions

For source value `p_i`, the current preregistered symmetric discount is `rho=0.5`:

- `m_i(F) = rho * p_i`
- `m_i(not F) = rho * (1 - p_i)`
- `m_i(Theta) = 1 - rho`

The normalized Dempster result carries `m(F)`, `m(not F)`, and residual `m(Theta)`. Raw conjunctive conflict `K = m1(F)m2(not_F) + m1(not_F)m2(F)` is exported separately; it is conflict before normalization, not mass retained as ignorance by the canonical normalized rule. Positive agreement gives `m(F)=0.75`; one-source-only support gives `m(F)=1/3`, `m(Theta)=1/3`, `K=0.25`; negative agreement gives zero fault belief and 0.25 ignorance.

The previous main-branch model used alpha=.99 and max-normalized belief, then separately tested full-union emission. It is retained as prior work, not conflated with the `rho=.5` candidate. The two surfaces share 31,614 positive cells (Jaccard 0.659931); dependence is possible. Both are sparse binary emissions rather than calibrated probabilities, so treating zero as counter-evidence is an assumption. `rho=0.5` is fixed before holdout, not estimated reliability. Full formulas and diagnostics are in `src/gemsdoe48/evidence.py` and `scripts/build_submission.py`.

## Preregistered geological hypotheses

The ranked H48 list was frozen before this branch's implementation and scoring; expected DTI is qualitative/unknown where data do not support a number.

| Rank | Hypothesis | Expected DTI / cost | Data availability checked |
|---:|---|---|---|
| 1 | H48-1: conflict-aware fusion of existing candidate surfaces | Unknown; low cost | Two owner-mirror surfaces hash-verified; not organizer-authenticated |
| 2 | H48-2: stratigraphic contact topology plus magnetic/gravity breaks | Potentially moderate; medium-high cost | Official USGS GeMS/SGMC catalog metadata checked; payload/coverage not audited |
| 3 | H48-3: OPERA InSAR displacement-gradient discontinuities | Low-moderate potential; high cost | NASA catalog checked; Earthdata Login required; no granules downloaded |
| 4 | H48-4: hydrography channel-profile breaks plus 3DEP | Terrain-dependent; medium cost | Official USGS pages checked; footprint coverage unaudited |
| 5 | H48-5: geothermal favorability plus ensemble spread | Unknown; high cost | Official USGS release metadata checked; large package not downloaded; favorability is not fault truth |

The archived H49 agenda is in `docs/archive-main-pages/hypotheses-main-20261006.html`; it is prior art for this project, not a second preregistration for H48. Full source and limitation details are in [`docs/sources.md`](docs/sources.md).

## Reproduce

Requires Python 3.11+ and Rasterio-compatible GDAL wheels. The repository contains small, hash-pinned owner-mirror inputs under `data/raw/`; these are not organizer-authenticated. The build scripts verify the expected hashes.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'

python scripts/restore_candidate_surfaces.py  # hash-pinned public owner mirrors
python scripts/restore_proxy_labels.py        # public labels/template mirrors only
python scripts/build_footprint_mask.py        # template mask; compares label footprint
python -m pytest -q                           # unit tests, no hidden labels required
python scripts/build_submission.py             # rho=.5 candidate + diagnostics
python scripts/validate_submission.py --receipt evidence/submission_validation_20261006.json
python scripts/run_spatial_holdout.py          # catalogue + SGMC proxy blocks; no slot decision
```

The current rho=.5 builder remains `scripts/build_submission.py`. The earlier alpha=.99 builder snapshot is retained as `scripts/previous_build_submission.py`, and the exact builder from the merged main branch is preserved as `scripts/previous_main_build_submission.py`; neither is the default. Build and holdout receipts are dated and hash-pinned. Four review passes—including API compatibility and like-for-like SGMC re-evaluation after main advanced—are recorded in [`evidence/review_passes_20261006.md`](evidence/review_passes_20261006.md).

## Sources

- [Official challenge page: metric, labels, and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) (single read 2026-10-06 UTC; no monitor)
- [DrivenData Terms of Use](https://www.drivendata.org/termsofuse/)
- [USGS GeMS/SGMC DOI 10.5066/P1A3DQZK](https://doi.org/10.5066/P1A3DQZK)
- [NASA OPERA DISP-S1](https://www.earthdata.nasa.gov/data/catalog/asf-opera-l3-disp-s1-v1-1)
- [USGS NHD product access](https://www.usgs.gov/national-hydrography/access-national-hydrography-products) · [USGS 3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services)
- [USGS Great Basin favorability DOI 10.5066/P14EET2C](https://www.usgs.gov/data/geothermal-resource-favorability-select-features-and-predictions-united-states-great-basin)
- Third-party owner mirrors and file hashes: [`docs/sources.md`](docs/sources.md)
