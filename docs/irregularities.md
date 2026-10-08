# Evidence and leaderboard irregularities

This ledger separates what was directly observed from what cannot be attributed. It is intended to prevent a plausible-looking filename or owner receipt from becoming an unsupported score claim.

> **Current superseding corrections (2026-10-07):** The historical H55/H56 live-score inversions assume `FPw = S − TPw`, which is generally false; their inferred hidden-truth counts, 0.2843 ceiling, 0.0649 projection, universal 0.0556 per-dot threshold and reachability claims are invalid. The related Gate-2 density-matching protocol uses that invalid inferred truth count and is not promotion-ready. Keep the receipts as historical audit only; see [`metric-identity-erratum-20261007.md`](research/metric-identity-erratum-20261007.md). The latest local training inventory says the named feature stack is absent now; older session-specific stack measurements do not imply it is staged or authenticated. The 2026-10-07 public leaderboard row at 0.2778 is #13 under `extradr19`; no organizer receipt links it to the local B2 TIFF. Current artifact status: download for inspection may be OK, but no file/slot is cleared to submit.

## One-time official leaderboard read — 2026-10-06 UTC

| Displayed participant | Displayed DTI | Rank on page | What this establishes |
|---|---:|---:|---|
| `xiaofanhu` | 0.3774 | #1 | Participant-level official leaderboard row at the time read |
| `alexoktaba` | 0.3345 | #2 | Participant-level official leaderboard row at the time read |
| `nchuzhoy` | 0.3262 | #3 | Participant-level official leaderboard row at the time read |
| DARD | 0.3195 | #7 | DARD had a 0.3195 row; it was **not** the highest displayed score |
| `extradr19` | 0.2778 | #13 (10 submissions) | The displayed 0.2778 row belonged to this participant |

Source: [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), opened once on 2026-10-06 UTC. No screenshot or raw page copy is treated as a score-to-file receipt. The number of submissions is a participant display field, not a file identity.

### Attribution not verified

- The local H33-2-B2 owner-mirror receipt says **“UNSCORED.”** No organizer receipt or file-level identifier links that exact artifact to the 0.2778 leaderboard row.
- The DARD 0.3195 row is not evidence that 0.3195 is the highest leaderboard score; the page displayed higher entries.
- The presence of H33-2-B2 and H33-D artifacts in public repositories does not establish that either exact file was used in a scored submission.
- Owner-reported projected scores, holdouts, and “slot eligible” labels are not organizer scores and are not used as this project's measured result.
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

### Leaderboard observation 2026-10-07 UTC (single read, not polled)

Top of the public board: 0.3774, 0.3345, 0.3262, 0.3222, 0.3220, 0.3218, 0.3195 (DARD), 0.2888; the 0.2778 row (extradr19, 11 submissions) is 13th. The brief's "top 0.3195" is therefore the 7th place, not the top. Recorded once; no automation.

### Historical live-ladder inversion — invalidated, forensic only

An earlier `scripts/live_ladder_analysis.py` report paired owner-reported A→B→C scores with an assumed zero-credit removal model and the substitution `FPw=S−TPw`. That is not an exact inversion of the official metric: prediction-centred `FPw=S−Q` and truth-centred `TPw=T` are generally different. The old estimates of `|G|`, `T`, recall, credit per dot, reachability, and any associated removal/addition thresholds are **not** ±10% estimates; they are invalid model outputs and must not be used as truth-density or promotion evidence. The script now refuses by default and writes forensic output only with an explicit opt-in. Preserve the owner-reported score/count pairs as reports, not as verified file-to-score links. See the [metric-identity erratum](research/metric-identity-erratum-20261007.md) and [historical receipt](../evidence/live_ladder_20261007.json).

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

During the H55 session, a hash-pinned 19-band third-party owner-mirror copy (SHA-256 `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`, 418,912,844 bytes) was temporarily present. It was not organizer-authenticated and is absent from the current training inventory. On that mirrored file, band 6's in-file description reads *"Tilt angle or total curvature - magnetic field derivative for edge detection"* and its `data_category` tag reads `magnetic_data`. Historical measurements over **5,164,300** in-footprint cells against the independently mirrored GeoDAWN radiometrics were:

| pair | Pearson r |
|---|---:|
| band 6 vs GeoDAWN **total count** | **0.9971** |
| band 6 vs GeoDAWN K | 0.8817 |
| band 6 vs the same file's own TMI (band 14) | −0.0409 |
| band 6 vs TMI horizontal gradient (band 3) | −0.1624 |

**Spearman ρ(band 6, total count) = 1.0000** on a 1-in-37 subsample. Band 6 ranges 2.95–88.57 with a median of 18.5. Severity **high**: anyone who takes band 6's description at face value builds a "magnetic tilt" feature out of radiometrics. Carried into hypothesis H55-C so it does not treat band 6 as a magnetic derivative.

