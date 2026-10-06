> **Historical archive.** This earlier upstream page is preserved for provenance and may contain superseded claims. Do not treat it as the current submission or validation decision. See the [current overview](../../index.html) and [current validation](../../validation.html).

---

# Hypotheses H48-1 … H48-5: untried here, ranked

Ranking = expected ΔDTI on the public board ÷ implementation cost. Every "obtainable" claim was
checked in this session (method stated). Every "not in this repo family" claim was checked by
`grep` across the four sibling repos cloned this session (GEMSDOE28, 32, 33, 47). The other ~43
sibling repos were **not** grepped, so that claim is limited to those four (see IR-48-08).

| Rank | ID | Hypothesis | Expected ΔDTI | Cost | Data obtainable? | Status |
|---|---|---|---|---|---|---|
| 1 (value) | **H48-2** | Native-resolution 1 m LiDAR scarp detection | **+0.01 to +0.05** (the only idea big enough to reach 0.32+) | High (~517 tiles, ~120 GB streamed) | **Yes.** TNM API returned tiles for the footprint (USGS 3DEP, public domain) | Specified. Needs GitHub Actions; this sandbox can't reach USGS |
| 2 (cost) | **H48-1** | Dempster–Shafer fusion of dotted × tip families | −0.0003 to +0.003 | Low | Yes (in repo) | **Built and validated: TIE.** Shipped as the requested unique file |
| 3 | **H48-5** | Phreatophyte / vegetation lineaments in late-summer Sentinel-2 NDVI | +0.003 to +0.015 (basin-floor faults that have no scarp) | Medium | **Yes.** Element84 STAC `sentinel-2-l2a` collection resolved | Specified |
| 4 | **H48-3** | ComCat microseismicity alignments | ≈0 to +0.003 | Medium | **Yes.** FDSN count = 267,774 events since 2000 in bbox | Specified. Probably weak (see below) |
| 5 | **H48-4** | Truth-intensity map from the live-score inversion, used to emit | Unknown | Low | Yes | **Not viable yet.** The instrument has negative top-8 rank power |

---

## H48-1 · Dempster–Shafer fusion that keeps disagreement (implemented)

* **Layers:** `h33-2-b2` (live 0.2778, dotted family) and `h32-1-prethin-tip` (live 0.2649, tip
  family). Both derive from the H19-5 ridge backbone, which is built from the official
  `training_features.tif` topo/geophysics bands.
* **Signature:** the 300 m kernel support of each family's dots becomes a basic probability
  assignment (BPA). Dempster's rule gives `m(F)`. Conflict `K` and Yager's `m(Θ)` are kept as
  diagnostic layers.
* **Why it targets off-catalogue faults:** the tip family deliberately protects fault-tip and
  step-over continuations. These are "newly mapped geometry of an existing fault system", which
  DrivenData staff explicitly count as new faults (thread 11536). The dotted family's
  catalogue-flank veto is carried as explicit `m(¬F)`, so nothing is emitted within 200 m of the
  catalogue.
* **How it differs:** no sibling repo checked uses belief functions (`grep dempster|belief
  function` returned 0 hits). Prior unions or averages blended surfaces. This rule takes sides,
  measured in the disagreement region: Pearson against the naive mean is 0.71 there, vs 0.96
  overall.
* **Validation:** see [method](method.html). LSI instrument: 0.26336 vs b2 0.26351, a tie.
  SGMC 4-quadrant blocked holdout: better in 2 of 4 folds. **Did not beat the holdout best.**
  Downside bounded at ≥ 0.2773.

## H48-2 · 1 m LiDAR scarp detection at native resolution (top expected value)

* **Layer:** USGS 3DEP 1 m bare-earth DEM. The competition's `1m_DEM_links.csv` lists the tiles,
  and the TNM API independently returned e.g.
  `USGS_1M_11_x37y438_NV_WestCentral_EarthMRI_2020_D20.tif` (262 MB, public domain).
* **Signature:** paired profile curvature, a convex crest above a concave toe 2–20 m apart,
  computed perpendicular to the local strike at metre scale. Then scarp height and facet slope,
  with a template-matching scarp-likelihood. Detections are aggregated to 100 m. Elevations are
  not resampled first.
