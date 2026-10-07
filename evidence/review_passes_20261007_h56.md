# H56 session — three-pass review log (2026-10-07)

## Pass 1 — implement completely
- `scripts/build_submission_h56.py`: frozen-recipe Dempster–Shafer belief builder
  (metric-kernel BPA, live-anchored discounts 0.95 / 0.95×0.2632/0.2778, backbone absence
  0.5/0.2, dotted-only flank absence 1.0, Dempster normalized rule, Bel normalized to [0,1],
  zeros outside footprint). Pins verified: dotted c55bafc4…, tip 87f857d5…, backbone ec1f9b56…,
  template 2176d08e…, labels 7ba308cc…, SGMC 643cbe99….
- Primary TIF + zip + NaN twin + diagnostics (m(Θ), K, Pl) written to docs/downloads/.
- `scripts/validate_h56.py`: 10-check format audit; uniqueness against all 67 downloads +
  registry pins; blocked holdout (H55 protocol, 4 quadrants, 300 m halo, 2 truths);
  live-model projection with sanity reconstruction (C at 0.2728, Cov 75,206.82023682502 vs
  calibration 75,206.82023682503); pre-registered G1/G2/G3 verdict.
- `scripts/h56_research_battery.py`: staged band screen (19 bands), H55-B strain-ridge field,
  H56-A DEMGLOW ladder + same-mass controls, conduit/basement stats.
- Docs: index/executive-summary/submission-guide/hypotheses/validation/next-steps/method/sources
  updated; pre-H56 pages archived from git HEAD into docs/archive-main-pages/pre-h56-20261007/.
- README: H56 decision block, submission section, slate summary, verbatim session prompt appendix.
- knowledge/research_notes.md: band inventory, screen table, killed candidates, reproductions.
- tests/test_site_h56.py added; tests/test_site_h55.py updated for the moved download card.

## Pass 2 — bug / requirement / edge-case review
1. **Live-model Cov bug found and fixed.** First projection reconstructed dotted-C at 0.1366
   instead of the calibration's 0.2728 (factor 2). Root cause: Cov had been computed as the
   kernel-max per prediction instead of the calibration's kernel-weighted truth credit
   Σ_g max_x p(x)k(d). Fixed to `weighted_tp_credit(p, B_elig)`; reconstruction now exact to
   14 decimals. All H56 numbers re-run after the fix.
2. **Nodata contamination in battery (IR-H56-02)**: first battery runs read the official raster
   without masking −3.4e38; caught via ladder-count comparison, fixed, final evidence regenerated.
3. **OOM kills on the 3 GB sandbox**: two silent kills of the battery; fixed by float32 band
   storage, staged checkpoints and on-demand band reads.
4. **Archive mistake caught**: the pre-H56 archive initially captured post-edit pages; replaced
   with `git show HEAD:docs/<page>` versions (0 H56 references, verified).
5. Requirement sweep against the brief: unique TIF ✓; obvious download/submit verdict banner on
   index, executive summary and guide ✓; DS combination of the two best families ✓; m(Θ) as own
   diagnostic ✓; Bel normalized to [0,1] ✓; naive-mean check ✓ (r = 0.389 binary, affine residual
   0.0111 kernel); range-error immunity ✓; unique name + 231-char note ✓; 3–5 hypotheses ranked ✓
   (5, two measured dead before any slot); prompt in README ✓; executive summary subpage ✓;
   GEMSDOE32 study ✓ (source repo fetched; UNSCORED/0.2747 note re-verified; IR-H56-01).
6. G2 gate fairness check: holdout fold medians taken from footprint row/col (matches H55
   evidence: catalogue NW fold n_truth 29,319 in both) — protocol continuity verified.

## Pass 3 — final re-check against the original request
- `python -m pytest -q tests` → all pass (3 pre-existing skips; test_site_h56 8 tests, updated
  test_site_h55 11 tests all green).
- Banner text on all three decision pages states the gates' computed outcome verbatim; no page
  claims an organizer score; diagnostics labelled "not submissions" on every page that lists them.
- "Is it OK to download and submit?" answered with one banner: DOWNLOAD OK (format-verified,
  unique, range-immune) — SUBMIT NOT RECOMMENDED (projection 0.0649 < 0.2778; holdout fails G2).
- Honest-status doctrine preserved: the requested graded surface is published exactly as
  specified AND the same page says it should not spend the slot; the improvement path is the
  slate (H56-F first), not the fusion.
- PR to be opened from arena/2a400049-gemsdoe48 and merged to main.

## Residual limitations (carried to next steps)
- No DrivenData auth: organizer data and live scoring remain human-only steps.
- 0.2778 attribution still OWNER-REPORT class (IR-H56-01 hardens the caveat).
- Sandbox egress: GitHub/PyPI/npm only; USGS/GDR/DrivenData hosts unreachable here, so runner
  pipelines carry anything native-resolution.
- The H56-F removal ladder needs one live slot to resolve — the single highest-information
  experiment identified this session.

## Pass 4 — merge reconciliation with the concurrent H56 open-world session (PR #17)

While PR #18 was open, a concurrent session merged its own H56 effort to main (commit 55cc9b6,
"H56 open-world D-S research artifact": OWDS B2×H33-D GeoTIFF 1f7b5a4f18db, Hessian-only
H56-A probe, own slate and receipts). Both sessions responded to the same brief with the same
verdict class (download OK, do not submit). Resolution, keeping both works intact:

- This session renamed to H56B: `scripts/build_submission_h56_belief.py`,
  `evidence/build_h56_belief_receipt_20261007.json`, `evidence/hypothesis_slate_h56b_20261007.json`;
  all page and test references updated; the submission filename itself was already unique
  (content id 9ec0d605c45b).
- README: H56B decision block first, then the open-world decision, then H55-previous; sections
  ordered H56B submission → H56B slate → open-world OWDS → H55. Duplicated H55 decision
  paragraphs collapsed to one.
- Site: index/executive-summary carry the H56B banner card first, then the OWDS card, then the
  preserved H55 card; submission-guide, validation and next-steps re-gained their H56B sections
  above the open-world content; hypotheses.html carries the H56B slate, then the open-world
  slate, then the preserved H55 slate. HTML tag balance verified programmatically on every page.
- tests/test_site_h55.py keeps the concurrent session's assertions and is extended so BOTH
  current H56 downloads must sit above the preserved H55 card; tests/test_site_h56.py reads the
  belief receipt. Full suite green.
