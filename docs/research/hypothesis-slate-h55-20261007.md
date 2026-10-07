# H55 hypothesis slate — five candidates, frozen 2026-10-07 before any scoring

Machine-readable twin: [`evidence/hypothesis_slate_h55_20261007.json`](../../evidence/hypothesis_slate_h55_20261007.json).
Each entry names the layers, the physical signature and its transform, why it should catch
a fault **missing** from the USGS/INGENIOUS catalogue rather than one already in it, how it
differs from everything already in this repository, its data-obtainability status, and its
expected ΔDTI against implementation cost.

The ranking is set by §3.1 of
[`h55-live-model-ceiling-and-candidate-20261007.md`](h55-live-model-ceiling-and-candidate-20261007.md):
**the h19-5 corridor field is capped at live-equivalent 0.2843 at any mass**, so a candidate
is only interesting if it can raise the *dense* truth yield above the backbone's measured
T = 6,813. Candidates that merely re-rank or re-thin the existing field are worth at most
+0.0065 and are ranked last on that basis.

Two screens measured this session are applied to every candidate and are worth restating,
because prior sessions used the opposite ones:

* **Catalogue coverage per emitted pixel is NOT a valid screen.** SGMC faults score 0.1418
  against the backbone's 0.1007 and still returned T = 1,026 live at the same mass — 5×
  worse. The ≥ 2× "catalogue lift" rule that rejected H52 is therefore not sound.
* **The SGMC off-catalogue proxy is NOT a model of the hidden truth.** An emission built
  directly on it scored 0.0512 live.

The only live-validated screen is `Cov(X; B_elig)` inside the family, and it cannot rank a
new family at all (measured transfer error −38 %).

---

## Rank 1 — H55-B: active-deformation localisation ridges (official bands 4/7/8/16)

| field | value |
|---|---|
| **Layers** | `data/raw/training_features.tif` band 4 *geodetic second invariant of strain rate*, band 7 *geodetic shear rate*, band 8 *geodetic dilatation rate*, band 16 *earthquake intensity/density*, band 10 *distance to earthquake* |
| **Physical signature and transform** | Not the amplitude — the **anisotropic localisation**. Strain localises into narrow shear zones, so apply a multi-scale vesselness / Sato ridge filter and the structure-tensor coherence `(\|λ1\|−\|λ2\|)²/(\|λ1\|+\|λ2\|)²` at 300–900 m, to `log(second invariant)` and `shear rate`, then keep only pixels whose coherence exceeds the 95th percentile. Measured here: the raw fields are diffuse (a multi-orientation line operator separates their top 2 % from background at only p90 0.0022 vs 0.0008), so the ridge transform is the whole hypothesis, not a refinement. |
| **Why it catches a MISSING fault** | Geodetic strain and microseismicity localise on faults that are *currently slipping*. A fault can be slipping and be completely buried under basin alluvium — no scarp, no lineament, no geomorphic expression — and therefore absent from the USGS state-map compilation and from the INGENIOUS Quaternary trace inventory, both of which are mapped from surface geology. Active deformation is the one signal in the official stack that does not require surface expression. |
| **Measured evidence it is unused** | Lift of C's 37,654 dots over the >200 m moat background, by band: second invariant **1.05**, shear rate **1.03**, dilatation rate **1.06**, earthquake intensity **1.04**, distance-to-earthquake 1.44 (inverted: C's dots sit *farther* from earthquakes). Compare TMI horizontal gradient 1.26 and detrended-elevation slope 1.16, which the family does use. Only **0.7–1.4 %** of C's dots lie in the top 1 % of these four bands. They are close to pure unused information. |
| **Difference from anything in the repository** | H48-3 proposed OPERA InSAR DISP-S1 displacement gradients and was never run ("Earthdata Login required; no granules downloaded"). These bands are **already inside the official competition raster**, restored byte-identical this session (SHA-256 `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`). No file in `evidence/` scores a strain-rate or seismicity surface in any form. |
| **Data obtainable?** | **YES, verified this session.** `python scripts/restore_h55_inputs.py --with-official-features` restores all 418,912,844 bytes from five hash-pinned shards and matches the manifest pin. Free, no login, no third-party host. 419 MB, deliberately not committed. |
| **Expected ΔDTI / cost** | Unknown but the largest available from data already in hand — it is the only candidate that could raise the *dense* ceiling above 6,813 rather than re-thinning below it. Cost **low-medium**: one ridge-filter module plus the existing emitter and budget rule, no new downloads. |
| **Kill criterion (pre-registered)** | Emit the dense ridge field and invert its `T` under the calibrated `\|G\|`. If dense `T < 6,813` the field is worse than the backbone and the hypothesis is dead regardless of how good its ridges look. This costs one weekly slot and is the single most informative slot the project can spend, because it also re-calibrates `rho` for a second family. |

