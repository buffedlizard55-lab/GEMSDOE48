"""Selection primitive for the H56-F dotted-parent pruning experiment."""
from __future__ import annotations

import numpy as np


def prune_dotted(
    dotted: np.ndarray,
    normalized_belief: np.ndarray,
    threshold: float,
) -> np.ndarray:
    """Keep only parent dotted pixels whose frozen normalized Bel(F) clears threshold.

    The helper is intentionally deletion-only: it cannot emit a cell outside the
    supplied binary dotted mask. It validates both arrays and the threshold before
    selection so malformed, non-binary, or NaN-contaminated inputs fail closed.
    """
    raw_parent = np.asarray(dotted)
    raw_belief = np.asarray(normalized_belief)
    try:
        belief = np.asarray(raw_belief, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        raise ValueError("normalized belief must be numeric") from exc
    try:
        cutoff = float(threshold)
    except (TypeError, ValueError) as exc:
        raise ValueError("threshold must be numeric and lie in [0, 1]") from exc

    if raw_parent.ndim < 1 or belief.ndim < 1:
        raise ValueError("dotted and belief inputs must be raster arrays")
    if raw_parent.shape != belief.shape:
        raise ValueError("dotted and belief rasters must have identical shapes")
    if not np.isfinite(cutoff) or not 0.0 <= cutoff <= 1.0:
        raise ValueError("threshold must lie in [0, 1]")
    if raw_parent.dtype != np.bool_:
        if not np.issubdtype(raw_parent.dtype, np.number):
            raise ValueError("dotted parent must be boolean or numeric binary 0/1")
        if not np.isfinite(raw_parent).all() or not np.isin(raw_parent, (0, 1)).all():
            raise ValueError("dotted parent must contain only finite binary 0/1 values")
    if not np.isfinite(belief).all() or np.any((belief < 0) | (belief > 1)):
        raise ValueError("normalized belief must be finite and within [0, 1]")

    parent = raw_parent.astype(bool, copy=False)
    # Float32 rasters cannot represent common decimal thresholds exactly (for example,
    # float32(0.95) is slightly below Python's float 0.95). Treat one input-dtype ULP
    # as the inclusive boundary, without making materially lower values pass.
    tolerance = (
        float(np.finfo(raw_belief.dtype).eps) * max(1.0, abs(cutoff))
        if np.issubdtype(raw_belief.dtype, np.floating)
        else 0.0
    )
    return parent & (belief >= cutoff - tolerance)
