> **HISTORICAL H53 SLATE — NOT CURRENT PROMOTION GUIDANCE.** The dated public-proxy results remain in their separate reports. The owner-reported live-ladder inversion, inferred hidden-truth mass, universal `0.2·DTI` removal bar, and claims that higher live scores require new signal are invalid under the [metric-identity erratum](metric-identity-erratum-20261007.md). The current research slate is [H57](hypotheses-h57-20261007.md); this page preserves H53 preregistration and planning priors only.

# Research slate H53 — 2026-10-07 UTC (preregistered BEFORE any H53 proxy scoring)

**Historical preregistration record.** All constants in §3 were frozen before any H53
candidate was scored on any proxy. Label-free distribution quantiles of the
lidar product (§3) were read to set ramp anchors; no proxy label was touched
before freezing. The unique files built from this slate are
`GEMSDOE48-H53-3SRC-DS-20261007-<sha8>-nan-outside.tif` (graded, primary) and
its pignistic budget-matched binary twin. This session's work is labelled
**H53** to avoid collisions with the concurrent H50/H50-B/H51/H52 labels.

## 1. Standing results this slate builds on (all receipts in `evidence/`)

* The owner-reported A/B/C score/count ladder is retained as an attribution-unresolved report. The former hidden-mass, credit-per-dot and removal-threshold interpretation used the invalid `FPw=S−TPw` identity; catalogue-adjacent pruning remains a plausible mechanism only, not a demonstrated explanation. See the [metric erratum](metric-identity-erratum-20261007.md) and [attribution analysis](why-02778-and-ceiling-20261007.md).
* The tested H48/H50/H51 two-source rules did not beat their better parent on the recorded public proxies. This does not establish that every fusion strategy fails on private labels or that a higher organizer score requires a particular type of signal. See the dated [H50/H51 results](h51-h50b-results-20261007.md).
* H52 (C + 2,000 native-lidar scarp dots) failed its gate: 0.096409 vs H49
  0.100751 on the shared SGMC proxy; the v1 detector's region-wide value is
  its terrain class, not its step height
  (`docs/research/holdout-h52-results-20261007.md`).
* Current blocked best: H49 Yager/pignistic, 0.100751 (SGMC newer,
  >300 m off-catalogue, 4-quadrant core+halo). No organizer score exists for
  any file in this repository; no weekly slot is cleared.

## 2. Ranked hypotheses (all new — none implemented in this repo or siblings)

