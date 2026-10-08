# Correction: the H55 fitted family ceiling is not a metric bound

**Status: research erratum, 2026-10-07. No candidate is cleared for a weekly upload.**

The published H55 pages and `src/gemsdoe48/live_model.py` use `FPw = S - TPw` to invert owner-reported scores and claim a 0.2843 ceiling for every emission from the corridor. **That identity is false in general, even for binary predictions.** The reported calibration and greedy frontier are an *assumption-dependent surrogate*, not an exact inverse of the competition metric, and not an upper bound on hidden-label DTI. Keep the historical receipts to audit what was computed, but do not use the resulting `|G|`, inverted `T`, credit/px, 0.2843 ceiling, 0.2736–0.2880 scenario band, or `0.0556` universal per-pixel threshold as established facts about the organizer's labels.

## Derivation from the organizer's definition

[Official problem description and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) define `k(d)=max(1-d/300m,0)`. Let `S=sum_x p(x)`, `T=sum_g max_x p(x)k(d(x,g))`, `Q=sum_x p(x)max_g k(d(x,g))`, and `N=|G|`. The two maxima operate on **different axes**, hence `T != Q` in general. Exactly:

```
TPw = T;  FPw = S - Q;  FNw = N - T
DTI = T / (0.2*T + 0.2*S - 0.2*Q + 0.8*N + epsilon)
```

For a 1×5 grid with truth at columns 1 and 2 and one binary prediction at column 1, `T=1+2/3=5/3`, `Q=1`, `S=1`, `FPw=0`, `FNw=1/3`. Exact DTI is `25/29≈0.8621`, while the H55 substitution `T/(0.2*S+0.8*N)` yields `25/27≈0.9259`; the purported `S-T` would even be **negative**. The repository's [exact metric implementation](../../src/gemsdoe48/metric.py) already distinguishes the two axes; see `tests/test_metric_identity.py` for this executable counterexample.

An added dot always weakly raises `T` but may raise `FPw`; its marginal benefit depends on **both** changes and on existing coverage. The frequently cited `0.2×DTI` break-even per added pixel applies only in restricted cases (e.g. that pixel has incremental FP exactly one and the competing numerator/denominator terms are held as assumed). A statement about greedy *coverage of the eligible public backbone* cannot prove a bound against an unknown private truth. The holdout catalogue/SGMC targets also do not establish transfer to previously unmapped faults.

## Other audit corrections

* SHA-256 of the tracked, downloadable H55 all-finite TIFF, independently recomputed with `sha256sum`, is `8f9a9d3d1ea2aed1c99e5ab5260aad9ceb10f4011c4b5a38791509261ddd284a`, matching `evidence/h55_primary_format_audit_20261007.json`. An older hash `f4671759…` in the README/report was wrong for that file.
* Local bounds/range checks are **not** an organizer acceptance receipt. The [published submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) asks for null/NaN outside the data bounds; H55's primary writes zero outside the survey footprint to avoid an observed range rejection. A validator may impose other requirements. Do not claim that the primary is immune to all portal rejection.
* The H55 score attribution remains an owner report, not a verified receipt connecting the exact local B2 bytes to 0.2778. Its historical Gate-2 receipt recorded `FAIL_MASS_NEUTRAL`, but the density-matched method depends on the invalid inversion; that verdict is withdrawn and cannot clear or reject a candidate under a validated promotion policy ([audit receipt](../../evidence/audit_gate2_h55_20261007.json)). **No weekly slot is cleared.**
* Normalized Dempster's rule divides by `1-K`: disagreement `K` is not assigned to `m(Θ)`. Publish `K` and `m(Θ)` separately. Yager's rule, not normalized Dempster, assigns conflict to uncommitted mass; strong parent overlap makes evidence independence doubtful.

## Gate-2 calibration is also under review

The historical `scripts/audit_candidate.py` / Gate-2 receipts use `LIVE_TRUTH_PX = 14,307`, derived from the same invalid hidden-truth inversion, to thin the public SGMC proxy. They also label `0.2 × 0.2778 = 0.05556` a live-scaled metric break-even bar. The narrow `0.2 × DTI` condition can be derived only under restrictive assumptions about how a single added prediction changes both `T` and `Q`; it is not a universal per-pixel rule. Thus the historical density-matched credit, raw-proxy scaling, and resulting `FAIL_MASS_NEUTRAL` / `PASS_MASS_NEUTRAL` verdicts are not validated evidence about private truth or general promotion readiness. The equal-emitted-mass scores remain public-proxy observations under their recorded protocol, not private-label outcomes. Keep all receipts for audit, but do not treat the old Gate-2 script or its pass/fail as a valid promotion gate until its truth-density and marginal-credit method is re-derived without the invalid inversion. No candidate is cleared in the meantime. The repository must not silently remove its stricter Gate-2 policy; revise its implementation and rationale before the next candidate promotion.

## Next validation before recommending any file

1. Evaluate candidate and parent at *equal emitted mass* on untouched spatial blocks with the exact `TPw`, `FPw`, `FNw` terms, and record `Q` and `T` separately. Maintain a random-addition negative control. Do not select a hypothesis on the same blocks used to quote its improvement.
2. Check an external official source's coverage, license and registration; do not infer the new-fault truth from catalogue-adjacency alone.
3. Recompute and publish any calibrated model with the correct denominator and held-out owner-reported scores; do not call the greedy frontier a private-label ceiling. Correct historic pages rather than deleting their audit trail.
4. For a *new* emission, write a uniquely named TIFF, independently re-open and inspect grid, mask, finite/in-range values and SHA-256; compare actual pixels/hashes with prior artifacts. Obtain organizer acceptance separately before making portal-compatibility claims.
