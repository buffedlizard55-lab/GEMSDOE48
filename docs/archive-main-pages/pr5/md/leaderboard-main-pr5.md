> **ARCHIVED — NOT CURRENT GUIDANCE OR DECISION EVIDENCE.** This file preserves superseded project narrative. Any live-score inversion using `FPw=S−TPw`, hidden-truth count, ceiling, score scenario, or universal break-even threshold is invalidated; do not submit from this archive. Current [overview](../../../index.html) · [metric erratum](../../../research/metric-identity-erratum-20261007.md).

---

> **Historical snapshot from the main branch after PR #5.** Preserved for provenance; superseded by the current no-slot decision. See the [current overview](../../../../../index.html) and [current validation](../../../../../validation.html). Any six-hour leaderboard-feed instructions are obsolete: the current branch disables the workflow under its Terms-of-Use review, and the retained parser has no network-fetch path.

---

# Public leaderboard snapshot and refresh status

**Snapshot read 2026-10-06 via the page-reader tool**, because direct sandbox requests to DrivenData closed during TLS negotiation. It is an observation, not a live-refresh verification. The first 25 rows were visible; rank 25's score was truncated. The corresponding [machine-readable data](../../../data/leaderboard.json) preserves only those visible values. The competition [official board](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) may have changed since then.

| Rank | Participant | Public score | Submissions shown |
|---:|---|---:|---:|
| 1 | xiaofanhu | 0.3774 | 11 |
| 2 | alexoktaba | 0.3345 | 23 |
| 3 | nchuzhoy | 0.3262 | 5 |
| 4 | kinghorton42 | 0.3222 | 8 |
| 5 | joeyfezster | 0.3220 | 22 |
| 6 | Batik Shirt Brothers | 0.3218 | 21 |
| 7 | DARD | 0.3195 | 15 |
| 8 | ndavis7 | 0.2888 | 8 |
| 9 | mzoorob | 0.2884 | 25 |
| 10 | GrigorSargsyan | 0.2876 | 12 |
| 11 | HardcoreTechGod | 0.2854 | 6 |
| 12 | op01 | 0.2792 | 6 |
| 13 | extradr19 | 0.2778 | 10 |
| 14 | wbg1 | 0.2750 | 12 |
| 15 | smashi34 | 0.2710 | 10 |

The project brief identifies a public score of 0.2778 at a GEMSDOE site and associates it with the b2 raster. The observed leaderboard row is 0.2778 at rank 13, participant `extradr19`; **there is no portal-provided TIFF hash linking that row to the local raster**. The participant/owner relationship is not verified. This project did not submit a new candidate and claims no score for one.

## Automated feed

`.github/workflows/feed.yml` schedules `scripts/refresh_leaderboard.py` every six hours and on manual dispatch, then runs `scripts/build_site.py` and commits the static snapshot to the repository's Pages source branch. The parser has offline fixture tests, including the current visible row format and a fail-closed minimum-row rule. A sandbox live HTTP fetch failed at TLS setup, so live parsing and the current workflow's most recent success must be checked in GitHub Actions; do not report it verified until then. Refreshing the visible board does not identify local submission files.

## Comparisons are context, not a candidate recommendation

The reported 0.2778 and the corrected public SGMC proxy are different evidence. The SGMC proxy does not predict leaderboard scores reliably and must not be used to attribute a public row to a TIFF or claim a private score. Current decision: the Yager file's proxy score is below each parent/mean baseline; H48-1 did not beat its reported holdout best. **No candidate is cleared to use a submission slot.** See [decision receipt](../../../index.html), [method and corrected metric](../../../method.html), and [irregularities](../../../irregularities.html).