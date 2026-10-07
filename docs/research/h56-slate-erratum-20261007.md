# H56-A preregistration-text erratum — 2026-10-07

**This is a post-score documentation erratum. The original frozen slate files are preserved unchanged.** It does not retroactively turn the H56-A run into a confirmatory test of more parameters than were recorded in the machine-readable frozen test.

## Discrepancy

The original Markdown slate [`hypothesis-slate-h56-20261007.md`](hypothesis-slate-h56-20261007.md) describes H56-A as a multi-scale Hessian ridge response **combined with structure-tensor line coherence**. Its implementation-cost sentence also mentions “Hessian/coherence.” The machine-readable preregistration [`evidence/hypothesis_slate_h56_20261007.json`](../../evidence/hypothesis_slate_h56_20261007.json), however, defines the explicit `frozen_test.strain_transform` as per-channel/scale P99.5-normalized absolute-Hessian line responses at 3/6/9 px, plus a weak earthquake-density term; it does not specify or parameterize a structure-tensor coherence factor.

The builder [`scripts/build_h56_strain_ridge_probe.py`](../../scripts/build_h56_strain_ridge_probe.py) followed that explicit machine-readable `frozen_test`: bands 4/7/8, log absolute magnitude, Hessian responses at 3/6/9 px, P99.5 scaling per channel/scale, mean of the nine response fields, and a 0.1 earthquake-density term. **It did not compute structure-tensor coherence.** The tested file and holdout receipt therefore answer only the machine-spec Hessian-only screen, not the prose's coherence-augmented hypothesis.

## Interpretation and action

- H56-A's recorded machine-spec screen failed H49 on both public proxies (catalogue `0.014282` vs `0.095353`; SGMC off-catalogue `0.006531` vs `0.100751`; 0/4 folds positive on either).
- The prose-only coherence augmentation is not retrospectively tuned or promoted after observing those results. No coherence operator/parameters were frozen in the machine test, so this session does **not** claim that the coherence-augmented idea was validated or rejected.
- This discrepancy does not affect H56-DS, its format/diagnostic/uniqueness audits, or the no-slot decision. Neither candidate is recommended for submission.
- Future work, if any, must preregister a fully specified coherence transform and an independent comparison before scoring; it must not reuse this holdout as fresh confirmation.
