"""The two detector families, and their belief surfaces.

Family definitions (each is a thing that has actually been submitted and scored
by the organizers; the score shown is the owner-reported live score, which this
repository re-uses only as an anchor, never as a receipt):

  * **dotted family** -- the spacing-tuned emission of the H19-5 / H27-4 habitat
    field, thinned with a geodesic dot operator at 2.8 px.  Its best live results
    are 0.2600 (44,090 px), 0.2708 (40,199 px, the same surface one catalogue-
    flank buffer step in) and 0.2778 (37,654 px, the buffer taken to B = 2 -- the
    highest live score the group has ever recorded).  `[OWNER-REPORT]`
  * **tip / step-over family** -- the tip / step-over analogue emission at
    R = 30, 41,865 px, owner-reported 0.2632.  `[OWNER-REPORT]`

Belief surface
--------------
Each family ships a raster of committed pixels, not a probability field.  The
family's belief surface is therefore defined *in the metric's own geometry*:

    b_family(x) = max over committed pixels y of k(d(x, y))

This is exactly the credit the family would earn if a truth pixel sat at x, so it
is the natural "degree of belief that a fault exists at x" for that source, on
[0, 1], and it is zero further than 300 m from any committed pixel.  It is
computed with the same 25 kernel offsets the official metric uses.

Nothing here re-fits a model: the two surfaces are the shipped artifacts' own
commitments, so a difference between them is a difference between the two
families, not between two random seeds.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from . import grid as G
from . import metric as M

FAMILY_FILES = {
    "dotted_02600": "data/families/dotted_d2_8_02600.tif",
    "dotted_02708": "data/families/dotted_d2_8_02708.tif",
    "tip_02632": "data/families/tip_stepover_r30_02632.tif",
    "dotted_b2_prune_02778": "data/families/dotted_b2_prune_02778.tif",
}

# Owner-reported live scores, for anchoring only.  Evidence class [OWNER-REPORT]:
# the owner read them off submission screens; no organizer receipt links these
# bytes to those rows (sibling irregularity IR-32-SCORE-01).
LIVE_SCORES = {
    "dotted_02600": 0.2600,
    "dotted_02708": 0.2708,
    "tip_02632": 0.2632,
    "dotted_b2_prune_02778": 0.2778,
}


def load_family_mask(name: str) -> np.ndarray:
    return G.read_mask(G.REPO / FAMILY_FILES[name])


def load_family_surface(name: str) -> np.ndarray:
    return G.read_surface(G.REPO / FAMILY_FILES[name])


def kernel_credit_surface(committed: np.ndarray) -> np.ndarray:
    """`b(x) = max over committed pixels y of k(d(x, y))` -- see module docstring."""
    return M.max_credit_field(committed.astype(np.float64))


def family_agreement(m1: np.ndarray, m2: np.ndarray) -> dict:
    a, b = np.asarray(m1, bool), np.asarray(m2, bool)
    inter = int((a & b).sum())
    uni = int((a | b).sum())
    return {
        "n_a": int(a.sum()),
        "n_b": int(b.sum()),
        "intersection": inter,
        "union": uni,
        "a_only": int((a & ~b).sum()),
        "b_only": int((~a & b).sum()),
        "jaccard": inter / uni if uni else float("nan"),
    }


def union_support(names: list[str]) -> np.ndarray:
    out = None
    for n in names:
        m = load_family_mask(n)
        out = m if out is None else (out | m)
    assert out is not None
    return out


def family_support_corridor(names: list[str], radius: int = 1) -> np.ndarray:
    """Union support dilated by `radius` px -- the corridor a fault may occupy."""
    from . import emit

    return emit.dilate_mask(union_support(names), radius)
