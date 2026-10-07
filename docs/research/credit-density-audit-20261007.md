# Credit-density audit (2026-10-07): why nothing was cleared, and what a cleared candidate must show

**Status:** measured audit on public proxies. **No weekly submission slot is cleared by this note.** The
instrument is `scripts/audit_candidate.py` (protocol `GEMSDOE48-GATE-2`); machine-readable results are in
[`evidence/credit_density_audit_20261007.json`](../../evidence/credit_density_audit_20261007.json) and the
per-candidate receipts it indexes.

## 1. The problem with the gate we were using

Every gate used so far (H48, H49, H50, H50-B, H51, H52) compared candidates **at their own emitted mass** on
the frozen blocked SGMC-off-catalogue proxy. That comparison is dominated by mass, because the proxy truth is
~4.3× denser than the live hidden truth:

| quantity | value | source |
|---|---:|---|
| proxy truth pixels (SGMC > 300 m off-catalogue, in footprint) | 62,122 | `evidence/holdout_h52_spatial_comparison_20261007.json` |
| live hidden truth pixels (ladder inversion, `N`) | ≈ 14,307 | `evidence/live_ladder_20261007.json`, `docs/research/why-02778-and-ceiling-20261007.md` |

On a denser truth, a *new* cell is far more likely to land within the 300 m kernel of something, so its
expected credit is inflated. The decisive control:

| emitted set | cells | proxy mean4 (4 quadrants) |
|---|---:|---:|
| incumbent C (H33-2-B2 dotted family) | 37,654 | **0.095607** |
| C + 18,000 **uniform-random** new cells (> 300 m off-catalogue) | 55,654 | 0.118872 |
| H49 ("proxy best", +0.0038 claimed, 4/4 folds) | 47,905 | 0.100968 |

Random mass added to the incumbent beats every curated candidate on that protocol. A ranking that a random
control wins cannot certify a candidate, and it explains the pattern of the last three sessions: every new
construction "won" on the proxy by emitting more cells and then failed the live-anchored checks.

## 2. The mass-neutral instrument

`scripts/audit_candidate.py` implements the two mass-neutral tests. Both use the repository's existing
four-quadrant core+300 m halo folds, the same official DTI parameters (α = 0.2, β = 0.8, triangular 300 m
kernel), the same evaluation mask (footprint minus exact known-fault pixels) and the same frozen proxy truth.

1. **Equal-mass test (credit density).** The candidate's support is uniformly subsampled to the incumbent's
   cell count (37,654) and scored. This measures how much credit one cell of the candidate buys, which is the
   quantity the live ladder actually pays for.
2. **Additions test (density-matched).** Cells the candidate emits that the incumbent does not are scored for
   marginal credit per added cell on a *density-matched* proxy — the proxy truth randomly thinned to the live
   truth count (14,307 cells, five seeds). This removes the ~4.3× density inflation. The pass bar is the
   metric's own break-even rule: adding one unit of mass pays only if it brings more than
   `credit_bar = 0.2 × DTI_incumbent = 0.0556` of new kernel credit.

## 3. Results (all receipts indexed in the evidence JSON)

| candidate | cells | proxy mean4 (own mass) | equal-mass mean4 | Δ equal-mass | added cells | additions: raw proxy / density-matched credit per cell | verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| **C incumbent** (`data/raw/scored/b2_02778.tif`) | 37,654 | 0.095607 | 0.095607 | +0.000000 | — | — | `IDENTICAL_TO_INCUMBENT` |
| H52 lidar additions | 39,654 | 0.096534 | 0.093181 | −0.002426 | 2,000 | 0.0418 / **0.0099** | FAIL |
| H49 DS conflict-balanced | 47,905 | 0.100968 | 0.087211 | −0.008397 | 10,251 | 0.0550 / **0.0125** | FAIL |
| H51 Pl-budget | 37,654 | 0.086641 | 0.086641 | −0.008966 | 5,375 | 0.0287 / **0.0063** | FAIL |
| H50 graded belief (> 0.5 cut) | 306,564 | 0.095604 | 0.075541 | −0.020067 | 268,910 | 0.0214 / **0.0049** | FAIL |
| h16-1 topo-geophys (dense) | 123,939 | 0.106212 | 0.077045 | −0.018562 | 96,673 | 0.0340 / **0.0077** | FAIL |
| h19-5 (dense) | 121,131 | 0.094522 | 0.071706 | −0.023904 | 83,477 | 0.0218 / **0.0050** | FAIL |
| hedge-v2 ensemble | 227,507 | 0.095659 | 0.058228 | −0.037384 | 222,693 | 0.0261 / **0.0060** | FAIL |
| uniform-random control (equal mass) | 37,654 | — | 0.067020 | −0.028587 | — | — | control |
| consensus-ranked re-selection (scratch, same folds) | 37,654 | — | 0.0548–0.0584 | −0.038…−0.041 | — | — | FAIL |

