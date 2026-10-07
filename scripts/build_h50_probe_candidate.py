#!/usr/bin/env python3
"""Build the preregistered H50-1 2 m probe persistence candidate.

This script reads only the GDR 1391 shallow-temperature archive plus the local
competition-footprint mask. It does not read labels, catalogue distances, SGMC,
or any parent prediction surface. The frozen rule is in
``docs/research/hypotheses-20261007.md``.

The 1.08 MB input archive and its provenance note are stored under
``data/external/``. The local bytes are from a pinned owner mirror, not a direct
GDR download; verify the source/license note before redistribution. The default
path matches this archive, or pass ``--probes-zip`` to use another copy.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import struct
import sys
import tempfile
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import rowcol
from rasterio.warp import transform as transform_xy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gemsdoe48.geotiff import (  # noqa: E402
    assert_competition_grid,
    display_path,
    write_float32,
)

DEFAULT_PROBES = ROOT / "data/external/2m_temperature_probe_INGENIOUS_regional_data.zip"
DEFAULT_FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
DEFAULT_OUTPUT_DIR = ROOT / "docs/downloads"
DEFAULT_RECEIPT = ROOT / "evidence/build_h50_probe_candidate_20261007.json"
DEFAULT_STATION_CSV = ROOT / "evidence/h50_selected_station_audit_20261007.csv"
EXPECTED_MIRROR_SHA256 = "1301f70d230058e616ea5d34d1c7a32fabf7d49198172f376c59c89bd652eca3"
PINNED_MIRROR = (
    "https://github.com/buffedlizard55-lab/GEMSDOE24/blob/"
    "07345ea0604953d7efb858d9cfbc21e20c7aca0b/"
    "data/external/2m_temperature_probe_INGENIOUS_regional_data.zip"
)
BUFFER_M = 300.0
MIN_DATE_GROUP_STATIONS = 5
PERSISTENCE_C = 2.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _numeric(value: str | float | int | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (float, int)):
        number = float(value)
        return number if math.isfinite(number) else None
    text = str(value).strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _read_dbf(data: bytes) -> tuple[list[dict[str, Any]], list[str]]:
    """Read the small dBase table with the Python standard library only."""
    if len(data) < 33:
        raise ValueError("DBF is truncated")
    record_count = int.from_bytes(data[4:8], "little")
    header_length = int.from_bytes(data[8:10], "little")
    record_length = int.from_bytes(data[10:12], "little")
    if header_length < 33 or record_length < 2:
        raise ValueError("DBF header has invalid record/header lengths")
    fields: list[tuple[str, int, int, str]] = []
    position = 1  # first byte is the dBase deleted-record marker
    offset = 32
    while offset < header_length and data[offset] != 0x0D:
        descriptor = data[offset : offset + 32]
        if len(descriptor) != 32:
            raise ValueError("DBF field descriptor is truncated")
        field_name = descriptor[:11].split(b"\0", 1)[0].decode("ascii", "strict").strip()
        field_type = chr(descriptor[11])
        field_length = descriptor[16]
        if not field_name or field_length <= 0:
            raise ValueError("DBF contains an invalid field descriptor")
        fields.append((field_name, position, field_length, field_type))
        position += field_length
        offset += 32
    if offset >= header_length or data[offset] != 0x0D:
        raise ValueError("DBF field-descriptor terminator was not found")
    if position != record_length:
        raise ValueError(f"DBF field lengths sum to {position}, record length is {record_length}")
    if len(data) < header_length + record_count * record_length:
        raise ValueError("DBF record table is truncated")

    rows: list[dict[str, Any]] = []
    deleted: list[int] = []
    for index in range(record_count):
        record = data[header_length + index * record_length : header_length + (index + 1) * record_length]
        if record[:1] == b"*":
            deleted.append(index)
            rows.append({"__deleted__": True})
            continue
        row: dict[str, Any] = {}
        for name, field_offset, field_length, field_type in fields:
            raw = record[field_offset : field_offset + field_length]
            text = raw.decode("latin1", "replace").strip()
            if field_type in ("N", "F") and text:
                try:
                    row[name] = float(text)
                except ValueError:
                    row[name] = text
            else:
                row[name] = text
        rows.append(row)
    if deleted:
        raise ValueError(f"DBF has deleted records at indices {deleted[:10]}; refusing to risk SHP/DBF misalignment")
    return rows, [field[0] for field in fields]


def _read_shp_points(data: bytes) -> list[tuple[float, float]]:
    """Read a point shapefile's coordinates, checking each record boundary."""
    if len(data) < 100 or int.from_bytes(data[:4], "big") != 9994:
        raise ValueError("SHP header is missing or invalid")
    file_length_bytes = int.from_bytes(data[24:28], "big") * 2
    if file_length_bytes != len(data):
        raise ValueError(f"SHP declared length {file_length_bytes} differs from payload {len(data)}")
    file_shape_type = int.from_bytes(data[32:36], "little")
    if file_shape_type != 1:
        raise ValueError(f"Expected ESRI point shape type 1, got {file_shape_type}")
    points: list[tuple[float, float]] = []
    offset = 100
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError("SHP record header is truncated")
        content_bytes = int.from_bytes(data[offset + 4 : offset + 8], "big") * 2
        start, end = offset + 8, offset + 8 + content_bytes
        if end > len(data) or content_bytes < 4:
            raise ValueError("SHP record content is truncated or too short")
        shape_type = int.from_bytes(data[start : start + 4], "little")
        if shape_type != 1 or content_bytes < 20:
            raise ValueError(f"Expected a point in every SHP record; got type={shape_type}, bytes={content_bytes}")
        x, y = struct.unpack("<2d", data[start + 4 : start + 20])
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError("SHP contains a non-finite point coordinate")
        points.append((x, y))
        offset = end
    return points


