# H50-1 candidate sweep — blocked SGMC proxy — 2026-10-07T03:10:55Z

Protocol: identical to `scripts/run_spatial_holdout.py` — four fixed quadrants, core + 300 m halo domain, truth = SGMC fault cells > 300 m from any public-catalogue cell (newer pinned derivative; raw-raster sensitivity in the second table), DTI with α = 0.2, β = 0.8, R = 300 m. The SGMC proxy is a *bedrock geologic-map* fault set; it is the agreed like-for-like instrument of this repository but a weak proxy for lidar-visible alluvial scarps, which is what H50-1 targets. Proxy scores are not organizer scores.

Inputs: base `/home/user/GEMSDOE48/data/families/dotted_b2_prune_02778.tif` (SHA-256 `c55bafc47005…`), scarp product `/home/user/GEMSDOE48/data/external/h50_scarp3m_100m.tif` (SHA-256 `b5e53d67c3a7…`), layer `h_gate12`, cover ≥ 0.9. Covered cells 3,657,635; eligible addition cells 2,027,126; Poisson-thinned pool 12,000.

## Label-free detector check (top cells of the gated height vs catalogue adjacency, per quadrant)

| Quadrant / tail | covered cells | selected | base near-rate | lift |
|---|---:|---:|---:|---:|
| NW_top2pct | 1,792,855 | 22,039 | 0.0368 | 1.188291 |
| NE_top2pct | 674,998 | 7,498 | 0.0303 | 2.268877 |
| SW_top2pct | 505,080 | 5,455 | 0.0510 | 1.532737 |
| SE_top2pct | 684,702 | 11,841 | 0.0356 | 1.633546 |
| NW_top1pct | 1,792,855 | 10,476 | 0.0368 | 1.165572 |
| NE_top1pct | 674,998 | 3,925 | 0.0303 | 2.247091 |
| SW_top1pct | 505,080 | 2,725 | 0.0510 | 1.483726 |
| SE_top1pct | 684,702 | 6,024 | 0.0356 | 1.563476 |

Global thresholds: top-2 % = 2.73 m, top-1 % = 2.94 m.

## Newer-SGMC off-catalogue proxy

| Candidate | dots | NW | NE | SW | SE | mean | Δ vs C | Δ vs H49 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C_dotted_02778 | 37,654 | 0.101822 | 0.099125 | 0.107461 | 0.073557 | 0.095491 | +0.000000 | -0.005260 |
| prior_union_decision | 47,905 | 0.102528 | 0.102656 | 0.106520 | 0.076262 | 0.096992 | +0.001500 | -0.003760 |
| h49_yager_balanced | 47,905 | 0.106053 | 0.107901 | 0.110414 | 0.078636 | 0.100751 | +0.005260 | +0.000000 |
| C + 500 lidar additions | 38,154 | 0.102209 | 0.099170 | 0.108395 | 0.073910 | 0.095921 | +0.000430 | -0.004830 (0/4 folds) |
| C + 1,000 lidar additions | 38,654 | 0.102070 | 0.099445 | 0.108353 | 0.074420 | 0.096072 | +0.000581 | -0.004679 (0/4 folds) |
| C + 2,000 lidar additions | 39,654 | 0.102006 | 0.099592 | 0.108025 | 0.076011 | 0.096409 | +0.000917 | -0.004343 (0/4 folds) |
| C + 3,000 lidar additions | 40,654 | 0.101926 | 0.099679 | 0.109263 | 0.076874 | 0.096935 | +0.001444 | -0.003816 (0/4 folds) |
| C + 4,000 lidar additions | 41,654 | 0.102325 | 0.100031 | 0.108527 | 0.077933 | 0.097204 | +0.001713 | -0.003547 (0/4 folds) |
| C + 6,000 lidar additions | 43,654 | 0.102843 | 0.100629 | 0.108073 | 0.079521 | 0.097767 | +0.002275 | -0.002985 (1/4 folds) |
| C + 8,000 lidar additions | 45,654 | 0.103907 | 0.100913 | 0.108061 | 0.081230 | 0.098528 | +0.003037 | -0.002223 (1/4 folds) |
| C + 12,000 lidar additions | 49,654 | 0.104757 | 0.101609 | 0.110186 | 0.086101 | 0.100663 | +0.005172 | -0.000088 (1/4 folds) |

