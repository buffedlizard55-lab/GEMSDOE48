# Evidence and leaderboard irregularities

This ledger separates what was directly observed from what cannot be attributed. It is intended to prevent a plausible-looking filename or owner receipt from becoming an unsupported score claim.

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
