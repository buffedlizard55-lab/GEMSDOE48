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

## IR-H55-02 · The repository's own format validator rejected the encoding used by its highest-scoring artifact

`scripts/validate_submission.py` required `nodata = NaN` and raised `SystemExit` otherwise. But `data/families/dotted_b2_prune_02778.tif` — the 0.2778 live-best — is **all-finite with zeros outside and `nodata` unset**: verified by reading the bytes (0 NaN cells of 12,279,160, min 0.0, max 1.0) and corroborated by `data/raw/audit-h33-2-b2.json`, which records `nodata: null` and `validator_range_0_1_guaranteed: true`. The organizers' own reference solution (`gems-prize-reference-solution`, notebook cell 19) also writes an all-finite float32 raster with `nodata` unset and no NaN handling at all.

**Action:** the validator now takes `--encoding {auto,nan,zeros}` (default `auto`), accepts either encoding, reports which it found, and states the portal exposure explicitly (`all_cells_finite`, `all_cells_in_range_0_1`, `portal_range_error_immune`, `portal_range_error_note`). A new writer `write_float32_zeros_outside` was added to `src/gemsdoe48/geotiff.py`; it re-reads the written bytes and asserts the encoding rather than trusting the in-memory array. The H55 primary uses the all-finite encoding. Severity **high**.

**Root cause of the reported portal rejection:** any NaN cell makes a vectorised `np.all((v >= 0) & (v <= 1))` test evaluate to `False`, because every comparison against NaN is false — which reproduces `Predicted values must be in range [0, 1]` exactly. Both encodings have owner-reported live scores in this family tree (0.2778 zeros-outside; 0.2708 NaN-outside), so NaN-outside is not always rejected — but the all-finite encoding cannot produce the error at all and is now primary.

## IR-H55-03 · The dense backbone's pixel count *and* truth yield are both misstated in this repository's own notes

`knowledge/research_notes.md` and the README describe dense H19-5 as "129 k px" with "the same T, triple the FP". Measured from the restored hash-pinned mirror (SHA-256 `ec1f9b56…`): **121,131** positive pixels, and inverting its owner-reported live 0.1922 under the calibrated `|G| = 14,027.5` gives **T = 6,813.1 — 30.8 % higher than C's 5,209.5**, not equal. The FP part of the claim is correct; the T part is not.

Severity **high**, because the error hid the binding constraint on the whole project: the field's *total* truth content is 6,813, and #1 at 0.3774 needs `T = 7,077` — more than the dense backbone contains. Corrected in §3.2 of [`docs/research/h55-live-model-ceiling-and-candidate-20261007.md`](research/h55-live-model-ceiling-and-candidate-20261007.md). The historical notes were left in place rather than edited, so the correction is additive and auditable.

## IR-H55-04 · The SGMC off-catalogue proxy that gated every prior session is contradicted by a live score

`gemsdoe29-sgmc-off-catalogue-44k` — 44,090 px at the same 2.8 px Poisson spacing as rung A, built *directly on the proxy layer* — is owner-reported at **0.0512** live, inverting to `T = 1,026.0` against the backbone family's 5,209 at the same mass. Were the proxy a good stand-in for the hidden truth, that file would have scored near 0.26.

**Action:** the proxy is retained as a *relative* ranking device over surfaces that all contain the backbone, and the blocked holdout is still run and reported in full — but every gate decision that turned on it (H50, H51, H52) is reclassified as **unresolved rather than settled**. Nothing was deleted; the receipt trail is intact. Severity **high**.

## IR-H55-05 · Catalogue coverage per emitted pixel does not predict live truth yield

| field | px | catalogue coverage per emitted px | live T at ≈44 k px |
|---|---:|---:|---:|
| h19-5 backbone | 121,131 | 0.1007 | 6,813 (dense) |
| SGMC faults | 83,593 | **0.1418** | 1,026 (at 44,090 px) |
| GDR wells/springs, all | 12,570 | 0.1023 | not measured |
| GDR wells/springs, *Hot* | 929 | **0.1897** | not measured |
| INGENIOUS Quaternary fault centroids | 1,125 | **0.3696** | not measured |

SGMC covers known faults 41 % more efficiently per pixel than the backbone and scores 5× worse live. **The `≥ 2× catalogue lift` rule that rejected H52 is therefore not a sound screen** and is not used anywhere in this session. Severity **high**: it means H52's rejection rests entirely on IR-H55-04 plus a rule invalidated here.

## IR-H55-06 · Two different hidden-truth calibrations coexist in this repository

`knowledge/research_notes.md`, `src/gemsdoe48/holdout.py` (`HIDDEN_TRUTH_PX = 12632`), `src/gemsdoe48/live_anchor.py` and `scripts/build_site_ds48.py` all use **|G| = 12,632**, derived by assuming the removed dots earned exactly the `τ = 0.05416` bar. This session's least-squares fit over the strictly nested triple A/B/C, assuming the removed dots earned **zero**, gives **|G| = 14,027.5** — and that value makes the three rungs invert to `T = 5,210.4 / 5,216.1 / 5,209.5`, self-consistent to **0.11 %**. The three pairwise closed-form solutions are 13,368 / 15,198 / 14,089, a ±6 % spread driven entirely by the 4-decimal rounding of the owner-reported scores.

