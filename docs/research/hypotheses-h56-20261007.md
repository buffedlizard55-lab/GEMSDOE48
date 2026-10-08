> **ARCHIVED / FORENSIC-ONLY H56 SLATE.** The live-model scores, hidden-truth assumptions, 0.0556/0.2727 thresholds, projected deltas, and Gate-2 reasoning in this historical document are invalidated under the [metric-identity erratum](metric-identity-erratum-20261007.md). The H56-F public-proxy pruning test was later run and failed at all three preregistered thresholds; see [measured results](h56-pruning-ladder-results-20261007.md). Keep measured feature/proxy observations only as historical context; do not use the old ranking or predictions for promotion. The current slate is [H57](hypotheses-h57-20261007.md).

# H56 hypothesis slate — five candidates frozen 2026-10-07; later outcomes recorded separately

Machine-readable twin: [`evidence/hypothesis_slate_h56_20261007.json`](../../evidence/hypothesis_slate_h56_20261007.json).
Measured screen and battery: [`evidence/h56_research_battery_20261007.json`](../../evidence/h56_research_battery_20261007.json)
and [`evidence/h56_band_screen_20261007.json`](../../evidence/h56_band_screen_20261007.json).

Each entry records the historical layers, physical signature, catalogue-gap rationale, prior-art distinction and data-access notes. Its old rank and expected ΔDTI estimates were not validated; all quantitative score projections are withdrawn under the erratum above.

## Historical 19-band public-proxy screen measurements

The 419 MB official 19-band GeoDAWN features raster was restored byte-identical from the
hash-pinned mirror (SHA-256 `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`,
manifest `registry/data_manifest_gemsdoe32.json`) and screened band by band against the
incumbent C (37,654 dots) over the >200 m catalogue moat:

| band | description (official tag) | lift | AUC |
|---:|---|---:|---:|
| 3 | TMI horizontal gradient | 1.264 | 0.576 |
| 19 | detrended elevation slope | 1.160 | **0.660** |
| 12 | detrended elevation | −0.463 | 0.560 |
| 13 | isostatic gravity anomaly | 0.773 | 0.549 |
| 10 | distance to earthquake | 1.441 | 0.532 |
| 8 | geodetic dilatation rate | 1.095 | 0.535 |
| 4 | geodetic second invariant | 1.082 | 0.529 |
| 7 | geodetic shear rate | 1.081 | 0.519 |
| 16 | earthquake intensity | 1.082 | 0.522 |
| 14 | total magnetic intensity | 0.954 | 0.509 |
| 17 | conductivity | 0.981 | 0.474 |
| 15 | depth to basement | 0.751 | 0.469 |
| 6 | tilt angle / total curvature | 0.906 | 0.373 |

The local feature screens reproduced these dated proxy statistics: band-3 lift 1.264 vs 1.26; band-19 1.160 vs 1.16; band-10 1.441 vs 1.44; band-4/7/8 1.08 vs 1.03–1.06; and C's mean basement depth 402.4 m vs moat 534.9 m (earlier screen 402 m vs 535 m). These are feature/catalogue-proximity measurements only. The old C live-model projection `0.2728` and associated calibration comparison are withdrawn under the metric erratum; they are not a measured score or valid comparator.

Two earlier candidate fields were screened using a live-anchored surrogate. Their area/overlap counts below are historical local measurements; every projected DTI, credit-per-dot comparison, and FAIL label is invalid under the metric erratum and is not a candidate rejection or promotion result:

* **H55-B strain-rate ridge field:** the historical screen reported 258,369 px (about 5% of the footprint) and 1,886 C dots (5.0%) inside the field. The associated standalone `0.0152`, combined `0.2152`, `0.017` credit/dot, and `0.0556` comparison are forensic surrogate outputs only.
* **H56-A DEMGLOW:** the historical conjunction count was 5,944 pixels and the associated Poisson emission had 1,991 dots. The `0.0028` vs `0.0023` comparison and `0.2673` combined projection were derived from the invalid live model; they do not establish a public-proxy or private-label outcome.

These historical model screens are not the H56-F pruning holdout. The later H56-F proxy results are reported separately and fail on the measured public proxies. No current candidate or weekly slot is cleared.

---

## Historical rank 1 — H56-F: absence-driven Dempster pruning ladder (later tested; failed)

> H56-F was subsequently evaluated against the catalogue and SGMC public proxies at each preregistered threshold and failed all three comparisons to H49. The measured results, fold values, and no-slot decision are in [the H56-F results report](h56-pruning-ladder-results-20261007.md). The `0.2727` live-score kill value below is withdrawn; it did not define or determine those proxy results.