## IR-H55-02 · Local format validation and the reported portal range error are separate

The old local validator required `nodata = NaN`; that implementation was changed to inspect both zero-outside and NaN-outside encodings. The owner-mirrored B2 TIFF is all-finite with zeros outside and `nodata` unset, but its association with a 0.2778 organizer score remains unverified. A locally all-finite raster with values in `[0,1]` passes the corresponding local range check; this does **not** prove that this encoding caused or fixes the user's reported portal error, since the exact uploaded bytes and organizer-side validation response are not available.

**Current H56B caveat:** the primary zero-outside artifact passes local core grid/dtype/range checks, but differs from the public problem-page null/NaN outside-footprint wording. A NaN-outside twin preserves in-footprint values; portal acceptance of either encoding is untested. Do not call either “portal-safe,” “accepted,” or immune to all rejection. See [`h56b-metric-erratum-20261007.md`](research/h56b-metric-erratum-20261007.md). Severity **high**.

## IR-H55-03 · Dense-backbone pixel count and inverse “truth yield” claim

The H19-5 mirror's positive-cell count was measured as 121,131 in a historical audit; this is a local raster count. The accompanying estimate of truth yield from its owner-reported 0.1922 score used the invalid `FPw=S−TPw` substitution and is withdrawn. No total hidden truth count or “binding ceiling” follows from those calculations. See the [metric erratum](research/metric-identity-erratum-20261007.md). Severity **high**.

## IR-H55-04 · SGMC proxy vs an owner-reported score

A separate owner-maintained registry associates a 44,090-cell SGMC-derived file with a reported 0.0512 score. No organizer receipt verifies the exact file-to-score link. The historical conversion of 0.0512 to `T=1,026` or to an expected score “near 0.26” is invalid because it used the false identity `FPw=S−TPw`. Keep the 0.0512 as an owner report only; it does not establish proxy validity, hidden truth density or a contradiction between public and private labels. Public-proxy results remain useful for conditional comparisons but cannot establish private-label performance. Severity **high**.

## IR-H55-05 · Catalogue-lift ratios and threshold validity

| source/proxy layer | historical count | historical catalogue-coverage ratio | current interpretation |
|---|---:|---:|---|
| H19-5 backbone | 121,131 positive cells | 0.1007 | Raster measurement only; any inverse `T` value is withdrawn. |
| SGMC faults | 83,593 positive cells | 0.1418 | Public proxy coverage statistic; not a private-truth yield estimate. |
| GDR wells/springs, all | 12,570 positive cells | 0.1023 | Historical statistic; not a measured private-label yield. |
| GDR wells/springs, Hot | 929 positive cells | 0.1897 | Historical statistic; not a measured private-label yield. |
| INGENIOUS Quaternary fault centroids | 1,125 positive cells | 0.3696 | Historical statistic; not a measured private-label yield. |

The prior claim that these ratios imply a live-score ordering, or invalidate H52's ≥2× catalogue-lift criterion by comparison with hidden truth, depended on the invalid inverse. H52's reported lift criterion is a historical preregistered screen, not a calibrated score rule; H52's spatial public-proxy test failed and no slot was cleared. Severity **high**.

## IR-H55-06 · Competing hidden-truth calibrations

Historical modules contain inferred `|G|` values of 12,632 and 14,027.5, produced from owner-reported scores under different assumptions. Neither value is established as the competition's hidden-label count: both calibrations depend on the invalid `FPw=S−TPw` substitution and unverified score-to-file attribution. They remain in old code/receipts to preserve history, not as current facts or inputs to promotion. The `14,307` value used by the old Gate-2 density-matching script is likewise invalid as a verified hidden-truth count. Severity **high**.

## IR-H55-07 · A tracked local mirror and its published upstream mirror are pixel-identical but byte-different

`data/raw/ref_h36_1_rung30.tif` (SHA-256 `7c74270a…`) and the GEMSDOE28 published file `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` (SHA-256 `5556aa14…`) have **identical emission pixel sets** (`np.array_equal` on the boolean mask, 37,660 px) and differ only in outside-footprint encoding and tags. The same holds for `data/raw/tip_h32_1_prethin_tip_euler.tif` (`26748e4b…`) versus `04d31922…` (42,294 px).

**Action:** `live_model.LIVE_ARTIFACTS` now points at the restored *published* mirrors under `data/raw/scored/` so every pin is the published one, with the pixel-identity check recorded in a code comment. `scripts/calibrate_live_model.py` fails closed on any pin mismatch. Severity **low**, but it is exactly the kind of thing that makes a "verified" hash meaningless if unnoticed.

## IR-H55-08 · `h52_scarp3m_100m.tif` band `facing_at` has unconfirmed units