**Action:** both are recorded; 14,027.5 is used everywhere in H55 and the alternative derivation is stated. The older constants were *not* edited out of the historical modules, because those modules belong to prior sessions' receipts. Severity **medium**.

## IR-H55-07 · A tracked local mirror and its published upstream mirror are pixel-identical but byte-different

`data/raw/ref_h36_1_rung30.tif` (SHA-256 `7c74270a…`) and the GEMSDOE28 published file `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` (SHA-256 `5556aa14…`) have **identical emission pixel sets** (`np.array_equal` on the boolean mask, 37,660 px) and differ only in outside-footprint encoding and tags. The same holds for `data/raw/tip_h32_1_prethin_tip_euler.tif` (`26748e4b…`) versus `04d31922…` (42,294 px).

**Action:** `live_model.LIVE_ARTIFACTS` now points at the restored *published* mirrors under `data/raw/scored/` so every pin is the published one, with the pixel-identity check recorded in a code comment. `scripts/calibrate_live_model.py` fails closed on any pin mismatch. Severity **low**, but it is exactly the kind of thing that makes a "verified" hash meaningless if unnoticed.

## IR-H55-08 · `h52_scarp3m_100m.tif` band `facing_at` has unconfirmed units

`strike_at` takes only the values 0, 1500, 3000, …, 16500 — consistent with a strike in 0.01° units quantised to 15° bins over 0–165°. `facing_at` ranges 0–10,000 with a median of 4,893. If `facing_at` were a dip direction in the same units the two should be perpendicular; the measured median deviation from perpendicularity over all 5,900,588 valid cells is **46°** (p10 8.9°, p90 81.4°), i.e. no perpendicular relationship at all.

**Action:** an along-strike extension of the hydrothermal conduit anchors was designed and then **withdrawn** rather than shipped on an unverified band. Recorded as the blocker on hypothesis H55-D with the exact check required: re-read `src/gemsdoe48/scarp3m.py` and `data/external/h52_scarp3m_merge_log.txt` against the GitHub Actions run that produced the mosaic. Severity **medium** — this is a case of refusing to guess.

## IR-H55-09 · The brief's "0.3195 is the highest score right now" is stale

Carried forward and now answered with a measurement rather than an assertion: the single manual read of the official leaderboard on 2026-10-06 UTC (`docs/data/leaderboard_20261007.json`) shows #1 xiaofanhu **0.3774**, #2 alexoktaba 0.3345, #3 nchuzhoy 0.3262, #7 DARD **0.3195**, and the 0.2778 row belonging to `extradr19` (#13, 10 submissions). The H55 ceiling table is computed against the whole snapshot. **None of 0.2888, 0.3195, 0.3262, 0.3345 or 0.3774 is reachable from the h19-5 corridor field at any mass**; the frontier maximum is live-equivalent 0.2843. Severity **medium**.

## IR-H55-10 · No organizer score exists for any file in this repository

`registry/live_scores.json` holds 17 entries, all classed **OWNER-REPORT** — a score pasted by the repository owner against a SHA-256. No organizer receipt, API response or page capture links any file to any score; the local receipt for the 0.2778 artifact says `UNSCORED`. The H55 forward model, its `|G|`, its `ρ`, all eight inverted `T` values and the entire scenario band are therefore labelled OWNER-REPORT-derived wherever they appear, and no projected leaderboard position is claimed. Severity **high** — it is the single largest limitation on everything above.

## IR-H56-01 · The 0.2778 site itself labels its primary file UNSCORED / projected 0.2747 (re-verified at the source)

On 2026-10-07 the H56 session fetched `docs/index.html` directly from the GEMSDOE32 source
repository (`api.github.com/repos/buffedlizard55-lab/GEMSDOE32/contents/docs/index.html`). The
page's own paste-ready note for `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`
(SHA-256 prefix `c55bafc470054e82…`, byte-identical to `data/families/dotted_b2_prune_02778.tif`)
reads: *"flank B=2 prune on the 0.2708 base: 37,654 dots, 0 within 200 m of the catalogue;
live-mirror +0.00487 in 4/4 folds, safety 2.08, projected 0.2747; UNSCORED"*. The
owner-reported leaderboard row `h33-h33-2-b2…: 0.2778` therefore remains **unauthenticated
against these exact bytes** by the producing site itself; 0.2778 is the owner-reported
leaderboard association and 0.2747 is the producer's own projection. This does not change any
H56 number (the live model is anchored on the owner-reported values and states its error band),
but it hardens the standing caveat in the README. Severity **medium**.

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
