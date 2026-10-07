# Historical credit-density audit — public-proxy diagnostics only

> **Correction (2026-10-07): this is not a validated promotion gate.** The “density-matched” analysis used an assumed hidden-truth count derived from the now-retracted `FPw=S−TPw` inversion, and its universal `0.0556` per-cell bar is not supported for arbitrary raster additions. Neither a pass nor a fail under `GEMSDOE48-GATE-2` establishes private-label performance, a score bound, or slot clearance. Preserve the calculations and receipts as provenance, not as current decision criteria.

## What remains directly measured

The audit script compared candidate rasters against public map layers under the named four-quadrant/core-plus-halo protocol. Raw own-mass and equal-mass DTI values in the original receipt are computations on those particular public rasters; they do not estimate private-label scores. The machine-readable roll-up is [`evidence/credit_density_audit_20261007.json`](../../evidence/credit_density_audit_20261007.json), with per-candidate GATE-2 receipts indexed there. The historical protocol and artifacts are preserved in `scripts/audit_candidate.py` and the receipts.

The SGMC off-catalogue set contained 62,122 public-proxy pixels, and a historical random-addition control scored 0.118872 versus 0.095607 for the then-incumbent C under that proxy protocol. Those observations describe proxy density and sensitivity to added mass; they do not establish that random mass performs well on private expert labels or that prior candidates failed on the organizer test set.

## What is withdrawn

1. The “live hidden truth” count of approximately 14,307 was inferred from owner-reported scores using `FPw=S−TPw`. That identity is generally false; the count is not a measured private-label total.
2. Thinning the public proxy to that assumed count does not reproduce the unknown private label distribution. Density matching is an exploratory sensitivity analysis only.
3. The `0.0556` hurdle was treated as a universal added-cell break-even threshold. The restricted one-pixel algebra does not justify applying it to arbitrary raster additions. See the [metric-identity erratum](metric-identity-erratum-20261007.md) for the correct `TPw`/`FPw` definitions and the coordinate-wise binary-maximizer proof.
4. The old pass/fail outcomes and statements that H52/H54 or any prior candidate did or did not “clear” a private-label gate are not supported by this audit. Its GATE-2 `FAIL` is a historical receipt label, not an organizer score or upload recommendation.

## Current candidate decision protocol

A public-proxy holdout can support a **relative proxy comparison** only when the candidate, baseline, masks, source construction, spatial blocks, and scoring code are matched and frozen. It cannot establish private-label transfer. H56B-NF loses to H49 on all four folds for each of the two public proxies (catalogue means 0.056305 vs 0.095353; SGMC off-catalogue 0.068987 vs 0.100751), so it is not recommended for submission; see the [H56B-NF review](h56b-review-erratum-20261007.md) and matched receipts. No current weekly slot is cleared.

## Provenance and limitations

- Original input/output hashes and measured summaries: [`evidence/credit_density_audit_20261007.json`](../../evidence/credit_density_audit_20261007.json).
- Original per-artifact computations: the receipt files listed in that JSON.
- Historical tool: [`scripts/audit_candidate.py`](../../scripts/audit_candidate.py); do not treat its legacy `GEMSDOE48-GATE-2` status as a validated promotion gate.
- No organizer score, private expert-label access, organizer file-to-score receipt, or portal acceptance is present in this audit.
