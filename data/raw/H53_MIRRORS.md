# Force-committed H53 input mirrors

`data/raw/` is git-ignored. The eight files listed here are force-committed anyway, because
`scripts/calibrate_live_model.py`, `scripts/build_submission_h53.py` and `tests/test_h53.py`
cannot run without them and they are small enough (10 MB total) to be consistent with the
43 MB and 26 MB rasters this repository already tracks.

Every one is a **third-party owner mirror**, not an organizer-authenticated artifact. Each was
fetched over `gh api` (GitHub egress only; DrivenData was never contacted — its terms of use
prohibit automatic access) and **fails closed on a SHA-256 mismatch**. Hash pinning establishes
byte identity only; reuse licences were not verified.

| file | SHA-256 | upstream | owner-reported live | role |
|---|---|---|---|---|
| `scored/h19_5_01922.tif` | `ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d` | GEMSDOE24 @ `07345ea0` | 0.1922 | dense corridor backbone, 121,131 px |
| `scored/d15_02477.tif` | `68d0e2e4fcc594f9a23f56c44b885fee733d026d39be55e18ad2a07289525310` | GEMSDOE24 @ `07345ea0` | 0.2477 | Poisson d = 1.5 px thinning, 60,069 px |
| `scored/h36_rung30_02710.tif` | `5556aa1438fd67376b60d5ffc99228ec09dcc11a8408298a743ccb88d6163641` | GEMSDOE28 @ `main` | 0.2710 | independent 37,660 px thinning |
| `scored/h32_prethin_tip_02649.tif` | `04d31922f5c1ea4016984fc470ab2b0ff8e266c615792f0e86020da3b940d3ff` | GEMSDOE28 @ `main` | 0.2649 | tip/Euler variant, 42,294 px |
| `scored/sgmc44k_00512.tif` | `9b83158bde01cd5d42e38229d70d01e67cecd2514eeb5fa8d1f3ab6851469dad` | GEMSDOE29 @ `main` | 0.0512 | **the out-of-family transfer test** |
| `external/gdr_wellspring_in_footprint.csv` | `122718e65bdf55aab0ee12ad20d80062f0deb1de957225a61ad880dd5dc196ea` | GEMSDOE24 @ `07345ea0` | — | GDR 1391 wells & springs, 27,092 records (H53-A) |
| `external/gdr_qfaults_traces.csv` | `9702f2e5c382a4f472ae834d22b94990983b059677a37adfafd51c50f75e643c` | GEMSDOE24 @ `07345ea0` | — | INGENIOUS Quaternary trace attributes (H53-E) |
| `external/gdr_volcanic_vents.csv` | `f91bafbaccaaf2754e71d60434fc0f9eb2c7b880c6e714883f4974542ff6a0bf` | GEMSDOE24 @ `07345ea0` | — | Quaternary volcanic vents, 22 records |

Upstream source for the three `external/` CSVs: Geothermal Data Registry submission 1391,
*INGENIOUS Great Basin Regional Dataset Compilation*, DOI
[10.15121/1881483](https://doi.org/10.15121/1881483),
<https://gdr.openei.org/submissions/1391>. Data.gov metadata reports CC BY 4.0; the GDR
asset-level attribution/reuse terms were **not** independently verified.

`gdr_wellspring_in_footprint.csv` carries a `dist_known_fault_px` column that is derived from the
competition labels. `src/gemsdoe48/conduit.py` drops it on read
(`conduit.LEAKY_COLUMNS`) and `tests/test_h53.py` asserts the drop.

## Deliberately NOT committed

| file | size | how to restore |
|---|---|---|
| `training_features.tif` (official 19-band stack) | 418,912,844 B | `python scripts/restore_h53_inputs.py --with-official-features` — reassembles five pinned shards from GEMSDOE @ `c0c06ac8` and verifies SHA-256 `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5` |
| `bridge/part-000..004` | ~472 MB | transient; deleted by the restore script after concatenation |
| `external/geodawn_extensions_u8.tif` | 27,132,925 B | `python scripts/restore_h53_inputs.py --only geodawn_extensions_u8`; only `scripts/compare_coverage_weightings.py` uses it, and that script skips the weighting with an explicit note when it is absent |

## Two local twins are byte-different but pixel-identical to the mirrors above

`data/raw/ref_h36_1_rung30.tif` (SHA-256 `7c74270a…`) and
`data/raw/tip_h32_1_prethin_tip_euler.tif` (SHA-256 `26748e4b…`) were already tracked. Each has
an **identical emission pixel set** to the corresponding published mirror above
(`np.array_equal` on the boolean mask, verified) and differs only in outside-footprint encoding
and tags. `src/gemsdoe48/live_model.py` pins the *published* mirrors so every hash in the
calibration is the upstream one. See IR-H53-07 in `docs/irregularities.md`.
