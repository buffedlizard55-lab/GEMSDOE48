# Geothermal fault discovery — sourced research note (2026-10-08)

Scope: what official and peer-reviewed sources say about finding faults that host geothermal systems,
and what that implies for a metric that scores only faults the catalogue does not contain. Every
claim cites a page read this session. Claims are labelled by strength:

* **[SOURCE]** stated directly by the cited page;
* **[INFERENCE]** my reasoning from those sources, not stated by them;
* **[UNVERIFIED]** plausible but not checked against a primary source.

## 1. The regional data programme (official, free)

* **INGENIOUS Great Basin Regional Dataset Compilation**, Geothermal Data Repository submission 1391, DOI [10.15121/1881483](https://doi.org/10.15121/1881483), [gdr.openei.org/submissions/1391](https://gdr.openei.org/submissions/1391). **[SOURCE]** The compilation includes earthquake density models, geodetic shear and dilation models, gravity and magnetic maps, and well and spring features, and it is "used in INGENIOUS as input features for predicting geothermal favorability throughout the Great Basin". Its licence and attribution terms were not checked in this session (see the repository's `data/external` notes).
* **Favorability mapping for hydrothermal power resource assessments of the Great Basin** (2025), [ScienceDirect S0375650525002019](https://www.sciencedirect.com/science/article/pii/S0375650525002019). **[SOURCE]** Its evidence layers include "Distance to Nearest Quaternary Fault" and "Distance to Nearest Quaternary Magmatic Activity" (both from INGENIOUS/GDR), magnetic field and isostatic gravity (USGS data releases), depth to basement, strain-rate invariants, and independent and aftershock seismic density.

## 2. Structural setting, not trace position (the strongest geological lead)

* **Faulds et al., "Favorable Structural Settings for Geothermal Systems in the Great Basin Region" (Stanford Geothermal Workshop 2026)**, [pangea.stanford.edu PDF](https://pangea.stanford.edu/ERE/db/GeoConf/papers/SGW/2026/Faulds.pdf). **[SOURCE]** "Favorable structural settings (FSS) along Quaternary faults control the location of many higher temperature geothermal systems"; they include "fault interaction zones, such as terminations, intersections, step-overs (or relay ramps), and accommodation zones", plus pull-aparts and displacement-transfer zones. The authors identified more than 1,430 FSS, occupying about 7.7% of the study area. **[SOURCE]** "The number of KGS and training sites does not account the unknown number of hidden geothermal systems, which likely comprise the majority of geothermal resources in the GBR."
  * **[INFERENCE] Contrarian point 1.** If hidden systems are the majority, a metric that rewards only unmapped faults rewards exactly the population the catalogue cannot see. Recovering it requires *geometric* priors (fault-interaction sites), not more copies of the mapped traces. This supports the tip/step-over family's rationale, and it is why H58-S1 ranks first in the slate.
  * **[INFERENCE] Caveat.** The FSS inventory is not verified as a public raster or vector download in this session. Data availability is therefore **[UNVERIFIED]**.

## 3. Permeability lives in damage zones, which are comparable to the metric's 300 m kernel

* **Faulkner, D.R., et al. (2010), "A review of recent developments concerning the structure, mechanics and fluid flow properties of fault zones", *Journal of Structural Geology* 32(11), 1557–1575**, DOI [10.1016/j.jsg.2010.06.009](https://doi.org/10.1016/j.jsg.2010.06.009). **[SOURCE, via secondary pages that quote it]** Fault-zone permeability depends on the damage zone and on fault architecture; "fracture density reaches 100/m before cataclasis converts the rock to fault core material" (Mitchell & Faulkner 2009, as summarised in a secondary page).
  * **[INFERENCE] Contrarian point 2.** The metric's 300 m kernel may be comparable to damage-zone widths for faults of moderate displacement **[UNVERIFIED: no width-versus-displacement figure was checked against a primary source here]**. If so, a prediction 100–200 m from a mapped trace may sit inside a productive damage zone and still score zero, because the organizers' truth excludes the trace pixels. This is why the flank rule (drop dots within 200 m of the catalogue) is not obviously physically correct, even though it improves the proxy. It removes both useless flank dots and useful damage-zone dots. The data here cannot separate those two effects (IR-H58-10).

## 4. Gravity edges: the physical method is old and sound, the signal here is not

* **Blakely, R.J., and Simpson, R.W. (1986), "Approximating edges of source bodies from magnetic or gravity anomalies", *Geophysics* 51, 1494–1498**, DOI [10.1190/1.1442197](https://doi.org/10.1190/1.1442197); [USGS publication page](https://www.usgs.gov/publications/approximating-edges-source-bodies-magnetic-or-gravity-anomalies). **[SOURCE]** The method locates maxima of the horizontal gradient of potential-field anomalies as the edges of source bodies.
  * **[INFERENCE] Contrarian point 3.** Gravity edges are density contrasts. They include lithologic and basin-margin contacts as well as faults, so the method is not fault-specific. This repository's preregistered test (H58-G1) found the signal at chance on the SGMC proxy (precision 0.0869 vs 0.0833 random; see [results](h58-results-20261008.md) §7). The method remains valid for edges. It does not isolate faults.

## 5. What the sources imply for this competition

1. **Known-fault adjacency is a trap, and the masking rule is the defence.** Models trained on distance-to-mapped-fault features (as in the 2025 favorability paper) will emit near the catalogue. The organizers' masking and the new-fault-only truth penalize exactly that behaviour. The B2 flank rule is one way of acting on this.
2. **Geometry priors may beat trace priors.** FSS and step-over sites are where the literature places most systems. An emission built on fault-interaction geometry would test the strongest geological hypothesis here (H58-S1). Its data availability is not yet verified.
3. **Hypothesis versus data.** Gravity and magnetic edges are cheap to compute from the official stack, but they are not fault-specific. They need a fault-specific filter (for example, alignment with structural trends or with FSS), and that filter has not been built.
4. **Contrarian bottom line [INFERENCE].** The proxies in this repository are not able to distinguish parents that differ by 0.001 to 0.002. The most useful next work is therefore not another proxy number. It is a preregistered geometric prior (H58-S1) tested against the density grid, with the owner's ladder discrepancy resolved first.

## 6. What this note does not establish

* It does not establish that any named FSS, edge, or focal-mechanism signal predicts the hidden competition labels.
* It does not verify the organizers' private labels or their density. The 12,632 px figure in the repository is a withdrawn inversion (see the metric-identity erratum).
* It does not verify the licence terms of the INGENIOUS compilation. The GDR page reports attribution terms that have not been checked against the asset-level licences.

## Sources (all read this session)

1. INGENIOUS GDR submission 1391 — https://gdr.openei.org/submissions/1391 (DOI 10.15121/1881483)
2. Faulds et al. 2026, Stanford Geothermal Workshop — https://pangea.stanford.edu/ERE/db/GeoConf/papers/SGW/2026/Faulds.pdf
3. Favorability mapping for hydrothermal power resource assessments of the Great Basin (2025) — https://www.sciencedirect.com/science/article/pii/S0375650525002019
4. Blakely & Simpson (1986) — https://www.usgs.gov/publications/approximating-edges-source-bodies-magnetic-or-gravity-anomalies (DOI 10.1190/1.1442197)
5. Faulkner et al. (2010), J. Struct. Geol. 32(11) — DOI https://doi.org/10.1016/j.jsg.2010.06.009 (bibliographic details from a secondary listing)
6. DrivenData forum masking clarification — https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516
7. DrivenData problem page (metric and format) — https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
