> **Historical snapshot from the main branch after PR #5.** Preserved for provenance; superseded by the current no-slot decision. See the [current overview](../../../../../index.html) and [current validation](../../../../../validation.html). Any six-hour leaderboard-feed instructions are obsolete: the current branch disables the workflow under its Terms-of-Use review, and the retained parser has no network-fetch path.

---

# Sources (each link opened or resolved in this session unless marked)

## Competition (official)
| what | link | checked |
|---|---|---|
| Competition home | <https://www.drivendata.org/competitions/306/competition-doe-gems/> | brief |
| Problem description, metric, format | <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> | **fetched, metric transcribed** |
| About / resources | <https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/> | brief |
| Data (login required) | <https://www.drivendata.org/competitions/306/competition-doe-gems/data/> | login wall (prior sessions) |
| Leaderboard | <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/> | **fetched 2026-10-06** |
| Rules PDF | <https://docs.nlr.gov/docs/fy26osti/96647.pdf> | brief |
| Reference solution | <https://github.com/drivendataorg/gems-prize-reference-solution> | brief |
| Staff: masked pixels | <https://community.drivendata.org/t/scoring-clarification-masked-pixels-and-re-evaluation/11516> | quoted via GEMSDOE47 (not reachable from sandbox) |
| Staff: what "new fault" means | <https://community.drivendata.org/t/where-do-you-draw-the-line/11536> | quoted via GEMSDOE47 |
| GDR submission 1391 | <https://gdr.openei.org/submissions/1391> | brief |
| GeoDAWN (USGS) | <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and> | linked from page 967 |

## Data used (hash-pinned)
`registry/data_manifest_gemsdoe32.json` lists every mirror with its repo, commit and sha256.
Live-scored files and their hashes are in `registry/live_scores.json`.

