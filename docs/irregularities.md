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
