# GEMSDOE48 — auditable fault-surface research (H48 → H49 → H53)

> **Decision (2026-10-07, H53 session — latest): no weekly submission slot is cleared.** The unique local research TIFF **H53-A** (C + 12,000 strike-coherent 3DEP scarp dots) passes the local format audit and bounded local uniqueness scan, but fails the preregistered spatial gate: newer SGMC proxy 0.098110 vs H49 0.100751 (−0.002641; 1/4 folds higher), older raw-SGMC sensitivity 0.097086 vs H49 0.099768 (−0.002682; 1/4 folds higher). No slot was used, no organizer score exists, and the public proxy is not private-label validation. See [`docs/research/holdout-h53-results-20261007.md`](docs/research/holdout-h53-results-20261007.md).

> **Earlier decisions (unchanged):** no weekly submission slot is cleared. The H48 `rho=0.5` candidate loses to the prior union on the shared SGMC blocked diagnostic (0.069261 vs 0.096992). The newer-main H49 balanced emission now scores 0.100751 vs that 0.096992 prior-union baseline (+0.003760, 4/4 folds) on the same protocol, and the direction repeats on the separate older SGMC raster. This is a post-selection re-score on related public proxy evidence, below the live instrument's roughly 0.005 resolution, and its live-anchored change bracket is −0.010 to +0.005. A format-only NaN-outside H49 copy passes local checks; organizer acceptance remains untested. No private-label or organizer score exists, so H49 is not slot-cleared.
>
> **2026-10-07 (later session) update:** the merged H50 artifact was re-audited line by line and every checked number reproduced exactly. Two new unique constructions were preregistered and tested on the same blocked holdout: **H51** (binary plausibility-budget emission of the H50 fusion; SGMC proxy 0.086537, catalogue 0.007589 — gate not cleared) and **H50-B** (GeoDAWN low-Th/K alteration anomalies inside H50 conflict corridors, using the DOI 10.5066/P93LGLVQ mirror restored byte-identical from the GEMSDOE24 repo; 0.019135 / 0.015312 — a recorded negative result). Both are downloadable, honestly labelled research candidates; neither is recommended for upload. The session's consolidated finding: **no fusion of the two best existing surfaces beats the better parent on the proxies — raising the live score requires higher credit density (new signal), not better combination.** See [`docs/research/h51-h50b-results-20261007.md`](docs/research/h51-h50b-results-20261007.md). *Note: the H50/H50-B/H51 labels belong to those concurrent sessions; the subsequent H52 and current H53 work are separately labelled to avoid collisions.*

## ⬇ This session's unique research TIFF (H53-A, 2026-10-07; not slot-cleared)

- **Download:** [`docs/downloads/GEMSDOE48-H53-STRIKE-COHERENCE-20261007-de35531d3867-nan-outside.tif`](docs/downloads/GEMSDOE48-H53-STRIKE-COHERENCE-20261007-de35531d3867-nan-outside.tif) (403,844 bytes, SHA-256 `de35531d386792da1950eac815f98db8f36304f78debb6b568138d070640d9bd`) — one-band float32, EPSG:32611, 100 m, 3,730 × 3,292; finite {0,1} in-footprint, NaN/nodata outside; 49,654 positives. [Format receipt](evidence/h53_submission_validation_20261007.json) passes locally; [bounded uniqueness receipt](evidence/h53_submission_identity_20261007.json) finds no exact match in 54 comparable local rasters. Neither check establishes organizer acceptance or global uniqueness.
- **Paste-ready note (133 characters):** `GEMSDOE48-H53 | C + 12k Poisson dots ranked by 500m strike-coherent 3DEP scarp support; proxy-tested research only; NOT slot-cleared.`
- **Method:** retain the 37,654 C dotted-family cells; add 12,000 Poisson-spaced candidates ranked by ≥4/5 strike-compatible scarp cells within an approximately 400–565 m 100 m-grid window. The derived 3DEP product and all construction thresholds were hash-pinned in the frozen [H53 slate](docs/research/hypotheses-h53-20261007.md). This uses stored 100 m strike summaries, not a new native 3 m line-trace run.
- **Blocked result:** newer SGMC off-catalogue DTI 0.098110 vs H49 0.100751 (−0.002641; 1/4 folds higher); older raw-SGMC sensitivity 0.097086 vs H49 0.099768 (−0.002682; 1/4 folds higher). H53 beats the prior union, but fails the preregistered gate against H49 on both proxies. **Do not upload or spend a weekly slot.** Full report: [`docs/research/holdout-h53-results-20261007.md`](docs/research/holdout-h53-results-20261007.md); paired receipt: [`evidence/h53_vs_h49_20261007.json`](evidence/h53_vs_h49_20261007.json); three-pass review: [`evidence/review_passes_h53_20261007.md`](evidence/review_passes_h53_20261007.md).
- **Why 0.2778 and what >0.3195 requires:** the prior live ladder indicates C's gain came from pruning known-catalogue-adjacent dots under the score's mask, not from adding confirmed geology. The current owner-read leaderboard snapshot records 0.3774 at #1 and 0.3195 at #7; neither value is attributable to a local TIFF here. See [`docs/research/why-02778-and-ceiling-20261007.md`](docs/research/why-02778-and-ceiling-20261007.md) and [leaderboard irregularities](docs/irregularities.md).
- **Required Dempster-Shafer deliverable is also retained:** H50 combines dotted H33-2-B2 × tip H36-1 on kernel-credit belief surfaces, keeps `m(Theta)` and raw conflict `K` as diagnostics, and explicitly checks it is not the naive mean. Download the NaN-outside belief TIFF [`here`](docs/downloads/gemsdoe48-h50-ds-b2xh36rung30-20261007-5b59e106-nan.tif), the separate [`m(Theta)` diagnostic](docs/downloads/diagnostics/gemsdoe48-h50-unassigned-mTheta-20261007-5b59e106.tif), and [`raw conflict K`](docs/downloads/diagnostics/gemsdoe48-h50-conflict-K-20261007-5b59e106.tif). H50 also failed the spatial gate and is not for upload; see [`docs/research/h50-method-20261007.md`](docs/research/h50-method-20261007.md).

## Previous unique research TIFF (H52, 2026-10-07; not slot-cleared)

