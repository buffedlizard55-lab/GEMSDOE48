# H56B review: score evidence, artifact identity, D-S assumptions, and chronology — 2026-10-07

**Decision: OK to download for inspection; SUBMIT NOT RECOMMENDED. No weekly slot is cleared.** This report separates owner-reported leaderboard context, local file checks, public-map proxy diagnostics, and unobserved private-label performance. It does not claim organizer acceptance or a score prediction.

## Why 0.2778 may have scored well — plausible mechanism, not established cause

The official challenge metric uses a 300 m triangular distance kernel and distance-weighted Tversky weights α=0.2, β=0.8. Predictions near a fault can receive partial credit; the false-positive penalty is also less heavily weighted than the false-negative term. The owner-reported B2 surface is described as spacing-tuned and pruned. Under that metric, removing low-credit predictions—particularly dots near a known-fault mask—or concentrating the remaining dots on higher-credit corridors could plausibly improve DTI. That is a mechanism consistent with the record, not a causal attribution.

The exact local B2 TIFF is labelled `UNSCORED` in its local producer record; no organizer receipt links its bytes to a leaderboard row. The one-time public leaderboard observation is context only. It cannot show that B2's local bytes earned 0.2778, that the new H56B files were scored, or that the private expert labels share the proxy patterns. See [`why-02778-and-ceiling-20261007.md`](why-02778-and-ceiling-20261007.md) and [`evidence/source_audit.json`](../../evidence/source_audit.json).

## Is a score above 0.2778 or 0.3195 supportable?

A score above 0.2778 is possible in principle, and the one-time leaderboard observation included displayed values above it. But no score above 0.2778—and especially not 0.3195—is supportable as a prediction for either H56B raster or any local file from the evidence here. The private test labels are unavailable. The old H56B live-equivalent projection `0.0649`, the fitted `0.2843` ceiling, hidden-truth inversions, and universal per-dot threshold claims relied on the generally false identity `FPw = S − TPw`; the official metric instead uses `FPw = S − Q`. Those surrogate figures are withdrawn, not score bounds. The corrected equations and executable counterexample are in [`metric-identity-erratum-20261007.md`](metric-identity-erratum-20261007.md).

The leaderboard was read once on 2026-10-07: top displayed value 0.3774; 0.3195 at rank 7; 0.2778 at rank 13 (11 displayed submissions at that observation). The display is not permanent, has no file-to-score receipt, and is not polled. The DrivenData Terms of Use prohibit unauthorized automated monitoring/copying and also manual monitoring/copying without written consent.

## Current research artifact: H56B-NF no-catalogue-flank ablation

- **Download:** [`GEMSDOE48-H56B-NF-DS-dotted-x-tip-20261007-5bb2c03c981e-nan-outside.tif`](../../docs/downloads/GEMSDOE48-H56B-NF-DS-dotted-x-tip-20261007-5bb2c03c981e-nan-outside.tif)
- **SHA-256:** `b9530b70065da1f5e9da82caf4f5aaba3d7175dbbbfb2851e4b2ab2dd13aa4f1`
- **Format:** single-band float32, EPSG:32611, 100 m, 3,292 × 3,730; in-footprint range `[0,1]`; NaN/nodata outside.
- **What changed:** this is a post-hoc Dempster–Shafer mass-assignment ablation of the earlier H56B recipe. It removes the dotted-only catalogue-flank absence term; it is not a new geological detector, not preregistered, and not a calibrated probability. It reduces one direct use of catalogue geometry, but the frozen B2 parent itself was pruned using catalogue proximity, so upstream label leakage remains possible.
- **Build/audit receipts:** [builder](../../evidence/build_h56b_noflank_receipt_20261007.json) · [independent recomputation](../../evidence/audit_h56b_noflank_artifact_20261007.json) · [local format check](../../evidence/h56b_noflank_format_validation_20261007.json) · [repository-local uniqueness comparison](../../evidence/h56b_noflank_uniqueness_20261007.json).
- **Short note (research only; do not submit):** `GEMSDOE48-H56B-NF-DS-5bb2c03c981e | relative D-S belief, no catalogue-flank term; m(Theta), K, support difference separate; research only, unscored, NOT slot-cleared.`

