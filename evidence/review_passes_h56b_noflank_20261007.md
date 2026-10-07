# Three-pass final review — H56B-NF / metric errata

Date: 2026-10-07. Branch: `arena/c75bda84-gemsdoe48`. This record distinguishes local verification from private-label validation and organizer acceptance.

## Pass 1 — requirements, result interpretation, and slot decision

- Confirmed the requested current TIFF is the unique local H56B-NF Dempster–Shafer ablation combining owner-mirror dotted B2 with the actual H33-D tip/step-over parent. It is post hoc, not a new geological detector or verified preregistered candidate.
- Verified the public-facing pages distinguish **download OK for inspection** from **submit not recommended**. The recommendation is no upload/no slot: H56B-NF loses to H49 on 4/4 catalogue folds and 4/4 SGMC-off-catalogue folds.
- Confirmed the local B2 artifact is labeled `UNSCORED` by its producer and no organizer receipt links exact B2 bytes to the owner-reported 0.2778. The pruning/tapered-credit explanation is explicitly labeled plausible, not causal proof.
- Confirmed no H56B-NF score above 0.2778 or the dated 0.3195 target is offered as a prediction. The 0.0649 and H55/H54-derived bounds are withdrawn.
- Confirmed the separate frozen H56-F dotted-parent pruning ladder was measured offline: all three thresholds lose to H49 on all four folds for both public proxies. It is distinct from H56B-NF and from the five unbuilt H57 ideas; neither screen clears a weekly slot.
- Confirmed the five unbuilt H57 hypotheses and their layer, physical signature, off-catalogue rationale, prior-art distinction, expected DTI impact, cost, and source availability are linked from the current site. No weekly slot is cleared.
- Confirmed no leaderboard polling was performed and the current snapshot was minimized to scores/ranks needed for dated context; no names, row table, or submission counts are republished.

## Pass 2 — metric, evidence semantics, code, and edge cases

- Rechecked the official metric identity: `TPw=T` is truth-centred, `FPw=S−Q` uses prediction-centred `Q`, and generally `Q≠T`. The old `FPw=S−TPw` live-model inversions and dependent thresholds/projections are marked withdrawn.
- Added the coordinate-wise endpoint proof: with other pixels fixed, `T(v)` is convex piecewise-linear, `F(v)=S−Q` is affine nondecreasing, derivative sign is constant on each segment and can only move negative-to-positive at breakpoints. This proves a binary maximizer exists for nonempty truth, but does not justify any fixed threshold or claim that binarizing a particular graded D-S field improves it.
- Replaced the old one-pixel-only binary-optimality test with a deterministic small-raster coordinate-replacement test. The test checks endpoint choice never lowers DTI and the final binary raster is no worse; the derivation, not randomized testing, is the general proof.
- Rechecked D-S semantics: `m(Theta)` is residual uncommitted/ignorance after normalized Dempster; raw `K` is separate pre-normalization conflict divided out; support difference is not a mass. The primary differs numerically from arithmetic means, with the high normalized-kernel-mean correlation disclosed as a limitation, not a quality claim.
- Rechecked artifact facts against receipts: SHA-256 `b9530b70065da1f5e9da82caf4f5aaba3d7175dbbbfb2851e4b2ab2dd13aa4f1`; float32, EPSG:32611, 3292×3730, finite in-footprint values in `[0,1]`, NaN/nodata outside. Local format/recomputation audits do not imply organizer acceptance; `portal_range_error_immune=false` remains explicit.
- Reviewed the separately committed H56-F evaluator, mask/threshold primitive, and machine receipt. It thresholds a pinned H56B surface only at dotted-parent pixels, records retained/removed counts, and reports public-proxy folds without a private-score inference. The report and receipt are now linked from the site.

## Pass 3 — README/site, provenance, and release checks

- Reviewed the visible README and site for stale H52/H54/H55 metric-model projections, the old H55 GATE-2 interpretation, portal-acceptance overclaims, and unsupported “binary-optimal” threshold language. Replaced current summaries and kept historical receipts labeled as audit-only.
- Preserved the original project brief/aims in README while adding dated corrections. Updated research, method, validation, hypotheses, irregularities, sources, and submission-status pages. Archived H55/H56 model analyses now carry explicit corrections; removed operational H55 upload instructions and the invalid live-equivalent submission note.
- Minimized the leaderboard JSON and updated site renderers so no participant table/names are republished. Reworded H49’s public-proxy change without the withdrawn live-score bracket.
- Synced the fixed working branch with the then-current `origin/main` (PR #20) to avoid basing the requested PR on stale main. Preserved its H56-F blocked result and receipts while keeping the stricter metric-validation code and current H56B-NF verdict; all merge conflicts were resolved and reviewed.
- Local HTML audits: before sync, **16 changed pages / 363 references / 0 missing**; after sync and H56-F links, **7 newly changed pages / 239 references / 0 missing**. These check local path existence, not external URL availability or browser rendering.
- Final post-sync `./.venv/bin/pytest -q`: passed; 3 tests skipped by their documented data-availability conditions.
- `./.venv/bin/python -m compileall -q src scripts tests`: passed.
- `git diff --check`: passed.

## Remaining limitations

Private expert labels are unavailable; owner-reported scores are not organizer receipts; public proxies are not validated substitutes and candidate surfaces/upstream sources were not rebuilt independently inside every fold; H56B-NF is post hoc; portal NaN acceptance is untested; no organizer score, upload, or acceptance is claimed. These limitations do not change the no-slot recommendation.