| field | value |
|---|---|
| **Layers** | `data/families/dotted_b2_prune_02778.tif` (C, owner-reported 0.2778; local bytes are marked UNSCORED) × `data/families/tip_stepover_r30_02632.tif` (H33-D, owner-reported 0.2632; not organizer-verified) — the two pinned family surfaces used in the historical proposal |
| **Physical signature and transform** | Not a new geophysical transform: the proposed rule thresholds a combined belief surface to retain a subset of C's emitted dots. Dempster's combination does not itself define a removal operation. Where the H33-D support surface is low, the combined belief may fall; that is a model-based ranking signal, not proof of "no fault". The historical proposal retained C dots with combined belief ≥ τ for τ ∈ {0.90, 0.95, 0.99}. |
| **Motivation to test (historical hypothesis, not a demonstrated mechanism)** | The owner-reported ladder and organizer's known-fault masking clarification motivated asking whether a tip-family support field could help prioritize which C-dots to retain. The ladder does not establish that the removed dots earned zero credit, nor does it identify a universal `0.2·DTI` bar. The two local families overlap substantially, so the tip surface is not established as independent evidence. H56-F must be judged only by its preregistered, comparable public-proxy measurements; those results failed and do not establish private-label performance. |
| **Difference from anything in the repository** | H49/H53/H54/H55 and this session's H56 all ADD or REWEIGHT. No artifact has ever removed C dots using the other family's evidence. The H55 slate explicitly left 200–300 m flank pruning as "owner decision, not recommendation" — this is a different, evidence-weighted removal rule with a ladder, not a spatial band. |
| **Data obtainable?** | YES — both parents are pinned and local; builder cost is one script reusing `scripts/build_submission_h56_belief.py`'s BPA. |
| **Historical expectation / cost** | The former `+0.002` to `+0.005` gain, `−0.003` loss, and “widest bet” statements depended on the invalid live-truth model and are withdrawn. The construction cost was estimated as low; that is a historical engineering estimate only. No live score or private-label effect was established. |
| **Original preregistered rule (withdrawn)** | Do not prune below τ = 0.90 in one rung; the former `0.2727` live-score kill check is invalid. H56-F was instead evaluated using the separately preregistered public-proxy fold protocol reported in `h56-pruning-ladder-results-20261007.md`; all three thresholds failed H49. |

## Original ranks 2–5 — other H56 hypotheses (historical order only)

The remaining concepts and source notes below are retained from the H56 planning slate. Their old quantitative ΔDTI ranges, transfer arguments and ordering are not validated and are not the current slate. The numerical predictions shown in this section are withdrawn as decision evidence under the metric erratum. See the [current H57 slate](hypotheses-h57-20261007.md) for the active research ranking.

### Historical rank 2 — H56-C: 3 m DEM channel-knickpoint clusters

| field | value |
|---|---|
| **Layers** | USGS 3DEP 1 m DEM (the same official source already fetched for H52/H54: 706 of 716 zone-11 tiles via `.github/workflows/dem-region-scarp.yml`), block-averaged to 3 m |
| **Physical signature and transform** | Stream-network extraction on the 3 m mosaic, then knickpoint detection as local maxima of the profile second derivative exceeding a 3σ noise floor, then RANSAC line-clustering of knickpoints into azimuth-coherent sets (≥ 4 knickpoints within a 300 m corridor of a common azimuth). Emit one Poisson dot per cluster centroid. |
| **Why it catches a MISSING fault** | A young fault perturbing base level leaves knickpoints in channel long-profiles **upstream of any mappable scarp** — including faults mantled by alluvium that show no trace at the surface and are therefore absent from the USGS Quaternary catalogue and the INGENIOUS inventory. Scarps (H52/H54) look at hillslopes; knickpoints look inside the drainage network — a disjoint observation space. |
| **Difference from anything in the repository** | H52/H54 used a step-height detector on hillslope cells; no channel-profile operator exists in `src/`. The H52 lesson (terrain class beat step height) is incorporated: clusters are the estimator, not individual detections. |
| **Data obtainable?** | YES — proven: the same workflow already downloaded and mosaicked 706 tiles on hosted runners (sandbox cannot reach USGS; runners can), compact products committed back. |
| **Historical estimate / cost** | The old `+0.002` to `+0.010` DTI range and any transfer from lidar/scarp scores are not validated and are withdrawn as decision evidence. Cost was estimated **medium-high** (runner mosaic plus a new detector); this is an engineering estimate, not a measured result. |

### Historical rank 3 — H56-D: conduit stepping-stone trace propagation

| field | value |
|---|---|
| **Layers** | `data/raw/external/gdr_wellspring_in_footprint.csv` (GDR/INGENIOUS wells and springs, local and hash-pinned) × official band 3 (TMI horizontal gradient) |
| **Physical signature and transform** | Tier-≥2 conduit anchors (1,005 off-catalogue, measured this session) paired within 15 cells; each pair joined by the straight segment, scored by mean band-3 HG along it (anchors sit at HG 28.77 vs moat background 26.33, a 1.09× lift — weak); emit dots along the top segments at Poisson spacing, ≥ 300 m from existing C dots. |
| **Historical physical rationale** | Hydrothermal discharge can indicate a fluid pathway and may motivate testing for connecting structures, but it is not direct proof of a fault. The historical proposal was to test segments between conduit anchors; no geological trace or hidden-label score is established by the anchors themselves. |
| **Difference from anything in the repository** | H55-A emitted isolated anchors; no session had connected anchors into traces. The former `−0.00003` modelled net value for H55-A is invalidated with the live-score inversion and is not a baseline. |
| **Data obtainable?** | YES — all inputs local. |
| **Historical estimate / cost** | The former `−0.001` to `+0.002` range was an unvalidated planning estimate, not a measured score effect. The 1.09× HG lift is a dated feature/catalogue statistic only. Cost was estimated low; no candidate was built or slot-cleared. |