## Rank 2 — H55-D: 3 m lidar scarp **traces** (re-test of H52 with the corrected gate)

| field | value |
|---|---|
| **Layers** | `data/external/h52_scarp3m_100m.tif` bands `h_gate12`, `h_all`, `sigma_mean`, `strike_at`, `cover`; upstream source USGS 3DEP 1 m DEM, 706 of 716 zone-11 tiles, block-averaged to 3 m then to 100 m in GitHub Actions |
| **Physical signature and transform** | **Line-persistent step height, selected as traces rather than points.** Gate on `h_gate12` ≥ its 99th percentile *inside* low `sigma_mean` (smooth terrain, so a step is not just roughness), then require the detection to persist along a consistent azimuth over ≥ 5 consecutive 100 m cells, and emit one dot per ~300 m of trace. H52 emitted the top-2,000 *individual* detections; a fault is a line and the metric's kernel is isotropic, so trace-level selection is a different estimator, not a tweak. |
| **Why it catches a MISSING fault** | A 100 m DEM cannot resolve a 1–3 m Quaternary scarp at all — the relief is inside one pixel's noise. Every 100 m layer the family uses (detrended elevation, its slope, magnetic gradients) is blind to exactly the young, alluvium-mantled basin faults that a 1 m/3 m DEM resolves. That is the population an expert reviewer would add to a catalogue. |
| **Difference from anything in the repository** | H52 (this repository, 2026-10-07) shipped C + 2,000 point detections and was rejected by **two screens this session shows to be unsound**: catalogue lift 1.19–2.27× against a ≥ 2× rule (§4.2), and "does not beat H49 on the SGMC proxy" (§4.1). The re-test changes the estimator (traces, not points) *and* the judge (live-calibrated cross-family recalibration, not catalogue lift). |
| **Data obtainable?** | **YES — already committed**, 43.8 MB, `data/external/h52_scarp3m_100m.json` records 697 merged tiles with per-tile SHA-256. |
| **BLOCKED on one verification** | `strike_at` is quantised to 15° bins (observed values 0, 1500, …, 16500, i.e. 0–165° in 0.01° units) and **`facing_at`'s units are unconfirmed**: the median perpendicularity between the two is 46°, not the ~0° a dip-direction/strike pair requires. An along-strike walk must not be built on `facing_at` until `src/gemsdoe48/scarp3m.py` and `data/external/h52_scarp3m_merge_log.txt` are re-read against the Actions run that produced them. Flagged as an irregularity rather than assumed away. |
| **Expected ΔDTI / cost** | Highest ceiling of any candidate here — §3.1 shows #1 at 0.3774 needs more truth than the whole backbone contains, and native-resolution lidar is the only data in hand that can supply it. Cost **medium**: the trace-persistence filter is new code, the emitter and budget rule are reused. |

## Rank 3 — H55-C: buried basement steps and isostatic-gravity gradients

