# Geological hypothesis slate H57 — frozen before candidate implementation

**Frozen:** 2026-10-07 UTC, before H57-A feature extraction or holdout scoring.
**Purpose:** rank distinct geological signal families by a qualitative planning range for blocked-proxy ΔDTI versus the current comparable reference, then by implementation cost and data readiness. These ranges are **not measured predictions, confidence intervals, or leaderboard projections**.
**Promotion rule:** no candidate may use a weekly slot unless its exact frozen construction beats the same-protocol H49 reference on both public proxy regimes (positive mean paired ΔDTI and wins in at least 3/4 geographic folds on each). A candidate must also pass format, uniqueness, provenance/licence review, and the owner’s final decision. Public-proxy wins alone are never slot clearance.

| Rank | Hypothesis | Expected blocked-proxy ΔDTI vs H49 (planning range) | Cost / readiness | Decision at freeze |
|---|---|---:|---|---|
| **1 — test now** | **H57-A: residual potassium alteration anomaly × magnetic-gradient corroboration** | **0.000 to +0.003**; small, uncertain upside; not measured before this slate | Low–medium; radiometric input local, magnetic extension restorable from a hash-pinned owner mirror | Run a single frozen 2,000-cell addition screen on both blocked proxies. |
| **2** | **H57-B: focal-mechanism strike/dip/rake lineation** | 0.000 to +0.004; uncertain and coverage-limited | Medium; official USGS ComCat FDSN count query returned 98 events; focal-mechanism product fields and local coverage are not audited | Park until records, product fields, coverage and terms are checked. |
| **3 — highest planning upside, not presently testable** | **H57-C: channel-profile knickpoint alignments** | +0.002 to +0.010 *if* repeated profile breaks are fault-related; wide uncertainty | High; public 3DEP/3DHP download routes, but exact full-footprint DEM/channel coverage is unaudited; only two 3 m pilot DEM tiles are present | Do not call implementation-ready; first verify coverage and obtain the exact source tiles. |
| **4** | **H57-D: multi-element hydrothermal pathfinder residuals (B/Li/As/Hg)** | 0.000 to +0.004; uncertain | High; USGS NGS national downloads are public, but target-area counts and analytical comparability have not been audited | Park pending coverage, semantics and terms checks. |

The shortlist is not four parameter variations on a single map: it covers airborne radiometrics/magnetics, earthquake focal mechanisms, drainage-profile morphology, and stream-sediment/soil chemistry. A fault interpretation is a hypothesis for each signal, not a property established by a proxy score.

## Frozen promotion protocol

- Reference: the pinned H49 raster and its same-protocol reference receipt.
- Targets: public catalogue labels and SGMC fault pixels more than 300 m from catalogue positives.
- Folds: four fixed quadrants on the full EPSG:32611, 100 m grid; evaluation domain is held-out core plus a 300 m footprint-clipped halo; score only core-quadrant truth.
- Pass: mean paired ΔDTI > 0 and at least 3/4 positive fold deltas on **both** targets.
- The proxy targets are not the private expert-labelled test set; a pass would still not establish private performance, a leaderboard score or organizer acceptance.

## H57-A preregistration — residual K × TMI-up150 gradient

- **Layers and source:** K and Th channels from `data/source_mirrors/geodawn_rad_u8.tif` (four-band uint8 GeoDAWN owner mirror; SHA-256 `c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682`) and `TMI_up150` from `data/raw/external/geodawn_extensions_u8.tif` (owner mirror, expected SHA-256 `a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b`). Compute the magnitude of the 100 m-grid central-difference gradient of `TMI_up150`. At freeze, the extension was not staged; the restore command is `python scripts/restore_h55_inputs.py --only geodawn_extensions_u8`. Hash identity verifies the mirror bytes only—not organizer authentication or licence compatibility. Official upstream context: USGS GeoDAWN [DOI 10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ) and [USGS release page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and). Abort if the restored raster lacks a matching-grid band named `TMI_up150`.
- **Transform frozen before scoring:** on valid in-footprint K/Th cells, fit a five-iteration Huber IRLS line `K = intercept + slope × Th` (Huber cutoff 1.345 robust residual standard deviations); calculate `zK = (residual − median(residual)) / (1.4826 × MAD(residual))`. Set the magnetic cutoff to the 75th percentile of gradient magnitude on valid cells. The admissible anomaly set is `zK ≥ 2`, gradient magnitude strictly greater than zero and at or above p75, and H49 reference value zero. Rank admissible cells by `zK × gradient_magnitude` (descending; row-major tie break), take at most 2,000, and add binary value 1 to those cells without changing H49 values. The catalogue geometry and either holdout truth are not used to fit features, define or rank the candidate set, or choose the budget. **There is no catalogue-distance filter in candidate construction; H49-positive cells are simply ineligible for an addition.**
- **Geological signature:** potassium enrichment not explained by local Th, corroborated by a magnetic edge. It could mark hydrothermal alteration near a buried structure, but radiometric response also follows lithology and a magnetic gradient may be a contact rather than a fault.
- **Why it may add off-catalogue evidence:** geophysical anomalies can generate candidate cells absent from a Quaternary fault inventory. This rationale does not prove the cells contain unmapped faults.
- **Prior-art difference:** H50-B tested a quantized low-Th/K ratio inside Dempster-conflict corridors and was negative; H53-RadEdge used radiometric-edge evidence, not K residualization plus a magnetic-gradient conjunction. H56-B proposed this K-residual idea but did not implement or score it. This is a distinct operator, not a new data source or wholly untested radiometric evidence.
- **Expected ΔDTI / cost:** +0.000 to +0.003 planning range versus H49, with a realistic chance of zero or negative change; low–medium effort. Not a live-score projection.
- **Frozen pass/fail rule:** same H49 reference, quadrants, 300 m evaluation halo and official DTI implementation; compare catalogue and SGMC positives >300 m from that catalogue. Require mean paired ΔDTI > 0 and at least 3/4 positive fold deltas on both. Any win would remain research-only.