- **Download:** [`docs/downloads/GEMSDOE48-H52-lidar-scarp-additions-20261007-38029417f6ca-nan-outside.tif`](docs/downloads/GEMSDOE48-H52-lidar-scarp-additions-20261007-38029417f6ca-nan-outside.tif) (346,152 bytes, SHA-256 `38029417f6cab01f9f56d4d3259a998affad6ae45a2a21a394682ee38b98e0c7`; [zeros-outside twin](docs/downloads/GEMSDOE48-H52-lidar-scarp-additions-20261007-38029417f6ca-zeros-outside.tif)) — one float32 band, EPSG:32611, 100 m, 3,730 × 3,292, {0,1} in-footprint, NaN outside, 39,654 positives. Byte- and pixel-distinct from every prior GEMSDOE artifact here ([identity receipt](evidence/h52_submission_identity_20261007.json)); [local format validation](evidence/h52_submission_validation_20261007.json) passes.
- **Paste-ready note (143 characters):** `GEMSDOE48-H52 | 0.2778 dotted family + 2,000 lidar-scarp dots (3 m USGS 3DEP step detector, >200 m off-catalogue); unscored research candidate.`
- **What it is:** the 0.2778 dotted family C (37,654 dots, untouched) plus 2,000 Poisson-spaced dots on the strongest line-persistent steps (effective height ≥ 3.29 m inside smooth terrain) found by `src/gemsdoe48/scarp3m.py` on all 700 zone-11 USGS 3DEP 1 m tiles, block-averaged to 3 m in GitHub Actions ([extract run](https://github.com/buffedlizard55-lab/GEMSDOE48/actions/runs/37561683197), [mosaic run](https://github.com/buffedlizard55-lab/GEMSDOE48/actions/runs/37565284104)); additions are > 200 m from the public catalogue and from any C dot. Builder: `scripts/build_submission_h52.py`.
- **Status: not slot-cleared.** Pre-registered gate ([slate §4](docs/research/hypotheses-h52-20261007.md)) fails on both criteria: it does not beat H49 on the proxy, and the detector's label-free catalogue lift is 1.19× / 2.27× / 1.53× / 1.63× by quadrant (pilot tiles: 2.3–3.2×) against a ≥ 2× rule. Random additions in the same footprint give −0.000155 at 2,000 and +0.000484 at 12,000 (control). Full sweep, controls and the pilot-vs-region discrepancy: [H52 report](docs/research/holdout-h52-results-20261007.md).

### What this session established (details in `docs/research/`)

1. **The live ladder is bookkeeping, not geology.** A (44,090 dots, 0.2600) → B (40,199, 0.2708) → C (37,654, 0.2778) is reproduced exactly by removing catalogue-adjacent dots that the organizer masks from scoring; both steps give the same hidden-mass estimate within 7.5 %. C recovers ≈ 37 % of the hidden kernel mass; 0.3195 needs ≈ 42 %, 0.3774 ≈ 50 % at the same mass. A dot is worth adding only if its expected kernel weight exceeds 0.2·DTI ≈ 0.056 ([why-0.2778 note](docs/research/why-02778-and-ceiling-20261007.md), [`evidence/live_ladder_20261007.json`](evidence/live_ladder_20261007.json)).
2. **No 100 m layer can re-rank C's dots profitably.** Best non-circular per-dot lift 1.43× (U/K), bar ≈ 2.6×; the 2 m u8 lidar descriptors are negative (≤ 0.91×); official band 6 `tc` is radiometric total count, not a magnetic derivative (irregularity logged).
3. **Native 3 m lidar is obtainable and processable for free** (two-tile pilot + 700-tile region run, ≈ 1 h wall clock on hosted runners; sandbox cannot reach USGS or artifact hosts, so compact products are committed back). The v1 detector's region-wide value on bedrock-fault proxies is its *terrain class* (random dots in the 0.7–2.5 m roughness band: +0.009 on the proxy, beating H49 by +0.0038 — a post-hoc control, not promoted), not its step height. The v2 detector is the top next step ([next steps](docs/next-steps.html)).

## Historical H50-GDR probe — failed gate; research archive

H50-GDR is a separate, single-source repeat-persistence experiment from the earlier probe session. It is **not** the current H52 lidar candidate or the later H50 Dempster-Shafer fusion. Its corrected v2 file is retained for reproducibility, but it failed the frozen spatial gate; **do not upload it or spend a weekly slot**.

- **Download:** [`GEMSDOE48-H50-2M-PERSIST-20261007-F12E5391BB9C-NAN`](docs/downloads/GEMSDOE48-H50-2M-PERSIST-20261007-f12e5391bb9c-nan.tif) · 225,114 bytes · SHA-256 `f12e5391bb9cd2709ae7331699bb0876cc4bf3c443f96ea8a5456c858eb67908`.
- **Result:** primary proxy mean 0.003923 vs H49 0.100751 (paired −0.096828; 0/4 folds positive); older-raster sensitivity −0.095837, 0/4 positive. V2 corrected exact-location/date aggregation after v1 scores were observed, so this is a post-selection implementation sensitivity—not confirmatory validation.
- **Checks:** local format audit passes; the refreshed bounded audit found no exact prediction/support match among 47 comparable local same-grid rasters. The closest is superseded v1 (support Jaccard 0.998179). This is not global or organizer-side uniqueness or acceptance.
- **Prior art:** main's H50-C slate already proposed a related INGENIOUS 2 m probe residual along family corridors. H50-GDR uses a different operator but does not establish concept-level thermal novelty. The original local `H50-1` identifier also collides with the main slate's splay ID; user-facing references use H50-GDR.
- **Review:** [H50-GDR research slate](docs/research/h50-gdr-probe-slate-20261007.md) · [prior-art/identifier erratum](evidence/h50_gdr_prior_art_errata_20261007.json) · [local format receipt](evidence/h50_probe_format_validation_20261007.json) · [bounded uniqueness receipt](evidence/h50_probe_uniqueness_20261007.json) · [proxy comparison](evidence/h50_probe_v2_exact_location_vs_h49_20261007.json) · [historical how-to and no-upload note](docs/submission-guide.html) · [review-pass log](evidence/review_passes_20261007.md).

Rebuild the historical H50-GDR TIFF into a scratch directory (the command does not overwrite the published download):

```bash
python scripts/build_h50_probe_candidate.py \
  --output-dir /tmp/h50-gdr-rebuild \
  --receipt /tmp/h50-gdr-build-receipt.json \
  --station-audit /tmp/h50-gdr-stations.csv \
  --require-pinned-mirror-sha
```

## Executive summary and downloads (H48/H49, unchanged)

GEMSDOE48 combines the public owner-mirror dotted and tip/step-over candidate families with reliability-discounted Dempster-Shafer mass assignments. It exports a graded belief raster plus separate residual-ignorance and raw-conflict diagnostics. A prior main-branch implementation also explored a full-confidence union decision surface; that historical result is retained and discussed below, not silently treated as a cleared submission.

- **H48 `rho=.5` research artifact (fails the spatial promotion gate):** `GEMSDOE48-DS-FUSION-20261006` · [`GeoTIFF`](docs/downloads/GEMSDOE48-DS-conflict-aware-fusion-20261006.tif)
- **Latest-main H49 proxy-best, still not slot-cleared:** `GEMSDOE48-H49-DS-CB-e6f08013888b-NAN` · [`NaN-outside format-audited GeoTIFF`](docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif) · [`H49 same-protocol report`](docs/research/holdout-h49-results-20261006.md)
- **H51 plausibility-budget emission (gate not cleared):** `GEMSDOE48-H51-PLAUSIBILITY-BUDGET` · [`zeros-outside GeoTIFF`](docs/downloads/gemsdoe48-h51-plausibility-budget-20261007-f8fa1d08-zeros.tif) · [`zip`](docs/downloads/gemsdoe48-h51-plausibility-budget-20261007-f8fa1d08-zeros.zip) · [`NaN-outside twin`](docs/downloads/gemsdoe48-h51-plausibility-budget-20261007-f8fa1d08-nan.tif) · [`build receipt`](evidence/build_h51_receipt_20261007.json) · [`blocked holdout`](evidence/holdout_h51_20261007.json)
- **H50-B alteration-conflict probe (negative result):** `GEMSDOE48-H50B-ALTERATION-CONFLICT` · [`zeros-outside GeoTIFF`](docs/downloads/gemsdoe48-h50b-alteration-conflict-20261007-806a4ba4-zeros.tif) · [`preregistration`](evidence/h50b_preregistration_20261007.json) · [`blocked holdout`](evidence/holdout_h50b_20261007.json) · [`restored GeoDAWN radiometric mirror`](data/source_mirrors/geodawn_rad_u8.tif) (SHA-256 `c22420f7…`, official DOI 10.5066/P93LGLVQ)
- **Session results (H51 + H50-B + H50 re-audit):** [`docs/research/h51-h50b-results-20261007.md`](docs/research/h51-h50b-results-20261007.md)
- **H48 diagnostics:** [`unassigned mass m(Theta)`](docs/downloads/GEMSDOE48-unassigned-mass-20261006.tif) · [`raw conflict K`](docs/downloads/GEMSDOE48-raw-conflict-K-20261006.tif)
- **H49 audit/format receipts:** [`upstream H49 audit`](docs/downloads/gemsdoe48-h49-ds-conflict-balanced-20261006-audit.json) · [`format conversion`](evidence/h49_format_audit_20261006.json) · [`independent local format validation`](evidence/h49_submission_validation_20261006.json)
- **Executive site:** [`docs/index.html`](docs/index.html)
- **Build receipt / SHA-256s:** [`evidence/build_receipt_20261006.json`](evidence/build_receipt_20261006.json)
- **Independent local format audit:** [`evidence/submission_validation_20261006.json`](evidence/submission_validation_20261006.json)
- **Catalogue + newer-derived SGMC blocked diagnostics:** [`evidence/holdout_20261006.json`](evidence/holdout_20261006.json)
- **Prior raw-SGMC sensitivity and input discrepancy audit:** [`evidence/holdout_raw_sgmc_20261006.json`](evidence/holdout_raw_sgmc_20261006.json) · [`evidence/sgmc_raster_comparison_20261006.json`](evidence/sgmc_raster_comparison_20261006.json)
- **Previous main-branch union artifact:** linked from the [historical result record](docs/validation.html); it is not the current candidate.

**Paste-ready note (129 characters):**

`GEMSDOE48 DS fusion | H33-2-B2 dotted + H33-D tip/step-over; rho=0.5; conflict/ignorance diagnostic; unscored research candidate.`

The H48 Dempster TIFF uses one `float32` band, EPSG:32611, 100 m pixels, the documented 3,730 × 3,292 grid, finite in-footprint values in `[0,1]`, and NaN/nodata outside. Its output was re-opened and audited locally; organizer portal acceptance has not been tested. The original H49 file stored zeros outside; [`prepare_h49_format_copy.py`](scripts/prepare_h49_format_copy.py) creates a separate H49 derivative with NaN/nodata outside while preserving every in-footprint value exactly. Its independent local format audit also passes, but organizer portal acceptance is untested. The earlier alpha=.99 decision file likewise encodes zeros outside and is not the format-preferred artifact.

## 2026-10-07 concurrent session — H50 Dempster-Shafer fusion (research-only; slot gate failed)

- **Deliverable:** `docs/downloads/gemsdoe48-h50-ds-b2xh36rung30-20261007-5b59e106-zeros.tif`
  (unique name `GEMSDOE48-H50-DS-B2xH36`, with a `.zip` twin), built by
  `scripts/build_ds50_submission.py`; receipt `evidence/build_ds50_receipt_20261007.json`.
- **Parents:** dotted H33-2-B2 (37,654 px, owner-reported 0.2778; organizer has not linked it to these local bytes) × tip H36-1 rung30 (37,660 px, reported sibling value 0.2710) — first-ever fusion of this pair. Belief surfaces are the metric-geometry
  kernel-credit fields; discounts are the preregistered RHO_MAX=0.95 ceiling × the live-score
  ratio (a v1 build with a perfect-reliability anchor was withdrawn because it forced the
  unassigned-mass diagnostic to zero).
- **Required checks (all pass):** normalized Bel(F) in [0,1], all-finite; not the naive mean
  (Pearson 0.9749, Spearman 0.99996, max |Δ| 0.2648, top-37,654 emission Jaccard 0.9687);
  zero SHA-256 collisions against 44 existing grid rasters; m(Θ) and raw K shipped as separate
  disagreement diagnostics.
- **Honest blocked-holdout result:** `evidence/holdout_ds50_20261007.json` — H50 beats the naive
  mean 4/4 folds on the SGMC off-catalogue proxy and improves on the raw-sparse DS recipe with
  the same parents, but loses to both parents and the union on both proxies. **The slot gate is
  not cleared; do not upload H50 or spend a weekly slot.** The runbook in
  `docs/h50/executive-summary.html` is future-use reference only, not authorization.
- **Top hypothesis validated with no new data:** the coarse 100–600 m splay band fails its
  blocked test (`evidence/splay_probe_holdout_20261007.json`); the fresh preregistered slate is
  `docs/research/hypotheses-20261007.md`.
- **Site:** `docs/h50/` sub-site generated by `scripts/build_site_h50.py`; the landing page
  `docs/index.html` puts the one-click download at the very top.
- **Leaderboard irregularity:** the brief's "0.3195 is the highest score" is stale; the official
  page (single manual read 2026-10-07) shows xiaofanhu #1 at 0.3774 and 0.3195 at #7 (DARD).
  Snapshot: `docs/data/leaderboard_20261007.json`.

## Starting prompt and project requirements

The starting brief is to autonomously build an auditable GEMS competition project; review the repository and prior work; combine the dotted-family and fault-tip/stepover surfaces with an evidence method that preserves disagreement; and generate a unique, downloadable competition-grid GeoTIFF plus separate uncertainty/disagreement diagnostics. Before any weekly submission, preregister three to five geological hypotheses with layers, physical signatures, off-catalogue rationale, differences from prior methods, ranked expected DTI/cost, verified free-data availability, and spatially blocked validation of the leading candidate. Include a project brief and repeat-use instructions, executive summary and one-click download, a unique name and paste-ready note, cited sources/limitations, at least three review passes, and a PR merged to `main` if feasible. Do not use a weekly submission slot unless a candidate beats the current spatially blocked best. Work autonomously, verify carefully, flag irregularities, and do not overstate uncertain evidence.

The original owner brief is reproduced verbatim in the final section below; this paragraph distills its acceptance requirements. The frozen H48 slate is in [`docs/research/hypotheses-20261006.md`](docs/research/hypotheses-20261006.md) and [`evidence/hypothesis_slate_20261006.json`](evidence/hypothesis_slate_20261006.json). The separate mainline H49 program is retained under [`docs/h49/`](docs/h49/) with source receipts and a same-protocol H48-style re-score in [`docs/research/holdout-h49-results-20261006.md`](docs/research/holdout-h49-results-20261006.md). Its proxy gain is not an independent blind holdout or a slot clearance.

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

The newer pinned SGMC-derived raster supplies 62,122 positive cells after excluding SGMC cells within 300 m of a positive public-catalogue cell. The very same quadrants, 300 m score halo, core-only truth, metric, and frozen candidate surfaces are used for each method:

| Candidate | NW | NE | SW | SE | Mean DTI |
|---|---:|---:|---:|---:|---:|
| Dotted input | 0.101822 | 0.099125 | 0.107461 | 0.073557 | 0.095491 |
| Tip/stepover input | 0.101429 | 0.100172 | 0.106455 | 0.073908 | 0.095491 |
| Arithmetic mean | 0.096056 | 0.092405 | 0.097484 | 0.069072 | 0.088755 |
| Prior full-union decision | 0.102528 | 0.102656 | 0.106520 | 0.076262 | **0.096992** |
| Historical Yager conflict-transfer alternative | 0.091474 | 0.085028 | 0.091131 | 0.063932 | 0.082891 |
| `rho=0.5` discounted Dempster belief | 0.074815 | 0.070333 | 0.079382 | 0.052515 | 0.069261 |

The fusion's paired mean delta is −0.026230 vs dotted (0/4 positive), −0.026230 vs tip/stepover (0/4), −0.019493 vs arithmetic mean (0/4), and −0.027730 vs the prior union decision (0/4). The Yager alternative improves over this Dempster fusion by +0.013630 (4/4), but loses to dotted (−0.012600), tip/stepover (−0.012600), arithmetic mean (−0.005863), and prior union (−0.014100), each 0/4. Neither fusion clears a slot gate. The SGMC surface is a public-map proxy, not private expert truth; the candidate source rasters remain frozen upstream products and were not independently reconstructed per fold.

### Latest-main H49 candidate: re-scored, higher proxy result, still no slot

Main added a distinct Yager conflict-transfer / pignistic-ranked / fixed-budget candidate with 47,905 cells. Its original TIFF is [`docs/downloads/gemsdoe48-h49-ds-conflict-balanced-20261006-e6f08013888b.tif`](docs/downloads/gemsdoe48-h49-ds-conflict-balanced-20261006-e6f08013888b.tif) (SHA-256 `e6f08013888b625db7d187d79bb75ba36c45d068081b77a3dd405ab7eec3d472`). The original uses finite zero outside the footprint. A format-only derivative, [`GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif`](docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif), changes only outside pixels to NaN/nodata (SHA-256 `9f028289c364c071065245799d7ed131600e80e9f0d10602806b12ce34d7cae8`) and passes [`scripts/validate_submission.py`](scripts/validate_submission.py) locally; organizer acceptance is not tested. Its unique label is `GEMSDOE48-H49-DS-CB-e6f08013888b-NAN`.

The H49 file was scored with the exact current four-quadrant/core-plus-300 m-halo evaluator, the same masks and >300 m off-catalogue rule, and the same official DTI parameters. On the newer SGMC derivative it reaches 0.100751188 versus 0.096991657 for the prior union best (paired +0.003759531, 4/4 folds); on the separate older raw raster it reaches 0.099768355 versus 0.095957265 (+0.003811091, 4/4). It also beats the two parents and arithmetic mean in these reported folds. See [`docs/research/holdout-h49-results-20261006.md`](docs/research/holdout-h49-results-20261006.md), the [newer-raster JSON](evidence/holdout_h49_spatial_comparison_20261006.json), and the separate [raw-raster sensitivity JSON](evidence/holdout_h49_raw_sgmc_sensitivity_20261006.json).

This is not a fresh blind holdout: H49 was developed and compared using related SGMC public-proxy evidence, and the frozen upstream source rasters were not rebuilt independently within folds. Its +0.00376 gain over the former blocked best is below the roughly 0.005 resolution discussed by the live-anchored instrument, whose H49 change bracket is −0.010 to +0.005. **It beats the prior best numerically on these proxy folds, but remains not slot-cleared.** Do not submit on this result alone.

### 2026-10-07 (later session): H51 plausibility-budget emission and H50-B alteration probe — both gate-failed

Two new unique constructions were preregistered (constants frozen before any scoring) and evaluated with the identical folds/domain/metric. Mean DTI on the same proxies:

| Candidate | Catalogue proxy | SGMC off-catalogue proxy |
|---|---:|---:|
| dotted H33-2-B2 (parent) | 0.006831 | 0.095491 |
| tip H36-1 (parent) | 0.047560 | 0.093315 |
| union decision (49,066 px) | 0.046889 | 0.097037 |
| H50 graded belief | 0.030323 | 0.071553 |
| H50 binary Bel-top-37,654 | 0.007604 | 0.087161 |
| **H51 binary Pl-top-37,654** | 0.007589 | 0.086537 |
| **H50-B alteration-conflict 37,654** | 0.015312 | 0.019135 |
| H49 Yager/pignistic 47,905 px | **0.095353** | **0.100751** |

H51 keeps the H50 fusion exactly and emits binary on the top-budget cells ranked by plausibility Pl(F) = Bel(F) + m(Θ) — the optimistic Dempster–Shafer decision bound. Its 37,654 cells all lie inside the parents' union (it is a budget-trimmed union), it is not the naive mean (Pearson 0.9754 vs 0.5·(b1+b2)), and it fails the preregistered gate (must beat H49 on SGMC and the union on catalogue in ≥3/4 folds each). H50-B crosses the restored GeoDAWN radiometric mirror (official USGS DOI 10.5066/P93LGLVQ; SHA-verified byte-identical from the GEMSDOE24 repo) with the H50 conflict corridors: a clear negative result, consistent with the mirror's own "lithology/alteration proxy, not a fault detector" caveat. Consolidated reading: three decision rules on the same two best families span 0.0076–0.0872 on SGMC while the better parent alone reaches 0.0955 — **no fusion of these surfaces beats the better parent; higher live scores need higher credit density (new signal), not new combinations.** Full report: [`docs/research/h51-h50b-results-20261007.md`](docs/research/h51-h50b-results-20261007.md). Receipts: [`evidence/build_h51_receipt_20261007.json`](evidence/build_h51_receipt_20261007.json), [`evidence/holdout_h51_20261007.json`](evidence/holdout_h51_20261007.json), [`evidence/h50b_preregistration_20261007.json`](evidence/h50b_preregistration_20261007.json), [`evidence/holdout_h50b_20261007.json`](evidence/holdout_h50b_20261007.json). No slot is cleared.

### SGMC raster discrepancy and prior-raster sensitivity

The newer primary derivative is `data/official/derived_sgmc_faults_100m.tif` (SHA-256 `643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0`, 83,593 positive cells). The prior raw mirror `data/raw/sgmc_faults_100m.tif` (SHA-256 `26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c`, 82,151 positive cells) shares the spatial grid but differs in nodata metadata and 1,450 positive-mask cells (1,446 newer-only; 4 older-only). The source/derivation discrepancy is unresolved; both are public owner mirrors, neither organizer-authenticated. The full comparison is in [`evidence/sgmc_raster_comparison_20261006.json`](evidence/sgmc_raster_comparison_20261006.json).

The older raster was evaluated separately with the same blocked-fold protocol and >300 m rule. Means were dotted 0.094503, tip/stepover 0.094491, arithmetic mean 0.087841, prior union 0.095957, Yager 0.082061, and rho=.5 Dempster 0.068574. The candidate still loses to its parents, mean, and prior union. See [`evidence/holdout_raw_sgmc_20261006.json`](evidence/holdout_raw_sgmc_20261006.json); do not pool the two raster reports.

See [`docs/research/holdout-results-20261006.md`](docs/research/holdout-results-20261006.md) for exact fold semantics, the full candidate set, and limitations.

### Previously merged `alpha=0.99` work (historical pooled experiment)

The previous main-branch experiment tested an `alpha=0.99` normalized DS belief and a binary full-union decision on SGMC faults more than 300 m from the catalogue. Its pooled tier sweep reported 0.096047 for the union/full-confidence tier versus 0.093965 dotted and 0.094245 tip; its normalized-belief gate is explicitly `PASS_offcat_blocked: false`. The earlier quadrant evaluator masked truth to one quadrant but retained full-grid predictions, so its fold scores are not comparable to the current core-plus-halo scores and must not be used as an independent holdout. This implementation rescored the same union decision, its normalized alpha=.99 belief, both parents, the arithmetic mean, and the rho=.5 candidate with identical current fold semantics. On the newer manifest-pinned SGMC derivative, union mean DTI is 0.096992; rho=.5 is 0.069261 and loses to union in all four folds (mean paired delta −0.027730). On the prior raw-raster sensitivity, union is 0.095957 and rho=.5 is 0.068574; these are kept in a separate report. The previous tier sweep and outputs remain preserved in [`evidence/round2_tier_sweep.json`](evidence/round2_tier_sweep.json), [`evidence/holdout_validation.json`](evidence/holdout_validation.json), and [`evidence/build_submission.json`](evidence/build_submission.json). No weekly slot is cleared.

### Separate historical Yager-rule candidate from PR #5

Main also produced a distinct Yager-rule candidate using reliability discounts 0.90 (dotted) and 0.85 (tip), transferring conjunctive conflict to unassigned mass and min-max normalizing the fault-belief layer. Its TIFF (`gemsdoe48-h48-ds-yager-conflict-20261006.tif`, SHA-256 `fe68ae6f57be013e26d20006551b43cd84bb5fe4a0b07d1d10ce4725c90fd16c`) is preserved with its audit and diagnostics, but is not the current deliverable. The audit explicitly records `official_null_or_nan_outside_requirement_met: false`: the raster is all-finite with zeros outside the footprint, so it does not meet the published null/NaN-outside wording and has no confirmed portal acceptance.

The PR #5 `docs/data/proxy-validation.json` used a different SGMC evaluator: it counted 63,121 cells at distance **at least** 300 m, excluded known catalogue pixels, and scored full-scene quadrant predictions. Under that specific protocol, Yager fusion scored 0.084070, versus dotted 0.096132, tip 0.097094, and arithmetic mean 0.090303; it lost to all three and failed its proxy gate. Those figures are not comparable to this README's 62,122-cell **greater than** 300 m, core-plus-halo results on the newer derivative. The Yager output has also been rescored with the current identical folds and masks; see the added candidate and paired deltas in [`evidence/holdout_20261006.json`](evidence/holdout_20261006.json). Both Yager evaluations are public-proxy diagnostics, not private-label evidence or a slot clearance. The prior PR #5 pages and README snapshot are preserved under [`docs/archive-main-pages/pr5/`](docs/archive-main-pages/pr5/).

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

The original H49 agenda is preserved in `docs/archive-main-pages/hypotheses-main-20261006.html`; the separate mainline H49 implementation and its receipts remain under `docs/h49/`. H49 is not a second preregistration for H48. Its post-selection re-score and the no-slot decision are documented in [`docs/research/holdout-h49-results-20261006.md`](docs/research/holdout-h49-results-20261006.md). Full source and limitation details are in [`docs/sources.md`](docs/sources.md).

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
python scripts/build_submission.py             # H48 rho=.5 candidate + diagnostics
python scripts/validate_submission.py --receipt evidence/submission_validation_20261006.json
python scripts/run_spatial_holdout.py --yager docs/downloads/gemsdoe48-h48-ds-yager-conflict-20261006.tif  # H48 pinned SGMC derivative by default
python scripts/prepare_h49_format_copy.py       # H49 format-only NaN-outside derivative
python scripts/validate_submission.py docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif --receipt evidence/h49_submission_validation_20261006.json
python scripts/run_spatial_holdout.py --combined docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif --candidate-name h49_yager_balanced --output evidence/holdout_h49_spatial_comparison_20261006.json
python scripts/run_spatial_holdout.py --combined docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif --candidate-name h49_yager_balanced --sgmc data/raw/sgmc_faults_100m.tif --allow-unpinned-sgmc --output evidence/holdout_h49_raw_sgmc_sensitivity_20261006.json

# --- H52 session (2026-10-07) ---
python scripts/live_ladder_analysis.py                       # exact inversion of the live ladder -> evidence/live_ladder_20261007.json
python scripts/pilot_scarp_eval.py                           # 3 m detector on the two committed pilot tiles (data/pilot/dem3m/)
# region product: push a commit starting with "[run-scarp]" touching .github/workflows/dem-region-scarp.yml (hosted runners; ~1 h);
# the mosaic is committed back as data/external/h52_scarp3m_100m.tif (+ .json receipt). Merge-only re-run: "[run-merge]" + registry/scarp_merge_source_run.txt
python scripts/h52_region_checks.py                          # label-free quadrant checks -> evidence/h52_region_detector_checks_20261007.json
python scripts/build_submission_h52.py --n-add 500,1000,2000,3000,4000,6000,8000,12000   # sweep -> evidence/h52_candidate_sweep_20261007.json, scratch/h52/*.tif
python scripts/build_submission_h52.py --control random --tag ctrl --n-add 2000,4000,8000,12000 --report evidence/h52_control_random_sweep_20261007.json
python scripts/build_submission_h52.py --control sigma_band --tag ctrlsig --n-add 4000,8000,12000 --report evidence/h52_control_sigma_band_sweep_20261007.json
python scripts/h52_report.py                                 # -> docs/research/holdout-h52-results-20261007.md (controls appended by hand from the JSONs)
python scripts/validate_submission.py docs/downloads/GEMSDOE48-H52-lidar-scarp-additions-20261007-38029417f6ca-nan-outside.tif --receipt evidence/h52_submission_validation_20261007.json
python scripts/run_spatial_holdout.py --combined docs/downloads/GEMSDOE48-H52-lidar-scarp-additions-20261007-38029417f6ca-nan-outside.tif --candidate-name h52_lidar_additions_2000 --output evidence/holdout_h52_spatial_comparison_20261007.json
python scripts/run_spatial_holdout.py --combined docs/downloads/GEMSDOE48-H52-lidar-scarp-additions-20261007-38029417f6ca-nan-outside.tif --candidate-name h52_lidar_additions_2000 --sgmc data/raw/sgmc_faults_100m.tif --allow-unpinned-sgmc --output evidence/holdout_h52_raw_sgmc_sensitivity_20261007.json

# --- H53 session (2026-10-07) ---
python scripts/build_h53_scarp_coherence.py  # frozen H53-A: C + 12,000 strike-coherent 3DEP additions
python scripts/validate_submission.py docs/downloads/GEMSDOE48-H53-STRIKE-COHERENCE-20261007-de35531d3867-nan-outside.tif --receipt evidence/h53_submission_validation_20261007.json
python scripts/run_spatial_holdout.py --combined docs/downloads/GEMSDOE48-H53-STRIKE-COHERENCE-20261007-de35531d3867-nan-outside.tif --candidate-name h53a_strike_coherent_12000 --output evidence/holdout_h53_spatial_20261007.json
python scripts/run_spatial_holdout.py --combined docs/downloads/GEMSDOE48-H53-STRIKE-COHERENCE-20261007-de35531d3867-nan-outside.tif --candidate-name h53a_strike_coherent_12000 --sgmc data/raw/sgmc_faults_100m.tif --allow-unpinned-sgmc --output evidence/holdout_h53_raw_sgmc_20261007.json
python scripts/compare_h53_with_h49.py --output evidence/h53_vs_h49_20261007.json
python scripts/audit_h53_candidate_uniqueness.py --output evidence/h53_submission_identity_20261007.json

# 2026-10-07 (concurrent session): H51 + H50-B (inputs already committed and SHA-pinned)
python scripts/build_h51_submission.py          # H51 plausibility-budget emission + preregistration receipt
python scripts/holdout_h51.py                   # blocked folds, both proxies, H49 as gate target
python scripts/build_h50b_probe.py              # H50-B alteration-conflict probe (uses data/source_mirrors/geodawn_rad_u8.tif)
python scripts/holdout_h50b.py                  # same protocol; negative result recorded
python scripts/validate_submission.py docs/downloads/gemsdoe48-h51-plausibility-budget-20261007-f8fa1d08-nan.tif
```

The H48 rho=.5 builder remains `scripts/build_submission.py`. H49's separate mainline generation pipeline is `scripts/build_submission_h49.py`; `scripts/prepare_h49_format_copy.py` only fixes its outside-footprint encoding and preserves all inside values. The earlier alpha=.99 builder snapshot is retained as `scripts/previous_build_submission.py`; the earlier main builder is `scripts/previous_main_build_submission.py`, and the later PR #5 main Dempster builder is preserved as `scripts/previous_main_build_submission_pr5.py.disabled`. Build and holdout receipts are dated and hash-pinned. Five review passes—including API compatibility and the follow-up against the newer SGMC derivative—are recorded in [`evidence/review_passes_20261006.md`](evidence/review_passes_20261006.md).

## Sources

- [Official challenge page: metric, labels, and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) (single read 2026-10-06 UTC; no monitor)
- [DrivenData Terms of Use](https://www.drivendata.org/termsofuse/)
- [USGS GeMS/SGMC DOI 10.5066/P1A3DQZK](https://doi.org/10.5066/P1A3DQZK)
- [NASA OPERA DISP-S1](https://www.earthdata.nasa.gov/data/catalog/asf-opera-l3-disp-s1-v1-1)
- [USGS NHD product access](https://www.usgs.gov/national-hydrography/access-national-hydrography-products) · [USGS 3DEP](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services)
- [USGS Great Basin favorability DOI 10.5066/P14EET2C](https://www.usgs.gov/data/geothermal-resource-favorability-select-features-and-predictions-united-states-great-basin)
- Third-party owner mirrors and file hashes: [`docs/sources.md`](docs/sources.md)

---

## The project brief (verbatim)

<details open><summary>Owner's brief, pasted 2026-10-06. Read at the start of every session. Wording is verbatim; only the per-site results list was reflowed to one line per site.</summary>

Review the repo.

THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION.  DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION.  BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION.

There should be an easy to download submission tif file as described by the prompt.  Read the entire prompt.

Combine your two best-performing families with a rule that preserves disagreement instead of averaging it away. The spacing-tuned "dotted" family (up to 0.2778) and the tip/step-over family (0.26–0.27) are your two strongest, independently-built results, and a naive weighted average of the two surfaces would wash out exactly the information in where they disagree. Dempster-Shafer evidence theory (Dempster, 1967; Shafer, A Mathematical Theory of Evidence, 1976) — already established in exactly this kind of GIS favorability mapping as an alternative to weights-of-evidence — combines two evidence sources via Dempster's rule of combination, which explicitly carries forward a mass of "uncertain/unassigned" belief wherever the sources disagree rather than forcing it into a single blended probability. Combine your best dotted-family surface and best tip-family surface this way, and treat the resulting unassigned-belief mass as its own diagnostic layer — a geologist reading this submission can see not just where the model believes there's a fault, but where its two strongest independent approaches actively disagree. Normalize the combined belief to [0,1], write to the required format, and verify the result isn't simply the average of the two inputs (a quick correlation check against a naive mean will show this) before presenting it for download.

The following sites should serve as a starting point for understanding how to generate TIF submissions.  These websites are researched, and tested and have generated TIF submissions.  But we need to generate high scoring submissions.

Here are the results from submissions into the competition, separated by ....:

https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html — gems-submission-20260925T001403Z-7f00890a: 0.1563
....
https://buffedlizard55-lab.github.io/6GEMSDOE/ — gems6_hgb88-topk03_33cec71ff0: 0.0286
....
https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html — pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193; pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830; pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152
....
https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html — gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560
....
https://buffedlizard55-lab.github.io/GEMSDOE4/ — gems-submission-20260926T163915Z-237f0063: 0.0343
....
https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html — gems-submission-20260926T175114Z-7f00890a: 0.1563
....
https://buffedlizard55-lab.github.io/7GEMSDOE/ — lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461
....
https://buffedlizard55-lab.github.io/8GEMSDOE/ — Hedge-v2_submission: 0.1563
....
https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html — 2314b599: 0.0107
....
https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html — gems-structural-area06-v1: 0.0202
....
https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html — r7-nms3-dem10-scarp_0c9199f14e62: 0.1294; r7-nms3-dem10-scarp_0c9199f14e62_allfinite: 0.1294
....
https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html — gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782
....
https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html — GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020
....
https://buffedlizard55-lab.github.io/17GEMSDOE/ — 17GEMSDOE_F-ensemble-2pct_20260930T050626Z: 0.0187
....
https://buffedlizard55-lab.github.io/18GEMSDOE/ — H19-C_20260930T212401Z_c11e495e: 0.0297
....
https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html — h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894; h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922
....
https://buffedlizard55-lab.github.io/GEMSDOE10/ — h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461; h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921; H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280; h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839
....
https://buffedlizard55-lab.github.io/13GEMSDOE/ — 20261001_r13-lattice-s5_v2_nan-outside: 0.0904
....
https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html — h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855; h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976; h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360
....
https://buffedlizard55-lab.github.io/GEMSDOE21/ — h19-4-reference-20260930-691e4dfa: 0.1894
....
https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html — h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890; h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan: 0.1859
....
https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html — h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002; h23-b-dti-optimal-emission-10pct-20261002-86176698-nan: 0.0748
....
https://buffedlizard55-lab.github.io/GEMSDOE23/ — h30-arrangement-matched-habitat-20261002-0d4e02e8-nan: 0.1352
....
https://buffedlizard55-lab.github.io/GEMSDOE24/ — h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477
....
https://buffedlizard55-lab.github.io/GEMSDOE25/ — dotted-h19-5-d2-8-20261002-e56ea318af89-nan: 0.2600
....
https://buffedlizard55-lab.github.io/GEMSDOE26/ — dilcond-oof-v1-20261003-47629f496133-nan: 0.1223
....
https://buffedlizard55-lab.github.io/GEMSDOE27/ — topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan: 0.2449
....
https://buffedlizard55-lab.github.io/GEMSDOE28/ — h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan: 0.2708; h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan: 0.2649; h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan: 0.2710; h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan: (no score)
....
https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html — efd28-repro-20261003-1cc7dc534d51-nan: 0.2600; repo-c0-habitat-emission-20261003-a4d439b07426-nan: 0.0041; sgmc-off-catalogue-44k-20261003-c8dcd780e3fd-nan: 0.0512; wormrank-d28-20261003-59dcaf6dd11d-zeros: ; wormsurv-filter-20261003-921f10960d6e-zeros: ; xfit-c0-habitat-20261003-ca879db0089a-zeros: ; xfit-h41-union-qfaults-20261003-9edb34b99e3a-zeros:
....
https://buffedlizard55-lab.github.io/GEMSDOE30/ — d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca: 0.2600
....
https://buffedlizard55-lab.github.io/GEMSDOE31/docs/ — h27-4-solo-d28-20261004-8acb75e1-nan: 0.2708
....
https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html — h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778
....
https://buffedlizard55-lab.github.io/GEMSDOE33/ — h33d-analog-tip-stepover-r30-20261004-cb490425926e: 0.2632
....
https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html — h34-scatter-q50-arr-matched-20261004T223317Z: 0.0778
....
https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html — h35-06-aaa86efb25-20261004T225420098147Z-candidate: 0.0418
....
https://buffedlizard55-lab.github.io/GEMSDOE36/docs/ — anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros: 0.2750
....
https://buffedlizard55-lab.github.io/GEMSDOE37/ — h6-physics-dotted-80k-20261005T055000Z-0bef9211631c: 0.1193
....
https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html — D-step-3p0-07pct-tipProt-20261005-ecfbf59e2b48-zero: 0.0763
....
https://buffedlizard55-lab.github.io/GEMSDOE39/ — h40-e-disc-h40e-30k-zeros: (no score)
....
https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html — h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1: ; h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1-hard: ; h45-eulerdepthreadcluster-20261006-f28e5cff6826-zeros: (no scores)
....
https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html — h42-submission-primary: (no score)
....
https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html — xscale-worm-persistence-20261006T000541Z-nan: (no score)
....
https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html — sup01-hgb21-sep40-n40000-20261006-bc2e4e9a8d6f-nan: (no score)
....
https://buffedlizard55-lab.github.io/GEMSDOE44/docs/ — h46-twostageAB_20261006T160000Z_b0cfe956-zeros: (no score)
....
https://buffedlizard55-lab.github.io/GEMSDOE45/ — h51-km-faultzone-20261006-zeros: (no score)
....
https://buffedlizard55-lab.github.io/GEMSDOE46/ — r11f-scarp-radiometric-fusion-00e049b51218-zeros: ; r12-scarp-rad-concordance-23e807e2de9f-zeros: (no scores)
....
https://buffedlizard55-lab.github.io/GEMSDOE47/ — (no score) · 48GEMSDOE … 54GEMSDOE — (no scores yet)
....

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html — h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition.  Must be unique submission unlike any within the GEMSDOE sites above.  Verify working line by line no hallucinations.

The following is the leaderboard for the competition: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/

We need to quickly look at the results and results from the GEMSDOE websites above.

Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We have a good understanding of how our hypothesis, methodology, calculations, analysis are done so we should be able to figure out a way to score higher on the leaderboard using previous results and scoring that we have across the sites listed above.  We need to come up with distinct and unique strategies to score higher in this competition leaderboard.  We need to start doing heavy and deep research into the part of the project that matters the most, which is the scientific discovery of geothermal vents.  We should store all of our information and knowledge that we can gather from official verified sources.  This will serve as a starting point for other projects as well.  We need to think outside the box but still be grounded in proper scientific research, we are ultimately aiming for a top prize that many others are competing for.  So it's important to be contrarian but be smart about it.  We need to find sources of data that others are over looking or areas of the project when it comes to geothermal vents.  We need to do deep research and critical thinking and come up with new hypothesis to test.

0.3195 is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website.  It should be unique, take unique approaches to generating a submission that can score higher than 0.3195.

Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use.  It should solve the problem of having to manually check everything ourselves and having an up to date current feed.

Review the repo.

The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.

Our Core Values

Maximize P(Win) — "Maximize the Probability of Winning": our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). "Maximize P(Win)" frees us from constraints and clarifies that we must put Arena first.

Own the Outcome — We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We need to focus on being able to generate a submission into the competition.

The site should be able to generate a TIF file that is required for submission.  It should be as easy as download to click a File to submit into the competition.  This needs to be in the executive summary or the very beginning of the site.  it should be obvious when you visit the site.

I tried to submit the document that i downloaded from the site but it returned this error on the submission form: "Predicted values must be in range [0, 1]"

Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Here is the submission page when i click submit file: New submission — File to submit (No file chosen). You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform. You may wish to review the competition rules first. Note (optional): A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Create a executive summary subpage that explains exactly how to make a submission into the contest.

Work on the next steps from the previous sessions first.

The goal of this project is to place top of the leaderboard in this competition.  The following is the competition: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/

We need to create a project that can compete and place top of the leaderboard.  We need to understand the problem, collect all the data and organize it into a clean easily auditable table with official verified links for manual verification.

This is the guidelines we need to follow. https://www.drivendata.org/competitions/306/competition-doe-gems/

Get familiar with the problem through the overview and problem description, https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/. You might also want to reference additional resources available on the about page, https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/.

Download the data from the data, https://www.drivendata.org/competitions/306/competition-doe-gems/data/, tab.

Create and train your own model. This reference solution, https://github.com/drivendataorg/gems-prize-reference-solution implements a simple approach.

Use your model to generate predictions that match the submission format.

Tell me what are you limitations and what you need access to during this project.  We will need to find free publicly available sources and data from official and verified sources if we are to use 3rd party or external data.

this pdf outlines how submissions must be entered into the competition. https://docs.nlr.gov/docs/fy26osti/96647.pdf

You must be able to do your own research, deep research, scientific literature research and organize the knowledge so that we can critically think through the problem and generate a solution through scientific and free publicly available information.  this must be done autonomously and must be constantly reviewed and improved upon.  Provide suggestions and improvements and implement them.

❌ No DrivenData auth → cannot auto-download training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv from https://www.drivendata.org/competitions/306/competition-doe-gems/data/ (verified redirect to login)

See below for links from the above site. https://gdr.openei.org/submissions/1391

Download competition data from https://www.drivendata.org/competitions/306/competition-doe-gems/data/ (requires login) to data/

See links below for competition data:
https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0
https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0
https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0
https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0
https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0

Site creation: Create a github page for this repo that has clean ui, user friendly, simple and easy to use.  It should be organized and clean.  It should include all relevant information in an easy to read format with official verified links as sources for review.  Work line by line verify everything no hallucinations.

**The single remaining blocker to training is data placement**: run `bash scripts/download_competition_data.sh` on any unrestricted machine into `data/`, then `python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready to run (GPU needed for training; metric/losses/validation all verified working here on CPU). — you need to complete the above task by yourself.

Run this task through multiple passes. Pass 1: Implement the task completely and verify the result. Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find. Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues. Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify that the final result fully satisfies the original request.

Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project.  It should be worked on in this next session or the next session.  Work line by line verify everything no hallucinations.

</details>

---

## DS48 fusion sub-site (PR #6; research-only, not slot-cleared)

The self-contained DS48 sub-site is retained at `docs/ds48-fusion/`; it does **not** replace the
current project landing page.

- **DS-ranked emission (audit only):** `docs/downloads/gemsdoe48-ds48-emission.tif` — 37,654 px,
  all-finite float32 `[0,1]`, EPSG:32611, 3730 × 3292. Its recorded owner-derived SGMC
  off-catalogue DTI is 0.09068 vs 0.09613 for the dotted baseline (about 5.7% lower).
- **Diagnostics:** `-belief.tif` (`Bel(F)`, `[0.0000, 0.8400]`), `-mtheta.tif` (unassigned mass,
  `[0.1600, 0.2500]`), `-conflict.tif` (Shafer's `K`, `[0.0000, 0.3600]`).
- **Artifact label:** `GEMSDOE48-DS48-FUSION` is retained from that experiment; it is not a
  submission recommendation. The finite-zero outside convention does not meet official
  null/NaN-outside wording, and portal acceptance is untested.
- **Decision:** no organizer score exists; the catalogue-based proxy is anti-monotone with the
  four known live anchors. Do not upload or spend a weekly slot on this unvalidated/losing artifact.

The page's 0.2778 analysis, Dempster–Shafer diagnostics, and historical H48-A–E proposal list are
preserved as research. Its H48-A 200–300 m interpretation is not the current hypothesis ranking;
use [`docs/md/hypotheses.md`](docs/md/hypotheses.md). The dotted and tip masks overlap
substantially (31,614 of b2's 37,654 positive pixels), so the Dempster independence/distinctness
assumption is unsupported and its layers are diagnostics, not calibrated probabilities. It also
does not re-rank union support (Spearman ρ≈1).

**Current validation (2026-10-07):** `.venv/bin/python -m pytest -o addopts= -q -ra` — 290 passed, 3 skipped, 185 subtests passed. The three skips require raw inputs not restored (`scripts/fetch_inputs.sh`); the completed suite did not require network access. The 262-, 216-, and 120-test counts above belonged to earlier snapshots and are historical, not current.

**Correction.** `DS48-IR-07` in the subsite records the hexagonal covering arm as unvalidated and
not slot-cleared; its +1.9% SGMC-side signal was within re-sampling noise.

## Session brief 2026-10-07 (verbatim owner prompt)

Review the repo.

THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION.  DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION.  BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION.

There should be an easy to download submission tif file as described by the prompt.  Read the entire prompt.

Combine your two best-performing families with a rule that preserves disagreement instead of averaging it away. The spacing-tuned "dotted" family (up to 0.2778) and the tip/step-over family (0.26–0.27) are your two strongest, independently-built results, and a naive weighted average of the two surfaces would wash out exactly the information in where they disagree. Dempster-Shafer evidence theory (Dempster, 1967; Shafer, A Mathematical Theory of Evidence, 1976) — already established in exactly this kind of GIS favorability mapping as an alternative to weights-of-evidence — combines two evidence sources via Dempster's rule of combination, which explicitly carries forward a mass of "uncertain/unassigned" belief wherever the sources disagree rather than forcing it into a single blended probability. Combine your best dotted-family surface and best tip-family surface this way, and treat the resulting unassigned-belief mass as its own diagnostic layer — a geologist reading this submission can see not just where the model believes there's a fault, but where its two strongest independent approaches actively disagree. Normalize the combined belief to [0,1], write to the required format, and verify the result isn't simply the average of the two inputs (a quick correlation check against a naive mean will show this) before presenting it for download.

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

[https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html)

h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition.  Must be unique submission unlike any within the GEMSDOE sites above.  Verify working line by line no hallucinations.

Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.

0.3195 is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website.  It should be unique, take unique approaches to generating a submission that can score higher than 0.3195.

Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use.

The following is taken from the Arena AI team: Core Values — Maximize P(Win): in every decision weigh tradeoffs, assess risk, choose the path that maximizes the probability of winning. Own the Outcome: own results end to end; when problems arise and we have the means to act, do so without waiting; treat failure and success as signals.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

The site should be able to generate a TIF file that is required for submission.  It should be as easy as download to click a File to submit into the competition.  This needs to be in the executive summary or the very beginning of the site.  it should be obvious when you visit the site.

The submission form error "Predicted values must be in range [0, 1]" must be addressed; give the submission a unique name and a short note for the submit form.

Create a executive summary subpage that explains exactly how to make a submission into the contest.

Run this task through multiple passes (implement+verify; review for bugs/missing requirements/edge cases; re-check against the original request).  Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project.

(Note: the full site list of prior campaign results, the complete link compendium, the NLR PDF reference, the Dropbox mirror links, and the detailed site-creation requirements are retained verbatim in the earlier "The project brief (verbatim)" section above and in the prior-session archives; this section records the operative requirements of the 2026-10-07 session.)

## H53 continuation addendum — active acceptance criteria

- Work the frozen H53 slate of hypotheses not previously implemented in this checkout. Rank expected DTI improvement qualitatively against implementation cost, distinguish unimplemented code from earlier proposals, and check actual data availability before calling a source viable. H53-B and H53-D are parked pending exact-payload/coverage audit; H53-C is related prior art and uses an owner mirror. Official source links and freshness limits are recorded in [`docs/research/hypotheses-h53-20261007.md`](docs/research/hypotheses-h53-20261007.md).
- H53-A was frozen as: use regional H52-derived `h_gate12`, `strike_at`, and `cover`; require height ≥0.30 m, cover ≥0.90, and strike-compatible support at ≥4/5 samples across an approximately 400–565 m trace; add 12,000 Poisson-spaced cells to parent C, excluding cells within 200 m of the public catalogue and C. Keep H52-1 distinct from proposed raw-DEM H52-v2.
- H53-A is built, locally format-validated, and evaluated. It loses to H49 on both pre-registered SGMC proxy comparisons. **The no-go is final for this candidate: do not promote or spend a weekly slot on these public-proxy results.** The paired receipt and exact limits are [`evidence/h53_vs_h49_20261007.json`](evidence/h53_vs_h49_20261007.json) and [`docs/research/holdout-h53-results-20261007.md`](docs/research/holdout-h53-results-20261007.md).
- Preserve a unique one-band float32 TIFF on the exact competition grid, finite `[0,1]` in-footprint values and NaN outside; use a content-derived name and short note. Local checks do not imply organizer acceptance or global uniqueness. Keep H50's `m(Theta)` and raw conflict `K` diagnostics distinct; do not replace the requested disagreement-aware Dempster-Shafer work with a naive average.
- Run the three passes: implementation/verification, bug-assumption-edge review, and complete requirement recheck. Keep the one-click candidate prominent on the site with clear no-upload status and reference upload instructions. A PR/merge is only for the research code/docs; it is never competition promotion.
