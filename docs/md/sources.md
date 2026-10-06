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
| USGS ComCat FDSN | [count](https://earthquake.usgs.gov/fdsnws/event/1/count?starttime=2000-01-01&minlatitude=37.3&maxlatitude=40.7&minlongitude=-120.0&maxlongitude=-116.0) | 267,774 |
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
