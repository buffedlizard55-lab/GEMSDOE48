# Evidence and leaderboard irregularities

This ledger separates what was directly observed from what cannot be attributed. It is intended to prevent a plausible-looking filename or owner receipt from becoming an unsupported score claim.

## One-time leaderboard context — attribution is not established

A single dated read for the current review observed a top displayed DTI of **0.3774**, **0.3195 at rank 7**, and a **0.2778 row at rank 13**. These are participant-level display values only; they do not establish any local TIFF's score. No leaderboard table or participant names are republished here. Older repository notes contain 2026-10-06 / 2026-10-07 readings and inconsistent submission counts (10 versus 11); without an auditable page capture, that discrepancy is preserved as unresolved rather than reconciled by another read.

The [DrivenData Terms of Use](https://www.drivendata.org/termsofuse/) restrict automated monitoring/copying and manual monitoring/copying without prior written consent. This repository does not poll or scrape the leaderboard. The one-time value observation is not a permanent ranking and should not be updated without authorization.

### Attribution not verified

- The local H33-2-B2 owner-mirror receipt says **“UNSCORED.”** No organizer receipt or file-level identifier links those exact TIFF bytes to the 0.2778 row.
- The observed 0.3195 at rank 7 is not the top displayed value; no score-to-file association is established by the row.
- The presence of H33-2-B2 and H33-D artifacts in public repositories does not establish that either exact file was used in a scored submission.
- Owner-reported projected scores, holdouts, and “slot eligible” labels are not organizer scores.
- No claim is made about what any participant's score would be if a different artifact were submitted.

## Provenance and label caveats

- The H33-2-B2 and H33-D inputs, and the label/template mirrors, are public third-party owner mirrors, pinned by commit and SHA-256. They are not organizer-authenticated, and those hashes do not establish a license grant.
- The mirrored labels are existing public catalogue faults. They are not the private expert-labelled test faults described by the challenge.
- The source surfaces are frozen upstream products and are not rebuilt fold-by-fold. An owner's H33-2-B2 audit describes a catalogue-proximity pruning operation; this means a block score against public catalogue labels cannot be described as leakage-free.
- The two surfaces share 31,614 positive cells (Jaccard 0.659931), so their evidence is not independent. Sparse zero may mean “no emitted candidate,” not known absence of fault.

## SGMC raster provenance discrepancy

Two locally tracked SGMC-derived rasters share the same 3,730 × 3,292 EPSG:32611 spatial grid but are not pixel-identical. The newer manifest-pinned derivative `data/official/derived_sgmc_faults_100m.tif` (SHA-256 `643cbe...`, 83,593 positives) has 1,446 positive cells absent from the prior raw raster `data/raw/sgmc_faults_100m.tif` (SHA-256 `26d142...`, 82,151 positives); the prior raster has 4 positive cells absent from the newer one. There are 1,450 differing cells total, and their nodata metadata also differs. The derivation difference is unresolved; neither raster is organizer-authenticated or private expert truth. The primary holdout now uses the newer pinned derivative and defines off-catalogue truth as 62,122 positive cells more than 300 m from catalogue positives. The earlier raw-raster result is preserved separately. See [`evidence/sgmc_raster_comparison_20261006.json`](../evidence/sgmc_raster_comparison_20261006.json), [`evidence/holdout_20261006.json`](../evidence/holdout_20261006.json), and [`evidence/holdout_raw_sgmc_20261006.json`](../evidence/holdout_raw_sgmc_20261006.json). The PR #5 proxy report's 63,121 count includes exactly-300 m cells and uses full-scene quadrant scoring; it is not directly comparable to the current core-plus-halo folds.

## Operational constraint

The [DrivenData Terms of Use](https://www.drivendata.org/termsofuse/) were checked. No leaderboard polling, automated monitor, or scraping loop is active. This branch disables the upstream six-hour workflow and preserves it as `.github/workflows/feed.yml.disabled`; `scripts/refresh_leaderboard.py` is parser-only and exits without network access. The snapshot above is a single dated observation and may become stale. Do not automate access; verify current rules and authorization before any future observation.

## Session 2026-10-07 UTC additions

### Official `training_features.tif` band 6 is radiometric total count, not a magnetic derivative

The organizer's layer list (problem description, page 967) describes the 19-band `training_features.tif`; its band 6 is named `tc`. Over the 12.3 M in-footprint cells, band 6 correlates at **r = 0.9971** with the independently mirrored GeoDAWN radiometric *total count* (`data/raw/external/geodawn_rad_u8.tif`, band TC) and at r = −0.04 with the total magnetic intensity bands. Any description of `tc` as "tilt angle" or "total curvature" of the magnetic field is therefore wrong; downstream users of the official stack should treat band 6 as gamma-ray total count. Measured this session with the hash-pinned mirrors in `data/raw/external/`; the training stack itself was assembled from the sibling-campaign shards (SHA-256 `4371c82e…`, see `evidence/external_fetch_receipt.json` for the external mirrors).

### Sandbox cannot reach GitHub artifact storage

`gh run download` and `gh run view --log` fail with EOF because `productionresultssa*.blob.core.windows.net` and `objects.githubusercontent.com` are unreachable from the sandbox (only `github.com`, `api.github.com`, `codeload.github.com`, `pypi.org` answer). CI outputs are therefore brought back by committing compact (<100 MB) products to the session branch (`data/pilot/dem3m/`, `data/external/h52_scarp3m_100m.tif`). This is a workflow constraint, not a data irregularity; the artifacts remain attached to the runs for manual review.

### Leaderboard observation 2026-10-07 UTC (single read; no table republished)

The one-time observation above places 0.3195 at rank 7 and 0.2778 at rank 13; the top displayed value was 0.3774. Older 2026-10-06 notes preserve an inconsistent submissions-display count. No participant names or row-by-row table are reproduced; no exact artifact is tied to a score, and the Terms of Use caveat remains in force.

### Live-ladder inversion assumes the removed dots carried ~zero credit

`scripts/live_ladder_analysis.py` inverts A→B→C with the exact metric algebra under the assumption that the removed catalogue-adjacent dots carried no credit. The two independent estimates of T/π (5,073 and 5,470) differ by 7.5 %, consistent with that assumption but not proving it; the organizer's statement that known-fault pixels are masked (community post 11516) applies to d = 0 cells only, so dots at 100–200 m may carry small residual credit. Derived quantities (|G|/π ≈ 14,300, recall ≈ 0.37) are therefore ±10 % estimates.

### H52-1 pilot lift did not generalise (2026-10-07)

The two-tile pilot measured 2.3–3.2× catalogue-adjacency lift for the top-2 % gated step-height cells (n = 44–98 cells per tile). The identical statistic over the 700-tile region product is 1.19× (NW), 2.27× (NE), 1.53× (SW), 1.63× (SE) — and a plain terrain-roughness band flag (σ_ctx 0.7–2.5 m) scores 1.57× with no ranking at all (`evidence/h52_region_detector_checks_20261007.json`). The pilot tiles were chosen for high catalogue density and are not representative; treat any future pilot lift from ≤ 100 cells as unconfirmed until the region statistic agrees. The pre-registered gate was applied as written and failed; the candidate file is published as unique-but-not-cleared.

### H53 session additions (2026-10-07)

* **H52 19-band lift numbers lack committed receipts.** The H52 slate reports per-band catalogue-lift measurements (geodetic 2nd-invariant 4.7× top-0.5 %, U/K 2.2×, per-dot re-ranker table) from the official 19-band `training_features.tif`, but no such raster or measurement receipt is committed here (verified: no `training_features*` file in the repo; no H52 evidence JSON records those numbers). Treat as unverified; the H53 slate does not rely on them.
* **No fresh leaderboard read this session.** Direct shell egress excludes `drivendata.org` and USGS/MRLC; the official challenge/3DEP/3DHP documentation pages were retrieved through the web tool, but the live leaderboard was not re-read. The 0.3774-top correction still rests on the dated 2026-10-06/07 observation.
* **H53-1 pignistic twin overlaps H51 strongly but is a distinct file.** Twin∩H51 = 35,941/37,654 (Jaccard 0.913); twin∩C = 33,385 (Jaccard 0.796). SHA-256 `9242c831…` differed from the 58 then-local rasters in the upstream pre-H53-A bounded scan; this is not a current or global uniqueness proof (`evidence/build_h53_receipt_20261007.json`).
* **H53-A shares its base with C by design.** After merging H53-1, the bounded scan attempted 65 local TIFFs and found 61 one-band exact-grid comparisons; no exact value/support match, with maximum positive-support Jaccard 0.758328 to parent C, retained in full. This proves only local distinctness, not global or organizer-side uniqueness (`evidence/h53a_scarp_submission_identity_20261007.json`).
* **H53-1 graded belief is diffuse by construction** (1.49 M positives, mass 260,260; SGMC proxy 0.071408). The budget-matched binary twin (0.089559) is the decision-surface comparator.

### Tile inventory covers UTM zone 11 only

`registry/dem_tiles_pilot.json` (700 records, 661 distinct tile names — 39 tiles are staged under two 3DEP projects) omits the 16 zone-10 tiles of the competition footprint; the region product therefore covers 3.66 M of the 5.17 M footprint cells at ≥ 90 % cover (the 2 m u8 descriptors cover 3.89 M). Cells within 150 m of a tile edge are flagged invalid by design.

---

# Session 2026-10-07 UTC — H55 additions

Machine-readable twin with the full evidence strings: [`evidence/hypothesis_slate_h55_20261007.json`](../evidence/hypothesis_slate_h55_20261007.json) → `irregularities`. Rendered: [`irregularities.html`](irregularities.html).

## IR-H55-01 · Official `training_features.tif` band 6 is gamma-ray total count, and its own metadata says otherwise — *independently reproduced*

The 2026-10-07 entry above is **confirmed**, with a stronger test. The official stack was restored this session byte-identical to its manifest pin (SHA-256 `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`, 418,912,844 bytes, 19 float32 bands). Band 6's in-file description reads *"Tilt angle or total curvature - magnetic field derivative for edge detection"* and its `data_category` tag reads `magnetic_data`. Measured over **5,164,300** in-footprint cells against the independently mirrored GeoDAWN radiometrics:

| pair | Pearson r |
|---|---:|
| band 6 vs GeoDAWN **total count** | **0.9971** |
| band 6 vs GeoDAWN K | 0.8817 |
| band 6 vs the same file's own TMI (band 14) | −0.0409 |
| band 6 vs TMI horizontal gradient (band 3) | −0.1624 |

**Spearman ρ(band 6, total count) = 1.0000** on a 1-in-37 subsample. Band 6 ranges 2.95–88.57 with a median of 18.5. Severity **high**: anyone who takes band 6's description at face value builds a "magnetic tilt" feature out of radiometrics. Carried into hypothesis H55-C so it does not treat band 6 as a magnetic derivative.

## IR-H55-02 · Local GeoTIFF validation does not establish portal acceptance

The historical B2 raster is all-finite with zeros outside and `nodata` unset; local bytes and `data/raw/audit-h33-2-b2.json` record that fact. The organizers' reference solution (notebook cell 19) also writes an all-finite float32 raster with `nodata` unset. These observations do not establish the portal's validator policy, the acceptance of any local file, or a file-to-score link. The local B2 receipt itself labels the file `UNSCORED`.

**Action:** `scripts/validate_submission.py` supports `--encoding {auto,nan,zeros}` and reports local exposure fields including `portal_range_error_immune`; the field means only that a simple whole-array `[0,1]` predicate would pass the re-read bytes. The current H56B-NF NaN-outside file reports `portal_range_error_immune: false`; portal behavior and acceptance remain untested. Severity **high**.

A NaN makes ordinary NumPy comparisons `(v >= 0) & (v <= 1)` false, so NaN is a plausible source of a range error from a simple vectorized check. **The cause of any reported organizer portal response is unknown.** Owner-reported scores associated with different encodings do not prove that exact local bytes passed or failed. See the [metric/format caveat](research/metric-identity-erratum-20261007.md) and [H56B-NF format receipt](../evidence/h56b_noflank_format_validation_20261007.json).

## IR-H55-03 · Dense-backbone pixel count is factual; the prior truth-yield inference is retracted

`knowledge/research_notes.md` and earlier README text described dense H19-5 as “129 k px.” The pinned mirror (`data/raw/scored/h19_5_01922.tif`, SHA-256 prefix `ec1f9b56…`) has **121,131** positive pixels; that raster count is directly measured. A former inversion of its owner-reported 0.1922 value to `T=6,813.1` used the invalid `FPw=S−TPw` identity and is **not a supported truth-yield estimate**. The related comparisons with C's former inferred `T=5,209.5` and leaderboard thresholds are withdrawn.

Severity **high**: preserve the corrected positive-cell count, but do not describe any inferred hidden-truth mass or “binding constraint” from these scores. See the [metric-identity erratum](research/metric-identity-erratum-20261007.md); the H55 report remains for historical audit with its correction banner.

## IR-H55-04 · A public SGMC proxy score is not an estimate of the organizer score

H49's direct score on the frozen SGMC>300m public-map test set is **0.100751**; the repository separately records an owner-reported **0.0512** value for a proxy-built candidate, without an organizer file-to-score receipt. Those observations warn against equating this public proxy with private truth. The former conversion of 0.0512 into hidden-truth mass, and resulting H55/H56 score-gap calculations, depended on the withdrawn `FPw=S−TPw` assumption; they are not evidence that this proxy systematically selects candidates or quantifies a live shortfall.

Severity **high**: retain direct public-proxy measurements with exact protocols, but report them as separate diagnostics. Do not infer private labels, score gaps, or hidden-set candidate rank. See the [H56B review](research/h56b-review-erratum-20261007.md), [metric-identity erratum](research/metric-identity-erratum-20261007.md), and `evidence/live_ladder_20261007.json` (historical, with H55 report correction).

## IR-H55-05 · Catalogue coverage per emitted pixel is a proxy statistic, not live truth yield

| field | positive pixels | catalogue coverage per emitted pixel |
|---|---:|---:|
| h19-5 backbone | 121,131 | 0.1007 |
| SGMC faults | 83,593 | 0.1418 |
| GDR wells/springs, all | 12,570 | 0.1023 |
| GDR wells/springs, *Hot* | 929 | 0.1897 |
| INGENIOUS Quaternary fault centroids | 1,125 | 0.3696 |

These measured ratios compare each public layer to a public catalogue under the cited calculation. They do **not** estimate private-truth yield or validate the former `≥2× catalogue lift` candidate rule. Any conclusions that interpreted the values as expected hidden-label credit or a slot gate are withdrawn. Severity **high**; see the [metric-identity erratum](research/metric-identity-erratum-20261007.md).

## IR-H55-06 · Historical hidden-truth calibrations are not identified by these scores

Prior files and notes contain two different assumed hidden-truth totals: **12,632**, from a fixed 0.05416 removed-dot credit, and a later fitted **14,027.5**, from an assumed zero-credit nested-rung model. Neither is identified from the available owner-reported scores under the official DTI: the calculations used a generally false `FPw=S−TPw` identity and additional assumptions about credit and file attribution.

**Action:** both constants and their derivations remain in historical modules and receipts for reproducibility, but treat them as assumption-indexed algebra, not measurements of `|G|`, recall, or an organizer ceiling. No model-dependent live-score conclusion follows. Severity **high**; see [`metric-identity-erratum-20261007.md`](research/metric-identity-erratum-20261007.md).

## IR-H55-07 · A tracked local mirror and its published upstream mirror are pixel-identical but byte-different

`data/raw/ref_h36_1_rung30.tif` (SHA-256 `7c74270a…`) and the GEMSDOE28 published file `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` (SHA-256 `5556aa14…`) have **identical emission pixel sets** (`np.array_equal` on the boolean mask, 37,660 px) and differ only in outside-footprint encoding and tags. The same holds for `data/raw/tip_h32_1_prethin_tip_euler.tif` (`26748e4b…`) versus `04d31922…` (42,294 px).

**Action:** `live_model.LIVE_ARTIFACTS` now points at the restored *published* mirrors under `data/raw/scored/` so every pin is the published one, with the pixel-identity check recorded in a code comment. `scripts/calibrate_live_model.py` fails closed on any pin mismatch. Severity **low**, but it is exactly the kind of thing that makes a "verified" hash meaningless if unnoticed.

## IR-H55-08 · `h52_scarp3m_100m.tif` band `facing_at` has unconfirmed units

`strike_at` takes only the values 0, 1500, 3000, …, 16500 — consistent with a strike in 0.01° units quantised to 15° bins over 0–165°. `facing_at` ranges 0–10,000 with a median of 4,893. If `facing_at` were a dip direction in the same units the two should be perpendicular; the measured median deviation from perpendicularity over all 5,900,588 valid cells is **46°** (p10 8.9°, p90 81.4°), i.e. no perpendicular relationship at all.

**Action:** an along-strike extension of the hydrothermal conduit anchors was designed and then **withdrawn** rather than shipped on an unverified band. Recorded as the blocker on hypothesis H55-D with the exact check required: re-read `src/gemsdoe48/scarp3m.py` and `data/external/h52_scarp3m_merge_log.txt` against the GitHub Actions run that produced the mosaic. Severity **medium** — this is a case of refusing to guess.

## IR-H55-09 · Brief's 0.3195 “top” statement and historical reachability claims

A one-time dated observation found 0.3195 at rank 7 and a top displayed value of 0.3774; a 0.2778 row appeared at rank 13. No participant names or full leaderboard table are republished here, and none of those rows is linked to a local TIFF hash. Earlier H55 ceiling and recovered-truth claims (including the 0.2843 live-equivalent “frontier”) depended on invalid metric identities and are superseded by [`metric-identity-erratum-20261007.md`](research/metric-identity-erratum-20261007.md). **No reachability conclusion or score prediction from those calculations is supported.** Severity **high**; historical outputs remain archived, but must not be used as private-label bounds.

## IR-H55-10 · No organizer score exists for any file in this repository

`registry/live_scores.json` holds owner-reported score entries with associated local hashes, but no organizer receipt, API response, or page capture links any exact local TIFF bytes to a score. The local receipt for B2 marks it `UNSCORED`. H55's fitted `|G|`, `rho`, inverted `T` values, and scenario band are retracted as private-label estimates because they depend on the invalid metric identity and owner-reported inputs. No projected leaderboard position is supported. Severity **high**—this is the central limitation on score attribution and forecasting.

## IR-H56-01 · The 0.2778 producer page says UNSCORED; attribution to local bytes remains unverified

On 2026-10-07 the H56 session fetched `docs/index.html` from the GEMSDOE32 source repository (`api.github.com/repos/buffedlizard55-lab/GEMSDOE32/contents/docs/index.html`). The producer's paste-ready note for `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` (SHA-256 prefix `c55bafc470054e82…`, byte-identical to `data/families/dotted_b2_prune_02778.tif`) states 37,654 dots, the 200 m catalogue prune, a public-proxy result, “projected 0.2747,” and `UNSCORED`. That is evidence about the producer's own label and method—not an organizer file-to-score receipt. The 0.2778 association remains owner-reported and unauthenticated against exact bytes; the 0.2747 projection is withdrawn under the metric correction.

Severity **medium**. H56/H56B public-proxy results are reported only as direct public-map computations and cannot establish private-label performance. See [`why-02778-and-ceiling-20261007.md`](research/why-02778-and-ceiling-20261007.md), the [H56B review](research/h56b-review-erratum-20261007.md), and [metric-identity erratum](research/metric-identity-erratum-20261007.md).

## IR-H56-02 · Battery development incident: official-band nodata contamination, caught and fixed before publication

During development of `scripts/h56_research_battery.py` the first two runs read the 19-band
official raster without masking the −3.4e38 nodata sentinel, which contaminated the DEMGLOW
z-score field in the nodata margin (one intermediate run reported 9,023 conjunction pixels for
the z≤−2 rung against 428 after masking). The bug was caught by comparing ladder counts across
runs, fixed (reference-solution convention `X[X < −1e38] = NaN`), and the final evidence files
(`evidence/h56_band_screen_20261007.json`, `evidence/h56_research_battery_20261007.json`) were
produced by the corrected script only. No published number used a contaminated value. Severity
**low** (process caught its own defect), recorded because the brief requires every
irregularity to be flagged.


## H56B review additions — 2026-10-07

### IR-H56B-01 · 0.2778 score attribution and H56B performance are unverified

The H56B-NF ablation combines two SHA-pinned public owner-mirror inputs; both parent score values are owner-reported. The local B2 audit says `UNSCORED`, and there is no organizer receipt linking exact local input/output bytes to leaderboard rows. The B2 producer's note says its B=2 prune removed dots within 200 m of the full catalogue; H56B-NF removes only the later D-S recipe's catalogue-flank absence term, so its parent is not catalogue-independent. H56B-NF itself has **no organizer score**. Its four-fold public-proxy DTI is 0.056305 catalogue and 0.068987 SGMC-off, below same-protocol H49 (0.095353 / 0.100751) in 0/4 folds on each. The proxy labels are public maps, not private expert truth, and the frozen sources are not reconstructed inside folds. It is a post-hoc ablation, not a new geological detector. See [`h56b-review-erratum-20261007.md`](research/h56b-review-erratum-20261007.md).

### IR-H56B-02 · `m(Theta)` is not a direct disagreement map

Normalized Dempster leaves residual `m(Theta)` as uncommitted/ignorance mass; raw conflict `K` is divided out and exported separately. Absolute support difference `|s_dot-s_tip|` is another diagnostic, not a D-S mass. Earlier copy describing `m(Theta)` as “where families disagree” was imprecise. At total/numerical conflict Dempster normalization is undefined; `src/gemsdoe48/h56.py`, `src/gemsdoe48/dempster_shafer.py`, and the H56B builder raise `ValueError` rather than substituting vacuous mass. Tests are part of this change.

### IR-H56B-03 · H56 slate chronology and recipe collision

The date-only main H56 slate ranks H56-A first; its H56-A holdout is timestamped 15:21Z and the build receipt 15:43Z, so build-before-holdout order is not established. The 15:17Z build and 15:20Z holdout are for the earlier H56 predecessor, not final H56B. A different H56B-specific slate claims a 16:00Z freeze, ranks H56-F first, and contains measurements; it follows the predecessor but precedes final H56B at 17:37Z/17:38Z, and describes a different recipe, so it is not a verified preregistration of final H56B. The two slates also reuse H56-B for different candidates. H56B-NF was built post hoc. Historical records and correction are preserved; see [`evidence/h56_preregistration_reconciliation_20261007.json`](../evidence/h56_preregistration_reconciliation_20261007.json) and [`evidence/h56b_review_corrections_20261007.json`](../evidence/h56b_review_corrections_20261007.json).

### IR-H56B-04 · Data availability does not equal verified coverage

The 19-band feature raster cited by historical H56 screens is absent from the current checkout; its prior sibling-mirror hash is not organizer authentication. H57-B therefore cannot currently build. H57-C has two local 3 m pilot tiles and a 100 m scarp summary, not the full-area 3 m DEM needed for channel profiles. The official magnetic and geochemical pages expose potential downloads, but no payload or footprint-wide coverage is present. The local GeoDAWN radiometric mirror is available with `nodata=0`; valid-zero/nodata semantics require review. Details: [`h57-hypothesis-slate-20261007.md`](research/h57-hypothesis-slate-20261007.md) and [`data-availability-geochem-magnetic-20261007.md`](research/data-availability-geochem-magnetic-20261007.md).

### IR-H56B-05 · Old 0.0649 projection and score “ceilings” are invalid

The old H56B projection uses `FPw=S−TPw`, whereas the official metric gives `FPw=S−Q` with a prediction-centred `Q` and truth-centred `TPw`. The 0.0649 projection and related H55/H56 live-equivalent ceilings/private-truth bounds are not supportable. The corrected identity and executable counterexample are documented in [`metric-identity-erratum-20261007.md`](research/metric-identity-erratum-20261007.md). The only current H56B evaluation reported here is its matched public-proxy holdout, which loses to H49.

### IR-H56B-06 · NaN-outside portal acceptance remains untested

The current H56B-NF file passes local format validation as float32, EPSG:32611, finite `[0,1]` in-footprint values, and NaN/nodata outside, matching the documented null-outside convention. However, the local receipt reports `portal_range_error_immune=false`: an all-pixel range check may treat NaNs as out of range. This is download-only for inspection; no organizer portal acceptance or score is claimed. See [`evidence/h56b_noflank_format_validation_20261007.json`](../evidence/h56b_noflank_format_validation_20261007.json).
