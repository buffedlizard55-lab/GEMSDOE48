# Review passes — H55 session, 2026-10-07 UTC

Three passes were run as the brief requires: (1) implement and verify, (2) review for bugs,
missing requirements, incorrect assumptions and edge cases and fix them, (3) re-check the whole
implementation against the original request and fix what was still wrong. This log records what
each pass found, including the things that were caught **before** anything was published, because
a pass that reports nothing is not a pass.

---

## Pass 1 — implement and verify

Delivered: `src/gemsdoe48/live_model.py`, `src/gemsdoe48/conduit.py`, `src/gemsdoe48/h55.py`,
`write_float32_zeros_outside` in `src/gemsdoe48/geotiff.py`, `scripts/restore_h55_inputs.py`,
`scripts/calibrate_live_model.py`, `scripts/compare_coverage_weightings.py`,
`scripts/build_submission_h55.py`, `scripts/audit_h55.py`, `scripts/build_site_h55.py`,
`tests/test_h55.py`, the H55 artifacts, nine regenerated site pages and the research report.

Verification actually run, not asserted:

* all nine live-scored mirrors restored and **SHA-256 verified against their published pins**,
  fail-closed on mismatch;
* containment of the family verified **pixel-wise** (`C ⊂ B ⊂ A ⊂ d1.5 ⊂ h19_5`, `h36 ⊂ h19_5`,
  `h32 ⊂ h19_5`, `h33d` = 41,732 of 41,865 px inside the backbone, matching its own receipt's
  "added_euler_clusters: 133");
* the nested-rung self-consistency of the `|G|` fit measured at **0.11 %**;
* the greedy's incremental coverage accumulation checked against a **full recomputation** at four
  prefix lengths, and again inside the builder (`abs_drift` recorded in the receipt, with a hard
  `SystemExit` if it exceeds 1e-6 relative);
* the built primary re-read from disk and audited on **18 independent checks**, all passing;
* two independent builds producing the **same content id and the same SHA-256**;
* `python -m pytest -q` → **158 passed, 3 skipped** (the three skips are pre-existing
  data-dependent tests);
* every relative link in all nine generated pages resolved on disk.

## Pass 2 — bugs, wrong assumptions, edge cases

Sixteen findings. Nine were caught in prototypes before any artifact was published; seven were
caught in shipped code or shipped prose and fixed.

**Correctness bugs in code**

1. `fit_hidden_truth`'s closed-form pairwise `|G|` had a sign/algebra error and returned
   **−34,543 px**. Caught because the least-squares fit was computed alongside it and disagreed
   wildly. Correct closed form is `G = 0.25 (l₂s₂ − l₁s₁)/(l₁ − l₂)`; both are now in
   `live_model.fit_hidden_truth` and the pairwise values (13,368 / 15,198 / 14,089) are published
   next to the least-squares value (14,027.5) rather than replacing it.
2. `-np.ones(shape, np.int32)` — `np.int32` is a type, not a value, so unary minus raised
   `TypeError`. Fixed to `dtype=np.int32`.
3. The submission note was truncated with `............` (four lots of `...`): the 300-character
   trim statement had been moved **inside** the four-iteration diagnostics loop. Removed; the note
   is now 202 characters and untrimmed.
4. `dti_core_model` was referenced in the A2 print before assignment → `UnboundLocalError`. Moved
   to where `dti_core_pred` is computed.
5. `a1_cap` was left referenced in the receipt after the allocation order was changed →
   `NameError`. Removed and replaced by `n_a1_out_of_family` / `n_a2_in_family`.
6. **Two scripts wrote the same receipt path.** `build_submission_h55.py --calibration` defaulted
   to `evidence/live_model_calibration_20261007.json`, which is owned by
   `calibrate_live_model.py` and carries the coverage frontier and ceiling table. Running the
   builder silently destroyed them. Separated: the builder now writes
   `evidence/h55_build_live_model_20261007.json` and its `--calibration` help text says so.
7. `validate_submission.py` hard-required `nodata = NaN` and therefore **rejected the encoding of
   the 0.2778 live-best artifact**. Now `--encoding {auto,nan,zeros}` with explicit reporting of
   the portal range-error exposure (IR-H55-02).

**Wrong risk accounting — the most consequential class of fix**

8. `worst_case_dti` was called with `base_emitted = interim.sum()` and `added = len(a1_rows)`,
   which double-counted A1 and produced a "worst case" of **0.2850 that was *higher* than the
   base prediction** — an obviously impossible result that would have been published as the
   downside bound. Root cause: `cov_after_a2` already includes A2's coverage while the denominator
   did not include A2's mass. Replaced by an explicit four-case decomposition with a hard
   consistency assertion.
9. `live_equivalent_a2_only` was **mislabeled**: it was priced on a base that already carried A1's
   652 px of dead mass, so it reported the combined A1-at-zero-credit case as if it were A2 alone.
   A2 is now priced separately (`cov_a2_only`, `s_core + n2`). The corrected decomposition is
   A2 alone **+0.00185**, A1 alone at zero credit **−0.00189**, net **−0.00003** — which is the
   design claim, and it only became verifiable once the two were separated.
