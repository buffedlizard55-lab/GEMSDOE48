from affine import Affine
from rasterio.crs import CRS
import numpy as np
import pytest

from gemsdoe48.geotiff import EPSG, HEIGHT, TRANSFORM, WIDTH, assert_competition_grid, display_path, write_float32


def test_official_grid_accepts_documented_profile():
    profile = {
        "width": WIDTH,
        "height": HEIGHT,
        "count": 1,
        "crs": CRS.from_epsg(32611),
        "transform": Affine(100, 0, 243350, 0, -100, 4508550),
    }
    assert profile["crs"].to_string() == EPSG
    assert profile["transform"] == TRANSFORM
    assert_competition_grid(profile)


def test_display_path_is_repository_relative():
    from pathlib import Path
    from gemsdoe48.geotiff import REPOSITORY_ROOT

    assert display_path(REPOSITORY_ROOT / "README.md") == "README.md"


def test_grid_mismatch_fails_closed():
    profile = {
        "width": WIDTH - 1,
        "height": HEIGHT,
        "count": 1,
        "crs": CRS.from_epsg(32611),
        "transform": TRANSFORM,
    }
    with pytest.raises(ValueError, match="width/height"):
        assert_competition_grid(profile)


def test_writer_requires_exact_competition_shape_and_explicit_mask(tmp_path):
    with pytest.raises(ValueError, match="expected array shape"):
        write_float32(
            tmp_path / "not-a-real-submission.tif",
            np.zeros((2, 2), dtype=np.float32),
            {"width": 2, "height": 2, "count": 1},
            valid_mask=np.ones((2, 2), dtype=bool),
            description="test",
        )