def read_probe_archive(path: Path) -> tuple[list[dict[str, Any]], list[tuple[float, float]], str, list[str]]:
    with zipfile.ZipFile(path) as archive:
        members = archive.namelist()
        dbf_members = [name for name in members if name.lower().endswith(".dbf")]
        shp_members = [name for name in members if name.lower().endswith(".shp")]
        prj_members = [name for name in members if name.lower().endswith(".prj")]
        if len(dbf_members) != 1 or len(shp_members) != 1 or len(prj_members) != 1:
            raise ValueError(
                f"Expected one DBF/SHP/PRJ in archive, got {len(dbf_members)}/{len(shp_members)}/{len(prj_members)}"
            )
        rows, field_names = _read_dbf(archive.read(dbf_members[0]))
        points = _read_shp_points(archive.read(shp_members[0]))
        prj = archive.read(prj_members[0]).decode("ascii", "replace")
    if len(rows) != len(points):
        raise ValueError(f"DBF has {len(rows)} rows but SHP has {len(points)} points")
    source_crs = CRS.from_wkt(prj)
    if source_crs.to_epsg() != 4269:
        raise ValueError(f"Expected NAD83 / EPSG:4269 point CRS, got {source_crs}")
    required = {"Area", "F2mDAB", "T2m", "Date"}
    required |= {f"T2m_{index}" for index in range(2, 8)}
    required |= {f"Date_{index}" for index in range(2, 8)}
    missing = sorted(required.difference(field_names))
    if missing:
        raise ValueError(f"Probe DBF is missing expected fields: {missing}")
    return rows, points, prj, field_names