10. The pre-registered budget check asserted `floor == LIVE_C − 0.0100` to within 1e-3 and failed,
    because using less than `n_max` raises the floor above the registered minimum. Changed to
    `floor >= LIVE_C − MAX_MODELLED_DOWNSIDE`, which is the actual rule.

**Wrong assumptions caught by measurement, not by argument**

11. The draft report quoted the family ceiling as **0.2821** with C "2.2 % short of
    coverage-optimal" and headroom "+0.0043". Those numbers came from a prototype run using
    provisional constants (ρ = 0.06869, |G| = 14,307). Recomputed with the final calibrated
    constants the frontier is **n = 37,167, Cov = 76,612.8, model DTI 0.27932, live-equivalent
    0.28435**, C is **1.84 %** short, and the headroom is **+0.00655**. Every occurrence replaced.
    The frontier is now computed *by a shipped script* so it cannot drift again.
12. The draft claimed "1,022 of the 1,124 admitted A2 dots come from the tip family". The receipt
    says **156 tip / 968 backbone-only**. Corrected in the report and on the site.
13. The draft claimed "100 % of the footprint differs from the naive mean". Measured:
    **13.71 %** differs by more than 0.05 (mean |Δ| 0.01347, max |Δ| 0.160, affine residual
    0.005912). Corrected; the honest framing is that the affine residual and the difference
    distribution are the informative tests, and the high rank correlation is expected.