Readings:

- **No existing artifact has a higher credit density than the incumbent.** The second-best equal-mass score
  belongs to H52 (0.093181) *and only because H52 contains 95 % of the incumbent's own cells*. Every
  foreign-selection set is far worse: h16-1 0.0770, h19-5 0.0717, uniform random 0.0670, hedge-v2 0.0582,
  consensus-ranked 0.0548–0.0584.
- **Every documented addition is 4–14× below the break-even bar.** Density-matched marginals: H49's added
  cells 0.0125, H52's 0.0099, h16-1's 0.0077, h19-5's 0.0050, H50's 0.0049 — against 0.0556. This is the
  quantitative reason the H52 gate failed, and it is independent of the catalogue-adjacency criterion that
  failed it.
- **The 2026-10-06 declaration that H49 "beats the prior best on the proxies (+0.00376, 4/4 folds)" is a mass
  artifact.** At equal mass H49 loses to the incumbent by −0.0084. It is flagged here as a protocol
  irregularity in our own record: H49's extra 10,251 cells buy 0.05499 raw-proxy credit per cell (≈ the raw
  proxy bar 0.0191, so it looked profitable) but only 0.0125 per cell on a live-density-matched truth.
- **The catalogue-label proxy has the same defect in the other direction** (it is anti-monotone at the top of
  the ladder): H36-1 (tip rung30) scores ≈ 7× the incumbent on it at parity live score (0.2710 vs 0.2778), and
  a 300 m band around the catalogue scores 0.166. Neither proxy number should be quoted as progress.

## 4. The live ladder is a mass-budget ladder, not a geology ladder

Inverting `DTI = T / (0.2·M + 0.8·N)` with `N = 14,307.4` gives the captured kernel credit `T` of each
owner-reported rung (`registry/live_scores.json`, OWNER-REPORT, not organizer-authenticated):

| file | cells | owner-reported live DTI | implied T |
|---|---:|---:|---:|
| d2.8 rung A (`dotted_d2_8_02600`) | 44,090 | 0.2600 | 5,268.6 |
| r1-solo rung B | 40,199 | 0.2708 | 5,276.7 |
| **C incumbent b2-prune** | 37,654 | 0.2778 | **5,271.7** |
| d1.5 (denser dotted) | 60,069 | 0.2477 | 5,811.1 |
| tgc-v2 | 61,328 | 0.2449 | 5,806.9 |
| h19-5 (dense) | 121,131 | 0.1922 | 6,856.2 |
| h16-1 (dense) | 123,939 | 0.1855 | 6,721.5 |
| hedge-v2 (ensemble) | 227,507 | 0.1563 | 8,901.4 |

- **A → B → C holds T constant at ≈ 5,270 (spread 0.1 %) while deleting 6,436 cells.** The ladder's gains
  are pure mass-budget gains; the deleted cells carried ~0 live credit.
- Going the other way, densification buys credit at only ≈ 0.019 per added cell (h19-5's 83,477 extra cells
  add +1,584). That is **3× below** the 0.0556 break-even bar, which is why every denser submission ranks
  below the incumbent even though it captures more total credit.