def collect_probe_stations(
    rows: list[dict[str, Any]],
    geographic_points: list[tuple[float, float]],
    utm_points: list[tuple[float, float]],
) -> tuple[
    dict[tuple[float, float], dict[str, Any]],
    dict[tuple[str, str], dict[tuple[float, float], list[float]]],
    dict[tuple[float, float], dict[str, list[float]]],
    dict[str, int],
]:
    """Aggregate measurements by exact source point geometry, not DBF row/label.

    The source's display station label is reused at different coordinates. Exact
    NAD83 point coordinates therefore define a physical location for this fixed
    data archive; duplicate location/date readings are median-aggregated before
    both the group size and the leave-one-location-out reference are computed.
    """
    station_records: dict[tuple[float, float], dict[str, Any]] = {}
    area_date_station_values: dict[
        tuple[str, str], dict[tuple[float, float], list[float]]
    ] = defaultdict(lambda: defaultdict(list))
    station_date_values: dict[tuple[float, float], dict[str, list[float]]] = defaultdict(
        lambda: defaultdict(list)
    )
    stats = {
        "records_total": len(rows),
        "dated_nonzero_observations": 0,
        "dated_zero_observations": 0,
        "blank_date_nonzero_fields": 0,
        "blank_date_zero_fields": 0,
        "invalid_nonblank_date_fields": 0,
        "missing_area_dated_observations": 0,
        "unique_exact_coordinate_locations": 0,
        "exact_coordinate_groups_with_multiple_records": 0,
        "records_beyond_first_at_exact_coordinates": 0,
        "raw_records_with_two_or_more_valid_dated_observations": 0,
        "raw_records_with_two_or_more_distinct_valid_dates": 0,
    }
    for index, (row, point, utm_point) in enumerate(zip(rows, geographic_points, utm_points)):
        longitude, latitude = float(point[0]), float(point[1])
        key = (longitude, latitude)
        area = str(row.get("Area") or "").strip()
        record = station_records.setdefault(
            key,
            {
                "location_key": key,
                "longitude_nad83": longitude,
                "latitude_nad83": latitude,
                "point_x_utm11_m": float(utm_point[0]),
                "point_y_utm11_m": float(utm_point[1]),
                "areas": set(),
                "station_labels": set(),
                "source_record_indices": [],
                "dab_values": [],
            },
        )
        record["source_record_indices"].append(index)
        if area:
            record["areas"].add(area)
        label = str(row.get("Station") or row.get("Org_Stn") or "").strip()
        if label:
            record["station_labels"].add(label)
        dab = _numeric(row.get("F2mDAB"))
        if dab is not None:
            record["dab_values"].append(dab)

        row_observation_count = 0
        row_dates: set[str] = set()
        for measurement_index in range(1, 8):
            temperature_field = "T2m" if measurement_index == 1 else f"T2m_{measurement_index}"
            date_field = "Date" if measurement_index == 1 else f"Date_{measurement_index}"
            temperature = _numeric(row.get(temperature_field))
            date = str(row.get(date_field) or "").strip()
            if not date or date.lower() == "nan":
                if temperature is not None and temperature != 0.0:
                    stats["blank_date_nonzero_fields"] += 1
                elif temperature == 0.0:
                    stats["blank_date_zero_fields"] += 1
                continue
            if not re.fullmatch(r"\d{8}", date):
                stats["invalid_nonblank_date_fields"] += 1
                continue
            try:
                datetime.strptime(date, "%Y%m%d")
            except ValueError:
                stats["invalid_nonblank_date_fields"] += 1
                continue
            if temperature is None:
                continue
            if temperature == 0.0:
                stats["dated_zero_observations"] += 1
                continue
            stats["dated_nonzero_observations"] += 1
            row_observation_count += 1
            row_dates.add(date)
            if not area:
                stats["missing_area_dated_observations"] += 1
                continue
            area_date_station_values[(area, date)][key].append(temperature)
            station_date_values[key][date].append(temperature)
        if row_observation_count >= 2:
            stats["raw_records_with_two_or_more_valid_dated_observations"] += 1
        if len(row_dates) >= 2:
            stats["raw_records_with_two_or_more_distinct_valid_dates"] += 1

    if stats["dated_zero_observations"]:
        raise ValueError(
            f"Found {stats['dated_zero_observations']} dated zero temperature fields; preregistration requires review, not silent exclusion"
        )
    if stats["invalid_nonblank_date_fields"]:
        raise ValueError(f"Found {stats['invalid_nonblank_date_fields']} invalid nonblank date fields")
    stats["unique_exact_coordinate_locations"] = len(station_records)
    stats["exact_coordinate_groups_with_multiple_records"] = sum(
        len(record["source_record_indices"]) > 1 for record in station_records.values()
    )
    stats["records_beyond_first_at_exact_coordinates"] = sum(
        len(record["source_record_indices"]) - 1 for record in station_records.values()
    )
    return station_records, area_date_station_values, station_date_values, stats


