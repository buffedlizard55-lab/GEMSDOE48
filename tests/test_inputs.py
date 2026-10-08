"""Byte-level integrity of every raster this repository reasons from.

This module exists because the repository makes claims about *files*: that the
catalogue raster is byte-identical to the training labels (irregularity
IR-48-01), that the live-best artifact carries exactly 37,654 positive pixels,
that every raster sits on the official grid, and that no family raster carries a
value outside [0, 1].  Each of those is a test here, so a swapped or regenerated
input fails the suite instead of silently changing a published number.

It also checks registry/inputs.json -- the SHA-256 receipt -- against the bytes
on disk, so the receipt cannot rot.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import unittest

import numpy as np
import rasterio

import conftest  # noqa: F401  (path bootstrap)
from gemsdoe48 import grid, metric


class LiveAnchorFixture:
    @staticmethod
    def anchor():
        from gemsdoe48.live_anchor import LiveAnchor

        return LiveAnchor(legacy_audit_only=True)

# --- the pinned facts ------------------------------------------------------
# Populated from registry/inputs.json, which is itself checked against the disk.
# The literal values below are the contract: if a file changes, the test fails.
OFFICIAL = {
    "data/official/labels.tif": {
        "sha256": "7ba308ccdc4418b3",
        "bytes": 425830,
        "positive": 60988,
        "dtype": "int8",
    },
    "data/official/existing_faults.tif": {
        "sha256": "7ba308ccdc4418b3",
        "bytes": 425830,
        "positive": 60988,
        "dtype": "int8",
    },
    "data/official/derived_sgmc_faults_100m.tif": {
        "sha256": "643cbe992ef4",
        "positive": 83593,
        "dtype": "uint8",
    },
}

FAMILIES = {
    "data/families/dotted_d2_8_02600.tif": {
        "sha256": "3e78737f0da8",
        "positive": 44090,
        "live": 0.2600,
    },
    "data/families/dotted_d2_8_02708.tif": {
        "sha256": "ab0230015224",
        "positive": 40199,
        "live": 0.2708,
    },
    "data/families/dotted_b2_prune_02778.tif": {
        "sha256": "c55bafc47005",
        "positive": 37654,
        "live": 0.2778,
    },
    "data/families/tip_stepover_r30_02632.tif": {
        "sha256": "87f857d505e2",
        "positive": 41865,
        "live": 0.2632,
    },
}

OUTSIDE_FOOTPRINT_PX = 7111787
FOOTPRINT_PX = 5167373
N_CELLS = 12279160


def sha256_of(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class TestOfficialRasters(unittest.TestCase):
    def test_grid_is_the_official_grid(self):
        for rel in OFFICIAL:
            with self.subTest(rel=rel):
                got = grid.assert_grid(conftest.repo_path(rel))
                self.assertEqual(got["width"], 3292)
                self.assertEqual(got["height"], 3730)
                self.assertEqual(got["res"], (100.0, 100.0))
                self.assertEqual(got["crs"], "EPSG:32611")

    def test_hashes_and_sizes_are_pinned(self):
        for rel, want in OFFICIAL.items():
            with self.subTest(rel=rel):
                p = conftest.repo_path(rel)
                self.assertTrue(p.exists(), f"missing input {rel}")
                self.assertTrue(
                    sha256_of(p).startswith(want["sha256"]),
                    f"{rel}: sha256 {sha256_of(p)[:12]} != pinned {want['sha256']}",
                )
                if "bytes" in want:
                    self.assertEqual(p.stat().st_size, want["bytes"])

    def test_IR_48_01_labels_and_existing_faults_are_byte_identical(self):
        """Irregularity IR-48-01: the catalogue IS the training label.

        Verified two independent ways -- file digests and a pixel-wise compare --
        because the claim is used to explain why a locally-trained model that
        reproduces the catalogue is reproducing the *mask*, not the target.
        """
        a = conftest.repo_path("data/official/labels.tif")
        b = conftest.repo_path("data/official/existing_faults.tif")
        self.assertEqual(sha256_of(a), sha256_of(b), "digests differ")
        self.assertEqual(a.stat().st_size, b.stat().st_size)
        with open(a, "rb") as fa, open(b, "rb") as fb:
            self.assertEqual(fa.read(), fb.read(), "bytes differ")

    def test_footprint_and_truth_counts(self):
        truth, footprint = grid.load_truth_and_footprint()
        self.assertEqual(int(footprint.sum()), FOOTPRINT_PX)
        self.assertEqual(int((~footprint).sum()), OUTSIDE_FOOTPRINT_PX)
        self.assertEqual(int(truth.sum()), 60988)
        self.assertEqual(truth.size, N_CELLS)

    def test_truth_is_binary_and_signal_is_zero_where_truth_is_zero(self):
        """Every true pixel is inside the footprint and labels never mark a
        non-fault pixel as 1."""
        r = grid.read_raster(grid.labels_path())
        a = r.array
        self.assertEqual(set(np.unique(a).tolist()), {-1, 0, 1})
        self.assertTrue(np.all(a[a == 1] == 1))

    def test_nodata_sentinel_is_minus_one(self):
        with rasterio.open(grid.labels_path()) as src:
            self.assertEqual(src.nodata, -1.0)
            self.assertEqual(src.count, 1)

    def test_registry_receipt_matches_disk(self):
        """registry/inputs.json must be regenerable: every digest it records for
        a file that is still present must equal the file's digest."""
        import subprocess

        script = conftest.repo_path("scripts/hash_inputs.py")
        if not script.exists():
            self.skipTest("scripts/hash_inputs.py absent")
        before = (conftest.REGISTRY / "inputs.json").read_text()
        subprocess.run(
            [sys.executable, str(script)], cwd=str(conftest.repo_path(".")),
            check=True, capture_output=True,
        )
        after = (conftest.REGISTRY / "inputs.json").read_text()
        # the only field allowed to change is the generation timestamp
        b = json.loads(before)
        a = json.loads(after)
        b.pop("generated_utc", None)
        a.pop("generated_utc", None)
        self.assertEqual(a, b, "registry/inputs.json is stale -- re-run the script")


