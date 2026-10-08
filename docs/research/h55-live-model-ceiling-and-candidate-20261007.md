# H55 report correction — historical live-model ceiling invalidated (2026-10-07)

> **INVALIDATED — DO NOT USE AS A SCORE ESTIMATE, SCIENTIFIC CEILING, THRESHOLD, OR PROMOTION GATE.** This page replaces the former H55 live-calibrated report. Its score inversion assumed `FPw = S − TPw`, which is generally false under the official metric. The original values are not measurements of private labels. The underlying dated receipts are retained for forensic reproducibility only; the historical H55 TIFF is **not cleared to submit**.

## Metric correction

For prediction surface `p(x)`, truth locations `g`, triangular distance kernel `k`, and total predicted mass `S`, define

```text
T = Σ_g max_x p(x) k(d(x,g))       # truth-centred true-positive credit
Q = Σ_x p(x) max_g k(d(x,g))       # prediction-centred matched credit
N = number of truth locations
TPw = T
FPw = S − Q
FNw = N − T
DTI = T / (0.2 T + 0.2 S − 0.2 Q + 0.8 N + ε)
```

`T` and `Q` maximize over different axes and are generally unequal. A leaderboard value paired with a raster pixel count therefore does **not** identify `N`, `T`, recall, or the value of adding/removing a pixel. The supposed `FPw = S − TPw` identity is false in general, even for binary predictions. The [metric-identity erratum](metric-identity-erratum-20261007.md) contains the derivation and executable counterexample.

## H55 claims withdrawn

The prior report combined an owner-reported score ladder, a fitted within-family coverage model, and the invalid metric substitution. Every downstream live-equivalent result based on that chain is withdrawn. This includes, but is not limited to:

| Former H55 output | Current status |
|---|---|
| `|G|` / hidden-truth totals and inverted `TPw` values (including the roughly 14,000-pixel estimates) | **Not identified by the inputs; invalid as hidden-label facts.** |
| `0.2843` family/frontier “ceiling,” and claims that other leaderboard values are unreachable from the backbone | **Not a bound.** It cannot establish that a score is or is not achievable. |
| The `0.2736–0.2880` live-equivalent bracket, H55 scenario bands/floors, conduit-anchor expected values, and recombination “live” values | **Invalid model outputs, not score forecasts.** |
| The universal `0.05556` per-dot threshold, raw-proxy scaling, and additions/removals priced against it | **Not a general metric rule.** A valid marginal analysis must account for the changes to both `T` and `Q` under the actual truth set. |
| H55 Gate-2 `FAIL_MASS_NEUTRAL`, including equal-mass delta `−0.002014` and density-matched credit `0.010245` | **Forensic reproduction only.** The density match used an inversion-derived truth count, and the bar used the same invalid calibration; the receipt cannot clear or reject a candidate under a validated promotion policy. |
| “Binary values are always optimal” / “an added pixel only costs denominator mass” as claims about the organizer metric | **Not established by the old derivation.** It omitted the prediction-centred `Q` term and cannot be generalized from its simplified model. |

See the [retired credit-density/Gate-2 audit](credit-density-audit-20261007.md) for the invalidation of the density-matched protocol. Its historical receipts remain available, explicitly invalidated.

## What can still be reproduced

The H55 TIFF is preserved as a historical research artifact:

- Name: `GEMSDOE48-H55-conduit-conflict-priced-20261007-055da9855353`.
- Local SHA-256: `8f9a9d3d1ea2aed1c99e5ab5260aad9ceb10f4011c4b5a38791509261ddd284a`.
- Local identity/format/holdout records: [`evidence/build_h55_receipt_20261007.json`](../../evidence/build_h55_receipt_20261007.json), [`evidence/h55_primary_format_audit_20261007.json`](../../evidence/h55_primary_format_audit_20261007.json), and [`evidence/holdout_h55_spatial_20261007.json`](../../evidence/holdout_h55_spatial_20261007.json).
- Historical invalid-model outputs: [`evidence/h55_build_live_model_20261007.json`](../../evidence/h55_build_live_model_20261007.json), [`evidence/live_model_calibration_20261007.json`](../../evidence/live_model_calibration_20261007.json), [`evidence/live_ladder_20261007.json`](../../evidence/live_ladder_20261007.json), and [`evidence/audit_gate2_h55_20261007.json`](../../evidence/audit_gate2_h55_20261007.json).

A local SHA, grid/range audit, or public-proxy holdout is not organizer acceptance, private-label performance, a leaderboard score, or a local-file-to-score link. No organizer receipt links H55 bytes to a score. **H55 is not cleared to submit.** `scripts/calibrate_live_model.py` and `scripts/build_submission_h55.py` are retired from default use; `scripts/build_site_h55.py` cannot overwrite the current site. Any explicitly enabled legacy run is for forensic reproduction only.

## Current project status

Do not use the H55 report or its model as a basis to spend a weekly slot. The current H56B file is **OK TO DOWNLOAD FOR INSPECTION; NOT OK / NOT CLEARED TO SUBMIT** because it fails the comparable H49 public-proxy gate and its outside-footprint encoding has no portal acceptance. H56-F's preregistered pruning ladder and H57-A also fail their current reported public-proxy tests; no H57 TIFF was generated. See [current validation](../validation.html), the [H56B corrected report](h56b-metric-erratum-20261007.md), the [H56-F results](h56-pruning-ladder-results-20261007.md), and the [H57-A results](h57-results-20261007.md). No candidate has a promotion-grade Gate-2 pass.
