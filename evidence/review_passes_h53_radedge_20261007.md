# H53-RadEdge-1 review passes — 2026-10-07

**Disposition after three review passes: preserve as a negative research result; do not upload or spend a slot.** The frozen gate failed, and no organizer score/file receipt exists.

## Pass 1 — scientific question, preregistration, and parent classification

- Re-read the owner-reported B2 0.2778 attribution alongside `registry/live_scores.json`, `evidence/source_audit.json`, and the local B2 audit. The safe conclusion remains conditional: the owner-reported ladder 0.2600 → 0.2708 → 0.2778 is algebraically consistent with removing catalogue-adjacent dots that the challenge masks, but no organizer receipt ties 0.2778 to the exact local B2 SHA; local projection is 0.2747 and labelled `UNSCORED`.
- Checked that the three-hypothesis RadEdge slate predates its build/holdout and that its transforms, ranking, expected-DTI priors, and promotion thresholds are preserved. The post-slate data note records source availability only; it does not tune or change the frozen candidate.
- Corrected the family classification: H36-1 rung30 is an H19-5/rung-30 repacking, not the tip/step-over family. H33-D is the explicit tip/step-over parent used in RadEdge-1. The already-merged lidar H53 candidate used H36, so it is a separate experiment and its old score cannot be presented as a B2 × H33-D result.
- **Outcome:** H53-RadEdge-1 scores 0.061821 versus H49 0.100751 on the newer-SGMC off-catalogue proxy, with 0/4 positive folds; it also loses on the older-raster sensitivity and trails both two-source baselines. The preregistered gate fails.

## Pass 2 — source hashes, D-S math, output bytes, and uniqueness

- Re-checked pinned B2 and H33-D parents and the radiometric mirror. H33-D source bytes match SHA-256 `87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757`; the receipt preserves distinct JSON-file and primary-TIFF hashes.
- Reviewed the edge-coherence transform and three-source Dempster implementation. Canonical residual ignorance `m(Theta)` and cumulative raw conflict `K` are separate outputs; conflict is not mislabeled as Dempster uncertainty. Maximum in-footprint mass-sum error is approximately `3.58e-7`. These reliabilities and normalized belief are modeling choices, not calibrated probabilities.
- Independently ran `scripts/validate_submission.py` on the exact RadEdge TIFF: one-band float32, EPSG:32611, 100 m, 3,292 × 3,730, footprint values in [0,1], NaN outside. This is a local format pass only.
- Ran `scripts/audit_h53_artifacts.py`: no exact match among 41 same-grid local TIFFs (re-run after integrating the already-merged lidar H53 artifact). The output is nevertheless highly correlated with the naive two-family mean (Pearson 0.99446; top-budget Jaccard 0.97685), and positive on 99.56% of footprint cells. It is not a useful new ranking on this proxy.

## Pass 3 — integration, public claims, links, and tests

- Reconciled the concurrent merge that had already placed a separate H53-1 lidar candidate on `main`. Namespaced the H33-D/radiometric experiment as **H53-RadEdge-1**, retained both candidates and their original measurements, and linked the namespace/classification errata. No raster samples or holdout values were changed by the namespace correction.
- Checked the landing page and executive summary: RadEdge has a prominent one-click TIFF, unique candidate name and ≤200-character note draft, separate D-S diagnostics, failed-gate warning, scientific limits, and future-only contest steps. The note is archival and must not be pasted for this failed candidate.
- Rechecked local links/anchors across all 26 current HTML pages and 26 current Markdown pages (archived snapshots excluded), JSON parsing for the five principal H53 receipts, and pinned H53/H33-D file hashes. All active references resolve and `git diff --check` passed. A broader scan found stale relative links in the preserved `docs/archive-main-pages/` and `docs/prev-pr*/` snapshots only; these archived pages are not linked as current site content and were not rewritten.
- Ran `PYTHONPATH=src .venv/bin/python -m compileall -q scripts src tests`; it passed. Full suite: `PYTHONPATH=src .venv/bin/python -m pytest -o addopts='' -q` — **286 passed, 3 skipped, 185 subtests passed** (includes three classification/landing-page regression checks).

**Final gate:** keep the competition slot unused. Neither H53 candidate has an organizer score or upload authorization.

## Post-merge integration recheck — H53-A branch

The subsequent H53-A merge added a separate strike-coherence research TIFF; it did not replace either H53-1 or H53-RadEdge-1. I reconciled the landing page, executive summary, method page, and README so all three candidate lines remain distinct and no H36 description calls it the tip/step-over parent. The H53-A note is marked archival/do-not-paste after its failed gate. The earlier archived H53-A preregistration/results are preserved unchanged.

- Re-ran active local-link/anchor checks: **26 HTML and 28 Markdown pages passed** (archived snapshots excluded).
- Re-ran compileall and the full test suite after integration: **307 passed, 3 skipped, 185 subtests passed**.
- Rechecked the 0.2778 summary: the A→B→C algebra is described as consistent with catalogue-mask pruning, not proof; the exact local-B2 attribution remains unverified.
- No candidate is slot-cleared, no organizer score is claimed, and no TIFF was uploaded.