The H56B-NF output has no byte-hash or exact in-footprint pixel match among 105 same-grid one-band rasters searched under `data/` and `docs/downloads/`. That is repository-local evidence, not global or organizer-side uniqueness. It shares the same positive-support mask as earlier two-family D-S artifacts; support identity alone does not mean continuous values are identical. The no-flank values differ from the prior H56 surface (`MAE=0.002849`, maximum difference `0.571798`, Pearson `r=0.990942`, top-37,654 Jaccard `0.998302`). This is a distinct post-hoc ablation, not a new geological signal or independent strategy.

### Earlier H56B with-flank rebuild — not a new candidate

The first H56B file [`...126ca59c2801-nan-outside.tif`](../../docs/downloads/GEMSDOE48-H56B-ds-belief-dotted-x-tip-20261007-126ca59c2801-nan-outside.tif), SHA-256 `3589e89a1ad4f78f54e6f17f9b7cdb0edb563f66aedfcdabd632ef8774968c3a`, used the same catalogue-flank recipe as the prior H56 TIFF. It had a different byte hash and was not exactly pixel-identical, but the in-footprint difference from H56 was only one-float32-rounding-scale (`max |Δ|=1.788139343e-7`, `MAE=3.055105e-9`, Pearson `r≈1`, top-37,654 Jaccard 1.0). Treat that file as a reproducibility/encoding derivative, **not** a meaningfully new candidate. The initial build receipt also reported a normalized-kernel-mean maximum difference of `0.666666686`; the unchanged numeric builder was rerun at 20:33Z, producing `0.417241454` and matching the independent audit. A further reproducibility run at 20:51Z retained that value after receipt metadata was corrected. Artifact bytes did not change. The original value and both rebuild timestamps are preserved in [`evidence/h56b_review_corrections_20261007.json`](../../evidence/h56b_review_corrections_20261007.json); the cause of the original statistic mismatch is unknown.

## Dempster–Shafer definitions and safeguards

For binary frame `Θ={fault, not-fault}`, each source supplies masses `m_i(F)`, `m_i(N)`, and `m_i(Θ)`. Here `m_i(Θ)` is uncommitted/ignorance mass under the constructed assignment. The pre-normalization conflict is

`K = m₁(F)m₂(N) + m₁(N)m₂(F)`.

Normalized Dempster combination divides the non-empty combined masses by `1−K`; K is therefore normalized away and exported separately. Residual combined `m₁₂(Θ)=m₁(Θ)m₂(Θ)/(1−K)` is **not** a direct map of source disagreement and is not K. The `abs(s_dot−s_tip)` GeoTIFF is a separate support-difference diagnostic, not a D-S mass or probability. The inputs overlap at 31,614 positive cells; statistical independence is not established. Reliability discounts and absence weights are heuristics, not calibrated reliabilities.

At total/numerical conflict (`K≈1`) normalized Dempster is undefined. The H56B builder and common implementation raise `ValueError`, not a vacuous-mass fallback; tests cover the edge case. See [`src/gemsdoe48/dempster_shafer.py`](../../src/gemsdoe48/dempster_shafer.py), [`src/gemsdoe48/ds.py`](../../src/gemsdoe48/ds.py), and `tests/test_h56.py`.

Separate H56B-NF diagnostics (not submissions): [residual m(Θ)](../../docs/downloads/diagnostics/gemsdoe48-h56b-noflank-mtheta-5bb2c03c981e.tif) · [pre-normalization K](../../docs/downloads/diagnostics/gemsdoe48-h56b-noflank-conflict-5bb2c03c981e.tif) · [support difference](../../docs/downloads/diagnostics/gemsdoe48-h56b-noflank-support_difference-5bb2c03c981e.tif) · [plausibility](../../docs/downloads/diagnostics/gemsdoe48-h56b-noflank-plausibility-5bb2c03c981e.tif). They are explicitly not submission rasters.

## Arithmetic-mean check

The H56B-NF belief is not pixel-identical to either stated arithmetic mean, but its high correlation with the normalized kernel mean is disclosed. Non-identity does not establish value:

| Comparator | Pearson r | Footprint MAE | Maximum absolute difference | Pixels differing by >0.05 |
|---|---:|---:|---:|---:|
| Binary mean `½(1_dot + 1_tip)` | 0.392708 | 0.072525 | 0.823061 | 14.36% |
| Normalized metric-kernel mean | 0.992499 | 0.018375 | 0.417241 | 12.58% |

