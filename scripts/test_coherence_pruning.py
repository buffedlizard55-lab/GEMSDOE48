#!/usr/bin/env python3
"""H-A: lateral lineament coherence as a pruning signal.

Geological statement
--------------------
A fault is a laterally persistent structure: a real (even unmapped) fault
produces a scarp, a drainage offset, a magnetic contact and a strain-rate
anomaly that are *collinear over kilometres*.  Noise that survives a ridge
detector -- alluvial-fan edges, ploughed-field boundaries, roads, canal banks,
DEM tile seams, isolated pits -- is either isolated, blobby, or short.  If a
dot's local neighbourhood is not elongated and persistent, the probability that
a hidden fault passes through it is lower, so its expected credit is lower and
it should carry less of the emission budget.

What is measured here
---------------------
For every dot of the incumbent emission we compute (i) the realised proxy
credit it contributes (an upper bound on what removing it would cost) and
(ii) several geometry features, then bin.  A removal is only admissible under
GEMSDOE32's published slot rule (safety >= 2) if the group's realised proxy
credit per dot is below 0.0368 proxy units = (alpha*DTI/2)/0.756, where 0.756 is
the live/proxy transfer ratio measured on group B in
``h49-instrument-calibration.json``.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_filter, label, uniform_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems48.evidence import kernel_support  # noqa: E402
from gems48.metric import ALPHA, credit_per_dot, dti  # noqa: E402

DOTTED = ROOT / "data/raw/dotted.tif"
TEMPLATE = ROOT / "data/raw/sample_submission.tif"
LABELS = ROOT / "data/raw/labels.tif"
SGMC = ROOT / "data/raw/external/derived_sgmc_faults_100m_u8.tif"

LIVE_DTI = 0.2778
TRANSFER = 0.7560057154680643     # [MEASURED] live/proxy credit ratio on group B
SAFETY = 2.0
BAR_LIVE = ALPHA * LIVE_DTI
REMOVE_IF_PROXY_BELOW = BAR_LIVE / SAFETY / TRANSFER


def rd(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        return s.read(1)


def structure_tensor_coherence(field: np.ndarray, sigma: float) -> np.ndarray:
    """Coherence = (l1 - l2) / (l1 + l2) of the smoothed structure tensor."""
    f = gaussian_filter(field.astype(np.float64), sigma)
    gy, gx = np.gradient(f)
    jxx = gaussian_filter(gx * gx, sigma)
    jyy = gaussian_filter(gy * gy, sigma)
    jxy = gaussian_filter(gx * gy, sigma)
    tr = jxx + jyy
    det = jxx * jyy - jxy * jxy
    disc = np.sqrt(np.maximum(tr * tr / 4.0 - det, 0.0))
    l1 = tr / 2.0 + disc
    l2 = tr / 2.0 - disc
    return np.where(l1 + l2 > 1e-12, (l1 - l2) / (l1 + l2 + 1e-12), 0.0)


def main() -> None:
    dotted = rd(DOTTED) > 0
    labels = rd(LABELS) > 0
    sgmc = rd(SGMC) > 0
    footprint = np.isfinite(rd(TEMPLATE))
    d_cat = distance_transform_edt(~labels)
    truth = sgmc & footprint & (d_cat >= 3.0)

    cred, _, _ = credit_per_dot(dotted.astype(np.float64), truth)
    sup = kernel_support(dotted.astype(np.float64))

    feats: dict[str, np.ndarray] = {}
    # local dot density (how many sibling dots within r cells, excluding itself)
    for r in (3, 5, 8):
        k = 2 * r + 1
        cnt = uniform_filter(dotted.astype(np.float64), size=k) * k * k
        feats[f"dot_density_r{r}"] = cnt - dotted
    # connected-component size of the dot set (connectivity radius sqrt(2)*2 cells)
    lab, n = label(dotted)
    sizes = np.bincount(lab.ravel())
    comp = np.where(lab > 0, sizes[lab], 0)
    feats["component_size_5x5"] = comp.astype(np.float64)
    # multi-scale ridge persistence: support of the support, at two widths
    feats["support_persistence_2px"] = kernel_support(np.clip(sup * 3.0, 0, 1))  # re-sharpened
    feats["coherence_sigma2"] = structure_tensor_coherence(sup, 2.0)
    feats["coherence_sigma4"] = structure_tensor_coherence(sup, 4.0)
    feats["dist_to_catalogue"] = d_cat
    feats["local_support_sum_r3"] = uniform_filter(sup, size=7) * 49

    report = {
        "schema": "GEMSDOE48-coherence-pruning-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "H-A: dots whose neighbourhood is not a laterally persistent, elongated lineament carry less credit than coherent ones and may be pruned.",
        "removal_rule": {
            "live_bar": BAR_LIVE,
            "safety_required": SAFETY,
            "live_over_proxy_transfer": TRANSFER,
            "remove_if_realised_proxy_credit_per_dot_below": REMOVE_IF_PROXY_BELOW,
            "calibration": "group B (2,545 flank dots known to have gained live when removed) has realised proxy credit 0.03046 -> safety 2.03, matching GEMSDOE32's independently reported 2.08.",
        },
        "base": {"dots": int(dotted.sum()), "proxy_dti": dti(dotted.astype(np.float64), truth).dti,
                 "proxy_tp": dti(dotted.astype(np.float64), truth).tp,
                 "realised_credit_per_dot": float(cred.sum() / dotted.sum())},
        "features": {},
    }

    for name, f in feats.items():
        q = np.quantile(f[dotted], np.linspace(0, 1, 6))
        bins = []
        for i in range(5):
            if i == 4:
                m = dotted & (f >= q[i]) & (f <= q[i + 1])
            else:
                m = dotted & (f >= q[i]) & (f < q[i + 1])
            n_i = int(m.sum())
            if n_i == 0:
                continue
            c = float(cred[m].sum() / n_i)
            bins.append({
                "bin": i + 1, "range": [float(q[i]), float(q[i + 1])], "dots": n_i,
                "realised_proxy_credit_per_dot": c,
                "fraction_earning": float(((cred > 0) & m).sum() / n_i),
                "eligible_for_removal_safety2": bool(c < REMOVE_IF_PROXY_BELOW),
            })
        # also test the cumulative removal of all bins below each cut
        cum = []
        for i in range(5):
            if i == 4:
                m = dotted & (f >= q[0]) & (f <= q[i + 1])
            else:
                m = dotted & (f >= q[0]) & (f < q[i + 1])
            n_i = int(m.sum())
            if n_i == 0:
                continue
            c = float(cred[m].sum() / n_i)
            cum.append({"up_to_bin": i + 1, "dots": n_i,
                        "realised_proxy_credit_per_dot": c,
                        "eligible_for_removal_safety2": bool(c < REMOVE_IF_PROXY_BELOW)})
        report["features"][name] = {"quintiles": bins, "cumulative_from_lowest": cum}

    (ROOT / "docs" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "data" / "h49-coherence-pruning.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ["removal_rule", "base"]}, indent=2))
    for name, d in report["features"].items():
        print("\n==", name)
        for b in d["quintiles"]:
            print(f"   q{b['bin']} range={b['range'][0]:.3f}-{b['range'][1]:.3f} dots={b['dots']:6d} "
                  f"credit/dot={b['realised_proxy_credit_per_dot']:.4f} earn={b['fraction_earning']:.3f} "
                  f"removable={b['eligible_for_removal_safety2']}")
        for b in d["cumulative_from_lowest"]:
            print(f"   cum<=q{b['up_to_bin']} dots={b['dots']:6d} credit/dot={b['realised_proxy_credit_per_dot']:.4f} removable={b['eligible_for_removal_safety2']}")


if __name__ == "__main__":
    main()