- Reach 0.3774 (#1 public) at the incumbent's mass requires +1,890 more credit: e.g. ~19,000 cells at 0.10
  credit each, or ~3,800 cells at 0.50 each. Nothing in this repository, and no recombination of the layers
  already measured, delivers that rate.

## 5. What a slot-clearing candidate must show (GATE-2)

A candidate clears the mass-neutral screen only if **all** of:

1. **Format**: single-band float32, EPSG:32611, 3,730 × 3,292, finite and in [0, 1] inside the finite
   footprint, NaN or 0 outside (`scripts/validate_submission.py` independently re-reads the bytes).
2. **Equal-mass test**: subsampled to the incumbent's cell count, mean4 on the frozen blocked proxy must be
   within −0.002 of the incumbent (repeat-resolution) — i.e. the candidate's *selection* must be as good per
   cell, not just bigger.
3. **Additions test**: every cell emitted beyond the incumbent's set must earn ≥ 0.0556 marginal credit per
   cell on the density-matched proxy (and this must hold across seeds), i.e. ≥ ~0.24/cell on the raw proxy
   before the 4.3× density correction.

Reproduce any row of the table with:

```bash
python scripts/audit_candidate.py <candidate.tif> --receipt evidence/audit_<name>_gate2.json
python scripts/audit_candidate.py <candidate.tif> --support-threshold 0.5   # graded candidates
python scripts/audit_candidate.py <candidate.tif> --random-control           # mass-hack control
```

## 6. Consequences and next steps

- **The incumbent remains the best-evidenced artifact in the repository.** Nothing here justifies replacing,
  re-weighting, thinning or densifying it: thinning loses under both live-anchored models and under the
  instrument; additions of any available provenance fail the additions test by 4–14×.
- **The next slot should be held for a new-signal detector that can demonstrate the additions rate**, not for
  another fusion or budget variant of the existing surfaces. The only line with any independent lift measured
  so far is the native-lidar scarp work (`src/gemsdoe48/scarp3m.py`, H52); its v1 additions fail this test
  (0.0099/cell), so the v2 detector needs a *demonstrated* density-matched marginal ≥ 0.0556 before a
  submission slot is spent.
- **Known limitations.** Both mass-neutral tests are still public-proxy measurements: SGMC traces are not the
  private expert truth, the 4.3× density correction assumes the credit inflation is spatially homogeneous, and
  the equal-mass subsample carries repeat noise of roughly ±0.002. For H52's additions the density-matched
  estimate (0.0099) sits between the two independent live-anchored models — λ-plausibility 0.0109 and λ-mixture
  0.0141 per cell (same 25-offset kernel, `N = 14,307.4`) — three instruments, same negative conclusion, all far
  below the 0.0556 bar. The λ-mixture numbers are now committed and reproducible:
  [`scripts/lam3_residual_probe.py`](../../scripts/lam3_residual_probe.py) →
  [`evidence/lam3_residual_probe_20261007.json`](../../evidence/lam3_residual_probe_20261007.json). Its frontier
  result is §7.

## 7. Frontier probe (2026-10-07): is *any* new dot worth adding?

Sections 3–6 show that no **shipped** addition pays. The sharper question is whether *any* dot could pay:
one placed wherever the best available truth model wants it. `scripts/lam3_residual_probe.py` rebuilds the
two-component hidden-truth density model λ3 (Dempster–Shafer plausibility of the dotted/tip families, mixed
50/50 with the normalized kernel-credit of the sixteen other scored submissions, fitted to the seventeen
owner-reported live scores: `a = 0.50`, `N = 17,000`, rms = 0.02998) and measures the marginal credit per
added cell, always inside the union with the intact incumbent.

| addition | cells | credit/cell (ladder mass 14,307) | credit/cell (fitted mass 17,000) |
|---|---|---|---|
| H49 Yager-balanced DS | 10,251 | 0.0220 | 0.0262 |
| H52 2,000 lidar-scarp dots | 2,000 | 0.0141 | 0.0168 |
| H54 1,000 strictly-gated lidar-scarp dots | 1,000 | 0.0140 | 0.0166 |
| random 2,000 cells inside the λ3 support | 2,000 | 0.0133 | 0.0158 |
| λ3's own greedy optimum: top 250 uncovered cells | 250 | 0.0498 | 0.0592 |
| … top 500 | 500 | 0.0490 | 0.0582 |
| … top 1,000 | 1,000 | 0.0461 | 0.0548 |
| … top 4,000 | 4,000 | 0.0328 | 0.0389 |
| **break-even bar** (`0.2 ×` incumbent live DTI) | — | **0.0556** | **0.0556** |

Reading:

1. **Every shipped addition is worth about what random cells are worth.** The lidar-scarp additions earn
   0.0140–0.0168 per cell against a random control of 0.0133–0.0158, i.e. almost no live-credit signal beyond
   chance under this model; H49's Yager additions (0.0220–0.0262) carry a little more but are still 2–2.5× below
   the bar.
2. **Even the model's own greedy best cells only straddle the bar** (0.049–0.059 per cell), depending on whether
   the truth mass is taken from the ladder inversion (14,307) or from the λ3 fit itself (17,000). The maximum
   model-admissible DTI gain from *any* addition to the incumbent is therefore ≈ **+0.000 to +0.0004** — real but
   score-invisible.
3. **Consequence.** The incumbent sits on the frontier of the *entire current information set*. The remaining
   +0.04 to the leader (which needs additions worth ≥ 0.0556 per cell, ~4× anything ever measured here) can only
   come from information that is not present in any current layer. This is the quantitative form of the
   "0.3774 needs a different information source" conclusion in
   [`why-02778-and-ceiling-20261007.md`](why-02778-and-ceiling-20261007.md).

**Limits of the probe.** λ3 is fitted to seventeen owner-reported scores of *existing* submissions whose detectors
are themselves members of Q, so it can bound what the current information set yields; a genuinely new detector's
cells are invisible to Q by construction, so this probe does **not** bound lidar. It also inherits the ladder anchors
(OWNER-REPORT, not organizer-authenticated) and the model form (two components, `Pl**0.60`, fitted `N` between
10,000 and 17,000). Receipt: [`evidence/lam3_residual_probe_20261007.json`](../../evidence/lam3_residual_probe_20261007.json).