## External data — obtainability checks
| source | check | result |
|---|---|---|
| USGS 3DEP 1 m DEM via TNM API | [query](https://tnmaccess.nationalmap.gov/api/v1/products?datasets=Digital%20Elevation%20Model%20(DEM)%201%20meter&bbox=-118.5,39.5,-118.4,39.6&max=2) | 2 tiles returned, public domain |
| USGS ComCat FDSN (older broad query) | [count](https://earthquake.usgs.gov/fdsnws/event/1/count?starttime=2000-01-01&minlatitude=37.3&maxlatitude=40.7&minlongitude=-120.0&maxlongitude=-116.0) | 267,774 across all returned magnitudes; the newer M≥2 query and focal-mechanism counts are recorded below |
| Sentinel-2 L2A (Element84 Earth Search) | [collection](https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a) | resolved, license = Copernicus legal notice |

## Science
| reference | link |
|---|---|
| Dempster, A.P. (1967) Upper and lower probabilities induced by a multivalued mapping. *Ann. Math. Statist.* 38(2):325–339 | <https://doi.org/10.1214/aoms/1177698950> |
| Shafer, G. (1976) *A Mathematical Theory of Evidence*. Princeton University Press | (book) |
| Yager, R.R. (1987) On the Dempster–Shafer framework and new combination rules. *Inf. Sci.* 41:93–137 | cited in <https://www.nature.com/articles/s41598-023-35195-4> |
| Denœux, T. (2008) Conjunctive and disjunctive combination of belief functions induced by nondistinct bodies of evidence. *Artif. Intell.* 172:234–264 | <https://doi.org/10.1016/j.artint.2007.05.008> |
| Evidential belief functions in GIS prospectivity mapping (Carranza & Hale 2003 lineage) | <https://www.tandfonline.com/doi/full/10.1080/27669645.2022.2129132> |
| Mathie et al. (2011) Phreatophytic land-cover map, Great Basin. USGS SIM 3169 | <https://pubs.usgs.gov/sim/3169/sim3169_pamphlet.pdf> |
| Phreatophyte patches vs faults (61 % within 50 m) | <https://www.researchgate.net/publication/321756798_Remote_sensing-derived_fractures_and_shrub_patterns_to_identify_groundwater_dependence> |

## Sibling repositories studied
GEMSDOE32 (0.2778 source): <https://github.com/buffedlizard55-lab/GEMSDOE32> ·
GEMSDOE28 (r1, h32-1, h36-1): <https://github.com/buffedlizard55-lab/GEMSDOE28> ·
GEMSDOE33 (h33-d): <https://github.com/buffedlizard55-lab/GEMSDOE33> ·
GEMSDOE47 (metric algebra): <https://github.com/buffedlizard55-lab/GEMSDOE47>

## Current Yager-candidate and leaderboard checks (2026-10-06)

| topic | official/trusted source | what was checked / limit |
|---|---|---|
| Competition task, score, CRS, grid and outside-footprint format | [DrivenData problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | Task/metric/format statement was read. Data downloads require login. The Yager TIFF uses finite zeros outside to maintain [0,1]; this does not meet the page's null/NaN-outside wording. |
| Public score snapshot | [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Read via page tool on 2026-10-06; #1=0.3774, #7=0.3195, #13=0.2778. Local raw HTML fetch failed TLS, so parser has only fixture tests. No row is linked to a local TIFF hash. |
| Corrected DTI | [official metric page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric) | Exact confidence-weighted TP and full-scene distances are implemented in `src/gems48/validation.py`; unit tests include brute-force small-grid comparison. See the versioned proxy receipt and v1 retraction. |
| Existing-fault mask clarification | [DrivenData staff response](https://community.drivendata.org/t/scoring-clarification-masked-pixels-and-re-evaluation/11516) | Staff say known USGS/INGENIOUS pixels are excluded. Proxy code masks exact catalogue pixels; 300 m target-buffer is a local proxy choice, not staff instruction. |
| GeoDAWN magnetic/radiometric source | [USGS ScienceBase item](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7), DOI [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ) | Public area TIF archive metadata are listed. Binary transfer failed TLS from this sandbox; bytes, checksums, and grid alignment were not checked. |
| Independent Nevada gravity | [USGS Data Series 42](https://pubs.usgs.gov/dds/dds-42/), DOI [10.3133/ds42](https://doi.org/10.3133/ds42) | USGS page reports about 80,000 stations and lists a 4.2 MB data ZIP. Page/link read; file bytes not retrieved. Gridding and uncertainty remain to be validated. |
| Potential-field boundary rationale | [USGS pymaxspots](https://www.usgs.gov/software/pymaxspots-computing-and-connecting-horizontal-gradient-maxima-potential-field-geophysics), DOI [10.5066/P13FSKEM](https://doi.org/10.5066/P13FSKEM) | USGS describes horizontal-gradient maxima as possible abrupt field boundaries (faults, intrusions, contacts); a maximum is not automatically a fault. |
| 3DEP availability and use | [USGS 3DEP products/services](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) | USGS says products are free and without use restrictions. Exact 1 m coverage per validation block and tile seams were not audited. |
| ComCat availability for the study bbox | [USGS FDSN documentation](https://earthquake.usgs.gov/fdsnws/event/1/) · [count query: events](https://earthquake.usgs.gov/fdsnws/event/1/count?format=text&starttime=2000-01-01&minlatitude=37.3641&maxlatitude=40.7247&minlongitude=-120.0024&maxlongitude=-116.1415&minmagnitude=2.0) · [focal mechanisms](https://earthquake.usgs.gov/fdsnws/event/1/count?format=text&starttime=2000-01-01&minlatitude=37.3641&maxlatitude=40.7247&minlongitude=-120.0024&maxlongitude=-116.1415&minmagnitude=2.0&producttype=focal-mechanism) · [moment tensors](https://earthquake.usgs.gov/fdsnws/event/1/count?format=text&starttime=2000-01-01&minlatitude=37.3641&maxlatitude=40.7247&minlongitude=-120.0024&maxlongitude=-116.1415&minmagnitude=2.0&producttype=moment-tensor) | Live counts on 2026-10-06: 16,919 events, 5,292 focal-mechanism products, and 474 moment-tensor products. Count availability only; event payload was not ingested. Full query parameters and limitations: [`data/source-checks.json`](../../../data/source-checks.json). |
| Earlier TMI persistence result | [GEMSDOE47 H47-B report](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/docs/validation-h47b-20261006.md) (owner-authored) | Owner report says locked public-catalogue DTI 0.02755 vs random 0.03716; not an organizer score or independent replication. Supports treating TMI-only persistence as previously tested. |
| External-data rules | [DrivenData contest rules](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/) · [GEMS Prize Rules](https://www.herox.com/GEMSPrize/resource/2274) | Verify source/derivative license permits challenge use and sponsor sharing before using any external layer. |

The machine-readable [`source-checks.json`](../../../data/source-checks.json) records dates, bbox parameters, live-fetch failures, catalog limitations, and owner-derived SGMC provenance. The source listing itself does not establish spatial coverage, license compatibility, or predictive value.