| field | value |
|---|---|
| **Layers** | official band 15 *depth to basement surface*, band 13 *isostatic gravity anomaly*, bands 5/11/18 *its slope and vertical/horizontal gradients*, band 17 *conductivity surface*, band 6 (see the irregularity below) |
| **Physical signature and transform** | **Lateral second derivative of basement depth** plus **horizontal-gradient magnitude and tilt angle of the isostatic gravity field**, intersected with a **conductivity contrast** (fault gouge and hydrothermal alteration are conductive relative to unaltered basement). Basin-range normal faulting produces a sharp basement-depth step; where the range front is buried the topography is flat but gravity and basement depth still record the offset. |
| **Why it catches a MISSING fault** | Measured blind spot: C's dots sit on **shallow** basement (mean 402 m against 535 m for the moat background, lift 0.75) and on **topographic highs** (detrended elevation +7.3 against −15.6, lift −0.47 relative to basin floor). The family therefore systematically favours *exposed* range fronts. Buried basin-margin faults — a basement step with no topographic expression, in the basin fill — are precisely the population it cannot see, and precisely the population that hosts geothermal reservoirs. |
| **Difference from anything in the repository** | H48-2 proposed "stratigraphic contact topology plus magnetic/gravity breaks" and was never implemented ("payload/coverage not audited"). No file in `evidence/` scores a gravity-gradient, basement-depth or conductivity surface. Nothing in `data/` needed to be fetched. |
| **Data obtainable?** | **YES, verified this session** — same official raster as H55-B, same restore command, same pin. |
| **Irregularity that must be carried forward** | Official band 6's in-file description reads *"Tilt angle or total curvature — magnetic field derivative for edge detection"* and its category tag reads `magnetic_data`. **That metadata is wrong.** Reproduced independently this session over 5,164,300 in-footprint cells: Pearson r = **0.9971** and Spearman ρ = **1.0000** against the separately mirrored GeoDAWN radiometric *total count*, and r = **−0.0409** against the file's own TMI band 14 and −0.1624 against its TMI horizontal gradient. Band 6 is gamma-ray total count. This confirms and strengthens the irregularity already logged in `docs/irregularities.md`; any downstream user who takes band 6's description at face value will build a "magnetic tilt" feature out of radiometrics. |
| **Expected ΔDTI / cost** | Moderate. Cost **low**: data in hand, transforms are standard. |

## Rank 4 — H55-A: hydrothermal conduit anchors — **SHIPPED in this session's candidate**

