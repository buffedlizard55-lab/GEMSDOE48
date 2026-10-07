# Research slate H50 — 2026-10-07 UTC

**Status: pre-registered before any weekly slot is considered.** *Addendum 2026-10-07 (after measurement, text below unchanged): the H50-1 gate in §4 was applied and **failed** on both criteria — see `holdout-h50-results-20261007.md`. The unique file `GEMSDOE48-H50-lidar-scarp-additions-20261007-38029417f6ca-nan-outside.tif` is published as not slot-cleared.* This session started from the previous session's open items (`docs/next-steps.html`): N1 native-resolution lidar extraction, measured lift tests for the 2 m u8 scarp descriptors and the official 19-band `training_features.tif`, an exact inversion of the live submission ladder, and only then a new candidate. Every number below is reproduced by a script in `scripts/` and stored in `evidence/`; nothing is quoted from memory.

## 1. What the live ladder says (exact metric algebra, no model)

`scripts/live_ladder_analysis.py` inverts the three nested live scores of the dotted family with the metric's own algebra (`DTI = T/(0.2T + 0.2FP + 0.8|G|)`; removing `n` empty dots gives `1/s_before − 1/s_after = 0.2n/T`; verified on synthetic data to ~1e-16):

| Rung | Dots | Live DTI | What changed |
|---|---:|---:|---|
| A `dotted_d2_8_02600` | 44,090 | 0.2600 | Poisson-disk dots, d = 2.83 px |
| B `dotted_d2_8_02708` | 40,199 | 0.2708 | A minus 3,891 dots within 100 m of the catalogue |
| C `dotted_b2_prune_02778` | 37,654 | 0.2778 | B minus 2,545 dots 100–200 m from the catalogue |

Both removals are consistent with the removed dots carrying ~zero credit (T/π = 5,073 from A→B and 5,470 from B→C, 7.5 % apart). Consequences (`evidence/live_ladder_20261007.json`):

* Hidden-truth kernel mass |G|/π ≈ 14,300; C recovers ≈ 37 % of it (T/π ≈ 5,270); the average C dot carries 0.14 of a full hit.
* A new dot is worth adding only if its expected kernel weight exceeds 0.2·DTI ≈ 0.056, i.e. 40 % of the average C dot. A dot is worth removing only if it carries less than that.
* Reaching 0.3774 at the same mass needs +36 % recovered truth (recall ≈ 0.50); 0.3345 needs +20 %; 0.3262 needs +17 %. No re-weighting of existing dots can do this — only *new information about where the hidden faults are*.

## 2. Measured negative results that shape the slate (do not re-run)

