#!/usr/bin/env python3
"""Render the H50 DS layers to PNG figures for the docs site.

Produces two figures:
  docs/assets/h50_ds_layers.png      -- belief / unassigned / conflict panels
  docs/assets/h50_disagreement.png   -- DS belief vs naive mean, disagreement map
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from gemsdoe48 import ds50
from gemsdoe48.geotiff import read_band

ROOT = Path(__file__).resolve().parents[1]
DOTTED = ROOT / "data/raw/dotted_h33_2_b2_zeros.tif"
TIP_H36 = ROOT / "data/source_mirrors/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif"
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
OUTDIR = ROOT / "docs/assets"


def finite(v: np.ndarray) -> np.ndarray:
    return np.where(np.isfinite(v), v, 0.0)


def main() -> int:
    import rasterio

    dotted = finite(read_band(DOTTED)[0])
    tip = finite(read_band(TIP_H36)[0])
    with rasterio.open(FOOTPRINT) as ds:
        footprint = ds.read(1) == 1

    belief_a = ds50.kernel_belief_surface((dotted > 0) & footprint)
    belief_b = ds50.kernel_belief_surface((tip > 0) & footprint)
    a_dotted = ds50.RHO_MAX
    a_tip = ds50.RHO_MAX * (ds50.LIVE_TIP_H36 / ds50.LIVE_DOTTED_B2)
    fusion = ds50.dempster_fuse(belief_a, belief_b, a_dotted, a_tip, footprint=footprint)
    naive = ds50.naive_mean_belief(belief_a, belief_b)
    naive = naive / naive[footprint].max()

    bel = np.where(footprint, fusion.belief_normalized, np.nan)
    unc = np.where(footprint, fusion.unassigned, np.nan)
    conf = np.where(footprint, fusion.conflict, np.nan)
    nv = np.where(footprint, naive, np.nan)
    diff = np.where(footprint, fusion.belief_normalized - naive, np.nan)

    rows, cols = np.nonzero(footprint)
    r0, r1 = int(rows.min()), int(rows.max()) + 1
    c0, c1 = int(cols.min()), int(cols.max()) + 1
    sl = (slice(r0, r1), slice(c0, c1))
    dpi_scale = 0.28  # keep figures small for the web

    fig, axes = plt.subplots(1, 3, figsize=(15 * dpi_scale * 2, 6.5 * dpi_scale * 2))
    for ax, data, title, cmap in (
        (axes[0], bel[sl], "Dempster belief Bel(F), normalized [0,1]", "magma"),
        (axes[1], unc[sl], "Unassigned mass m(Θ) — carried uncertainty", "viridis"),
        (axes[2], conf[sl], "Raw conflict K — active disagreement", "inferno"),
    ):
        im = ax.imshow(data, cmap=cmap, vmin=np.nanmin(data), vmax=np.nanmax(data))
        ax.set_title(title, fontsize=8)
        ax.axis("off")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    fig.suptitle("GEMSDOE48 H50 — best dotted × best tip, Dempster-Shafer layers", fontsize=9)
    fig.tight_layout()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTDIR / "h50_ds_layers.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(15 * dpi_scale * 2, 6.5 * dpi_scale * 2))
    for ax, data, title, cmap, vm in (
        (axes[0], nv[sl], "Naive mean 0.5·(b_dotted + b_tip)", "magma", None),
        (axes[1], bel[sl], "DS belief (this submission)", "magma", None),
        (axes[2], diff[sl], "DS belief − naive mean (disagreement preserved)", "RdBu_r", None),
    ):
        if vm is None:
            vmax = np.nanmax(np.abs(data)) if title.startswith("DS belief −") else np.nanmax(data)
            vmin = -vmax if title.startswith("DS belief −") else np.nanmin(data)
        im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax)
        ax.set_title(title, fontsize=8)
        ax.axis("off")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
    fig.suptitle("GEMSDOE48 H50 — not the average: where the DS rule moves mass", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUTDIR / "h50_disagreement.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    receipt = {
        "figures": [
            "docs/assets/h50_ds_layers.png",
            "docs/assets/h50_disagreement.png",
        ],
        "inputs": {
            "dotted_sha256": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
            "tip_h36_sha256": "5556aa1438fd67376b60d5ffc99228ec09dcc11a8408298a743ccb88d6163641",
        },
    }
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