| field | value |
|---|---|
| **Layers** | `data/raw/external/gdr_wellspring_in_footprint.csv` — GDR 1391 *Well and Spring Temperature and Chemistry*, 27,092 records, columns `thermalclass`, `temp_c`, `geothermquartz_c`, `geothermchalc_c`, `geothermcat_c`, `row`, `col`, `layer`, `name`. `dist_known_fault_px` is **dropped on read** (label-derived). |
| **Physical signature and transform** | Direct measurement of deep fluid temperature at a point, tiered: **tier 3** = discharge class `Hot` (median 75.0 °C, p90 171.1 °C, max 296.5 °C) *or* any silica/calcite geothermometer ≥ 150 °C (180 records, max 269.1 °C); **tier 2** = discharge ≥ 50 °C or geothermometer ≥ 100 °C; `Warm` (max 38.9 °C, effectively ambient) and `Cold` (≤ 20 °C) excluded as non-indicators. No smoothing: a geothermometer is already an integral along the flow path, so the point *is* the evidence. |
| **Why it catches a MISSING fault** | A hot spring needs a heat source, deep circulation and a permeable upflow path; in the extensional Great Basin that path is a fault. Crucially, upflow through an *already-mapped, already-eroded* range front is not what produces a thermal spring in a basin floor — those appear where a **buried** fault carries hot fluid up through alluvium. Measured: of 12,570 distinct grid cells holding a well or spring, **219 (1.7 %) are inside the h19-5 backbone** and **11,651 (92.7 %) are > 200 m from the public catalogue**. |
| **Difference from anything in the repository** | H50-GDR used the INGENIOUS **2 m soil-temperature probe** archive with a *repeat-visit residual persistence* operator (live-equivalent proxy 0.003923, failed). H52 used **lidar topography**. H50-B used **gamma-ray spectrometry ratios**. This uses **well/spring discharge temperature and silica/calcite reservoir geothermometry** — a different physical quantity (deep fluid, not shallow soil, not topography, not radiometrics), a different source file, and a static tiering operator. No prior GEMSDOE artifact of any session emits on this layer. |
| **Data obtainable?** | **YES, verified.** Free and official: GDR submission 1391, DOI [10.15121/1881483](https://doi.org/10.15121/1881483), <https://gdr.openei.org/submissions/1391>, Data.gov metadata <https://catalog.data.gov/dataset/ingenious-great-basin-regional-dataset-compilation> reporting CC BY 4.0 (asset-level GDR terms not independently verified — flagged, not assumed). Local mirror SHA-256 `122718e65bdf55aab0ee12ad20d80062f0deb1de957225a61ad880dd5dc196ea`, restored with `scripts/restore_h55_inputs.py`. |
| **Expected ΔDTI / cost** | 652 anchors shipped. Scenario band **+0.0019 to +0.0102** live-equivalent as per-anchor credit rises from break-even to 0.30; worst case −0.0019, and A2's in-family gain of +0.0019 pre-pays it (net −0.00003). Cost **low** — implemented, tested, shipped. |

## Rank 5 — H55-E: three-source Dempster–Shafer conjunction (Quaternary trace × conduit × strain)

| field | value |
|---|---|
| **Layers** | `data/raw/external/gdr_qfaults_traces.csv` (1,125 INGENIOUS Quaternary fault trace centroids **with attributes**: `slip_rate`, `recency`, `dip_direct`, `slip_sense`, `map_scale`, `full_length_m`, `clipped_length_m`) × H55-A conduit tier × H55-B strain-rate ridge |
| **Physical signature and transform** | **Conjunction, not union.** Extend the frame to three independent sources and admit a dot only where at least two of {a Quaternary trace with a recorded slip rate, a tier-≥2 hydrothermal conduit, a strain-rate localisation ridge} agree within 300 m. Slip rate and recency are used as *reliability weights* in Dempster's discounting (a trace with `slip_rate > 0.2 mm/yr` and recency `< 1,600,000 yr` gets a higher α than an unspecified one) — the first use of the attribute columns rather than the geometry alone. |
| **Why it catches a MISSING fault** | The INGENIOUS Quaternary traces are *not* the competition catalogue: measured catalogue coverage per pixel 0.3696 — the highest of any layer tested — yet only **1.3 %** of the centroids fall inside the h19-5 backbone. §4.2 says that high catalogue coverage is *not* a reason to trust a layer on its own. The conjunction is the point: a trace with a measured slip rate **and** hot fluid at the surface **and** localised active strain is a fault an expert reviewer would add, and each pair alone is much weaker. |
| **Difference from anything in the repository** | `gemsdoe29-xfit-h41-union-qfaults` was a plain **union** and was never live-scored. No prior artifact in any GEMSDOE session used the `slip_rate` / `recency` / `slip_sense` attributes, and none combined **three** sources under Dempster's rule — every fusion here has combined exactly two. |
| **Data obtainable?** | **YES — all three inputs are already local and hash-pinned** (`gdr_qfaults_traces.csv` SHA-256 `9702f2e5c382a4f472ae834d22b94990983b059677a37adfafd51c50f75e643c`, plus the conduit CSV and the official raster). No external fetch. |
| **Expected ΔDTI / cost** | Small mass (~100–400 dots), so small in both directions: worst case ≈ −0.001, upside ≈ +0.003 if the conjunction is real. Cost **low**. Best used as a rider on H55-A once A's live score is known, because A's returned score is what tells us whether conduit evidence carries credit at all. |

---

## Rejected before ranking, with reasons

| idea | why rejected |
|---|---|
| Coverage-optimal re-emission of the backbone (greedy max-coverage from scratch) | **Already measured.** Frontier maximum is n = 37,167 at model DTI 0.2793 → live-equivalent **0.2843**. That is the whole in-family prize: +0.0065, 1.3× the instrument's resolution. It also requires *removing* C dots, which forfeits the only live-verified T in the repository. Not worth a slot on its own. |
| Density-weighted or corroboration-weighted coverage | **Already measured, negative.** Seven weightings tested against the eight live scores; density weighting is worse than uniform (RMS 2.13–2.63 % vs 1.76 %), radiometric corroboration is neutral (1.80 %). |
| Any re-weighting or fusion of the dotted and tip families | **Proven impossible to help.** §3.3: the union is priced at −0.0140 and the two parents' `T` differ by 1 %. |
| Pruning C's 200–300 m catalogue-flank band (rung D) | The live ladder proves the 0–200 m band earns ≈ 0 credit but says nothing about 200–300 m, and 2,171 of C's dots sit there. Removal is irreversible against a Phase-2 truth that is expanded by expert review of *all* Phase-1 submissions. H55 is additive-only for exactly this reason. Left as an owner decision, not a recommendation. |
| INGENIOUS 2 m soil-temperature probes | H50-GDR already ran a repeat-persistence operator on them: proxy 0.003923, 0/4 folds. A different operator is conceivable but the layer is shallow-soil, not deep-fluid, and H55-A's well/spring chemistry is the stronger version of the same idea. |
| OPERA InSAR DISP-S1 displacement gradients | Earthdata Login required; no granules downloadable from this sandbox. Superseded by H55-B, which uses the geodetic strain bands already inside the official raster. |
| USGS Mineral Resources Data System | Excluded upstream: updates ceased in 2011. |
