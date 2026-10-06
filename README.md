# GEMSDOE48 — auditable, conflict-aware GEMS research candidate

> **Current decision: research artifact only — not scored, not organizer-validated, and not cleared for a weekly submission slot.** The public-owner-mirror blocked diagnostic is not the competition's private expert-label validation. Do not submit this TIFF unless it later beats the current spatially blocked best under the leakage-aware gate documented below.

## Executive summary and download

**Executive project page:** [`docs/index.html`](docs/index.html).

GEMSDOE48 tests whether two distinct sparse fault-candidate families can be combined without deleting one-family detections or hiding where they disagree. It discounts each binary source opinion by a preregistered symmetric reliability factor `rho = 0.5`, applies normalized Dempster combination, and exports the raw conflict `K` and residual unassigned mass as separate diagnostic rasters.

- **Candidate name:** `GEMSDOE48-DS-FUSION-20261006`
- **Download candidate GeoTIFF:** [`GEMSDOE48-DS-conflict-aware-fusion-20261006.tif`](docs/downloads/GEMSDOE48-DS-conflict-aware-fusion-20261006.tif)
- **Paste-ready competition note (129 characters):**

  `GEMSDOE48 DS fusion | H33-2-B2 dotted + H33-D tip/step-over; rho=0.5; conflict/ignorance diagnostic; unscored research candidate.`

- **Separate diagnostics:** [`unassigned mass m(Theta)`](docs/downloads/GEMSDOE48-unassigned-mass-20261006.tif) · [`raw conflict K`](docs/downloads/GEMSDOE48-raw-conflict-K-20261006.tif)
- **Build receipt / file hashes:** [`evidence/build_receipt_20261006.json`](evidence/build_receipt_20261006.json)
- **Local format audit:** [`evidence/submission_validation_20261006.json`](evidence/submission_validation_20261006.json)
- **Holdout diagnostic:** [`evidence/holdout_20261006.json`](evidence/holdout_20261006.json)

The GeoTIFF follows the official template convention: one `float32` band, EPSG:32611, 100 m pixels, the documented competition grid, finite in-footprint values in `[0,1]`, and `NaN`/NaN-nodata outside the valid footprint. This is a local file audit—not proof that the organizer's upload service will accept it. The in-footprint fault layer is not min–max stretched; its values retain their Dempster-belief interpretation under the stated assumptions.

## User's project prompt — faithful restatement

The starting brief for this repository is to autonomously build an auditable GEMS competition project from the repository and prior work; combine the dotted-family and fault-tip/stepover candidate surfaces with an evidence method that preserves disagreement; and produce a unique, downloadable, competition-format GeoTIFF plus a separate uncertainty/disagreement diagnostic. Before using a submission slot, preregister three to five geological hypotheses, their data layers and physical signatures, why each could find off-catalogue faults, how it differs from prior methods, a ranked expected DTI/cost assessment, verified free-data availability, and spatially blocked holdout validation of the leading candidate. Include a project brief and repeat-use instructions, an executive summary and one-click download, a unique name and paste-ready note, cited sources and limitations, and at least three review passes. Do not use a weekly slot unless the new candidate beats the current spatially blocked best. Work autonomously, prioritize the chance of winning and ownership of the result, verify claims carefully, and flag irregularities. Merge a PR to `main` if feasible.

This is a faithful restatement of the requirements retained in the working session, not a claim that this paragraph reproduces the original prompt verbatim. The ranked slate was frozen before implementation and holdout scoring in [`docs/research/hypotheses-20261006.md`](docs/research/hypotheses-20261006.md) and [`evidence/hypothesis_slate_20261006.json`](evidence/hypothesis_slate_20261006.json).

## Decision gate and evidence status

**No submission slot is cleared.** The input surfaces and labels currently available here came from public third-party owner mirrors, not the competition organizer. The two source surfaces are frozen upstream artifacts; they were not rebuilt independently for each spatial fold, and their generation has used catalogue information or prior catalogue-derived artifacts. A score on these fixed surfaces against mirrored public labels would therefore be conditional and potentially leaky. The label raster is a catalogue proxy, not the private faults manually identified by competition experts. The owner mirrors' reusable license terms were not verified; hash pinning is not permission. Confirm applicable rights before any external submission or redistribution. No holdout result is a leaderboard estimate.