14. The draft ceiling table answered "reachable?" with a single test (is the required `T` inside
    the dense field's total yield?), which said **yes** for 0.2888, 0.3195, 0.3262 and 0.3345.
    That test is necessary but not sufficient. Two more were added — achievable by a 37,654 px
    subset, and achievable at **any** mass, the latter being the frontier argmax — and under them
    **every leaderboard row above 0.2778 is unreachable from this field**. The stronger claim
    replaced the weaker one.
15. An **along-strike conduit-trace extension was designed and then withdrawn.** It would have
    walked ±300 m from each hot-spring anchor along the 3 m lidar product's `strike_at` band.
    `strike_at` is quantised to 15° bins, and its companion `facing_at` fails the perpendicularity
    check a dip-direction/strike pair must pass (measured median deviation **46°**, not ~0°) over
    5,900,588 valid cells. Shipping it would have meant building geometry on an unverified band.
    Recorded as IR-H55-08 and as the blocker on hypothesis H55-D instead.
16. A **catalogue-lift justification for the conduit layer was drafted and then discarded.** The
    conduit layer does have the second-highest catalogue coverage per pixel of anything measured
    (Hot sites 0.1897 against the backbone's 0.1007). But SGMC faults score **higher** than the
    backbone on that same statistic (0.1418) and returned `T = 1,026` live against the family's
    5,209 — so the statistic does not predict live truth yield. Using it would have been exactly
    the hallucinated justification the brief forbids. Recorded as IR-H55-05; the conduit case now
    rests on physics and on spatial disjointness (1.7 % overlap with the backbone), and its credit
    is reported only as a scenario band.

**Edge cases explicitly handled**

* `K = 1` (total conflict with α = 1): Dempster's rule is undefined; the code falls back to
  vacuous mass instead of dividing by zero, and a test asserts it.
* Trailing whitespace in the GDR mirror: **121 records** carry `"Hot "` rather than `"Hot"`. The
  reader normalises, so they count; a test asserts the normalisation rather than leaving it
  implicit.
* The label-derived `dist_known_fault_px` column is dropped on read, and a test asserts the drop.
* Duplicate site reports across the six GDR layers collapse by maximum tier and maximum score, so
  a multiply-reported site cannot out-rank a genuinely stronger neighbour.
* `Warm` (≤ 38.9 °C, effectively ambient) and `Cold` (≤ 20 °C) are excluded as non-indicators by
  an explicit tier-0 rule rather than by a threshold that happens to fall there.
* The dart-throw is **seed-free** (rank, then tier, then row-major index) so the build is
  deterministic; a test asserts two runs are identical.
* The empty-pool and zero-gain paths of the greedy return empty arrays rather than raising.

## Pass 3 — re-check against the original request

| requirement in the brief | where it is met | status |
|---|---|---|
| MUST generate a **unique** TIF submission | `GEMSDOE48-H55-…-055da9855353-zeros-outside.tif`; 18/18 audit checks; no SHA-256 collision with any raster or recorded hash here; highest pixel-set Jaccard against any prior artifact 0.9550 | done |
| do not copy a previous submission | additive-only *by design*, and the reason is stated rather than hidden: `TPw` is a maximum over emitted pixels, so carrying the 37,654 px core means its live-verified `T = 5,209.5` cannot be lost. The 1,776 added pixels are new construction | done, with the reasoning recorded |
| combine the two best families with a rule that preserves disagreement instead of averaging it | Dempster's rule on the two families' kernel-coverage surfaces, α₁ = α₂ = 0.6; Bel/Pl/m(Θ)/K shipped as four separate [0,1] diagnostic layers; DS enters the *placement* (A2's pool is the disagreement set; A1 is vetoed at maximal K unless a third independent source arbitrates). **And the brief's premise is answered with a measurement rather than complied with silently:** the union is priced at −0.0140 live-equivalent, so a blended surface would lose | done |
| verify the result is not the naive mean | Pearson 0.996429, Spearman 0.999953, mean \|Δ\| 0.013470, max \|Δ\| 0.160000, 13.71 % of the footprint differs by > 0.05, best affine fit residual **0.005912**, `is_the_naive_mean: false` | done |
| export normalised Bel(F) in [0,1] in the required format | `diagnostics/gemsdoe48-h55-bel-055da9855353.tif`, Bel ∈ [0, 0.84], all-finite, [0,1] | done |
| export m(Θ) as its own diagnostic layer | `diagnostics/gemsdoe48-h55-mtheta-055da9855353.tif`, m(Θ) ∈ [0.16, 0.25], maximal exactly on one-sided support | done |
| easy one-click download, obvious at the very top of the site / in the executive summary | first element after the header on both `docs/index.html` and `docs/executive-summary.html`; a full-width button plus .zip and NaN-twin alternates | done |
| unique submission name + short paste-ready note | name and 202-character note in the build receipt, on the download card and in the six-step guide | done |
| executive-summary subpage explaining exactly how to submit | `docs/executive-summary.html` plus `docs/submission-guide.html` (six numbered steps, format list, checksum, note text, what to record afterwards) | done |
| fix `Predicted values must be in range [0, 1]` | primary encoding is all-finite with zeros outside and `nodata` unset; asserted on the re-read bytes; validator extended; root cause explained (IR-H55-02) | done |
| put the prompt into the README as a permanent starting point | already present verbatim from prior sessions; this session's re-issued brief appended with a per-requirement mapping | done |
| work on the previous sessions' next steps first | `docs/md/next-steps.md` listed N1 (native-resolution 1 m DEM) and H50-A (coverage-budget credit repacking with a faithful break-even bar) as the top two; H55-A/H55-D continue N1 and A2 **is** H50-A, with the bar derived from live scores and applied at 1.25× | done |
| 3–5 new hypotheses, each naming layers, signature, why it catches a *missing* fault, and how it differs from the repo; ranked by expected ΔDTI and cost; external data named and obtainability confirmed | five, frozen before scoring, in `docs/research/hypothesis-slate-h55-20261007.md` and its JSON twin; every one has a verified local hash-pinned source; seven further ideas are listed as rejected *with reasons* | done |
| validate the top candidate on the spatially-blocked holdout before touching a slot | `evidence/holdout_h55_spatial_20261007.json`, four quadrants, core truth + 300 m halo, `run_spatial_holdout.py` unmodified; H55 beats **both** parents in **4/4** folds on the SGMC-off proxy and its dotted parent on both proxies; `slot_decision.cleared: false` | done |
| do not spend a slot on an idea that has not beaten the holdout best | no slot was spent. The report states plainly that the numeric proxy passes are not a clearance, and that the two proxies this project has gated on are contradicted by a live score | done |
| work line by line from official, verified, trusted sources with links for manual review | `docs/sources.html` and the slate's `sources` array: 12 entries, each with URL, what it supports, its limit, and whether it is reachable from this sandbox | done |
| no manual input | every input restored programmatically over `gh api` with fail-closed SHA verification; the only human step left is the upload itself, because DrivenData's terms of use prohibit automatic access | done |
| flag irregularities for review | ten, IR-H55-01 … IR-H55-10, in `docs/irregularities.md`, `docs/irregularities.html` and the slate JSON | done |
| no hallucinations | pass 2 items 11–16 are exactly this: six claims that were drafted and then corrected or withdrawn because measurement contradicted them. Every number on the site is read from a receipt by `scripts/build_site_h55.py`, so no page can drift from the artifacts | done |
| Maximize P(Win) / Own the Outcome | the family ceiling is proved rather than guessed, so effort stops going into spacing/fusion/pruning sweeps; the slot budget is redirected to the one experiment that can recalibrate the instrument; the candidate's downside is bounded exactly and its arithmetic was arranged so the returned score is legible | done |
| three passes, then PR and merge to `main` | this file; PR opened from `arena/312ae2b4-gemsdoe48` and merged to `main` | done |
| suggest remaining work and limitations | `docs/next-steps.html` — seven ordered priorities and eight limitations with their consequences | done |

**Not met, stated plainly:** the brief asks for a submission that scores higher than 0.3195. This
session's candidate is modelled at 0.2778 – 0.2880 live-equivalent. §3 of the report proves that
0.3195 is unreachable from the h19-5 corridor field at any mass, and that #1 at 0.3774 requires
more recovered truth than that field contains in total. The deliverable is therefore the highest
expected-value move available from the data in hand, plus a priced, unblocked path (H55-B/C/D and
the restored official 19-band stack) that could reach it — not a claim that the target was hit.
