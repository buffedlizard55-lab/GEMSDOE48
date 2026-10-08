# H58 hypothesis slate — geological candidates not yet scored (2026-10-08)

Ranked by **expected DTI gain × probability of surviving the gate, per unit cost**. Expected gains are
qualitative, because the local proxy cannot resolve differences below about 0.001 (see
[`h58-results-20261008.md`](h58-results-20261008.md) §4). No candidate here is cleared for a slot. Every
candidate needs a preregistration before it is scored.

Previously tried and **not** re-proposed: DS fusions (H48, H49, H50, H53, H56, H57-RELIEF), lidar scarps
(H52), H56-F belief pruning, H51 plausibility budget, H50-B alteration conflict, H57-A K~Th residuals, H55
conduit/wells, H32-1 tip/Euler (already a parent), H33-D flank and tip protection, and the H48-1 flank rule.

| Rank | ID | Hypothesis (one line) | Status after this session |
|---:|---|---|---|
| 1 | **H58-S1** | Step-overs and accommodation zones (favorable structural settings) mark where new faults sit, so emission should target geometric fault-interaction sites. | Not built. Literature support is strong (Faulds et al. 2026). The public FSS polygon dataset is **not yet verified as downloadable**. |
| 2 | **H58-E1** | Focal-mechanism strike/dip/rake lineations from earthquakes locate active, unmapped faults. | Planned as H57-B and parked. The ComCat service is not reachable from this sandbox. It can run from GitHub Actions. |
| 3 | **H58-M1** | Choose the emission rule by **minimax regret across truth densities**, not by the single full-footprint proxy. | Decision-layer, not geology. Testable now. Observed: H49 has the smaller worst-case regret over the measured candidates. Not a promotion. |
| 4 | **H58-G1** | Isostatic-gravity horizontal-gradient maxima (Blakely–Simpson 1986), >300 m from catalogue. | **Tested this session: NOT CLEARED.** Precision at matched mass is at chance (0.0869 vs 0.0833). Budget infeasible (12,600 eligible). |
| — | (H58-T1) | Flank rule applied to the tip family (H32-1). | **Not new.** Already applied in H48-1 and H33-D. Re-tested this session: it closes most of the proxy gap to B2 (0.09476 → 0.09534). Exploratory only. |

## H58-S1 — favorable-structural-setting (FSS) emission

* **Layers.** Fault-interaction geometry: terminations, intersections, step-overs and relay ramps, accommodation zones, and pull-aparts. The source is the INGENIOUS/Faulds FSS inventory, plus the catalogue trace geometry (vector traces are not in the raster repo; they must be obtained, not inferred).
* **Physical signature.** Transtensional or extensional fault-interaction zones create dilation and fracture permeability, which is the mechanism behind geothermal upflow in the Great Basin ([Faulds et al. 2026](https://pangea.stanford.edu/ERE/db/GeoConf/papers/SGW/2026/Faulds.pdf); [Faulkner et al. 2010, DOI 10.1016/j.jsg.2010.06.009](https://doi.org/10.1016/j.jsg.2010.06.009) for damage-zone permeability).
* **Why it can catch a fault missing from USGS/INGENIOUS.** The FSS paper states that the hidden geothermal systems "likely comprise the majority of geothermal resources in the GBR". The mapped-trace catalogue misses many of the fault-interaction sites that produce those systems.
* **Difference from the repository.** Earlier tip/step-over work (H33-D, H32-1) used Euler and tip geometry on the owner's ridge backbone. An FSS polygon prior has not been used as the emission rule.
* **Expected DTI gain:** unknown; plausible but unmeasured. **Cost:** medium (vector data acquisition and polygon rasterization).
* **Validation needed:** blocked SGMC proxy plus the density grid, with budget matched to B2 (37,654 px) and random controls.
* **Data status:** the FSS inventory is described in the 2026 paper. **Public download not verified in this session.** The INGENIOUS GDR submission [1391](https://gdr.openei.org/submissions/1391) (DOI [10.15121/1881483](https://doi.org/10.15121/1881483)) is public and lists fault and geophysical layers.

## H58-E1 — focal-mechanism lineations

* **Layers.** Event epicentres and moment-tensor or focal-plane solutions from the USGS ComCat FDSN event service (official, free).
* **Physical signature.** Focal planes that align with a regional stress field indicate slip on active faults. Their orientation gives a fault plane, not just a density.
* **Why off-catalogue.** Recent seismicity can occur on unmapped faults. The feature stack already contains earthquake density (bands 10 and 16) but **not** focal-plane orientations, so this is a different signal.
* **Difference from the repository.** H57-B (focal mechanisms) was planned and parked. Earthquake density is in the feature stack and is not focal-plane data.
* **Expected DTI gain:** low to moderate (earthquake locations are sparse in the footprint; the count query returned 98 events in the H57 planning note). **Cost:** medium.
* **Data status:** ComCat is not on this sandbox's allowlist. It must be fetched from GitHub Actions (which has general internet access, per the external-receipt provenance in `data/raw/external_receipt_g30.json`) and hash-pinned.

## H58-M1 — minimax-regret emission choice (decision layer)

* **Idea.** The best candidate depends on the unknown truth density. Pick the candidate whose worst-case regret across the density grid is smallest, instead of the one with the best full-footprint proxy.
* **Observed (this session, measured candidates only):** at 62,122 px B2 trails H49 by 0.00613; at 12,632 px H49 trails B2 by 0.00041. H49 therefore has the smaller maximum regret. This is an observation, not a decision. H49 is not cleared.
* **Why it matters.** It makes the choice explicit, which the owner asked for ("own the outcome"). It also shows that a single proxy number can flip the ranking.
* **Cost:** low, using existing receipts. **Status:** computed, not preregistered.

## H58-G1 — gravity-edge maxima (tested, NOT CLEARED)

Preregistered and scored; see [`h58-gravity-edge-preregistration-20261008.md`](h58-gravity-edge-preregistration-20261008.md) and [`h58-results-20261008.md`](h58-results-20261008.md) §7. The signal is at chance on the SGMC proxy. A variant (band 5 slope, multi-scale edges, or a larger budget) would need a new preregistration.

## Next actions, in order

1. Verify the FSS polygon source (INGENIOUS/GDR or the authors' release) and record its hash-pinned download path. If it cannot be verified, H58-S1 stays unscored.
2. Preregister H58-M1 (regret-based choice) with the density grid frozen, and report it beside the proxy gate.
3. Preregister the flank-pruned union (H58-B2) with its gate written first. It is the only candidate that beat B2 on 4 of 4 quadrants, and it is still below B2 at both sparse densities.
4. Only then consider H58-E1, after ComCat is pinned through GitHub Actions.