The independent artifact audit recomputes both the D-S output and these comparison statistics. The primary is a heuristic relative-belief/favorability surface, not a validated probability model.

## Matched spatial holdout — no slot clearance

Higher DTI is better. H56B-NF was compared with same-protocol H49 on four fixed spatial folds. These targets are public-map proxies, not private competition truth; the source surfaces were frozen upstream, not rebuilt independently inside folds.

| Proxy target | H56B-NF mean DTI | H49 mean DTI | Delta | H56B-NF fold wins |
|---|---:|---:|---:|---:|
| Public catalogue | 0.056305 | 0.095353 | −0.039048 | 0/4 |
| SGMC faults >300 m off catalogue | 0.068987 | 0.100751 | −0.031764 | 0/4 |

Full comparison: [`evidence/holdout_h56b_noflank_vs_h49_currentprotocol_20261007.json`](../../evidence/holdout_h56b_noflank_vs_h49_currentprotocol_20261007.json). H56B-NF also loses to the tip parent on the SGMC proxy (0.068987 vs 0.095491); the no-flank ablation improves the catalogue proxy relative to the original H56B build (0.056305 vs 0.032347) but does not beat H49 or the stronger parent. It fails the gate. No weekly submission slot is cleared.

## Format and portal caveat — download OK; do not submit

The local format receipt passes the finite-footprint checks, expected CRS/shape/transform, float32 range `[0,1]`, and NaN outside convention. It explicitly records `portal_range_error_immune=false`: a portal implementation that range-checks **all** pixels without masking nodata can treat outside NaNs as out of range and return the previously observed “Predicted values must be in range [0, 1]” error. The official challenge description documents null/NaN outside, but portal acceptance of this file is untested. **OK to download for inspection; not OK/recommended to submit.**

## Corrected chronology and preregistration limits

The prior chronology summary mislabelled an H56 predecessor receipt as the H56B build. The corrected file-level timeline is:

1. Main machine H56 slate stores only `frozen_utc: "2026-10-07"` and ranks H56-A first; the exact freeze ordering is unverified. Its H56-A holdout is timestamped 15:21:52Z and its build receipt 15:43:08Z, so build-before-holdout ordering is not established by those receipt times.
2. The receipt at 15:17:03Z is `evidence/build_h56_belief_receipt_20261007.json`, and it names the earlier `GEMSDOE48-H56-...9ec0...` zero-outside artifact—not H56B. Its initial H56 holdout is 15:20:25Z.
3. The separate H56B-specific slate says 16:00Z, ranks H56-F first, and contains measurements. That is after the H56 predecessor's measured run, but before the final H56B build at 17:37Z and holdout at 17:38Z. Because it includes measurements and describes a different recipe, it is not a verified preregistration of final H56B.
4. The final with-flank H56B artifact was rebuilt at 20:33Z and independently audited; the current H56B-NF ablation was built at 20:41Z and evaluated at 20:44Z. H56B-NF is post-hoc, not preregistered.
5. The two H56 slates reuse H56-B for different ideas (basement-step edges versus radiometric K-residual halos). The original main slate's requested `alpha=0.60`, `q=0.10` recipe also differs from the with-flank H56B recipe. Do not merge their ranks/IDs or claim a single validated H56B ranking.

See the original timestamped records in [`evidence/h56_preregistration_reconciliation_20261007.json`](../../evidence/h56_preregistration_reconciliation_20261007.json) and the correction record [`evidence/h56b_review_corrections_20261007.json`](../../evidence/h56b_review_corrections_20261007.json). Five different future hypotheses with target signatures, off-catalogue rationale, prior-art distinctions, expected DTI/cost, and verified data availability are preserved in [`h57-hypothesis-slate-20261007.md`](h57-hypothesis-slate-20261007.md) and [`evidence/hypothesis_slate_h57_20261007.json`](../../evidence/hypothesis_slate_h57_20261007.json). Several required layers are unavailable or only partial; no H57 geological detector was built in this review.

**Decision:** Download is OK for inspection. Submission is not recommended. The final H56B-NF artifact loses the comparable H49 baseline on all eight proxy folds, remains based on heuristic masses and frozen owner-mirror inputs, and has unresolved portal NaN handling. No score above 0.2778 or 0.3195 is supportable for it. No slot is cleared.