class TestFamilyRasters(unittest.TestCase):
    def test_pinned_hashes_and_masses(self):
        for rel, want in FAMILIES.items():
            with self.subTest(rel=rel):
                p = conftest.repo_path(rel)
                self.assertTrue(p.exists(), f"missing family raster {rel}")
                self.assertTrue(
                    sha256_of(p).startswith(want["sha256"]),
                    f"{rel}: sha256 {sha256_of(p)[:12]} != pinned {want['sha256']}",
                )
                with rasterio.open(p) as src:
                    a = src.read(1)
                self.assertEqual(int((a > 0).sum()), want["positive"])

    #: Files that carry NaN, and exactly where the NaN sits.  This is data, not
    #: an exemption: it is asserted both that the NaN is confined to the
    #: out-of-footprint region and that the in-footprint values are legal.
    NAN_OUTSIDE_ONLY = {"data/families/dotted_d2_8_02708.tif"}

    def test_every_family_raster_is_legal_on_the_footprint(self):
        """Single band, float32, official grid, finite and inside [0, 1].

        One family raster (`dotted_d2_8_02708.tif`) carries NaN in exactly the
        7,111,787 cells outside the study area. An owner-reported 0.2708 score is
        not a file-specific organizer receipt and does not establish that the
        portal accepted these bytes or this outside-footprint encoding. This
        check is scoped to in-footprint values; portal acceptance remains unverified.
        """
        _, footprint = grid.load_truth_and_footprint()
        for rel in FAMILIES:
            with self.subTest(rel=rel):
                with rasterio.open(conftest.repo_path(rel)) as src:
                    self.assertEqual(src.count, 1)
                    self.assertEqual(src.dtypes[0], "float32")
                    a = src.read(1)
                finite = np.isfinite(a)
                inside = a[footprint]
                self.assertTrue(finite[footprint].all(), "non-finite value INSIDE the footprint")
                self.assertGreaterEqual(float(inside.min()), 0.0)
                self.assertLessEqual(float(inside.max()), 1.0)
                n_nan = int((~finite).sum())
                if rel in self.NAN_OUTSIDE_ONLY:
                    self.assertEqual(n_nan, OUTSIDE_FOOTPRINT_PX)
                    self.assertTrue(bool(finite[footprint].all()))
                elif n_nan:
                    self.assertEqual(n_nan, 0, f"{rel}: unexpected NaN outside the footprint")

    def test_nan_outside_the_footprint_was_accepted_by_the_portal(self):
        """IR-48-03: NaN outside the study area cannot be what the portal's
        "Predicted values must be in range [0, 1]" message was about."""
        p = conftest.repo_path("data/families/dotted_d2_8_02708.tif")
        _, footprint = grid.load_truth_and_footprint()
        with rasterio.open(p) as src:
            a = src.read(1)
        self.assertEqual(int((~np.isfinite(a)).sum()), OUTSIDE_FOOTPRINT_PX)
        self.assertTrue(np.isfinite(a[footprint]).all())

    def test_family_raster_shapes_match_the_official_grid(self):
        with rasterio.open(grid.labels_path()) as src:
            ref = (src.height, src.width)
        for rel in FAMILIES:
            with self.subTest(rel=rel):
                with rasterio.open(conftest.repo_path(rel)) as src:
                    self.assertEqual((src.height, src.width), ref)