| Rank by expected DTI | ID | Layers / physical signature | Why off-catalogue | How it differs from prior work | Expected DTI / cost / data |
|---:|---|---|---|---|---|
| 1 | **H53-2 scarp detector v2** (next step, not this session) | Same USGS 3DEP 1 m tiles (zone 11 + missing zone-10 strip): dual-baseline offset consistency (±21 m AND ±42 m must agree), relative step test (0.3–1.5 m) in the smooth-basin class (σ_ctx < 0.3 m), ≥ 500 m connected-component line tracing at 3 m, playa/agricultural exclusion by strike-cardinality + NLCD cultivated classes | Rejects the canals/road cuts/terrace risers that pollute v1 heights while recovering subtle basin scarps v1's absolute-height ranking misses | v1 uses one baseline, an absolute height floor, and 150 m averaging; no sibling emits a consistency-gated relative-step map | Highest expected gain (directly targets H52's measured failure mode); medium–high cost (≈ 1 h free CI re-run). Data obtainable: USGS 3DEP public S3 bucket, no login (precedent: H52 runs 37561683197/37565284104); NLCD 2021 free from MRLC (mrlc.gov), no login |
| 2 | **H53-1 three-source adaptive Dempster fusion** (implemented + validated this session) | (A) dotted B2 kernel-credit belief, (B) tip H36-1 kernel-credit belief, (L) line-persistent lidar scarp height `h_gate12` (σ<1.2 m gate) ramped to a graded belief; per-pixel reliability discount by terrain class (context-dependent discounting) | Lidar resolves unmapped piedmont/basin scarps invisible to the 100 m geophysics both families were built from; the discount map admits ignorance (low reliability) where the detector is unproven instead of asserting counter-evidence | First 3-source fusion anywhere in the campaign (all prior fusions are 2-source); first context-dependent (per-pixel) reliability discount (all prior builds use scalar ρ); first fusion to add new-sensor information rather than re-weight the same two surfaces | Small/uncertain gain: every 2-source fusion lost to its parents, but a new-source fusion is untested — this is the experiment. Low cost (all inputs committed and SHA-pinned) |
| 3 | **H53-3 drainage-deflection detector on the 3 m DEM** | Same 3DEP tiles: channel long-profiles extracted from the DEM itself, aligned knickpoints, systematic lateral deflection vectors | Strike-slip or low-rate faults leave deflected channels with no preserved scarp; fluvial geometry is independent of mapped-fault proximity | H48-4 proposed this with NHDPlus vectors (never implemented); H53-3 derives channels from the 3 m DEM already in hand | Uncertain (no pilot measurement); medium–high cost. Data obtainable via the same CI path as H53-2 |
| 4 | **H53-4 U/K halo tie-break for additions** | GeoDAWN radiometric mirror `data/source_mirrors/geodawn_rad_u8.tif` (K/Th/U/TC, official USGS DOI 10.5066/P93LGLVQ, SHA-verified): eU/K ratio as a hydrothermal-alteration halo proxy | A buried/eroded fault can keep a geochemical halo after its scarp is gone | 15GEMSDOE used alteration as a *generator*; H50-B crossed alteration with conflict corridors (negative result, 0.019); H53-4 would only *order* lidar additions, never generate or veto them | Historical planning prior was small; the measured 1.43× top-20% catalogue-proximity lift is a feature-screen statistic only. The old ≈2.6× removal comparison is invalid; low implementation cost (mirror committed) |
| 5 | **H53-5 NLCD exclusion + Quaternary-alluvium validation proxy** | NLCD 2021 land-cover (cultivated/open-water classes) to mask playa/agricultural false positives; a held-out subset of public-catalogue *Quaternary* traces in alluvium (σ_ctx < 1.2 m, > 1 km from SGMC bedrock faults) as a scarp-like proxy | Removes non-tectonic linears from future additions; gives lidar candidates an instrument that does not reward bedrock faults by construction (the documented SGMC-proxy bias) | No sibling uses land-cover masking or an alluvium-conditioned proxy | ≈ Zero direct DTI; enables future validation. Low–medium cost (NLCD via CI; sandbox allowlist excludes mrlc.gov) |

Not viable without new external data: OPERA InSAR displacement gradients
(Earthdata login required; sandbox cannot authenticate) — recorded so it is
not re-proposed. Geodetic strain-rate grids for dot-density modulation
(H52-3) are blocked on the login-walled official `training_features.tif`
unless a public strain grid (e.g. Kreemer et al. GSERM) is verified
obtainable; not proposed as viable today.

## 3. Frozen H53-1 constants (fixed before scoring; builder enforces them)

Label-free anchors only (distribution of `data/external/h52_scarp3m_100m.tif`
over the 3,657,635 covered in-footprint cells; no proxy labels involved):

* `H_LO = 1.0 m` (≈ q80 of covered `h_gate12`; above the 0.26 m median
  small-offset noise), `H_HI = 2.8 m` (= q99; saturates the top-1 % heights,
  max 4.12 m). Lidar belief `b_L = clip((h_gate12 − H_LO)/(H_HI − H_LO))`
  where `cover ≥ 0.9` and finite, else 0.
* Reliability map `a_L`: **0.75** where covered and `σ_mean < 1.2 m`
  (54.8 % of covered cells; the class with 2.3–3.2× pilot lift and the only
  class where the detector is evidence rather than noise — set below the
  0.95 family ceiling because a detector is not a validated family);
  **0.25** where covered but rough (detector unproven → mostly ignorance);
  **0.05** where uncovered/non-finite (near-vacuous; admits ignorance).
