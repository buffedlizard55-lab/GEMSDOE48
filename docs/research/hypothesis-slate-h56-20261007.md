> **ARCHIVED / FORENSIC-ONLY H56 PLAN.** This dated plan retains its original wording for provenance. Its live-model projections, inferred truth, universal marginal bars, and threshold-based kill criteria were invalidated by the metric-identity erratum. Do not use those values for promotion or slot decisions. Current slate and results: [H57 hypotheses](hypotheses-h57-20261007.md), [H57-A results](h57-results-20261007.md), [H56-F pruning results](h56-pruning-ladder-results-20261007.md).

# H56 hypothesis slate — frozen before new candidate scoring (2026-10-07)

This slate follows the standing project brief in [`README.md`](../../README.md). It is a
pre-scoring research plan, not a claim that any surface is geologically correct. “Expected
DTI” is an ordinal prior, not a fabricated numeric forecast: the hidden expert labels are not
available locally, and the public SGMC/catalogue proxies are imperfect and have already been
shown to disagree with at least one owner-reported live score.

## Evidence and access constraints

- The official [GEMS problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
  says the target is fault structure indicative of geothermal resources; the initial hidden
  faults were expert-identified and are absent from the existing public USGS fault database.
  It lists strain, gravity, magnetic, earthquake, and conductivity/elevation features in the
  provided 100 m EPSG:32611 feature stack.
- The official [GeoDAWN USGS release](https://doi.org/10.5066/P93LGLVQ) describes magnetic and
  radiometric grids and coordinated lidar. USGS marks the release CC0. The official [3DEP
  metadata page](https://www.usgs.gov/3d-elevation-program/3dep-spatial-metadata) exposes
  public lidar/DEM work-unit availability and project metadata.
- The official [USGS National Geochemical Survey](https://mrdata.usgs.gov/geochem/) offers
  geographic downloads and a national CSV, but sample media, age, analytical method, and local
  coverage must be audited before use.
- The official [USGS blind-geothermal play-fairway report](https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and)
  describes integrating structural, geophysical, geochemical, lidar, and temperature evidence;
  it supports hypothesis generation, not a claim that any particular transform predicts the
  hidden labels.
- The competition feature stack is not present in tracked `data/`. DrivenData's data tab is
  login-gated in this environment. A separate, hash-pinned GitHub mirror is available through
  `scripts/restore_h55_inputs.py`; it is a third-party copy, not organizer-authenticated. If
  restored, its bytes can support a reproducible proxy experiment, but provenance/license
  review remains necessary before external redistribution.

## Ranked hypotheses

| Rank | Hypothesis and layers | Target signature / why it may find a fault missing from the catalogue | Prior art and difference | Expected DTI upside / cost / data gate |
|---:|---|---|---|---|
| **1** | **H56-A — active-deformation strain ridges:** competition feature bands 4 (second invariant of strain rate), 7 (shear strain rate), 8 (dilatation rate), plus 16 (earthquake density) and 10 (distance to earthquake); exact band descriptions must be confirmed from the restored GeoTIFF before use. | Apply scale-normalized Hessian ridge response at 300/600/900 m (3/6/9 pixels) to log-transformed positive strain magnitudes; combine with structure-tensor line coherence and a weak, independently normalized earthquake-density term. A buried or alluvium-covered active structure can lack a mapped surface trace, whereas geodetic deformation/seismicity may remain spatially expressed. The claim is conditional: regional strain fields are diffuse and can reflect distributed deformation, not a single fault. | No H48–H55 submission in this repository emits a strain-ridge prediction. H55-B proposed it but did not build/score it. This uses derivatives/coherence, not amplitude thresholding; it is not independent of the competition feature stack. | **Highest plausible new-signal upside; unknown numeric ΔDTI. Medium cost.** Top candidate to test first. Data is available only through the login-gated competition stack or its hash-pinned, non-organizer mirror; restore and SHA-verify before use. Do not spend a slot unless it beats the comparable blocked best and passes the independent leakage/provenance gate. |
| **2** | **H56-B — basement-step edges:** depth-to-basement band 15, isostatic gravity band 13 and derivatives (bands 5/11/18), conductivity band 17; confirm names/units before use. | Multi-scale lateral basement-depth curvature and gravity horizontal-gradient/tilt edges, corroborated by a conductivity contrast. A fault offset beneath basin fill can be invisible in surface morphology yet create a subsurface density/resistivity boundary. | H55-C proposed this but no matching raster candidate or holdout score exists. It differs from H53's radiometric-edge transform and H52/H53 lidar scarp detectors. | **Moderate/unknown upside; medium cost.** Requires the same competition feature stack or a source-verified equivalent; stack currently requires a login or owner mirror. Validate geologic-map, lithology, and coverage confounding before any ranking. |
| **3** | **H56-C — lidar scarp traces, not point detections:** `h_gate12`, `sigma_mean`, `strike_at`, and `cover` in `data/external/h52_scarp3m_100m.tif`, derived from the documented USGS 3DEP 1 m/3 m processing. | Detect low-amplitude height steps that persist along a compatible trace over several adjacent 100 m cells, rather than scoring isolated maxima. Young extensional scarps can be absent from a generalized fault inventory because they are subtle, unmapped, or buried/partly exposed. | H52 emitted individual scarp points; H53-A tested a different strike-coherent point-addition rule and failed its frozen proxy gate. H55-D proposed trace persistence but did not implement it. This is a line-persistence estimator, not a relabelled point detector. | **Moderate but unverified upside; medium/high cost.** Compact regional product is already local; source tile coverage and `facing_at` units remain flagged in existing receipts. Do not infer full-region lidar coverage from selected pilot tiles. |
| **4** | **H56-D — high-resolution magnetic edge continuation:** official USGS GeoDAWN magnetic grids, not the existing K/Th/U/total-count radiometric mirror. | Compute analytic-signal magnitude and tilt-angle/edge coherence across scales; test line continuations beneath basin cover where magnetization contrasts across basement faults survive but topography does not. | H53-RadEdge used radiometric edges and failed its holdout; magnetic potential-field gradients are a distinct physical observable. The official GeoDAWN DOI lists magnetic grids, but the exact competition-footprint overlap/resolution must be measured from the downloaded payload. | **Moderate/unknown upside; high cost.** Official free CC0 source is identified at DOI 10.5066/P93LGLVQ; no magnetic payload or exact footprint coverage was verified for this slate. Obtain/inspect the official product before implementation. |
| **5** | **H56-E — hydrothermal pathfinder geochemistry:** USGS National Geochemical Survey sample locations/analyses (e.g., B, Li, As and Hg only after dictionary, units, and method audit), spatially joined to the official footprint and structural corridors. | Robust within-method/medium geochemical anomalies may indicate hydrothermal alteration or fluid pathways near faults absent from a generalized fault catalogue. Stream transport, lithology, sample age, and analytical limits can mimic or erase anomalies; this is a weak, conditional hypothesis. | No NGS geochemical predictor is in the current candidate outputs. It differs from H50-B's airborne radiometric alteration proxy and H55-A's point spring/well temperatures. | **Low-to-moderate, highly uncertain upside; high cost.** Official USGS download page is public and offers CSV/shapefile packages; actual Great Basin footprint coverage and reuse/field semantics still need an audited payload. |

### Required first validation and decision rule

H56-A is the first candidate because it is the strongest plausible source of *new* information in
an existing official feature stack, not because a score is known. Freeze the transform and budget
before opening either proxy result. Use a deterministic mass-matched (37,654-cell) emission for
comparison, the existing four fixed quadrants, each held-out core plus the 300 m metric halo, and
both the catalogue and >300 m off-catalogue SGMC proxy. Compare against the current H49 proxy-best
on the same executable/protocol. A numerical proxy improvement is only a research result: the
sources are public-map proxies, source construction may have used full-scene data, and the SGMC
proxy has a live-score contradiction. **No weekly submission is authorized by this slate.**

### Separate required deliverable experiment — H56-DS

The owner-requested two-family experiment is distinct from the five geological hypotheses above:
combine the hash-pinned H33-2-B2 dotted surface and the actual H33-D tip/step-over surface with
Dempster–Shafer evidence theory; publish normalized relative Bel(F), canonical residual
`m(Theta)`, and a separate conflict diagnostic. The existing repository already contains older
symmetric D-S family combinations, so novelty cannot be claimed for “D-S fusion” in general.
H56-DS will use a preregistered sparse/open-world BPA in which a missing pixel is mostly
uncommitted rather than automatically asserted as “no fault.” Its result must be compared to the
current blocked best before any slot decision. The build is for a unique, format-audited research
candidate; it is not approval to upload.
