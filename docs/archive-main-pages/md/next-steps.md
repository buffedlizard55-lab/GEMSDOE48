> **Historical archive.** This earlier upstream page is preserved for provenance and may contain superseded claims. Do not treat it as the current submission or validation decision. See the [current overview](../../index.html) and [current validation](../../validation.html). Any six-hour leaderboard-feed instructions are obsolete: the current branch disables the workflow under its Terms-of-Use review, and the retained parser has no network-fetch path.

---

# Next steps, ranked by P(Win) impact

1. **H48-2: native 1 m LiDAR scarps via GitHub Actions** (the only path to 0.32–0.38).
   The matrix workflow streams one 3DEP tile per job, computes paired profile curvature at 1 m,
   and commits a 100 m detection raster (~kB) per tile. Data obtainability was verified (TNM API).
   Blocker: this sandbox has no USGS egress, so it must run on Actions runners.
2. **Spend 3 slots on the λ-probe.** Submit S1 = this file, S2 = this file × 0.5, and
   S3 = this file + N dots far from any fault. `1/DTI` is linear in `1/λ`, so the three returns
   give exact `T`, `F`, `K`. That turns LSI from a coarse instrument into an exact one and settles
   IR-48-06 and IR-48-12. All three probes score ≤ the anchor, so they cannot cost rank.
3. **H48-5: dry-season Sentinel-2 NDVI lineaments** (Actions job via Element84 STAC). Mask
   NLCD cultivated land.
4. **Extend the uniqueness audit** to all ~47 sibling repos (git-tree listing, then download
   only `.tif` files with matching pixel counts).
5. **Replace Dempster with Denœux's cautious rule** once a second genuinely independent source
   (H48-2 or H48-5) exists. Then the fusion has real independent evidence to fuse.
6. **Record every live score** in `registry/live_scores.json`. Each new score tightens LSI.

## Limitations / access needed
* **DrivenData login.** Not available, and never requested. Scores are owner-reported, and the
  owner must upload files.
* **Network.** No egress to USGS, AWS, ScienceBase or community.drivendata.org from the sandbox.
  GitHub Actions has egress.
* **Compute.** 2 CPU, 3 GB RAM, no GPU. Enough for 100 m work, not for 1 m processing of the
  whole footprint.
* **Truth.** The hidden expert labels are unknowable offline, so fine-scale selection needs live
  probes.