def station_residuals(
    area_date_station_values: dict[
        tuple[str, str], dict[tuple[float, float], list[float]]
    ],
) -> tuple[
    dict[tuple[float, float], list[dict[str, float | str | int]]],
    dict[str, int],
]:
    residuals: dict[tuple[float, float], list[dict[str, float | str | int]]] = defaultdict(list)
    eligible_groups = 0
    locations_in_eligible_groups = 0
    duplicate_location_date_groups = 0
    duplicate_readings_collapsed = 0
    for (area, date), location_values in sorted(area_date_station_values.items()):
        location_medians = {location: statistics.median(values) for location, values in location_values.items()}
        duplicate_location_date_groups += sum(len(values) > 1 for values in location_values.values())
        duplicate_readings_collapsed += sum(max(0, len(values) - 1) for values in location_values.values())
        if len(location_medians) < MIN_DATE_GROUP_STATIONS:
            continue
        eligible_groups += 1
        locations_in_eligible_groups += len(location_medians)
        for location, own_value in location_medians.items():
            other_values = [value for other_location, value in location_medians.items() if other_location != location]
            if len(other_values) < MIN_DATE_GROUP_STATIONS - 1:
                raise AssertionError("eligible group did not leave the minimum number of other locations")
            residual = float(own_value - statistics.median(other_values))
            residuals[location].append(
                {"date": date, "residual_c": residual, "group_stations": len(location_medians)}
            )
    return residuals, {
        "eligible_area_date_groups": eligible_groups,
        "station_dates_in_eligible_groups": locations_in_eligible_groups,
        "duplicate_station_date_groups_collapsed": duplicate_location_date_groups,
        "duplicate_location_date_readings_collapsed": duplicate_readings_collapsed,
        "station_locations_with_any_eligible_residual_date": len(residuals),
    }