## Raw-SGMC sensitivity (separate raster, not pooled)

| Candidate | mean | NW | NE | SW | SE |
|---|---:|---:|---:|---:|---:|
| C_dotted_02778 | 0.094503 | 0.101822 | 0.095184 | 0.107461 | 0.073546 |
| prior_union_decision | 0.095957 | 0.102528 | 0.098529 | 0.106520 | 0.076252 |
| h49_yager_balanced | 0.099768 | 0.106053 | 0.103980 | 0.110414 | 0.078627 |
| C + 500 | 0.094934 | 0.102209 | 0.095234 | 0.108395 | 0.073899 |
| C + 1,000 | 0.095088 | 0.102070 | 0.095518 | 0.108353 | 0.074410 |
| C + 2,000 | 0.095426 | 0.102006 | 0.095674 | 0.108025 | 0.076001 |
| C + 3,000 | 0.095936 | 0.101926 | 0.095693 | 0.109263 | 0.076864 |
| C + 4,000 | 0.096208 | 0.102325 | 0.096056 | 0.108527 | 0.077923 |
| C + 6,000 | 0.096763 | 0.102843 | 0.096625 | 0.108073 | 0.079512 |
| C + 8,000 | 0.097528 | 0.103907 | 0.096925 | 0.108061 | 0.081221 |
| C + 12,000 | 0.099666 | 0.104757 | 0.097627 | 0.110186 | 0.086093 |

## Pre-registered gate

* Best variant: C + 12,000 additions, mean 0.100663 (Δ vs C +0.005172; Δ vs H49 -0.000088, 1/4 folds above H49).
* Beats H49 on the mean **and** ≥ 3/4 folds: **no**.
* Detector top-2 % lift ≥ 2× in all four quadrants: **no**.
* **Slot decision: NOT slot-cleared.**

Machine-readable: `evidence/h50_candidate_sweep_20261007.json`.

## Controls (post-hoc, not pre-registered)

Two controls separate *what the detector ranks* from *where the lidar footprint and terrain class put the dots*. Both use the same eligibility, spacing and scoring as the main sweep; only the ordering of candidate cells differs.

| Additions | height-ranked (pre-registered) Δ vs C | random eligible cells Δ vs C | random cells in the 0.7–2.5 m roughness band Δ vs C | roughness-band folds above H49 |
|---:|---:|---:|---:|---:|
| 2,000 | +0.000917 | -0.000155 | — | —/4 |
| 4,000 | +0.001713 | +0.000168 | +0.003921 | 2/4 |
| 8,000 | +0.003037 | +0.000552 | +0.006048 | 3/4 |
| 12,000 | +0.005172 | +0.000484 | +0.009078 | 3/4 |

Reading: height-ranked additions beat random additions by ~10× on this proxy, but random dots confined to the 0.7–2.5 m context-roughness band (dissected piedmont / range-front terrain) do better still (+0.009078 at 12,000, beating H49 by +0.003818 on the mean, 3/4 folds). On the SGMC bedrock-fault proxy the detector's value is therefore its *terrain class*, not its step height; the label-free check agrees (top-2 % height cells 1.48× catalogue-adjacency lift vs 1.57× for the roughness band alone, `evidence/h50_region_detector_checks_20261007.json`). The roughness-band result is a post-hoc control on a proxy that systematically favours rock-exposed terrain; it is **not** promoted to a candidate and clears no slot.

## Pilot vs region

The two pilot tiles gave 2.3–3.2× top-2 % lift for the gated height (`evidence/h50_pilot_scarp_eval_20261007.json`, n = 44–98 cells); region-wide the same statistic is 1.19× (NW), 2.27× (NE), 1.53× (SW), 1.63× (SE). The pilot did not generalise: the pre-registered label-free gate (≥ 2× in all four quadrants) fails. Visual inspection of the pilot tiles (hillshade overlays, this session) shows why — the top-2 % height cells sit on fan-head incision and terrace risers along range fronts (≥ 2.7 m effective steps), while the catalogue's faint basin-floor scarps (0.3–1 m) fall below the threshold and the flattest terrain class (σ_ctx < 0.2 m) is dominated by playas and agriculture (lift 0.5×).
