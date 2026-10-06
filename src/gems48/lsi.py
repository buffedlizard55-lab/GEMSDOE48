"""Live-Score Inversion (LSI) — a selection instrument calibrated on owner-reported live scores.

Idea (new in GEMSDOE48).  For a binary emission P and hidden truth G*:

    TP_w(P) = sum_{g in G*} k(d_P(g))                    (linear in the truth indicator)

Model the truth as an inhomogeneous Bernoulli field with intensity q_b that is constant
inside covariate bins b.  Then

    E[TP_w(P)] = sum_b q_b * A_{P,b},   A_{P,b} = sum_{x in b} k(d_P(x))
    E[K]       = sum_b q_b * N_b

FP_w = S - Phi with Phi = sum_{x in P} k(d_G(x)).  Phi is not linear in q; we use the
geometric ratio rho_P = TP_w/Phi measured for the same dot pattern against a line-network
stand-in (SGMC faults — used ONLY for geometry, its *location* skill is nil, see
evidence/proxy_calibration.json).  Then

    DTI_P(q) = T / (T + alpha*(S - T/rho_P) + beta*(K - T))

q >= 0 is fit by bounded least squares to the live scores; validity is measured by
leave-one-raster-out prediction of each live score.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi
from scipy.optimize import least_squares

from .metric import ALPHA, BETA, kernel, components

DCAT_EDGES = [0, 1.01, 2.01, 3.01, 5.01, 10.01, 25.01, 1e9]


def make_bins(G, backbone):
    """Integer bin id per evaluated pixel (-1 = not evaluated).

    bins = dcat band (7) x on/off the H19-5 backbone (within 1 px)."""
    ev = ~G["mask"]
    dbb = ndi.distance_transform_edt(~backbone)
    onbb = (dbb <= 1.0).astype(np.int16)
    band = np.digitize(G["dcat"], DCAT_EDGES[1:-1]).astype(np.int16)  # 0..6
    b = band * 2 + onbb
    b[~ev] = -1
    return b, 14


def bin_names():
    out = []
    labs = ["d<=1", "1<d<=2", "2<d<=3", "3<d<=5", "5<d<=10", "10<d<=25", "d>25"]
    for l in labs:
        out += [f"{l}|off-backbone", f"{l}|on-backbone"]
    return out


def features(p, G, bins, nb, geom_truth):
    """Sufficient statistics of one binary emission for the LSI model."""
    ev = ~G["mask"]
    dots = (p > 0) & ev
    S = float(dots.sum())
    kd = kernel(ndi.distance_transform_edt(~dots)) if dots.any() else np.zeros(p.shape)
    A = np.bincount(bins[ev], weights=kd[ev], minlength=nb)[:nb]
    c = components(dots.astype(float), geom_truth, G["mask"])
    rho = c["TP"] / max(c["S"] - c["FP"], 1e-9)  # TP / Phi
    return dict(S=S, A=A, rho=rho)


def predict(q, f, N):
    T = float(q @ f["A"]); K = float(q @ N)
    Phi = T / f["rho"]
    den = T + ALPHA * (f["S"] - Phi) + BETA * (K - T)
    return T / den if den > 0 else 0.0


def fit(fs, live, N, ridge=1e-3, q0=None):
    nb = len(N)
    q0 = np.full(nb, 2e-3) if q0 is None else q0
    scale = 1e-2

    def res(z):
        q = z * scale
        r = [predict(q, f, N) - y for f, y in zip(fs, live)]
        # weak ridge toward the pooled mean intensity (keeps empty-information bins sane)
        r += list(ridge * (z - z.mean()))
        return np.array(r)

    sol = least_squares(res, q0 / scale, bounds=(0, np.inf), method="trf")
    return sol.x * scale


def loo(fs, live, N, ridge=1e-3):
    preds = []
    for i in range(len(fs)):
        idx = [j for j in range(len(fs)) if j != i]
        q = fit([fs[j] for j in idx], [live[j] for j in idx], N, ridge)
        preds.append(predict(q, fs[i], N))
    return np.array(preds)