* Family reliabilities keep the H50 live-anchored scheme:
  `a_A = 0.95`, `a_B = 0.95 × 0.2710/0.2778 ≈ 0.9268` [OWNER-REPORT ratio].
* Rule: canonical normalized Dempster (Dempster 1967; Shafer 1976) applied
  sequentially `(A ⊕ B) ⊕ L` (associative; order is documentation only).
* Primary submission: `Bel_ABC(F) / max(footprint)` graded in [0,1], float32,
  NaN/nodata outside. Binary twin: pignistic `BetP = Bel + m(Θ)/2` top-37,654
  (parent-A-mass-matched budget), NaN outside.
* Naive-mean baselines for the not-an-average check: mean of the three belief
  surfaces and mean of the two family beliefs (both max-normalized).

## 4. Pre-registered H53-1 validation gate (before any slot)

1. Score the primary graded file AND the binary twin with the identical
   4-quadrant core + 300 m halo protocol on the newer-SGMC >300 m
   off-catalogue proxy (`scripts/run_spatial_holdout.py`), plus the
   raw-SGMC sensitivity (`--allow-unpinned-sgmc`).
2. Comparators: H49 (0.100751, current blocked best), prior union decision,
   both parents, arithmetic mean.
3. Slot rule: no slot unless a candidate beats H49 on the SGMC-newer mean
   AND on ≥ 3/4 folds with same-direction raw-SGMC sensitivity, exactly as
   H52's gate. Stated expectation: likely fails (all prior fusions lost to
   their parents); the experiment's value is testing whether a *new-source*
   fusion breaks that pattern.
4. Regardless of outcome, publish: primary + twin + `m(Θ)`/`K_AB`/`K_(AB)L`
   diagnostics, build receipt, uniqueness audit, format audits, and this
   slate's results note. Label files honestly (scored-proxy values are
   public-proxy diagnostics, never organizer scores).

## 5. Sources (official, read or cited with dated access)

* Metric, labels, submission format: <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> (repo-held reading; sandbox allowlist excludes drivendata.org, so no fresh fetch this session — see irregularities).
* Known-fault pixels masked from scoring: <https://community.drivendata.org/t/11516>; no further test-fault detail: <https://community.drivendata.org/t/11527/7> (prior-session reads).
* USGS 3DEP 1 m staged products (public domain, no login): <https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/> (bucket URLs per tile in `registry/dem_tiles_pilot.json`; H52 CI precedent).
* GeoDAWN airborne radiometrics: USGS DOI [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ) (mirror SHA `c22420f7…` restored byte-identical from GEMSDOE24).
* Scarp physics: Bucknam & Anderson (1979) *Geology* 7, 11–14; Hanks et al. (1984) *JGR* 89, 5771–5790; Hilley et al. (2010) *GRL* 37, L04301.
* DS theory: Dempster (1967) "Upper and Lower Probabilities Induced by a Multivalued Mapping", *Ann. Math. Statist.* 38, 325–339 (doi:10.1214/aoms/1177698950); Shafer (1976) *A Mathematical Theory of Evidence*, Princeton Univ. Press; contextual discounting: Mercier, Quost & Denœux (2005) "Contextual Discounting of Belief Functions", ECSQARU 2005, LNCS 3571 (<https://link.springer.com/chapter/10.1007/11518655_47>), refined at IPMU 2006 — discount rate varying with source context. All three verified by web search 2026-10-07.
* NLCD 2021 Land Cover (CONUS): <https://www.mrlc.gov/> (Multi-Resolution Land Characteristics Consortium; dataset doi:10.5066/P9JZ7AO3; free direct download, no login; not fetched — sandbox allowlist excludes mrlc.gov; CI path only).
