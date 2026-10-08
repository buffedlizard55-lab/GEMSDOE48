> **HISTORICAL H52 SLATE — FORENSIC ONLY.** The former live-ladder inversion, inferred `|G|`/`T`/recall, 0.0556 threshold, and any reachability or profitability claims below are invalid under the [metric-identity erratum](metric-identity-erratum-20261007.md). The H52-1 candidate was later tested and failed its preregistered public-proxy gate; it is not slot-cleared. Preserve the dated feature/proxy observations as history, not as a current ranking or promotion basis. Use the [current H57 slate](hypotheses-h57-20261007.md) and [H52 results](holdout-h52-results-20261007.md) for current context.

# Research slate H52 — 2026-10-07 UTC

**Historical preregistration:** the slate was frozen before a weekly slot was considered. The H52-1 gate in §4 was later applied and **failed** on both criteria — see `holdout-h52-results-20261007.md`. The unique file `GEMSDOE48-H52-lidar-scarp-additions-20261007-38029417f6ca-nan-outside.tif` remains a historical artifact, not slot-cleared. This session started from the prior open items (`docs/next-steps.html`): N1 native-resolution lidar extraction, measured lift tests for the 2 m u8 scarp descriptors and official 19-band training features, plus candidate testing. The original H52 page also included a live-ladder interpretation that is invalidated below.

## 1. Owner-reported live-ladder context

The historical report included these owner-reported score/count pairs; they are not verified links to local TIFF files:

| Rung | Dots | Owner-reported live DTI | Reported change |
|---|---:|---:|---|
| A `dotted_d2_8_02600` | 44,090 | 0.2600 | Poisson-disk dots, d = 2.83 px |
| B `dotted_d2_8_02708` | 40,199 | 0.2708 | Reported removal of 3,891 dots within 100 m of the catalogue |
| C `dotted_b2_prune_02778` | 37,654 | 0.2778 | Reported removal of 2,545 dots 100–200 m from the catalogue |

### Invalid derived values from the former inversion

The historical calculation assumed the removed dots earned zero credit and used `FPw=S−TPw`. Neither assumption follows from the official metric. The following numbers from `evidence/live_ladder_20261007.json` are preserved only to audit the old calculation and **must not be cited as valid estimates**:

- `T/π`, `|G|/π`, inferred hidden-truth size or density, recall, and per-dot credit;
- the universal `0.2·DTI`/approximately `0.0556` addition or removal bar and any related profitability claims;
- projected reachability of leaderboard scores, including the old percentage-recall scenarios.

They do not provide a confidence interval or an approximate truth-density estimate. The score/count pairs above remain owner reports only; local-file identity and leaderboard linkage are unverified. See the [metric-identity erratum](metric-identity-erratum-20261007.md).

## 2. Measured negative results that shape the slate (do not re-run)