`strike_at` takes only the values 0, 1500, 3000, …, 16500 — consistent with a strike in 0.01° units quantised to 15° bins over 0–165°. `facing_at` ranges 0–10,000 with a median of 4,893. If `facing_at` were a dip direction in the same units the two should be perpendicular; the measured median deviation from perpendicularity over all 5,900,588 valid cells is **46°** (p10 8.9°, p90 81.4°), i.e. no perpendicular relationship at all.

**Action:** an along-strike extension of the hydrothermal conduit anchors was designed and then **withdrawn** rather than shipped on an unverified band. Recorded as the blocker on hypothesis H55-D with the exact check required: re-read `src/gemsdoe48/scarp3m.py` and `data/external/h52_scarp3m_merge_log.txt` against the GitHub Actions run that produced the mosaic. Severity **medium** — this is a case of refusing to guess.

## IR-H55-09 · The brief's "0.3195 is the highest score right now" is stale

A single manual official leaderboard observation on 2026-10-07 (`docs/data/leaderboard_20261007.json`) showed #1 xiaofanhu 0.3774, #2 alexoktaba 0.3345, #3 nchuzhoy 0.3262, #7 DARD 0.3195, and a 0.2778 row for `extradr19` at #13 (11 submissions). This dated snapshot corrects the stale claim; ranks may change. Any H55 statement that board rows were unreachable from a corridor field at any mass, or any “0.2843 ceiling,” is invalidated by the metric erratum. Severity **medium**.

## IR-H55-10 · No organizer score exists for any local artifact

`registry/live_scores.json` is an owner-maintained registry; labels such as `OWNER-REPORT` do not constitute an organizer receipt. The local B2 source audit says `UNSCORED`. No organizer response identifies exact local TIFF bytes or links them to a public leaderboard row. H55's inferred `|G|`, `ρ`, inverted `T` values and live-equivalent scenario bands are invalid historical outputs, not owner-derived measurements or projected leaderboard positions. No organizer score is claimed for any local file. Severity **high**.

## IR-H56-01 · Local B2 attribution and the producer's own UNSCORED label

A historical source-page note for the B2 artifact reports a projected value and explicitly labels the local file `UNSCORED`; the SHA-pinned local copy matches that owner's mirrored artifact bytes. The exact 0.2778 leaderboard association remains unverified. The producer's projection is also not a valid score estimate because its underlying inversion uses `FPw=S−TPw`. This strengthens the no-attribution caveat; it does not establish any local B2 score or change the current proxy results. Severity **high**.

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

## IR-H58-01 · A "new" pairing was not new (H48-1 already fused B2 × tip H32-1 with the flank rule)

**Severity: high (process).** On 2026-10-08 I first described the B2 × tip H32-1 Dempster pairing as untried. It was already built as `docs/downloads/gemsdoe48-h48-1-ds-fusion-b2xh32tip-20261006-407bb7f4-zeros.tif` (H48-1, 37,754 binary dots, zero within 200 m of the catalogue; receipt `docs/downloads/receipt-…json`). The first scan missed it. Corrected in [`h58-results-20261008.md`](research/h58-results-20261008.md) §2. A flank-pruned DS variant (H58-B) was built and then **removed**: its support has Jaccard 0.982 with H48-1, so it is not unique. Its scores are kept, labelled as a duplicate, in `evidence/h58_flank_transfer_explore_20261008.json`.

## IR-H58-02 · The repository's "catalogue proxy" scores the faults the organizers mask

**Severity: high.** The organizers mask pixel-exact known faults from scoring (forum clarification, 2026-09-21). The catalogue proxy (`src/gemsdoe48/holdout.py` docstring, and the "catalogue labels" rows in `docs/research/h57-results-20261007.md` and the H49 reference) uses the catalogue itself as truth, so it scores recovery of the very pixels that are excluded. It cannot measure new-fault prediction. The SGMC off-catalogue proxy is the closer target, but it is also a public map and not expert labels. Preserved for history. Do not use the catalogue proxy as a gate.

## IR-H58-03 · Leaderboard snapshot disagrees with the live page for ranks #4–#6, and the board is moving

**Severity: medium.** The repository snapshot `docs/data/leaderboard_20261007.json` disagrees with the live page for ranks #4–#6. On 2026-10-08 the live page showed joeyfezster 0.3260 (#4), kinghorton42 0.3222 (#5), and Batik Shirt Brothers 0.3221 (#6). The new verified snapshot is [`docs/data/leaderboard_20261008.json`](data/leaderboard_20261008.json) (rows #1–#22; row #23 cut off in the read). Ranks change between reads, so every leaderboard claim needs a dated snapshot.

## IR-H58-04 · Stale "highest score" framing and an unlinked 0.2778 row