def select_station_records(
    station_records: dict[tuple[float, float], dict[str, Any]],
    station_date_values: dict[tuple[float, float], dict[str, list[float]]],
    residuals: dict[tuple[float, float], list[dict[str, float | str | int]]],
    inside_location_keys: set[tuple[float, float]],
    *,
    raw_records_total: int,
    raw_records_inside_finite_footprint: int,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    selected: list[dict[str, Any]] = []
    summary = {
        "records_total": raw_records_total,
        "records_inside_finite_footprint": raw_records_inside_finite_footprint,
        "station_locations_total": len(station_records),
        "station_locations_inside_finite_footprint": len(inside_location_keys),
        "station_locations_with_two_or_more_valid_dated_observations": 0,
        "station_locations_with_two_or_more_distinct_valid_dates": 0,
        "inside_locations_with_two_or_more_eligible_residual_dates": 0,
        "inside_persistent_repeat_locations": 0,
        "inside_positive_dab_locations": 0,
        "inside_fallback_positive_dab_locations": 0,
        "inside_excluded_repeat_locations_failing_persistence": 0,
        "inside_selected_locations": 0,
    }
    for location, record in sorted(station_records.items()):
        dates = station_date_values.get(location, {})
        valid_observation_count = sum(len(values) for values in dates.values())
        distinct_dates = len(dates)
        if valid_observation_count >= 2:
            summary["station_locations_with_two_or_more_valid_dated_observations"] += 1
        if distinct_dates >= 2:
            summary["station_locations_with_two_or_more_distinct_valid_dates"] += 1
        if location not in inside_location_keys:
            continue
        dab_values = record["dab_values"]
        dab = float(statistics.median(dab_values)) if dab_values else None
        station_residual_rows = sorted(residuals.get(location, []), key=lambda item: str(item["date"]))
        eligible_dates = len({str(item["date"]) for item in station_residual_rows})
        reason = ""
        median_residual: float | None = None
        positive_fraction: float | None = None
        if eligible_dates >= 2:
            summary["inside_locations_with_two_or_more_eligible_residual_dates"] += 1
            values = [float(item["residual_c"]) for item in station_residual_rows]
            median_residual = float(statistics.median(values))
            positive_fraction = float(sum(value >= PERSISTENCE_C for value in values) / len(values))
            if median_residual >= PERSISTENCE_C and positive_fraction >= 0.5:
                reason = "persistent_repeat_residual"
                summary["inside_persistent_repeat_locations"] += 1
            else:
                summary["inside_excluded_repeat_locations_failing_persistence"] += 1
        elif dab is not None and dab > 0.0:
            reason = "positive_2mDAB_insufficient_repeat_dates"
            summary["inside_fallback_positive_dab_locations"] += 1
        if dab is not None and dab > 0.0:
            summary["inside_positive_dab_locations"] += 1
        if not reason:
            continue
        summary["inside_selected_locations"] += 1
        lon, lat = location
        labels = sorted(record["station_labels"])
        selected.append(
            {
                "record_index": record["source_record_indices"][0],
                "source_record_indices": ";".join(map(str, record["source_record_indices"])),
                "source_record_count": len(record["source_record_indices"]),
                "station_key": f"EPSG:4269:{lon:.12f},{lat:.12f}",
                "station": ";".join(labels) if labels else f"location-{lon:.8f}-{lat:.8f}",
                "area": ";".join(sorted(record["areas"])),
                "dab_c": dab,
                "selection_reason": reason,
                "valid_dates": ";".join(sorted(dates)),
                "eligible_residual_dates": eligible_dates,
                "median_residual_c": median_residual,
                "fraction_residual_ge_2c": positive_fraction,
                "residuals_by_date": ";".join(
                    f"{item['date']}:{float(item['residual_c']):.3f}" for item in station_residual_rows
                ),
                "longitude_nad83": float(record["longitude_nad83"]),
                "latitude_nad83": float(record["latitude_nad83"]),
                "point_x_utm11_m": float(record["point_x_utm11_m"]),
                "point_y_utm11_m": float(record["point_y_utm11_m"]),
            }
        )
    summary["selected_positive_dab_locations"] = sum(
        item["dab_c"] is not None and item["dab_c"] > 0.0 for item in selected
    )
    return selected, summary


def rasterize_buffer_points(
    selected: list[dict[str, Any]],
    footprint: np.ndarray,
    profile: dict[str, Any],
    radius_m: float = BUFFER_M,
) -> np.ndarray:
    """Rasterize Euclidean point buffers by exact cell-centre distance."""
    if footprint.ndim != 2 or footprint.shape != (int(profile["height"]), int(profile["width"])):
        raise ValueError("footprint/profile dimensions differ")
    result = np.zeros(footprint.shape, dtype=bool)
    affine = profile["transform"]
    pixel_x, pixel_y = abs(float(affine.a)), abs(float(affine.e))
    if not math.isclose(pixel_x, 100.0) or not math.isclose(pixel_y, 100.0):
        raise ValueError("the frozen 300 m rasterizer expects a 100 m grid")
    pad_rows = int(math.ceil(radius_m / pixel_y)) + 1
    pad_cols = int(math.ceil(radius_m / pixel_x)) + 1
    for item in selected:
        x = float(item["point_x_utm11_m"])
        y = float(item["point_y_utm11_m"])
        center_row, center_col = rowcol(affine, x, y)
        row0, row1 = max(0, center_row - pad_rows), min(footprint.shape[0], center_row + pad_rows + 1)
        col0, col1 = max(0, center_col - pad_cols), min(footprint.shape[1], center_col + pad_cols + 1)
        for row in range(row0, row1):
            for col in range(col0, col1):
                if not footprint[row, col]:
                    continue
                center_x, center_y = affine @ (col + 0.5, row + 0.5)
                if math.hypot(center_x - x, center_y - y) <= radius_m + 1e-9:
                    result[row, col] = True
    return result


def write_station_csv(path: Path, selected: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "record_index",
        "source_record_indices",
        "source_record_count",
        "station_key",
        "station",
        "area",
        "dab_c",
        "selection_reason",
        "valid_dates",
        "eligible_residual_dates",
        "median_residual_c",
        "fraction_residual_ge_2c",
        "residuals_by_date",
        "longitude_nad83",
        "latitude_nad83",
        "point_x_utm11_m",
        "point_y_utm11_m",
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(selected)


def build(args: argparse.Namespace) -> dict[str, Any]:
    probes_zip = args.probes_zip.resolve()
    footprint_path = args.footprint.resolve()
    if not probes_zip.is_file():
        raise FileNotFoundError(
            f"Probe ZIP not found: {probes_zip}\nDownload GDR 1391 2m Temperature Probes.zip or pass --probes-zip."
        )
    if not footprint_path.is_file():
        raise FileNotFoundError(f"Footprint mask not found: {footprint_path}")
    source_sha = sha256_file(probes_zip)
    if args.require_pinned_mirror_sha and source_sha != EXPECTED_MIRROR_SHA256:
        raise ValueError(f"Probe ZIP SHA-256 {source_sha} != pinned mirror hash {EXPECTED_MIRROR_SHA256}")

    rows, geographic_points, source_prj, field_names = read_probe_archive(probes_zip)
    lons, lats = zip(*geographic_points)
    with rasterio.open(footprint_path) as mask_ds:
        assert_competition_grid(mask_ds.profile, path=footprint_path)
        if mask_ds.dtypes != ("uint8",) or mask_ds.nodata is not None:
            raise ValueError("Footprint must be the project's uint8/no-nodata binary mask")
        footprint_values = mask_ds.read(1)
        if not np.isin(footprint_values, (0, 1)).all():
            raise ValueError("Footprint mask contains values other than 0 and 1")
        footprint = footprint_values == 1
        profile = mask_ds.profile.copy()
        grid_transform = mask_ds.transform
        grid_crs = mask_ds.crs

    # `transform_xy` returns parallel x/y arrays; form the point tuples explicitly.
    utm_xs, utm_ys = transform_xy("EPSG:4269", grid_crs, list(lons), list(lats))
    point_rows_cols = [mask_ds_index(grid_transform, x, y) for x, y in zip(utm_xs, utm_ys)]
    if len(point_rows_cols) != len(rows):
        raise AssertionError("coordinate transformation returned an unexpected number of points")
    raw_inside = np.asarray(
        [
            0 <= row < footprint.shape[0]
            and 0 <= col < footprint.shape[1]
            and bool(footprint[row, col])
            for row, col in point_rows_cols
        ],
        dtype=bool,
    )
    station_records, area_date_values, station_date_values, observation_stats = collect_probe_stations(
        rows,
        geographic_points,
        list(zip(utm_xs, utm_ys)),
    )
    inside_location_keys: set[tuple[float, float]] = set()
    for location, record in station_records.items():
        row, col = mask_ds_index(
            grid_transform,
            float(record["point_x_utm11_m"]),
            float(record["point_y_utm11_m"]),
        )
        if 0 <= row < footprint.shape[0] and 0 <= col < footprint.shape[1] and footprint[row, col]:
            inside_location_keys.add(location)

    residuals, residual_stats = station_residuals(area_date_values)
    selected, selection_stats = select_station_records(
        station_records,
        station_date_values,
        residuals,
        inside_location_keys,
        raw_records_total=len(rows),
        raw_records_inside_finite_footprint=int(raw_inside.sum()),
    )
    support = rasterize_buffer_points(selected, footprint, profile)
    values = np.full(footprint.shape, np.nan, dtype=np.float32)
    values[footprint] = 0.0
    values[support] = 1.0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".h50-build-", dir=args.output_dir) as temporary_dir:
        temporary_path = Path(temporary_dir) / "candidate.tif"
        write_float32(
            temporary_path,
            values,
            profile,
            valid_mask=footprint,
            description="H50-1 repeat-survey 2 m thermal residual persistence; binary 300 m support",
            tags={
                "hypothesis_id": "H50-1",
                "build_rule_version": "v2-exact-location-key",
                "model": "GDR 1391 2m probe residual persistence; source-identity correction 2026-10-07",
                "station_identity": "Exact EPSG:4269 point coordinates; median same-location same-Area/date readings",
                "buffer_radius_m": str(BUFFER_M),
                "source_archive_sha256": source_sha,
                "source_data_license": "GDR page-reported CC BY 4.0; verify asset attribution before redistribution",
                "outside_footprint": "NaN/nodata",
            },
        )
        candidate_sha = sha256_file(temporary_path)
        stem = f"GEMSDOE48-H50-2M-PERSIST-20261007-{candidate_sha[:12]}-nan"
        output_path = args.output_dir / f"{stem}.tif"
        if output_path.exists():
            if sha256_file(output_path) != candidate_sha:
                raise FileExistsError(f"Refusing to overwrite non-identical file: {output_path}")
        else:
            temporary_path.replace(output_path)

    write_station_csv(args.station_audit, selected)
    with rasterio.open(output_path) as output_ds:
        reread = output_ds.read(1)
        audit_profile = output_ds.profile.copy()
        if output_ds.count != 1 or output_ds.dtypes != ("float32",):
            raise ValueError("Re-opened candidate is not a single-band float32 GeoTIFF")
        if output_ds.nodata is None or not np.isnan(output_ds.nodata):
            raise ValueError("Re-opened candidate is missing NaN/nodata outside")
        assert_competition_grid(audit_profile, path=output_path)
        if not np.array_equal(np.isfinite(reread), footprint):
            raise ValueError("Re-opened candidate finite mask differs from the footprint")
        if np.any((reread[footprint] < 0.0) | (reread[footprint] > 1.0)):
            raise ValueError("Re-opened candidate contains in-footprint values outside [0,1]")
        if not np.array_equal(reread[support], np.ones(int(support.sum()), dtype=np.float32)):
            raise ValueError("Re-opened candidate support differs from the constructed raster")

    positive_cells = int(support.sum())
    positive_dab_locations = int(selection_stats["selected_positive_dab_locations"])
    report = {
        "schema_version": 1,
        "status": "BUILT_LOCAL_FORMAT_CHECKED_RESEARCH_ARTIFACT_NOT_SLOT_CLEARED",
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis_id": "H50-1",
        "submission_name": stem.upper(),
        "short_upload_note": "GDR 2m probe repeat-persistence; 300 m buffers; research proxy only, no slot clearance.",
        "candidate": {
            "path": display_path(output_path),
            "sha256": sha256_file(output_path),
            "bytes": output_path.stat().st_size,
            "single_band": True,
            "dtype": "float32",
            "crs": str(audit_profile["crs"]),
            "shape": [int(audit_profile["height"]), int(audit_profile["width"])],
            "transform": list(audit_profile["transform"])[:6],
            "nodata": "NaN",
            "positive_cells": positive_cells,
            "positive_mass": float(positive_cells),
            "min_in_footprint": float(reread[footprint].min()),
            "max_in_footprint": float(reread[footprint].max()),
            "all_in_footprint_values_in_0_1": bool(
                np.all((reread[footprint] >= 0.0) & (reread[footprint] <= 1.0))
            ),
            "finite_footprint_cells": int(footprint.sum()),
            "nan_outside_cells": int(np.isnan(reread).sum()),
        },
        "source": {
            "official_landing": "https://gdr.openei.org/submissions/1391",
            "doi": "10.15121/1881483",
            "reported_license": "CC BY 4.0 per GDR listing; verify asset-level attribution/redistribution terms",
            "local_bytes_source": PINNED_MIRROR,
            "archive_path_at_build": display_path(probes_zip),
            "archive_path_is_in_repository": probes_zip.is_relative_to(ROOT),
            "reproducible_default_path": display_path(DEFAULT_PROBES),
            "archive_bytes": probes_zip.stat().st_size,
            "archive_sha256": source_sha,
            "expected_pinned_mirror_sha256": EXPECTED_MIRROR_SHA256,
            "archive_hash_matches_pinned_mirror": source_sha == EXPECTED_MIRROR_SHA256,
            "shapefile_crs": CRS.from_wkt(source_prj).to_string(),
            "dbf_fields_used": ["Station", "Org_Stn", "Area", "F2mDAB", "T2m", "Date", "T2m_2..T2m_7", "Date_2..Date_7"],
            "excluded_field": "dist_known_fault_px from a separate vent CSV was not read or used",
        },
        "footprint": {
            "path": display_path(footprint_path),
            "sha256": sha256_file(footprint_path),
            "finite_cells": int(footprint.sum()),
            "records_on_finite_footprint": int(raw_inside.sum()),
            "unique_in_footprint_pixels": int(
                len({point_rows_cols[index] for index, is_inside in enumerate(raw_inside) if is_inside})
            ),
            "unique_station_locations_on_finite_footprint": len(inside_location_keys),
        },
        "frozen_rule": {
            "station_identity": "exact NAD83 source point coordinates; the display Station label is descriptive only because labels repeat at different coordinates",
            "source_date_group": "Area x exact Date; aggregate all same-location same-date T2m readings by median; eligible only with at least five distinct point locations",
            "baseline": "leave-one-location-out median of other point locations in the same Area/date",
            "persistent_station": "at least two eligible distinct dates, median residual >=2 C, and >=50 percent of residuals >=2 C",
            "fallback": "only locations with fewer than two eligible residual dates may use median source F2mDAB>0; repeated locations with >=2 dates that fail persistence are excluded",
            "binary_support": "value 1 inside a 300 m Euclidean-radius buffer of selected points; 0 on other finite footprint cells; NaN/nodata outside",
            "buffer_radius_m": BUFFER_M,
            "persistence_threshold_c": PERSISTENCE_C,
            "minimum_stations_per_area_date": MIN_DATE_GROUP_STATIONS,
            "labels_used_in_build": False,
            "known_fault_distance_used": False,
            "parent_prediction_surfaces_used": False,
        },
        "observation_audit": {
            **observation_stats,
            **residual_stats,
            **selection_stats,
            "selected_positive_dab_locations": positive_dab_locations,
            "selected_station_locations_csv": display_path(args.station_audit),
            "selected_station_csv_sha256": sha256_file(args.station_audit),
        },
        "slot_decision": {
            "cleared": False,
            "reason": "A local build receipt cannot clear a weekly slot. Consult the separate hash-checked spatial holdout comparison; even a public-proxy pass is not organizer/private-label evidence.",
        },
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def mask_ds_index(affine, x: float, y: float) -> tuple[int, int]:
    """Call affine index without retaining a closed Rasterio dataset handle."""
    row, col = rowcol(affine, x, y)
    return int(row), int(col)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probes-zip", type=Path, default=DEFAULT_PROBES)
    parser.add_argument("--footprint", type=Path, default=DEFAULT_FOOTPRINT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--station-audit", type=Path, default=DEFAULT_STATION_CSV)
    parser.add_argument(
        "--require-pinned-mirror-sha",
        action="store_true",
        help="fail unless the archive bytes match the recorded pinned owner-mirror SHA-256",
    )
    args = parser.parse_args()
    result = build(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
