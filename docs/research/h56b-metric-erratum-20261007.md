# H56B metric and terminology erratum — 2026-10-07

**Decision: H56B is OK to download for inspection, but NOT OK / NOT CLEARED to submit.** The historical score projection is invalidated; the replacement spatial-proxy comparison is below H49 on both targets. This is not a private-label score, file-to-leaderboard link, or organizer acceptance.

## 1. Superseded H56B score projection

The first H56B validator reported a live-equivalent DTI of `0.0649` (and related thresholded values) using an algebra that substitutes `FPw = S − TPw`. That identity is generally false for the official metric: the prediction-centred false-positive credit is `FPw = S − Q`, while `TPw = T` is truth-centred, and `Q` is generally not `T`. The projection is retained only as a historical artifact in [`evidence/h56_live_model_projection_20261007.json`](../../evidence/h56_live_model_projection_20261007.json); it is now marked `INVALIDATED_SURROGATE_DO_NOT_USE`, and no projection is used by the current validator or as a gate.

See the derivation and small executable counterexample in the [metric-identity erratum](metric-identity-erratum-20261007.md). The old projected value cannot be compared with a leaderboard score or interpreted as H56B performance.

## 2. Replacement public-proxy evaluation

[`scripts/validate_h56.py`](../../scripts/validate_h56.py) now uses the same-protocol H49 reference, exact DTI implementation, pinned masks, four fixed quadrants and 300 m halo used by [`scripts/run_spatial_holdout.py`](../../scripts/run_spatial_holdout.py). It has no live-model score projection.

| Proxy | H49 mean DTI | H56B graded Bel(F) | Δ vs H49 | Folds above H49 |
|---|---:|---:|---:|---:|
| Catalogue labels | 0.095353 | 0.032347 | −0.063006 | 0/4 |
| SGMC, >300 m from catalogue | 0.100751 | 0.070552 | −0.030199 | 0/4 |

The current rule requires positive mean paired change and at least 3/4 positive fold changes on both proxies. H56B fails both. The H49 row is a comparable **public-proxy reference**, not the official leaderboard leader, private-label best, or a hidden-test estimate. Inputs are frozen upstream surfaces and are not reconstructed inside folds; results remain conditional and potentially leaky.

Reproduction: `./.venv/bin/python scripts/validate_h56.py --primary docs/downloads/GEMSDOE48-H56-ds-belief-dotted-x-tip-20261007-9ec0d605c45b-zeros-outside.tif`.

- Detailed receipt: [`evidence/holdout_h56_belief_h49_20261007.json`](../../evidence/holdout_h56_belief_h49_20261007.json).
- Format receipt: [`evidence/h56_format_audit_20261007.json`](../../evidence/h56_format_audit_20261007.json).
- Bounded identity receipt: [`evidence/h56_uniqueness_20261007.json`](../../evidence/h56_uniqueness_20261007.json).

## 3. Download and format status

- **OK TO DOWNLOAD FOR INSPECTION:** [`GEMSDOE48-H56-ds-belief-dotted-x-tip-20261007-9ec0d605c45b-zeros-outside.tif`](../downloads/GEMSDOE48-H56-ds-belief-dotted-x-tip-20261007-9ec0d605c45b-zeros-outside.tif), SHA-256 `4d6548d4ec07a47a25b83d28ebc05d58b57448c1507b460aed52cec395bdb6b5`.
- It is one float32 band on EPSG:32611 / 100 m / 3,292 × 3,730. All 12,279,160 values are finite and in `[0,1]`; nodata is unset; 791,389 cells are positive. Local core grid/dtype/range checks pass.
- The zero-outside encoding does **not** satisfy the public problem-page wording that outside-footprint values be null/NaN. A NaN-outside twin is available and has exactly the same in-footprint values. The public instructions, historical portal range error and an owner-cited reference-solution encoding are not a file-specific organizer acceptance receipt; this ambiguity remains unresolved. No upload has been made.
- The primary is byte-distinct from the other local downloads. The NaN-outside twin is a separate encoding of the same H56B in-footprint prediction; this is not a claim of two independent candidates or a globally unique geological surface.

## 4. Dempster–Shafer layer semantics and prior art

The two sparse family masks have 31,614 positive cells in common (Jaccard 0.65993); independence is not established. The normalized combination returns fault belief, no-fault belief and residual `m(Θ)`. **`m(Θ)` is unassigned/ignorance mass—not conflict, not family disagreement, and not a fault-probability uncertainty estimate.** The raw pre-normalization conflict `K` is exported separately and is the conflict diagnostic. H56B also exports plausibility; the H56 open-world artifact has an additional direct absolute support-surface difference, which is not a Dempster mass.

In the H56B receipt, raw `m(Θ)` spans 0.004996–0.664188 in-footprint; raw `K` peaks at 0.855068, with 30,499 cells above 0.3. These layers answer different questions and must not be merged or described as interchangeable “disagreement.” The normalized Bel(F) is a relative, max-normalized favorability surface, not a calibrated fault probability.

H53 already contained a D-S diagnostic from the same B2 × H33-D family pair. H56B is a distinct, fully audited recipe and local file, but it is not a new D-S combination concept or a new geological evidence family. It differs from both the arithmetic mean and the binary mean (see [`evidence/build_h56_belief_receipt_20261007.json`](../../evidence/build_h56_belief_receipt_20261007.json)); that numerical difference is not evidence of improved geological prediction.

## 5. Decision

The former `0.0649` projected score is invalid, H56B fails the corrected same-protocol H49 proxy comparison, and local format checks are not portal acceptance. **Download for inspection: OK. Submission: NOT OK / NOT CLEARED. No weekly slot is cleared.** The separate H56-F threshold ladder also fails H49; see [`h56-pruning-ladder-results-20261007.md`](h56-pruning-ladder-results-20261007.md).