## H57-B — earthquake focal-mechanism orientations

- **Layers:** event epicentres and focal-mechanism strike/dip/rake products from the official [USGS ComCat FDSN event service](https://earthquake.usgs.gov/fdsnws/event/1/). A reproducible count query over the transformed competition bounding box (37.331–40.728° N, 120.038–116.141° W), 1900-01-01 through 2026-10-07, M≥4.5 and `producttype=focal-mechanism` returned **98 events** at preregistration. This is count-level availability, not a downloaded or inspected catalogue; the query is recorded in [`evidence/h57_data_access_checks_20261007.json`](../../evidence/h57_data_access_checks_20261007.json).
- **Signature and off-catalogue rationale:** cluster mechanisms with compatible nodal-plane orientations along a common lineation, then investigate short coherent segments in gaps >300 m from the mapped catalogue. This targets possible unmapped active structures, not event-density peaks.
- **Difference from prior art:** earlier seismicity proposals and the feature-stack earthquake-density band use counts/density; H57-B uses focal-plane orientations. No local event products have been audited.
- **Planning range / cost:** 0.000 to +0.004; medium. A count does not establish coverage, complete time range, mechanism quality, or challenge-compatible licensing. Do not implement until record fields, event depth, magnitude bias, spatial distribution and reuse terms are checked.

## H57-C — channel-profile knickpoint lineations

- **Layers:** free USGS [3DEP elevation products](https://www.usgs.gov/faqs/what-types-elevation-datasets-are-available-what-formats-do-they-come-and-where-can-i-download), 1 m where available, plus USGS [National Hydrography / 3DHP products](https://www.usgs.gov/national-hydrography/access-national-hydrography-products). USGS documents availability maps and public download paths; it does not follow that 1 m coverage is complete for this footprint. The checkout has two 3 m pilot DEM tiles, not a full-area mosaic.
- **Signature and off-catalogue rationale:** detect repeated along-channel slope/profile breaks and common azimuth clusters consistent with fault-related base-level perturbations. Drainage-profile anomalies may persist upstream of a subdued or alluvium-mantled trace, but hydrology, lithology and human modifications can confound them.
- **Difference from prior art:** H52/H54/H53-A used hillslope/scarp morphology and point/strike filters; H57-C uses channel-longitudinal profiles and a drainage network. Prior H48-4 was a proposal, not a validated implementation.
- **Planning range / cost:** +0.002 to +0.010 only if the cluster signal is fault-related; high effort. Exact region-wide DEM and channel coverage, resolution and ingestion cost must be checked first. This is not the leading feasible experiment in the current checkout.

## H57-D — multi-element hydrothermal pathfinders

- **Layers:** USGS [National Geochemical Survey](https://mrdata.usgs.gov/geochem/) stream-sediment/soil analyses. The official page exposes national public downloads, including a 74,409-sample shapefile package and a 77,212-record CSV package; these national counts do not establish target-area sample counts or comparability.
- **Signature and off-catalogue rationale:** within-method and sample-medium-aware B/Li/As/Hg residual anomalies or coherent gradients near geophysical structures may indicate hydrothermal alteration along faults missing from generalized surface-trace maps. Stream transport, sampling bias, analytical method, censoring and lithology are major confounders.
- **Difference from prior art:** H50-B is airborne gamma-ray radiometry; H55-A is well/spring point temperature/chemistry; H57-D would use regional stream-sediment/soil assays and method-aware multi-element residuals. No such candidate raster is staged.
- **Planning range / cost:** 0.000 to +0.004; high effort. Public download availability is documented, but target-area coverage, reuse licence, field semantics and method harmonization are not. Park until those checks pass.

## Source and metric cautions

The official competition page defines distance-weighted Tversky with a 300 m triangular kernel, α=0.2, β=0.8, and single-band GeoTIFF grid/format requirements. A public-proxy result is not private expert-labelled performance, and a leaderboard row does not identify local TIFF bytes. Do not use the invalid surrogate identity `FPw = S − TPw` or a fitted live-model projection as an acceptance gate; see the [metric-identity erratum](metric-identity-erratum-20261007.md).

## Post-freeze correction and H57-A outcome

The frozen machine-readable slate's original H57-A `layers` list included the contradictory phrase “current catalogue geometry for a fixed >300 m exclusion.” The frozen transform itself correctly specifies eligibility as valid footprint and `H49 prediction == 0`; **the H57-A builder applies no catalogue-distance filter**. The eligibility mask avoids overwriting H49-positive cells. The >300 m catalogue exclusion is part of the SGMC *evaluation target*, not candidate construction. This is a text correction only; it does not change the frozen transform, budget or results. The correction is recorded in [`evidence/hypothesis_slate_h57_20261007.json`](../../evidence/hypothesis_slate_h57_20261007.json).

After freeze, `TMI_up150` was restored to the git-ignored local tree with the expected SHA-256. See [`evidence/h57_data_access_checks_20261007.json`](../../evidence/h57_data_access_checks_20261007.json). This verifies the owner-mirror bytes only—not the official USGS payload, organizer authentication, sponsor-sharing licence, or challenge-use terms.

H57-A was scored according to the frozen rule; it failed the two-proxy H49 gate and did not beat same-pool random controls. **No H57 TIFF was generated and no slot is cleared.** See [`h57-results-20261007.md`](h57-results-20261007.md) and [`evidence/holdout_h57a_20261007.json`](../../evidence/holdout_h57a_20261007.json).