* **Why off-catalogue:** of the 376 USGS Qfault traces whose centroid is in the footprint,
  **359 (95.5 %) carry `map_scale = 250`** and 17 carry `100` (re-counted this session from
  `gdr_qfaults_traces.csv`). We read "250" as a 1:250,000 compilation scale. That reading is an
  interpretation of the field name, flagged as IR-48-09. Short, low-relief (< 2 m) scarps fall
  below that compilation's resolution. At 100 m a 1 m scarp is a ~1 % perturbation, which is why
  every 100 m layer in the family plateaued at 0.26–0.28.
* **How it differs:** no Python code in the four checked repos reads 3DEP 1 m tiles (`grep
  "3DEP|1m_DEM"` in `*.py`: 0 hits). The family's DEM work used 100 m pre-derived rasters
  (`lidar_scarp_features_u8.tif`) or a 10 m product (12GEMSDOE "dem10-scarp", live 0.1294, judging
  by its submission name). GEMSDOE47 lists native 1 m processing as its #1 next step but did not
  run it.
* **Blocker:** this sandbox has no USGS/AWS egress (HTTP 000). Runnable path: a GitHub Actions
  matrix job (runners have internet) streams one tile, derives the 100 m detection raster,
  commits only that, and discards the tile.

## H48-5 · Vegetation (phreatophyte) lineaments in late-summer NDVI

* **Layer:** Sentinel-2 L2A B04/B08 at 10 m, late July–September composites (Element84 Earth
  Search STAC, collection `sentinel-2-l2a`, resolved this session). Landsat C2 L2 is the
  fallback.
* **Signature:** linear, strike-coherent positive anomalies of dry-season NDVI on basin floors,
  where groundwater ponds against a fault barrier and feeds phreatophytes. The transform is a
  directional ridge filter (oriented second derivative) on the NDVI anomaly.
* **Why off-catalogue:** basin-floor faults with eroded or buried scarps have little
  topographic signal, which makes them the class a topography-driven catalogue misses. The USGS
  mapped Great Basin phreatophyte cover ([SIM 3169](https://pubs.usgs.gov/sim/3169/sim3169_pamphlet.pdf)).
  A peer-reviewed semi-arid case found 61 % of phreatophyte patches within 50 m of faults
  ([Ecohydrology study](https://www.researchgate.net/publication/321756798_Remote_sensing-derived_fractures_and_shrub_patterns_to_identify_groundwater_dependence)).
* **How it differs:** no NDVI/phreatophyte work in the repos checked. Judging only by its submission name
  (`conj_alteration_mag`, live 0.0782), 15GEMSDOE's spectral work targeted alteration, not
  vegetation water access. Not verified in its code.
* **Risk:** irrigation and riparian corridors cause false positives. They need masking (USGS
  NLCD cultivated class).

## H48-3 · ComCat microseismicity alignments

* **Layer:** USGS ComCat FDSN event catalogue (267,774 events since 2000 in the region bbox,
  verified).
* **Signature:** planar clustering of hypocentres (3-D PCA per cluster), projected up-dip to a
  surface trace.
* **Why off-catalogue:** these would be blind faults without surface scarps.
* **Differs:** the supplied `ieq` band is a smooth density (GEMSDOE32 measured autocorrelation
  0.9986 at 1 km).
* **Why ranked low:** routine ComCat epicentral uncertainty in Nevada is typically of order
  1 km. That is larger than the 300 m kernel, so most projected traces would earn ~0 credit. It
  only pays where relocated catalogues exist.

## H48-4 · Emit from the LSI truth-intensity map

The live-score inversion fits a truth intensity per (distance-to-catalogue × backbone) bin. It
would be attractive to emit into high-intensity bins. **Not viable:** the leave-one-out rank
correlation within the top-8 family is −0.69, so the fine structure is not trustworthy. Revisit
after the λ-probe (see [next steps](next-steps.html)) supplies exact `T`, `F`, `K` for one file.