| Test | Instrument | Result | Evidence |
|---|---|---|---|
| 2 m u8 lidar descriptors (`lidar_scarp_features_u8.tif`, 12 bands) as a per-dot re-ranker of the 44,090 A dots | hit = dot ≤100 m from the catalogue; lift of the top-20 % vs the A average | step/upface/exm ≤ 0.91× (negative); as pixel rankers vs the catalogue AUC 0.49–0.59 | this session (numbers also in `docs/irregularities.md` §band-6 note) |
| 19 official `training_features.tif` bands, single-band top-tail lift vs the catalogue | near-rate ≤100 m, base 0.0355 | only geodetic 2nd-invariant (top 0.5 %: 4.7×) and U/K ratio (2.2×) exceed 1.5×; detrended elevation top-tail 0.00× | this session |
| Per-dot re-rankers on A (`−dist SGMC`, U/K, grav_slope, geod_2ndinv, K, det_elev, lidar) | top-20 % lift vs A average, per quadrant | −dist SGMC 2.34× (circular: SGMC shares the catalogue's faults); U/K 1.43× (1.24–1.56 across quadrants); grav_slope 1.38×; all others ≤ 1.26×. None reaches the ≈2.6× needed for a profitable removal (§1) | this session |

Conclusion: at 100 m resolution no available layer separates the dotted family's dots strongly enough to pay for a removal or an addition. The only lever left is **new, higher-resolution information**, which is what H50-1 provides.

## 3. Ranked hypotheses

| Rank | Hypothesis | Layers / physical signature | Why off-catalogue | How it differs from this repo and the sibling campaigns | Expected DTI gain / cost / data status |
|---:|---|---|---|---|---|
| **1 — implemented and pilot-validated** | **H50-1 native-lidar linear scarp detector** (`src/gemsdoe48/scarp3m.py`) | USGS 3DEP 1 m DEM (NV_WestCentral_EarthMRI_2020_D20 and the other zone-11 projects in `registry/dem_tiles_pilot.json`), block-averaged to 3 m. Per 3 m pixel: detrended surface `z_6m − z_60m`; for 12 strikes the mean far-field offset across a ±21 m baseline averaged along a 150 m strike-parallel line (`H`, metres); strike; facing relative to the regional slope; context roughness `σ_ctx` (150 m window). Scarp candidates are *steps that persist along strike inside smooth terrain* (`σ_ctx < 0.7–1.2 m`). | The test truth is "faults experts identified that are not in USGS/INGENIOUS" (organizer page 967); participants' public discussion and the geometry of the catalogue in the pilot hillshade both point to subtle piedmont/basin scarps that only lidar resolves. A 0.5–3 m step persisting for >300 m in alluvium with no channel is the textbook lidar signature of a young fault (Bucknam & Anderson 1979; Hilley et al. 2010). | The repo's existing lidar product (2 m u8 descriptors, 12 bands) aggregates *per-pixel* step/slope statistics to 100 m and is dominated by bedrock texture (lift ≤ 1×). H50-1 adds the three ingredients a mapper uses — along-strike persistence, far-field offset rather than local slope, and a smooth-context gate — at 3 m, before aggregation. 7GEMSDOE's region-wide DEM workflow produced a different (unpublished) feature set; nothing in the sibling list emits a line-persistent scarp height. | **Pilot (two 10 × 10 km tiles, `evidence/h50_pilot_scarp_eval_20261007.json`):** top-2 % cells of the σ-gated height carry **2.3–3.2× the catalogue-adjacency rate** of the covered area in both tiles, versus ≤ 1× for every u8 descriptor on the same cells and ≤ 1× for the ungated score. The smooth-piedmont gate alone (σ_ctx 0.4–1.2 m) has 2.0–2.3× lift. Cost: a hosted CI run over all 716 zone-11 tiles (`.github/workflows/dem-region-scarp.yml`, ~1 h wall clock, free) — launched this session; the sandbox cannot reach USGS hosts. Verified obtainable: both pilot sources downloaded with SHA-256 in `data/pilot/dem3m/dem_pilot_receipt.json`. |
| 2 | **H50-2 radiometric alteration-contrast corroboration (U/K)** | GeoDAWN airborne radiometrics (K, Th, U; ratios eU/K). Fault zones in the Great Basin channel hydrothermal fluids that leach K or deposit U; the catalogue's traces sit preferentially on high eU/K cells. | A buried or eroded fault may keep a geochemical halo at the surface after the scarp is gone. | 15GEMSDOE combined alteration with magnetics as a *generator*. H50-2 only re-ranks existing dots. | Measured 1.43× top-20 % hit lift on A dots (consistent across quadrants), 2.2× top-0.5 % on the catalogue — real but ~2× short of the removal bar (§1). Zero data cost (already mirrored and hash-verified). Keep as a tie-breaker inside H50-1 additions, not as a stand-alone candidate. |
| 3 | **H50-3 geodetic strain-rate modulation of dot density** | Official bands: dilatation, shear, 2nd-invariant strain rate. Active faults cluster where present-day strain is accumulating. | Strain is independent of whether a fault was ever mapped. | GEMSDOE51 used a strain budget as a generator; here it would modulate the *density* of dots per 10 km block. | Top-0.5 % catalogue lift 4.7× but only 1.10× as a per-dot re-ranker (SW/SE 1.3–1.5×). Regional, not trace-level — it can tell where to spend FP budget, not where the trace is. Low cost; expected gain small; test only after H50-1. |
| 4 | **H50-4 drainage-deflection / knickpoint detector on the 3 m DEM** | Same DEM tiles: channel long-profiles, aligned knickpoints, systematic lateral deflections. | Strike-slip or low-rate faults leave deflected channels without a preserved scarp. | H48-4 proposed it with NHDPlus; H50-4 would derive channels from the 3 m DEM itself (now available via the same CI path). | Medium–high cost, uncertain; only after H50-1 is scored. |
| — | InSAR (OPERA DISP-S1) | — | — | — | **Not viable**: requires an Earthdata login; the sandbox cannot authenticate or reach the host. Recorded so it is not re-proposed. |

## 4. Pre-registered H50-1 validation gate (before any slot)

1. Build the region-scale 100 m product `data/external/h50_scarp3m_100m.tif` by CI (receipt with per-tile source SHA-256 and the run URL).
2. Candidate construction (`scripts/build_submission_h50.py`): keep C (37,654 dots) unchanged; add Poisson-spaced dots on cells where the σ-gated line-persistent height exceeds a quantile threshold, outside 200 m of the catalogue, outside 300 m of existing C dots, with the number of additions swept (so that the holdout can locate the break-even).
3. Score on the identical 4-quadrant core + 300 m halo protocol with the newer SGMC >300 m off-catalogue proxy (`scripts/run_spatial_holdout.py`), against union, C, T and H49 (0.100751). Also record the raw-SGMC sensitivity.
4. Slot rule: no slot unless the candidate beats H49 on the mean and on ≥ 3/4 folds **and** the additions' catalogue-adjacency lift is ≥ 2× in all four quadrants of the lidar footprint (a stricter, label-free second check). If the region run does not finish inside this session, the session's unique TIF carries only the pilot-area additions and is labelled *not slot-cleared*.

## Sources (official, read this session)

* Problem description, metric, GeoTIFF format: <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>
* Organizer statements that known-fault pixels are masked from scoring: <https://community.drivendata.org/t/11516> (chrisk-dd, 2025-09-16) and that no further detail on the test faults will be given: <https://community.drivendata.org/t/11527/7>
* USGS 3DEP 1 m staged products (bucket URLs recorded verbatim per tile in `registry/dem_tiles_pilot.json`; project NV_WestCentral_EarthMRI_2020_D20): <https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/> — public domain, no login.
* Scarp degradation physics: Bucknam & Anderson (1979) *Geology* 7, 11–14; Hanks et al. (1984) *JGR* 89, 5771–5790; Hilley et al. (2010) *GRL* 37, L04301.
