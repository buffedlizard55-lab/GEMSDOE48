"""GEMSDOE48 — Dempster-Shafer disagreement-preserving fusion of two independently
built fault-detector families for the DOE GEMS Prize (DrivenData competition 306).

The package is deliberately dependency-light (numpy + rasterio) and every module is
written to be auditable line by line.
"""

__version__ = "1.0.0"

__all__ = [
    "metric",
    "grid",
    "ds",
    "emit",
    "holdout",
    "families",
]
