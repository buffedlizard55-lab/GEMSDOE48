# H56-F pruning-ladder results — no submission slot

**Decision: all three preregistered H56-F rungs fail the current same-protocol H49 holdout comparison; no H56-F slot is cleared.** The old live-model kill threshold was not used: its score projection is invalidated because the derivation assumes the generally false identity `FPw = S − TPw`. This is a blocked-proxy test only, not a private-label score.

## Construction

H56-F keeps the dotted C parent cells where the H56B normalized Dempster belief is at least τ ∈ {0.99, 0.95, 0.90}. These thresholds and the primary τ=0.99 rung were recorded in the H56B slate before scoring. The candidate is a *binary retained subset of C*, not the H56B belief raster. A same-count random pruning control draws 24 masks from the 37,654 dotted pixels at the τ=0.99 budget (31,614 cells), seed 20261007.

## Exact spatially blocked results

The comparison uses the same fixed full-grid 2×2 quadrants, 300 m footprint-clipped halo, core-only truth, and official DTI implementation as [`scripts/run_spatial_holdout.py`](../../scripts/run_spatial_holdout.py). H49 is the current comparable best on both proxies: 0.095353 catalogue and 0.100751 SGMC off-catalogue.

| H56-F rung | Kept cells | Removed from C | Catalogue mean DTI | SGMC off-catalogue mean DTI | Δ vs H49 (catalogue / SGMC) | Folds above H49 (catalogue / SGMC) |
|---|---:|---:|---:|---:|---:|---:|
| τ=0.99 (primary) | 31,614 | 6,040 | 0.005337 | 0.081123 | −0.090016 / −0.019629 | 0/4 / 0/4 |
| τ=0.95 | 37,142 | 512 | 0.006744 | 0.094821 | −0.088609 / −0.005930 | 0/4 / 0/4 |
| τ=0.90 | 37,654 | 0 | 0.006831 | 0.095491 | −0.088523 / −0.005260 | 0/4 / 0/4 |

The τ=0.90 mask is exactly the original dotted parent (no removal). τ=0.95 removes only 512 cells; τ=0.99 removes 6,040. None clears the required positive-mean and ≥3/4-fold rule against H49 on both proxies.

### Primary τ=0.99 rung — fold values

| Fold | H56-F DTI, catalogue | H56-F DTI, SGMC off-catalogue |
|---|---:|---:|
| NW | 0.004901 | 0.090059 |
| NE | 0.005975 | 0.082872 |
| SW | 0.006388 | 0.089135 |
| SE | 0.004083 | 0.062424 |

### Same-budget random deletion control

For the primary τ=0.99 rung, the 24-mask random-pruning mean was 0.005932 on catalogue and 0.084944 on SGMC off-catalogue; the belief-ranked subset scored 0.005337 and 0.081123, respectively. **All 24 random masks scored above the H56-F rung on both means.** This is descriptive, not a significance test, and strongly rejects spending a slot on this threshold construction.

## Reproduction / decision

- Receipt: [`evidence/holdout_h56_pruning_ladder_20261007.json`](../../evidence/holdout_h56_pruning_ladder_20261007.json).
- Re-run: `./.venv/bin/python scripts/validate_h56_pruning_ladder.py`.
- The script checks the pinned H56B, C, H33-D, H49, label, SGMC and footprint inputs; it also reproduces the pinned H49 fold values before reporting candidates.
- The original projection-based kill criterion is invalid; no live score is inferred.
- H56-F is an evidence-selection operator, not a distinct geological hypothesis or independent data source. Its failure does not establish that geological signals are unhelpful; it rejects this frozen deletion rule on these proxies.

**Verdict: H56B remains OK to download for inspection, but NOT OK / NOT CLEARED to submit. H56-F creates no submission.** The public proxies cannot authorize a weekly slot, and no organizer receipt maps any local H56 TIFF to a public leaderboard score.