**Severity: medium.** The brief describes 0.3195 as the highest score. On 2026-10-08 it is rank #7. Rank #1 is 0.3774. The 0.2778 row is `extradr19` at #13. Rank #12 (`op01`, 0.2797, submitted about 10 min before the read) is above it. No local file is proven to be the submission behind the 0.2778 row (see IR-H55-01 for the original caveat).

## IR-H58-05 · `data/raw/sample_submission_template.tif` is not an all-absence sample

**Severity: medium.** The repository treats this file as a sample. It contains **60,988 positive cells, exactly the catalogue** (`np.array_equal(template > 0, labels > 0)` is true). The official sample is described as predicting total absence. Anyone who builds from this template inherits the known-fault mask. Verify against the organizers' own sample before relying on it.

## IR-H58-06 · "Immune to the portal's range error" is an overclaim

**Severity: medium.** `docs/research/h51-h50b-results-20261007.md` says the zeros primary "is immune to the portal's ‘Predicted values must be in range [0, 1]’ rejection by construction". The H58 validator records `portal_range_error_immune: true` only for the all-finite file, and only as a local statement. The NaN twin is recorded as `false`. Neither encoding has portal acceptance evidence. The official text asks for null/NaN outside the bounds, and a zeros encoding does not follow that text.

## IR-H58-07 · A withdrawn density constant is still the holdout default

**Severity: medium.** `src/gemsdoe48/holdout.py` still defines `HIDDEN_TRUTH_PX = 12632` and uses `HIDDEN_DENSITY` as the default in `evaluate_pair`. The metric-identity erratum withdrew the inversion that produced this number. The constant is still in code. It should be removed or labelled as a sensitivity grid point, not a measured density.

## IR-H58-08 · Name collision: "H56-B" means two things

**Severity: low.** `docs/research/hypotheses-h56-20261007.md` plans **H56-B**, a basement-step gravity signal. The DS artifact `GEMSDOE48-H56B` is a different object. Use the full names in any new record.

## IR-H58-09 · Gravity-edge preregistration: budget infeasible; mask mismatch

**Severity: low, but it changes the comparison.** The frozen budget of 37,654 could not be met. Only 12,600 eligible off-catalogue maxima exist. The emitted mass is one-third of the budget, so the comparison is not mass-matched. In addition, band 13 has 3,061 footprint cells without a finite gravity value. The preregistration's exclusion rule (step 1) handles them, and the count is recorded. Result: NOT CLEARED. The exploratory mass-matched check at 12,600 cells is labelled as post-gate. Receipt: `evidence/h58_gravity_edge_holdout_20261008.json`.

## IR-H58-10 · The owner's pruning gain is not reproduced by the proxy

**Severity: high for attribution.** The owner ladder gives +0.0070 for the 0.2708 → 0.2778 step (flank pruning). On the SGMC off-catalogue proxy the same step gives +0.00009 at 62,122 px, +0.00085 at 25,000 px and +0.00124 at 12,632 px. The direction is reproduced, but the magnitude is not, at any tested density. Possible causes, none verified: the hidden truth is much sparser or located differently; the owner's numbers are not comparable; or flank dots carry damage-zone credit the proxy cannot see. The explanation stays open.

## IR-H58-11 · The Dempster output ranks almost like the average inside its support

**Severity: medium.** The brief asks that the combination not be the naive average. Inside the emission support, H58-A's Spearman against the kernel-credit mean is **0.99998**, and the top-37,654 Jaccard is 0.984. The disagreement is visible in magnitudes (mean absolute difference 0.0226, maximum 0.270) and in the separate K and m(Θ) layers, not in the ranking. Disclosed in `evidence/build_h58_receipt_20261008.json` (`not_average_checks`) and in the results note §5.

## IR-H58-12 · The uniqueness checker's companion rule and maximum are weak

**Severity: low (tooling).** `scripts/check_candidate_uniqueness.py` identified companion files by name prefix only, so a candidate's NaN twin and its diagnostic layers were flagged as duplicates of the candidate. It also reported the maximum by raw overlap cells, not by Jaccard. A `--companion-token` option and a `max_jaccard_excluding_companions` field were added. Existing receipts keep their original fields and are unchanged.

## IR-H58-13 · The training feature stack is an owner mirror

**Severity: medium.** `data/raw/training_features.tif` (SHA-256 `4371c82e…`) was restored from the repository's pinned GitHub owner mirror, not from an organizer-authenticated source. It was used only for the H58-G1 test. The band names and descriptions were checked in the file. The file carries no units tags, so units are not verified.

## IR-H58-14 · Process: output-name variable shadowing (caught, fixed)

**Severity: low.** During the first H58 build, a loop variable reused the name `name`, which made the output files `both-…` and wrote the wrong receipt names. It was caught by listing the output directory, the bad files were deleted, and both variants were rebuilt. The shipped H58-A bytes are the same as the first correct build (SHA-256 prefix `b92ba079`). No shipped file was affected.
