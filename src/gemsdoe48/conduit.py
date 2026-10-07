"""Hydrothermal-conduit anchors from the INGENIOUS/GDR well-and-spring compilation.

Source (free, official, verified)
---------------------------------
* Geothermal Data Repository submission 1391, "INGENIOUS Great Basin regional
  dataset compilation": https://gdr.openei.org/submissions/1391
* DOI 10.15121/1881483 ; Data.gov metadata reports CC BY 4.0
  (https://catalog.data.gov/dataset/ingenious-great-basin-regional-dataset-compilation)
* Local hash-pinned mirror: ``data/raw/external/gdr_wellspring_in_footprint.csv``
  SHA-256 ``122718e65bdf55aab0ee12ad20d80062f0deb1de957225a61ad880dd5dc196ea``
  (pinned in ``registry/data_manifest_gemsdoe32.json``).

Physical basis
--------------
A hydrothermal spring or a thermal well discharging at 75-296 degC requires three
things at once: a heat source, deep meteoric circulation, and a *permeable upflow
pathway*.  In the extensional northwestern Great Basin that pathway is a fault or
fracture zone; the region's producing fields (Beowawe, Brady's Hot Springs, Desert
Peak, Stillwater, McGinness Hills) are all fault-controlled.  Silica and calcite
geothermometers go one step further: they estimate the *reservoir* temperature
reached at depth, so a cool-discharge well with a 200 degC quartz geothermometer
still evidences deep fracture-controlled circulation.

Why this should catch faults the catalogue misses
-------------------------------------------------
Upflow through a mapped, eroded range-front scarp is not what produces a thermal
spring in a basin: those springs appear where a *buried* fault brings hot fluid
through alluvium.  Measured here: of 12,570 distinct grid cells holding a well or
spring, only 219 (1.7 %) lie inside the h19-5 corridor backbone and 11,651 (92.7 %)
are more than 200 m from the public catalogue.  The layer is therefore almost
completely spatially disjoint from every surface this repository has shipped.

Explicitly NOT used
-------------------
The mirror's ``dist_known_fault_px`` column is derived from the competition labels
and would be leakage.  ``thermal_class`` / ``temp_c`` / the three geothermometer
columns are physical measurements and are used; ``dist_known_fault_px`` is dropped
on read.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

LEAKY_COLUMNS = ("dist_known_fault_px",)

HOT = "Hot"
WARM = "Warm"
COLD = "Cold"

#: geothermometer columns estimate reservoir temperature (degC)
GEOTHERMOMETERS = ("geothermquartz_c", "geothermchalc_c", "geothermcat_c")


@dataclass(frozen=True)
class ConduitSite:
    """One well/spring record reduced to the competition grid."""

    row: int
    col: int
    layer: str
    name: str
    thermal_class: str
    temp_c: float | None
    geotherm_max_c: float | None
    tier: int
    score: float


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return None
    try:
        out = float(text)
    except ValueError:
        return None
    return out if math.isfinite(out) else None


def thermal_tier(thermal_class: str, temp_c: float | None, geotherm_max_c: float | None) -> int:
    """Pre-registered conduit tier (frozen before any scoring).

    3  discharge class ``Hot`` (median 75 degC, max 296.5 degC in this mirror), or
       any silica/calcite geothermometer >= 150 degC  -> deep hydrothermal conduit
    2  measured discharge >= 50 degC, or any geothermometer >= 100 degC
    1  measured discharge >= 35 degC (above the mirror's Warm maximum of 38.9 degC)
    0  everything else, including ``Warm`` (<= 38.9 degC, effectively ambient) and
       ``Cold`` (<= 20 degC) -- deliberately excluded as non-indicators
    """
    klass = (thermal_class or "").strip()
    if klass == HOT:
        return 3
    if geotherm_max_c is not None and geotherm_max_c >= 150.0:
        return 3
    if temp_c is not None and temp_c >= 50.0:
        return 2
    if geotherm_max_c is not None and geotherm_max_c >= 100.0:
        return 2
    if temp_c is not None and temp_c >= 35.0:
        return 1
    return 0


def conduit_score(site_tier: int, temp_c: float | None, geotherm_max_c: float | None) -> float:
    """Continuous rank inside a tier: tier, then reservoir temperature, then discharge."""
    reservoir = geotherm_max_c if geotherm_max_c is not None else -1.0
    discharge = temp_c if temp_c is not None else -1.0
    return float(site_tier) + 0.5 * math.tanh(reservoir / 200.0) + 0.25 * math.tanh(discharge / 200.0)


def read_sites(csv_path: str | Path) -> list[ConduitSite]:
    """Parse the GDR well/spring mirror into tiered :class:`ConduitSite` records."""
    path = Path(csv_path)
    out: list[ConduitSite] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for record in csv.DictReader(handle):
            leaked = [c for c in LEAKY_COLUMNS if record.get(c)]
            if leaked:  # never carry the label-derived column forward
                for column in leaked:
                    record[column] = None
            try:
                row = int(float(record["row"]))
                col = int(float(record["col"]))
            except (KeyError, TypeError, ValueError):
                continue
            klass = (record.get("thermalclass") or "").strip()
            temp = _to_float(record.get("temp_c"))
            geo = [g for g in (_to_float(record.get(c)) for c in GEOTHERMOMETERS) if g is not None]
            geo_max = max(geo) if geo else None
            tier = thermal_tier(klass, temp, geo_max)
            out.append(ConduitSite(
                row=row, col=col,
                layer=(record.get("layer") or "").strip(),
                name=(record.get("name") or "").strip(),
                thermal_class=klass, temp_c=temp, geotherm_max_c=geo_max,
                tier=tier, score=conduit_score(tier, temp, geo_max),
            ))
    return out


def site_arrays(sites: list[ConduitSite], shape: tuple[int, int], min_tier: int = 1
                ) -> tuple[np.ndarray, np.ndarray]:
    """Rasterise sites to ``(best_tier, best_score)`` grids, collapsing duplicates.

    Several GDR layers report the same physical site (features / temperature /
    chemistry).  Collapsing by maximum tier and maximum score avoids letting a
    multiply-reported site out-rank a genuinely stronger neighbour.
    """
    height, width = shape
    tier = np.zeros((height, width), dtype=np.int8)
    score = np.zeros((height, width), dtype=np.float64)
    for site in sites:
        if site.tier < min_tier:
            continue
        if not (0 <= site.row < height and 0 <= site.col < width):
            continue
        if site.tier > tier[site.row, site.col]:
            tier[site.row, site.col] = site.tier
        if site.score > score[site.row, site.col]:
            score[site.row, site.col] = site.score
    return tier, score


def summarize(sites: list[ConduitSite]) -> dict:
    """Audit summary used in the build receipt."""
    from collections import Counter

    tiers = Counter(s.tier for s in sites)
    layers = Counter(s.layer for s in sites)
    classes = Counter(s.thermal_class or "NONE" for s in sites)
    temps = [s.temp_c for s in sites if s.temp_c is not None]
    geos = [s.geotherm_max_c for s in sites if s.geotherm_max_c is not None]
    return {
        "records": len(sites),
        "by_tier": {str(k): int(v) for k, v in sorted(tiers.items())},
        "by_layer": {k: int(v) for k, v in sorted(layers.items())},
        "by_thermal_class": {k: int(v) for k, v in sorted(classes.items())},
        "temp_c": ({"n": len(temps), "min": min(temps), "p50": float(np.percentile(temps, 50)),
                    "p90": float(np.percentile(temps, 90)), "max": max(temps)} if temps else None),
        "geotherm_max_c": ({"n": len(geos), "p50": float(np.percentile(geos, 50)),
                            "p90": float(np.percentile(geos, 90)), "max": max(geos),
                            "n_ge_150": int(sum(1 for g in geos if g >= 150.0))} if geos else None),
        "leaky_columns_dropped": list(LEAKY_COLUMNS),
    }