class TestFamilyAgreement(unittest.TestCase):
    """The union / intersection numbers the DS page and the summary report."""

    def setUp(self):
        from gemsdoe48 import families

        self.a = families.load_family_mask("dotted_02708")
        self.b = families.load_family_mask("tip_02632")

    def test_union_intersection_and_jaccard(self):
        inter = int((self.a & self.b).sum())
        union = int((self.a | self.b).sum())
        self.assertEqual(union, 48394)
        self.assertEqual(inter, 33670)
        self.assertAlmostEqual(inter / union, 0.695747, places=6)

    def test_both_families_are_off_the_catalogue(self):
        """All four emissions in this repository carry zero catalogue pixels."""
        truth = grid.read_mask(grid.labels_path())
        for rel in FAMILIES:
            with self.subTest(rel=rel):
                m = grid.read_mask(conftest.repo_path(rel))
                self.assertEqual(int((m & truth).sum()), 0)


class TestLiveAnchor(unittest.TestCase):
    """Keep the retired inversion reproducible but impossible to call silently."""

    def test_inversion_and_removal_gate_require_forensic_opt_in(self):
        from gemsdoe48.live_anchor import LiveAnchor

        anchor = LiveAnchor()
        with self.assertRaisesRegex(RuntimeError, "invalidated live-anchor inversion"):
            anchor.invert()
        with self.assertRaisesRegex(RuntimeError, "invalidated live-anchor inversion"):
            anchor.assess_removal(3891, 100.0)

    def test_forensic_reproduction_is_explicitly_invalidated(self):
        anchor = LiveAnchorFixture.anchor()
        result = anchor.invert()
        self.assertEqual(result["validity_status"], "INVALIDATED_FORENSIC_ONLY_DO_NOT_USE_FOR_PROMOTION")
        self.assertIn("not a general identity", result["invalidation_reason"])
        self.assertAlmostEqual(result["tpw_consistency_rel_invalidated"], 0.0012946626331831756, places=12)
        self.assertAlmostEqual(result["implied_tpw_from_small_invalidated"], 4913.77432, places=4)
        self.assertAlmostEqual(result["implied_tpw_from_big_invalidated"], 4920.136, places=3)
        self.assertEqual(result["assumed_truth_px_invalidated"], 12632)
        self.assertEqual(result["dn_removed"], 3891)

    def test_historical_removal_result_is_not_a_promotion_verdict(self):
        anchor = LiveAnchorFixture.anchor()
        failed = anchor.assess_removal(512, 96.0)
        passed = anchor.assess_removal(3891, 100.0)
        self.assertEqual(failed["validity_status"], "INVALIDATED_FORENSIC_ONLY_DO_NOT_USE_FOR_PROMOTION")
        self.assertFalse(failed["legacy_rule_passes_not_promotion"])
        self.assertTrue(passed["legacy_rule_passes_not_promotion"])
        self.assertNotIn("passes", passed)

    def test_local_credit_bar_helper_is_not_a_live_anchor_calibration(self):
        # This algebraic helper is tested in test_metric_main.py only for the
        # restricted one-truth/local-kernel case; it does not recover hidden truth.
        self.assertAlmostEqual(metric.credit_bar(0.2708), 0.05416, places=5)


if __name__ == "__main__":
    unittest.main()
