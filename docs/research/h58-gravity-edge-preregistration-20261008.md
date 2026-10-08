# H58-G1 preregistration — isostatic-gravity edge maxima (Blakely–Simpson), off-catalogue

**Status: FROZEN before scoring (2026-10-08).** Parameters below are fixed; any change requires a new
preregistration entry, not an edit to this one.

## Hypothesis

Density contrasts across buried basement steps and lithologic boundaries produce maxima of the
horizontal gradient of the isostatic gravity anomaly. Blakely and Simpson (1986) give the standard
automated edge-location method: local maxima of the horizontal-gradient magnitude mark the
approximate location of abrupt lateral density changes
([USGS publication page](https://www.usgs.gov/publications/approximating-edges-source-bodies-magnetic-or-gravity-anomalies);
*Geophysics* 51, 1494–1498, DOI [10.1190/1.1442197](https://doi.org/10.1190/1.1442197)).

If a gravity edge lies more than 300 m from every catalogue trace, it is a candidate for a fault or
fault-bounded boundary that the USGS/INGENIOUS catalogue does not contain. That is the only reason
it could add metric credit that the parents lack.

**What it is not:** an edge is not a fault. Lithologic contacts also produce gravity edges, so the
SGMC off-catalogue proxy may favour this signal for reasons unrelated to faulting. Treat any gain as
evidence about a proxy, not about faults.

## Layers (official feature stack, not labels)

* `data/raw/training_features.tif` (SHA-256 `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`;
  restored from the repo's pinned owner mirror, not organizer-authenticated). Band 13,
  `iso_grav_anom` — "Isostatic gravity anomaly - gravity after compensating for topographic mass".
  Band 18 (`iso_grav_anom_hg`) takes both signs, so it is **not** a gradient magnitude and is not used.
* The magnitude is computed from band 13 on the 100 m grid with `np.gradient`.
* Catalogue: `data/official/labels.tif` (public catalogue, 60,988 px), used only for the distance filter below.
* Public proxy truth: SGMC off-catalogue (`data/official/derived_sgmc_faults_100m.tif`, >300 m from catalogue,
  62,122 px), exactly as in `scripts/run_spatial_holdout.py`.

## Frozen procedure

1. Restrict to the footprint `data/source_mirrors/footprint-mask.tif`. Compute `G = sqrt(gx² + gy²)`.
   Exclude any cell with a non-finite or out-of-footprint 8-neighbour.
2. Edge candidates: cells where `G` is ≥ all 8 neighbours (3×3 local maximum; ties kept).
3. Off-catalogue filter: keep candidates whose distance to the catalogue is **> 300 m**.
4. Budget: keep the **top 37,654 candidates by G** (budget matched to the dotted B2 parent, so
   emitted mass is equal). Emit value 1.0 on the kept cells, 0 elsewhere.
5. Controls, same budget: (a) a uniform random budget of 37,654 footprint cells (seeds 1–5, mean);
   (b) the dotted B2 parent (owner 0.2778); (c) the H58 dot-supported DS artifact (this session).
6. Scoring: the official metric (`src/gemsdoe48/metric.py`), with pixel-exact catalogue cells zeroed in
   predictions (organizer clarification, 2026-09-21), on (i) the full footprint and (ii) four spatial
   quadrants with a 300 m halo and core-only truth (`scripts/build_h58_ds_b2_h32.py`, quadrant protocol).
   The truth-density sensitivity (25,000 and 12,632 px random draws, seeds 1–3) is also reported.

## Decision rule (frozen)

The candidate **passes the proxy gate** only if all three hold:

* (a) full-footprint DTI > dotted B2 DTI on the SGMC off-catalogue proxy;
* (b) it beats dotted B2 in **≥ 3 of 4** quadrants;
* (c) it beats dotted B2 in mean DTI at **both** the 25,000 px and 12,632 px truth densities.

A pass means only "eligible to be considered for a preregistered slot review". It does not clear a
submission: no organizer or private-label evidence exists in this repository, and AGENTS.md's gate
also requires that the proxy and source construction are defensible against leakage.

## Known limits (stated before scoring)

* The public proxy is a published map, not expert new-fault labels. Its truth density (62,122 px) is an
  assumption. Earlier repository densities were withdrawn with the metric-identity erratum.
* Gravity-edge maxima are not fault-specific.
* The gate uses fixed budgets and fixed quadrants. Rank reversals with density are already documented
  (`evidence/holdout_h58_density_20261008.json`).