| Test | Instrument | Result | Evidence |
|---|---|---|---|
| 2 m u8 lidar descriptors (`lidar_scarp_features_u8.tif`, 12 bands) as a per-dot re-ranker of the 44,090 A dots | hit = dot ≤100 m from the catalogue; lift of the top-20 % vs the A average | step/upface/exm ≤ 0.91× (negative); as pixel rankers vs the catalogue AUC 0.49–0.59 | this session (numbers also in `docs/irregularities.md` §band-6 note) |
| 19 official `training_features.tif` bands, single-band top-tail lift vs the catalogue | near-rate ≤100 m, base 0.0355 | only geodetic 2nd-invariant (top 0.5 %: 4.7×) and U/K ratio (2.2×) exceed 1.5×; detrended elevation top-tail 0.00× | this session |
| Per-dot re-rankers on A (`−dist SGMC`, U/K, grav_slope, geod_2ndinv, K, det_elev, lidar) | top-20 % lift vs A average, per quadrant | −dist SGMC 2.34× (circular: SGMC shares the catalogue's faults); U/K 1.43× (1.24–1.56 across quadrants); grav_slope 1.38×; all others ≤ 1.26×. These are historical feature-screen statistics, not removal thresholds or DTI gain estimates. | this session |

Conclusion: these 100 m proxy feature screens reported the lifts listed above. They do not establish a per-dot break-even rule, the profitability of additions/removals, or that higher-resolution data is the only remaining path. H52-1 was subsequently evaluated on the blocked holdout and failed its preregistered gate.

## 3. Original H52 hypothesis slate (historical ordering)

| Historical order | Hypothesis | Layers / physical signature | Why off-catalogue | How it differs from this repo and the sibling campaigns | Historical expectation / cost / data status |
|---:|---|---|---|---|---|
| **H52-1 — historical rank 1; full holdout failed** | **H52-1 native-lidar linear scarp detector** (`src/gemsdoe48/scarp3m.py`) | USGS 3DEP 1 m DEM (NV_WestCentral_EarthMRI_2020_D20 and the other zone-11 projects in `registry/dem_tiles_pilot.json`), block-averaged to 3 m. Per 3 m pixel: detrended surface `z_6m − z_60m`; for 12 strikes the mean far-field offset across a ±21 m baseline averaged along a 150 m strike-parallel line (`H`, metres); strike; facing relative to the regional slope; context roughness `σ_ctx` (150 m window). Scarp candidates are *steps that persist along strike inside smooth terrain* (`σ_ctx < 0.7–1.2 m`). | The test truth is "faults experts identified that are not in USGS/INGENIOUS" (organizer page 967); participants' public discussion and the geometry of the catalogue in the pilot hillshade both point to subtle piedmont/basin scarps that only lidar resolves. A 0.5–3 m step persisting for >300 m in alluvium with no channel is the textbook lidar signature of a young fault (Bucknam & Anderson 1979; Hilley et al. 2010). | The repo's existing lidar product (2 m u8 descriptors, 12 bands) aggregates *per-pixel* step/slope statistics to 100 m and is dominated by bedrock texture (lift ≤ 1×). H52-1 adds the three ingredients a mapper uses — along-strike persistence, far-field offset rather than local slope, and a smooth-context gate — at 3 m, before aggregation. 7GEMSDOE's region-wide DEM workflow produced a different (unpublished) feature set; nothing in the sibling list emits a line-persistent scarp height. | **Pilot (two 10 × 10 km tiles, `evidence/h52_pilot_scarp_eval_20261007.json`):** top-2 % cells of the σ-gated height carry **2.3–3.2× the catalogue-adjacency rate** of the covered area in both tiles, versus ≤ 1× for every u8 descriptor on the same cells and ≤ 1× for the ungated score. The smooth-piedmont gate alone (σ_ctx 0.4–1.2 m) has 2.0–2.3× lift. Cost: a hosted CI run over all 716 zone-11 tiles (`.github/workflows/dem-region-scarp.yml`, ~1 h wall clock, free) — launched this session; the sandbox cannot reach USGS hosts. Verified obtainable: both pilot sources downloaded with SHA-256 in `data/pilot/dem3m/dem_pilot_receipt.json`. |
| 2 | **H52-2 radiometric alteration-contrast corroboration (U/K)** | GeoDAWN airborne radiometrics (K, Th, U; ratios eU/K). Fault zones in the Great Basin channel hydrothermal fluids that leach K or deposit U; the catalogue's traces sit preferentially on high eU/K cells. | A buried or eroded fault may keep a geochemical halo at the surface after the scarp is gone. | 15GEMSDOE combined alteration with magnetics as a *generator*. H52-2 only re-ranks existing dots. | Measured 1.43× top-20 % hit lift on A dots (consistent across quadrants), 2.2× top-0.5 % on the catalogue. These are proxy feature-screen results only; they do not establish a removal threshold or expected DTI gain. Zero data cost (already mirrored and hash-verified). Historical suggestion: test only as a tie-breaker within H52-1, not as a stand-alone candidate. |
| 3 | **H52-3 geodetic strain-rate modulation of dot density** | Official bands: dilatation, shear, 2nd-invariant strain rate. Active faults cluster where present-day strain is accumulating. | Strain is independent of whether a fault was ever mapped. | GEMSDOE51 used a strain budget as a generator; here it would modulate the *density* of dots per 10 km block. | Top-0.5 % catalogue lift 4.7× but only 1.10× as a per-dot re-ranker (SW/SE 1.3–1.5×). Regional, not trace-level — may help prioritize broad areas but does not identify trace locations. Low cost; historical expectation was modest; it was listed after H52-1. |
| 4 | **H52-4 drainage-deflection / knickpoint detector on the 3 m DEM** | Same DEM tiles: channel long-profiles, aligned knickpoints, systematic lateral deflections. | Strike-slip or low-rate faults leave deflected channels without a preserved scarp. | H48-4 proposed it with NHDPlus; H52-4 would derive channels from the 3 m DEM itself (now available via the same CI path). | Medium–high cost, uncertain; only after H52-1 is scored. |
| — | InSAR (OPERA DISP-S1) | — | — | — | **Not viable**: requires an Earthdata login; the sandbox cannot authenticate or reach the host. Recorded so it is not re-proposed. |

## 4. Historical H52-1 validation gate and outcome

The following criteria were preregistered for H52-1; the candidate was later evaluated and **failed both criteria** (see `holdout-h52-results-20261007.md`). They are retained as the dated record, not as current promotion guidance.

1. Build the region-scale 100 m product `data/external/h52_scarp3m_100m.tif` by CI (receipt with per-tile source SHA-256 and the run URL).
2. Candidate construction (`scripts/build_submission_h52.py`): keep C (37,654 dots) unchanged; add Poisson-spaced dots on cells where the σ-gated line-persistent height exceeds a quantile threshold, outside 200 m of the catalogue and 300 m of existing C dots, with the number of additions swept so outcomes could be compared across budgets. No break-even inference is licensed by the old inversion.
3. Score on the identical 4-quadrant core + 300 m halo protocol with the newer SGMC >300 m off-catalogue proxy (`scripts/run_spatial_holdout.py`), against union, C, T and H49 (0.100751). Also record the raw-SGMC sensitivity.
4. Historical slot rule: no slot unless the candidate beats H49 on the mean and on ≥ 3/4 folds **and** the additions' catalogue-adjacency lift is ≥ 2× in all four quadrants of the lidar footprint (a label-free second check). The measured candidate did not pass; its unique TIF is *not slot-cleared*.

## Sources cited in the original H52 session

* Problem description, metric, GeoTIFF format: <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>
* Organizer statements that known-fault pixels are masked from scoring: <https://community.drivendata.org/t/11516> (chrisk-dd, 2025-09-16) and that no further detail on the test faults will be given: <https://community.drivendata.org/t/11527/7>
* USGS 3DEP 1 m staged products (bucket URLs recorded verbatim per tile in `registry/dem_tiles_pilot.json`; project NV_WestCentral_EarthMRI_2020_D20): <https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/> — public domain, no login.
* Scarp degradation physics: Bucknam & Anderson (1979) *Geology* 7, 11–14; Hanks et al. (1984) *JGR* 89, 5771–5790; Hilley et al. (2010) *GRL* 37, L04301.