The official leaderboard was read once on 2026-10-06 UTC. That snapshot showed `xiaofanhu` at 0.3774 (#1), `alexoktaba` at 0.3345 (#2), `nchuzhoy` at 0.3262 (#3), and DARD at 0.3195 (#7); it did **not** show 0.3195 as the highest. The displayed 0.2778 row was `extradr19` (#13, 10 submissions). The local H33-2-B2 receipt says “UNSCORED”; no organizer evidence links it to the 0.2778 row. See [`docs/irregularities.md`](docs/irregularities.md). No automatic leaderboard monitor was built.

A numeric proxy pass, if any, is necessary but not sufficient. Promotion requires positive paired mean DTI and improvement on at least 3 of 4 fixed blocks versus **each** source input, plus a leakage-free, fold-independent source rebuild and a validation target appropriate to the competition. If that cannot be done, retain this as an unscored research artifact and do not spend a weekly slot.

The preregistered four-quadrant diagnostic **failed**: mean DTI was 0.032588 for fusion versus 0.086820 for tip/stepover and 0.046406 for arithmetic mean. Fusion lost to both comparators in all four blocks (deltas −0.054232 and −0.013819 respectively); it improved over dotted-only by +0.025757 in 4/4 blocks. This is a conditional, potentially leaky catalogue-proxy measurement, not a competition score. **Do not use a weekly slot for this candidate.** Full fold-by-fold results and caveats: [`docs/research/holdout-results-20261006.md`](docs/research/holdout-results-20261006.md).

## Geological research slate

The five hypotheses below were preregistered; expected DTI is qualitative or explicitly unknown, not fabricated. Full layer descriptions, signatures, rationales, costs, source checks, distinctions from prior methods, and the frozen gate are in the slate.

| Rank | Candidate hypothesis | Expected DTI / cost | Verified-data status |
|---:|---|---|---|
| 1 | H48-1: discounted conflict-aware fusion of dotted and tip/stepover candidate surfaces | Unknown; low implementation cost | Two owner-mirror inputs hash-verified; neither organizer-authenticated |
| 2 | H48-2: stratigraphic-contact topology and geophysical-break coincidence | Potentially moderate; medium-high cost | Official USGS GeMS/SGMC metadata listed; data payload and exact coverage not yet audited |
| 3 | H48-3: persistent OPERA InSAR displacement-gradient discontinuities | Low-moderate public-label DTI potential; high cost | NASA catalog/access metadata checked; no granules or footprint counts downloaded; Earthdata Login required |
| 4 | H48-4: 3D hydrography channel-profile breaks and offsets | Low-moderate, terrain-dependent; medium cost | Official USGS NHDPlus HR/3DEP product pages checked; footprint coverage not audited |
| 5 | H48-5: Great Basin favorability plus ensemble spread as a structural search prior | Unknown, likely low-moderate public DTI; high cost | Official USGS release metadata checked; ~1.22 GB package not downloaded; favorability is not fault truth |

The external hypotheses are research candidates, not production layers. Availability was checked at official catalog/product pages, but exact overlap with the competition grid remains unverified. See [`docs/sources.md`](docs/sources.md) and the cited links in the hypothesis slate.

## Method, outputs, and assumptions

For each source surface `p_i`, the fixed binary-frame mass assignment is:

- `m_i(F) = rho * p_i`
- `m_i(not F) = rho * (1 - p_i)`
- `m_i(Theta) = 1 - rho`, with `rho = 0.5`

The discounted source masses are combined with the normalized Dempster rule. Raw conjunctive conflict is separately recorded as `K = m1(F)m2(not F) + m1(not F)m2(F)`. It is a diagnostic **before** normalization, not mass retained by canonical Dempster combination. The unassigned `m(Theta)` after normalization is the uncertainty layer. For the binary source masks at `rho=0.5`, positive agreement yields fault belief `0.75`; a one-source-only detection yields `1/3` fault belief, `1/3` residual ignorance, and `K=0.25`; negative agreement yields zero fault belief and `0.25` ignorance.

Material assumptions and limitations:

1. The inputs are treated as operational opinions even though they are sparse binary emissions, not calibrated probabilities. A zero may mean “not emitted”, not evidence of no fault.
2. `rho=0.5` is a disclosed symmetric discount chosen to avoid singular total conflict—not an empirically estimated reliability.
3. The sources share 31,614 positive cells (Jaccard 0.6599) and may share a backbone; statistical independence is not assumed.
4. The surface is a fusion of existing candidate artifacts, not a new independently validated geology model. It may fail to improve DTI or discover novel faults.
5. `K` does not remain unassigned under the normalized Dempster rule. It is reported in its own raster so disagreement remains inspectable.

The exact implementation and formulas live in `src/gemsdoe48/evidence.py`; the challenge metric is reproduced in `src/gemsdoe48/metric.py`. Metric equations and file requirements were checked against the [official challenge page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/).

## Reproduce the project

Requires Python 3.10+ and GDAL-compatible Rasterio wheels. The scripts use only public, hash-pinned GitHub owner-mirror files for the conditional catalogue-proxy diagnostic; they do not log into or download from DrivenData.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'

# Restore public owner-mirror labels/template; every downloaded file is SHA-256 checked.
python scripts/restore_proxy_labels.py

# Only the template's finite mask is used. The sample pixel values are never labels.
# The mask is compared cell-by-cell against the mirrored labels' nodata mask.
python scripts/build_footprint_mask.py

# Unit tests, then build the unique submission and its two diagnostics.
pytest
python scripts/build_submission.py
python scripts/validate_submission.py \
  --receipt evidence/submission_validation_20261006.json

# Conditional diagnostic against existing public catalogue labels. This does not clear a slot.
python scripts/run_spatial_holdout.py
```

The hash-pinned source surfaces are restored into `data/source_mirrors/`; public proxy labels/template live in the ignored `data/proxy/`; and the derived footprint mask is reproducible and ignored. The small requested submission and diagnostic TIFFs are shipped in `docs/downloads/`, with their hashes and provenance in the tracked receipts. The mirror files are not silently bundled or redistributed by this repository. Re-running with the same pinned inputs, mask, parameters, Python numerical stack, and script version reproduces the same pixel values; file bytes may differ with GeoTIFF/GDAL versions.

## Review record

Review passes, including formula, provenance, leakage, and output-format checks, are recorded in [`evidence/review_passes_20261006.md`](evidence/review_passes_20261006.md). The project requires a new review if input hashes, fusion parameters, mask, metric implementation, output format, or slot decision changes.

## Sources

- Official competition brief, metric, and required GeoTIFF format: <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>
- Official leaderboard, one read on 2026-10-06 UTC: <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/>
- DrivenData Terms of Use: <https://www.drivendata.org/termsofuse/> (no automated leaderboard monitoring; no further data scraping is implemented)
- Official USGS GeMS/SGMC catalog: <https://doi.org/10.5066/P1A3DQZK>
- NASA OPERA DISP-S1 catalog: <https://www.earthdata.nasa.gov/data/catalog/asf-opera-l3-disp-s1-v1-1>
- USGS NHD product access: <https://www.usgs.gov/national-hydrography/access-national-hydrography-products>
- USGS 3DEP: <https://www.usgs.gov/3d-elevation-program/about-3dep-products-services>
- USGS Great Basin geothermal favorability: <https://www.usgs.gov/data/geothermal-resource-favorability-select-features-and-predictions-united-states-great-basin>
- USGS Great Basin heat-flow catalog: <https://www.sciencebase.gov/catalog/item/6297d2fad34ec53d276c5b28>
- Official forum topic on hidden-label interpretation: <https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516>
- Third-party owner mirrors (not organizer-authenticated): <https://github.com/buffedlizard55-lab/GEMSDOE32>, <https://github.com/buffedlizard55-lab/GEMSDOE33>, pinned label/template mirror commit [`07345ea`](https://github.com/buffedlizard55-lab/GEMSDOE24/tree/07345ea0604953d7efb858d9cfbc21e20c7aca0b).
