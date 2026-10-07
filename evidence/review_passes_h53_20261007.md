# H53 review passes — 2026-10-07 UTC

## Pass 1 — implement completely and verify

* Preregistered slate first: `docs/research/hypotheses-h53-20261007.md` +
  `evidence/hypothesis_slate_h53_20261007.json` (5 hypotheses ranked by
  expected DTI and cost; H53-1 constants frozen from label-free quantiles
  only, before any proxy scoring).
* Implemented `src/gemsdoe48/ds53.py` + `tests/test_h53.py` (10 tests:
  ramp anchors, mass conservation, commutativity/associativity, vacuous
  third source, conflict semantics, m(Θ) > 0, footprint normalization,
  not-the-mean closed form, slate-constant match). Two test bugs found and
  fixed during Pass 1 (normalized-vs-naive collapse on single-pixel
  beliefs; kernel-support cell-count threshold).
* Implemented `scripts/build_submission_h53.py` (SHA pins, slate-drift
  guard, row-chunked exact fusion for the 3 GB sandbox, NaN-outside
  primary + zeros twin + pignistic twin + 4 diagnostics + zip,
  anti-average checks vs two baselines, SHA uniqueness vs all local TIFs,
  twin-overlap table, post-rename byte audit). One bug fixed: the 7-band
  lidar product tripped the single-band grid assertion (grid-identity
  check now bypasses the band count).
* Built deterministically (byte-identical rebuild, SHA `9242c831…`, 0
  collisions vs 58 rasters). Format audits pass for both scored files.
* Scored all four preregistered holdout runs with the official script:
  graded newer 0.07140846, twin newer 0.08955914, graded raw 0.070510,
  twin raw 0.088542. Gate fails (0/4 folds vs H49 for both files).
* Verified cross-run comparability claim by reading
  `scripts/holdout_h51.py` (same pinned truth, 62,122 positives asserted,
  same quadrants/halo/metric) before comparing H53 means to H50/H51/H36.
* Full suite: 279 passed, 3 skipped, 185 subtests passed.
* Site: H53 download-first blocks on `docs/index.html` and
  `docs/executive-summary.html` (with reference-only portal steps),
  validation/hypotheses/method/next-steps/irregularities/submission-guide
  updates, README session header + reproduce commands.

## Pass 2 — bugs, missing requirements, edge cases

* Fixed misleading receipt path (temp name → shipped path) with a
  post-rename re-open byte audit in the builder; rebuilt and re-verified.
* Caught and fixed invented precision: validation-table fold values now
  copied exactly from the holdout JSONs (8 dp); all paired deltas
  re-computed from receipts (graded vs H49 −0.029343, twin vs H49
  −0.011192, vs union −0.025583/−0.007433, all 0/4).
* Verified all new artifacts by re-opening: zeros twin all-finite [0,1]
  with zeros outside and in-footprint identity to primary; all four
  diagnostics finite-in/NaN-out/[0,1]; twin strictly binary with 37,654
  support; zip holds exactly one TIF with clean `testzip`.
* Verified every local href on all touched pages resolves; all H53
  evidence JSON parses.
* Verified citations by web search (this log's §Citations): Dempster 1967
  (doi:10.1214/aoms/1177698950), Shafer 1976 (Princeton UP), Mercier–Quost–
  Denœux contextual discounting (ECSQARU 2005, Springer link), Bucknam &
  Anderson 1979 (Geology 7, 11–14), NLCD 2021 CONUS (mrlc.gov,
  doi:10.5066/P9JZ7AO3). Corrected the slate's "Mercier et al.
  (2005–2008)" and the unverified NLCD deep URL.
* Logged irregularities: H52 19-band lifts lack committed receipts;
  sandbox allowlist blocks fresh leaderboard/USGS reads; twin↔H51 overlap
  vs hash-distinctness; graded diffuseness by construction.
* `registry/inputs.json` timestamp bump is a test side-effect
  (digests unchanged); kept.
* Updated README test count (262 → 279) and added the H53 method section.

## Pass 3 — re-check against the original brief

* Unique TIF submission (not a copy): graded NaN-outside primary +
  binary twin, SHA-unique vs 58 local rasters, first 3-source adaptive
  fusion in the campaign. ✓
* DS combination of best dotted (0.2778) × best tip (0.2710) preserving
  disagreement: canonical Dempster with m(Θ), K_AB, K_ABL diagnostics. ✓
* Normalized to [0,1], required format, not-the-average verified
  (Pearson 0.86 vs mean3, max |Δ| 0.47, top-budget Jaccard 0.55). ✓
* Easy download at top of site + executive-summary subpage with exact
  portal steps + unique name + ≤200-char note. ✓
* "Predicted values must be in range [0, 1]" addressed: in-footprint
  finite [0,1], NaN/nodata outside, zeros twin immune; both scored files
  pass `validate_submission.py`. ✓
* Why-0.2778 PhD-level answer + beat-it verdict: live-ladder bookkeeping
  (≈37 % hidden-mass recovery), H53 extends the no-fusion-beats-parent
  finding to three sources; H53-2 v2 detector is the path. ✓
* 3–5 new hypotheses with layers/signatures/off-catalogue rationale/
  differences, ranked by expected DTI and cost; top implementable
  candidate (H53-1) validated on the blocked holdout before any slot;
  non-viable-without-new-data items name free official sources with
  obtainability checked (USGS 3DEP public bucket with H52 CI precedent;
  NLCD free via mrlc.gov; InSAR/strain recorded not-viable). ✓
* No slot spent or recommended: gate failed, decision stated on every
  touched page. ✓
* Prompt-in-README + core values: standing brief already verbatim in
  README (re-read at session start); H53 session header added. P(Win)
  was maximized by testing the most generous fusion variant once,
  closing the fusion line honestly, and pointing the next session at
  the only remaining lever (v2 extraction). ✓
* Limitations stated: no organizer score/acceptance anywhere; proxies
  are public-map, possibly leaky; owner-reported anchors; sandbox
  egress limits. ✓

## §Citations (verified 2026-10-07 by web search)

* Dempster 1967: https://link.springer.com/chapter/10.1007/978-0-387-34897-1_4
  (ref list); paper doi:10.1214/aoms/1177698950 (via scirp reference page).
* Shafer 1976: Princeton UP (via the same Springer ref list).
* Mercier–Quost–Denœux 2005: https://link.springer.com/chapter/10.1007/11518655_47
  (+ IPMU 2006 follow-up via Denœux publication list).
* Bucknam & Anderson 1979: https://www.nationalacademies.org/read/624/chapter/14
  (ref: Geology 7, 11–14).
* NLCD 2021 CONUS: https://www.mrlc.gov/faq (free direct download);
  dataset doi:10.5066/P9JZ7AO3 (via Miami GDSC mirror page).