### Historical rank 4 — H56-B: radiometric K-residual alteration halos

| field | value |
|---|---|
| **Layers** | `data/source_mirrors/geodawn_rad_u8.tif` (GeoDAWN K/Th/U/TC, uint8 1st–99th percentile quantisation, band order K, Th, U, TC per the mirror's own metadata; source DOI [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ)) |
| **Physical signature and transform** | Robust regression K ~ Th (lithology control; both quantised), residual field R_K; anomaly = robust z of R_K; emit where z ≥ 2 AND band-3 HG ridge ≥ p75 (conjunction with structure). |
| **Why it catches a MISSING fault** | Potassic metasomatism along upflow zones persists under cover long after surface expression erodes; the catalogue is a surface-trace compilation. K enrichment *at constant Th* is a chemistry signal no geomorphic layer sees. |
| **Difference from anything in the repository** | H50-B used the Th/K *ratio* inside DS conflict corridors (failed its gate); GEMSDOE46 used scarp∩radiometric coincidence; H53-RadEdge used radiometric *edges*. A lithology-regressed K **residual** is a different operator with a different null. |
| **Data obtainable?** | YES — mirror already local and hash-pinned. Caveat: uint8 quantisation coarsens the regression; flagged as an implementation risk. |
| **Historical estimate / cost** | The old `+0.000` to `+0.003` DTI range was not tested or validated; it is not evidence or a forecast. Cost was estimated low. |

### Historical rank 5 — H56-E: cover-gated additions (basement-depth prior)

| field | value |
|---|---|
| **Layers** | official band 15 (depth to basement) × any future addition candidate |
| **Physical signature and transform** | Not a detector: a proposed **sampling gate**. The historical local screen measured C dots at mean basement depth 402.4 m vs 534.9 m for the moat background; 42.5% of C's dots were below the moat median depth. This describes the local feature distribution only; it does not establish that the family under-emits real faults or that deep basins are missing labels. Any future gate would require an independent holdout test. |
| **Historical rationale** | Thick alluvial cover can obscure surface traces and motivates a testable hypothesis. The catalogue's relative completeness by cover depth and the probability that an added dot is genuinely new were not established in this screen. |
| **Difference from anything in the repository** | H55-C proposed basement-depth × gravity × conductivity *conjunction as a detector*; this uses depth as a **sampling prior on additions**, which no session has done. |
| **Data obtainable?** | YES — band 15 is in the restored official raster. |
| **Historical estimate / cost** | The former `±0.001` DTI modifier is an unvalidated planning number, not evidence or a forecast. Cost was estimated trivial. |

---

## Historical screens that used the invalid live model

| idea | preserved observation / corrected status |
|---|---|
| H55-B strain-rate ridge emission | The old report records 25,837 Poisson dots. Its `0.0152` standalone / `0.2152` C+field projection, `0.017` credit-per-dot value, and comparison to `0.0556` all came from the invalid surrogate; they are forensic output, not a valid candidate failure. |
| H56-A DEMGLOW emission | The old report records 1,991 dots. The `0.0028` vs `0.0023` simulation and `0.2673` C+field projection used the same invalid surrogate and are not a public-proxy result or valid reason to reject a geological hypothesis. |
| Band-16 seismicity dots | Historical catalogue-proximity lift/AUC were 1.082/0.522. These are feature-screen statistics only; comparisons with surrogate “failures” do not establish a ranking. |
| Band-17 conductivity ridge | Historical AUC was 0.474 in the stated feature screen. It is a proxy statistic, not validation of a geological sign or a candidate rejection. |
| Further dotted × tip reweighting/fusion | The former live-model union price, H56B 0.0649 projection, and parent `T` comparison are withdrawn. Measured public-proxy results for H56B/H56-F and other current work are listed on the [validation page](../validation.html); no universal conclusion that this entire method family is exhausted follows. |

## Promotion policy correction

The former H56 rule requiring a live-model projection at or above `0.2778` (with a pruning-ladder exception) is withdrawn because it depended on invalid score inversion and unverified score-to-file attribution. Do not use it to promote, reject, or rank candidates. Current guidance requires a comparable spatially blocked public-proxy holdout and, before any future promotion, a re-derived and validated mass-neutral audit that does not infer private-label density from a reported score. **No weekly slot is cleared.**
