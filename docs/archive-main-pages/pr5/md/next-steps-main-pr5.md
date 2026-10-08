> **ARCHIVED — NOT CURRENT GUIDANCE OR DECISION EVIDENCE.** This file preserves superseded project narrative. Any live-score inversion using `FPw=S−TPw`, hidden-truth count, ceiling, score scenario, or universal break-even threshold is invalidated; do not submit from this archive. Current [overview](../../../index.html) · [metric erratum](../../../research/metric-identity-erratum-20261007.md).

---

> **Historical snapshot from the main branch after PR #5.** Preserved for provenance; superseded by the current no-slot decision. See the [current overview](../../../../../index.html) and [current validation](../../../../../validation.html). Any six-hour leaderboard-feed instructions are obsolete: the current branch disables the workflow under its Terms-of-Use review, and the retained parser has no network-fetch path.

---

# Next steps, ranked by expected P(Win) and evidence value

1. **Keep the slot gate closed.** The corrected H48-Yager proxy failed (0.08407 vs tip 0.09709, dotted 0.09613, naïve mean 0.09030; 0/4 quadrant wins). H48-1 did not beat its holdout best. PR #6's DS48 re-emission measures 0.09068 on its SGMC off-catalogue proxy vs 0.09613 for dotted; its catalogue-based proxy is anti-monotone with the known live ladder. All remain unscored research artifacts. Do not spend a competition slot on any of them or an unvalidated probe.
2. **Validate N1 native-resolution 1 m DEM detection without using a slot.** On a GitHub Actions runner with egress, inventory official 3DEP tiles over the exact spatial blocks, record tile IDs/checksums/CRS/seams, derive native-resolution scarp features, aggregate to the submission grid, and run the preregistered corrected spatial holdout. No numeric gain target is assumed; stop if full coverage/licensing or reproducible validation fails.
3. **Stage N2 gravity–magnetic edge coherence** only after the competition feature stack or official public GeoDAWN/gravity files are actually retrieved and aligned. Audit coverage, survey seams, geotransforms and contest terms before implementing a detector. Validate on fixed spatial blocks against the current best baselines.
4. **Consider N3 ComCat planes or N4 drainage deflections** only with uncertainty controls and a pre-registered holdout. ComCat counts establish availability, not usable geometry; 1 m DEM catalog listing establishes neither full coverage nor validation.
5. **Treat N5 radiometric asymmetry as lower priority.** Related scarp–radiometric concordance was previously explored; test only the distinct signed, cross-strike feature after source bytes and survey metadata are available.
6. **Historical recommendation (superseded): monitor the six-hour leaderboard Action.** The workflow references in this archive are obsolete: the current branch disables scheduled leaderboard access and the parser is offline-only. Never infer a leaderboard row's TIFF hash or score attribution.
7. **Extend the bounded uniqueness/data audit** only if it changes a decision: keep owner mirror hashes, CRS/bounds, external-data license checks, and exact candidate-to-score provenance explicit.

## Limitations / access needed

* **DrivenData login:** unavailable; no private scores, portal acceptance, or organizer-input download is possible here.
* **Network:** local TLS to DrivenData/USGS hosts failed for raw page/binary requests. The public ComCat count queries and catalog/page metadata were read, but they do not replace event/raster files. GitHub Actions runners may have egress; verify the run before relying on it.
* **Compute:** sandbox is constrained; native 1 m processing should be tiled and audited. No GPU is needed for the current raster/metric work.
* **Truth:** SGMC is an owner-derived public geologic-map proxy, not hidden expert truth. Its relationship with leaderboard performance is poor/uncertain; never call its DTI an organizer score.
* **Format:** the present Yager file is all finite in [0,1] but stores zero outside, contrary to official null/NaN-outside text. Portal acceptance remains unknown.

See [hypotheses](../../../hypotheses.html), [method](../../../method.html), [irregularities](../../../irregularities.html), and [source checks](../../../data/source-checks.json).