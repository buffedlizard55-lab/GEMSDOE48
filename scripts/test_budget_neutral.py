#!/usr/bin/env python3
"""Budget-neutral fusion: spend the live-tuned budget over BOTH families.

The live record fixes the budget near 37,654 emitted dots (every recorded move
away from it in either direction is unmeasured, and the proxy cannot price a
budget change because its truth set is ~5.7x denser than the hidden set).  So
the fusion is done with the budget held constant: rank the union of the two
families' candidate cells by the Dempster-Shafer pignistic probability and keep
the live-tuned number of them.  At equal mass this is a like-for-like
comparison on the blocked proxy, and it is a genuine fusion -- the weakest
dotted-only cells are traded for the strongest tip/step-over cells.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems48.evidence import (  # noqa: E402
    combine_dempster,
    combine_yager,
    discounted_binary_mass,
    kernel_support,
    pignistic,
)
from gems48.emission import poisson_sample  # noqa: E402
from gems48.metric import dti  # noqa: E402

R_DOTTED = 0.90
R_TIP = 0.90 * (0.11987588720357811 / 0.13446190223260976)
DOTTED = ROOT / "data/raw/dotted.tif"
TIP = ROOT / "data/raw/tip.tif"
TEMPLATE = ROOT / "data/raw/sample_submission.tif"
LABELS = ROOT / "data/raw/labels.tif"
SGMC = ROOT / "data/raw/external/derived_sgmc_faults_100m_u8.tif"
NB = 4


def rd(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        return s.read(1)


def pick(score: np.ndarray, n: int, allowed: np.ndarray, spacing: float | None = None) -> np.ndarray:
    h, w = score.shape
    idx = np.flatnonzero(allowed.ravel())
    order = idx[np.argsort(-score.ravel()[idx], kind="stable")]
    out = np.zeros(score.size, bool)
    if spacing is None:
        sel = order[:n]
        out[sel] = True
        return out.reshape(score.shape)
    r = int(np.ceil(spacing))
    offs = [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1) if dy * dy + dx * dx <= spacing * spacing]
    blocked = np.zeros(score.size, bool)
    taken = 0
    for flat in order:
        if taken >= n:
            break
        if blocked[flat]:
            continue
        y, x = divmod(int(flat), w)
        out[flat] = True
        taken += 1
        for dy, dx in offs:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w:
                blocked[yy * w + xx] = True
    return out.reshape(score.shape)


def blocks(shape, n=NB):
    h, w = shape
    return [(slice(i * h // n, (i + 1) * h // n), slice(j * w // n, (j + 1) * w // n))
            for i in range(n) for j in range(n)]


def main() -> None:
    dotted = rd(DOTTED) > 0
    tip = rd(TIP) > 0
    labels = rd(LABELS) > 0
    sgmc = rd(SGMC) > 0
    footprint = np.isfinite(rd(TEMPLATE))
    d_cat = distance_transform_edt(~labels)
    truth = sgmc & footprint & (d_cat >= 3.0)

    sup_d = kernel_support(dotted.astype(np.float64))
    sup_t = kernel_support(tip.astype(np.float64))
    a = discounted_binary_mass(sup_d, R_DOTTED)
    b = discounted_binary_mass(sup_t, R_TIP)
    bel, dis, u, k = combine_yager(a, b)
    bel_d, _, _ = combine_dempster(a, b)
    betp = pignistic(bel, dis)

    union = dotted | tip
    N = int(dotted.sum())
    cands = {
        "dotted_parent": dotted,
        "tip_parent": tip,
        "union_binary": union,
        "union_top_betp_37654": pick(betp, N, union),
        "union_top_betp_37654_s20": pick(betp, N, union, spacing=2.0),
        "union_top_bel_yager_37654": pick(bel, N, union),
        "union_top_bel_dempster_37654": pick(np.nan_to_num(bel_d, nan=-1.0), N, union),
        "union_top_support_sum_37654": pick(sup_d + sup_t, N, union),
    }
    blks = blocks(truth.shape)
    rows = {}
    for name, mask in cands.items():
        arr = mask.astype(np.float64)
        r = dti(arr, truth)
        per = [dti(arr[ys, xs], truth[ys, xs]).dti for ys, xs in blks if truth[ys, xs].sum() >= 50]
        per_parent = [dti(dotted.astype(np.float64)[ys, xs], truth[ys, xs]).dti for ys, xs in blks if truth[ys, xs].sum() >= 50]
        rows[name] = {**r.as_dict(), "dots": float(mask.sum()),
                      "block_dti_mean": float(np.mean(per)),
                      "blocks_won_vs_parent": int(np.sum(np.array(per) > np.array(per_parent))),
                      "blocks": len(per),
                      "overlap_with_dotted_parent": float((mask & dotted).sum()),
                      "overlap_with_tip_parent": float((mask & tip).sum())}
    base = rows["dotted_parent"]["dti"]
    for v in rows.values():
        v["delta_vs_dotted_parent"] = v["dti"] - base

    out = {
        "schema": "GEMSDOE48-budget-neutral-fusion-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "budget": N,
        "candidates": rows,
    }
    (ROOT / "docs" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "data" / "h49-budget-neutral-fusion.json").write_text(json.dumps(out, indent=2) + "\n")
    for kk, v in sorted(rows.items(), key=lambda kv: -kv[1]["dti"]):
        print(f"{kk:34s} dots={v['dots']:7.0f} dti={v['dti']:.6f} d={v['delta_vs_dotted_parent']:+.6f} "
              f"blk={v['block_dti_mean']:.6f} won={v['blocks_won_vs_parent']}/{v['blocks']} "
              f"ovD={v['overlap_with_dotted_parent']:.0f} ovT={v['overlap_with_tip_parent']:.0f}")


if __name__ == "__main__":
    main()
