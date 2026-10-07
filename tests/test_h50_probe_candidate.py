from __future__ import annotations

from affine import Affine
import numpy as np

from scripts.build_h50_probe_candidate import (
    collect_probe_stations,
    rasterize_buffer_points,
    select_station_records,
    station_residuals,
)


def test_exact_location_and_date_rows_collapse_before_leave_one_location_out():
    rows = []
    points = []
    utm_points = []
    for index, temperature in enumerate((10.0, 10.0, 10.0, 10.0, 10.0)):
        rows.append(
            {
                "Station": "reused-label" if index in (0, 1) else f"S{index}",
                "Area": "Area A",
                "F2mDAB": 1.0,
                "T2m": temperature,
                "Date": "20200101",
            }
        )
        points.append((-118.0 + index * 0.01, 39.0))
        utm_points.append((500000.0 + index * 1000.0, 4300000.0))
    # This is a duplicate source row for the first physical location/date.
    rows.append(
        {
            "Station": "renumbered-label",
            "Area": "Area A",
            "F2mDAB": 2.0,
            "T2m": 20.0,
            "Date": "20200101",
        }
    )
    points.append(points[0])
    utm_points.append(utm_points[0])

    station_records, grouped, station_dates, audit = collect_probe_stations(rows, points, utm_points)
    residuals, residual_audit = station_residuals(grouped)

    first_location = points[0]
    assert len(station_records) == 5  # the repeated display label at point 1 is not used as identity
    assert audit["records_beyond_first_at_exact_coordinates"] == 1
    assert grouped[("Area A", "20200101")][first_location] == [10.0, 20.0]
    assert len(grouped[("Area A", "20200101")]) == 5  # five physical locations, not six rows
    assert residuals[first_location][0]["residual_c"] == 5.0  # median(10, 20) minus peer median 10
    assert residual_audit["duplicate_station_date_groups_collapsed"] == 1
    assert station_dates[first_location]["20200101"] == [10.0, 20.0]


def test_selection_requires_persistence_for_repeat_locations_and_dab_for_fallback():
    locations = [(float(index), 39.0) for index in range(4)]
    station_records = {
        key: {
            "dab_values": [dab],
            "source_record_indices": [index],
            "station_labels": {label},
            "areas": {"A"},
            "longitude_nad83": key[0],
            "latitude_nad83": key[1],
            "point_x_utm11_m": 500000.0 + index * 100.0,
            "point_y_utm11_m": 4300000.0,
        }
        for index, (key, dab, label) in enumerate(
            zip(locations, (-1.0, 5.0, 2.0, 0.0), ("persistent", "unstable", "fallback", "no-support"))
        )
    }
    dates = {
        locations[0]: {"20200101": [1.0], "20210101": [1.0]},
        locations[1]: {"20200101": [1.0], "20210101": [1.0]},
        locations[2]: {"20200101": [1.0]},
        locations[3]: {},
    }
    residuals = {
        locations[0]: [
            {"date": "20200101", "residual_c": 3.0, "group_stations": 5},
            {"date": "20210101", "residual_c": 2.0, "group_stations": 5},
        ],
        locations[1]: [
            {"date": "20200101", "residual_c": 3.0, "group_stations": 5},
            {"date": "20210101", "residual_c": 0.0, "group_stations": 5},
        ],
        locations[2]: [{"date": "20200101", "residual_c": 10.0, "group_stations": 5}],
    }

    selected, summary = select_station_records(
        station_records,
        dates,
        residuals,
        set(locations),
        raw_records_total=4,
        raw_records_inside_finite_footprint=4,
    )

    assert [(item["station"], item["selection_reason"]) for item in selected] == [
        ("persistent", "persistent_repeat_residual"),
        ("fallback", "positive_2mDAB_insufficient_repeat_dates"),
    ]
    assert summary["inside_persistent_repeat_locations"] == 1
    assert summary["inside_fallback_positive_dab_locations"] == 1
    assert summary["inside_excluded_repeat_locations_failing_persistence"] == 1


def test_buffer_uses_exact_cell_centre_distance_and_clips_to_footprint():
    # 7x7 grid with 100 m square cells; point lies at the centre of the middle cell.
    profile = {
        "height": 7,
        "width": 7,
        "transform": Affine(100.0, 0.0, 0.0, 0.0, -100.0, 700.0),
    }
    footprint = np.ones((7, 7), dtype=bool)
    footprint[3, 6] = False
    selected = [{"point_x_utm11_m": 350.0, "point_y_utm11_m": 350.0}]

    support = rasterize_buffer_points(selected, footprint, profile)

    assert support[3, 3]
    assert support[3, 6] == 0  # excluded even though it is within 300 m
    assert support[0, 3]  # exactly 300 m at cell centres is included
    assert not support[0, 2]  # sqrt(100^2 + 300^2) > 300 m
    assert np.all(~support | footprint)
