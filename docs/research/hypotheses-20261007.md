# Preregistered hypothesis slate — H50 session, 2026-10-07 UTC

**Status: preregistered before holdout scoring.** Distinct from the frozen
2026-10-06 slate (H48-1…H48-5) and from everything implemented in this or the
reviewed sibling repos. Ranking is expected value-of-information per cost, not
a promised gain. No candidate is promoted to a submission slot on this page.

## Session-later results (added 2026-10-07, later session)

- **H50-A** — not yet validated on the blocked folds; still the top slate
  priority (implementation sketch in `docs/md/next-steps.md`).
- **H50-B** — **tested this session, negative result.** Preregistered
  construction (conflict K>0.3 corridor ∩ high-K gate ∩ robust-z low-Th/K,
  budget 37,654) scored 0.015312 catalogue / 0.019135 SGMC off-catalogue,
  far below every structure-based comparator. Receipts:
  `evidence/h50b_preregistration_20261007.json`,
  `evidence/holdout_h50b_20261007.json`. The GeoDAWN mirror used is committed
  SHA-verified at `data/source_mirrors/geodawn_rad_u8.tif`.
- **H50-C / H50-D / H50-E** — untested; H50-D's LiDAR scarp mirror is now
  restorable via the same GitHub-mirror path used for the radiometrics.
- **H51 (method family, added post-slate, preregistered before its own
  scoring)** — plausibility-ranked budget emission of the H50 fusion: gate
  failed (0.086537 SGMC / 0.007589 catalogue vs required wins over H49 and
  the union). See `docs/research/h51-h50b-results-20261007.md`.

## H50-A — coverage-budget credit repacking on scatter-blurred family fields

- **Layers:** the two frozen family surfaces, the mirrored catalogue
  (footprint/geometry only), no new external data.
- **Physical signature:** the hidden expert set is inferred (GEMSDOE32
  derivation, [DERIVED]) to be ~12,632 px scattered around true fault surfaces
  at ~1.85 px scale; covering the family fields *blurred* at that scale with a
  greedy credit-packing budget (break-even bar k > 0.2·DTI) instead of fusing
  them should raise credit density where the families are corroborated and cut
  budget where they are lone.
- **Why off-catalogue:** the repacker is free to spend budget on
  single-family corridors far from the catalogue whenever the marginal credit
  model says so; it is not tied to catalogue proximity.
- **Difference from prior art:** H33/H49 emitted fixed-budget unions or
  pignistic ranks; this is a two-round objective (cover the blurred field,
  then spend residual budget on the highest marginal-credit single-family
  cells), measured +0.0247±0.0005 in 12/12 draws on the sibling live-anchored
  truth model ([DERIVED], not a score).
- **Expected DTI / cost:** highest expected gain of the slate; medium cost;
  fully computable locally. **Validation required before any slot.**

## H50-B — radiometric alteration ratio × DS conflict corridors

- **Layers:** GeoDAWN airborne radiometrics K/Th/U/TC (owner-mirror
  `ext_geodawn_rad_u8`, upstream official USGS data release DOI
  [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ), restorable from the
  GEMSDOE24 public mirror) crossed with the H50 conflict layer K.
- **Physical signature:** hydrothermal alteration (clay/potassic) depresses
  Th/K; a *linear* low-Th/K trend inside a high-K disagreement corridor is a
  fluid-pathway candidate the two structural families split on.
- **Why off-catalogue:** alteration records past fluid flow along buried or
  weakly expressed structures absent from the Quaternary-fault inventory.
- **Difference:** no reviewed campaign crosses alteration *ratios* with a
  two-family conflict prior; prior radiometric work (r11f 0.1589) fused raw
  channels with scarps.
- **Expected / cost:** moderate, uncertain; medium cost (restore mirror, audit
  bands, holdout). Official source free and obtainable (verified present in
  the sibling mirror with SHA pin).

## H50-C — shallow temperature probe residual prior along family corridors

- **Layers:** INGENIOUS 2 m temperature probes (GDR 1391, CC BY 4.0, DOI
  [10.15121/1881483](https://doi.org/10.15121/1881483); fetched by sibling CI
  per `data/raw/external_receipt_g30.json`) residualized against elevation and
  depth; intersect family support corridors.
- **Physical signature:** localized shallow heat anomalies on a structural
  corridor indicate a permeable, possibly unmapped, pathway.
- **Why off-catalogue:** active seeps are independent of scarps; several known
  systems have no mapped Quaternary trace at the vent.
- **Difference:** temperature has appeared only as a regional favorability
  channel, never as a residual point prior gated by two-family support.
- **Expected / cost:** low–moderate (sparse points); medium cost; free data
  obtainable (receipt shows successful sibling fetch).

## H50-D — scarp-youth continuation past catalogue tips

- **Layers:** LiDAR-derived scarp features (owner-mirror
  `ext_lidar_scarp_features_u8`, upstream USGS 3DEP 1 m DEM, no use
  restrictions per sibling receipt) morphology (height/length, dissection) at
  catalogue trace tips.
- **Physical signature:** youthful, continuous scarp segments extending beyond
  a mapped trace tip are candidate unmapped continuations; rank by relief
  index, emit only where the family corridor also supports.
- **Why off-catalogue:** explicitly spends budget past the catalogue endpoint.
- **Difference:** GEMSDOE38 used step-over/Euler tip protection (0.0763); this
  uses scarp *morphology youth*, a different observable.
- **Expected / cost:** moderate; medium cost; data restorable from sibling
  mirror with SHA pin.

## H50-E — oriented splay prior from SGMC contact topology (refined H50-1)

- **Layers:** USGS SGMC structure vectors (NV/CA zips; public domain; sibling
  CI receipt `data/raw/external_receipt_g30.json`) + catalogue trace geometry.
- **Physical signature:** damage-zone splays branch at characteristic angles
  from parent traces at extensional bends; build oriented offset bands from
  *vector* geometry, not isotropic distance.
- **Why off-catalogue:** targets unmapped splays by construction.
- **Difference from tested coarse version:** the coarse isotropic 100–600 m
  band was validated this session and **failed** (SGMC offcat 0.0518 vs 0.0970
  union; see `evidence/splay_probe_holdout_20261007.json`); orientation gating
  is the untested refinement.
- **Expected / cost:** low–moderate; medium–high cost; official data verified
  obtainable in sibling CI.

## Validation rule carried forward

A candidate touches a weekly slot only after beating the current blocked
holdout best (union 0.0970 SGMC offcat; H49 0.1008 on the same proxy) in ≥3/4
folds on *both* proxy regimes, with the construction re-derived inside folds
where feasible, and with the leakage limitation restated. The coarse splay
band (H50-1) did not clear this and is recorded as a negative result.

## Append-only related probe implementation result (after merge)

The separately documented H50-GDR repeat-persistence raster uses the same
INGENIOUS 2 m probe source as H50-C, but does **not** implement H50-C's
family-corridor gate or elevation/depth residualization. It is therefore a
related single-source operator test, not a completed H50-C run. Its corrected
v2 sensitivity scored 0.003923 versus H49 0.100751 (paired −0.096828; 0/4
positive folds) on the primary public proxy and failed the promotion gate.
Because v2 corrected source identity after v1 scores were observed, this is not
confirmatory evidence. See [`h50-gdr-probe-slate-20261007.md`](h50-gdr-probe-slate-20261007.md)
and [`../../evidence/h50_gdr_prior_art_errata_20261007.json`](../../evidence/h50_gdr_prior_art_errata_20261007.json).
