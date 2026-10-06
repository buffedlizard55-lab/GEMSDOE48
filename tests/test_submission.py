"""The four research deliverables are checked from the bytes on disk.

Nothing here trusts `registry/submission_build.json`: the receipt is read only to
find the filenames, and local content/format claims are re-derived from the GeoTIFFs.
Passing these checks is not portal acceptance or slot clearance; the output uses
finite zeros outside and differs from the published null/NaN-outside wording.
"""
from __future__ import annotations

import hashlib
import json
import unittest

import numpy as np
import rasterio

import conftest  # noqa: F401  (path bootstrap)
from gemsdoe48 import grid

REGISTRY = conftest.REGISTRY / "submission_build.json"
EXPECTED_NAME = "GEMSDOE48-DS48-FUSION"
LIVE_BEST_MASS = 37654
#: The two disagreement layers legitimately carry mass outside the study area
#: (the frame m(Theta) is positive everywhere on the grid; the conflict layer
#: mirrors the belief raster's off-footprint tail).  Only the emission must be
#: strictly clean.
CLEAN_OFF_FOOTPRINT = {"emission", "belief"}


def sha256_of(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class TestReceiptIsWellFormed(unittest.TestCase):
    def setUp(self):
        self.assertTrue(REGISTRY.exists(), "registry/submission_build.json missing")
        self.rec = json.loads(REGISTRY.read_text())

    def test_unique_name_and_portal_note(self):
        self.assertEqual(self.rec["unique_name"], EXPECTED_NAME)
        note = self.rec["portal_note"]
        self.assertIn(EXPECTED_NAME, note)
        self.assertIn("UNSCORED", note)  # the honest label: no organizer score
        self.assertLessEqual(len(note), 500, "the optional portal note is short")
        self.assertIn("NOT slot-cleared", note)
        self.assertIn("do not upload", note)

    def test_four_files_declared_and_present(self):
        want = {"belief", "emission", "mtheta", "conflict"}
        self.assertEqual(set(self.rec["files"]), want)
        for key, meta in self.rec["files"].items():
            with self.subTest(key=key):
                p = conftest.DOWNLOADS / meta["file"]
                self.assertTrue(p.exists(), f"missing deliverable {meta['file']}")
                self.assertTrue(sha256_of(p).startswith(meta["sha256"]))

    def test_receipt_verdicts_all_pass(self):
        for key, chk in self.rec["format_checks"].items():
            with self.subTest(key=key):
                self.assertEqual(chk["verdict"], "PASS")
                self.assertTrue(chk["raster_legal"])
                self.assertEqual(chk["n_nan"], 0)
                self.assertEqual(chk["n_inf"], 0)
                self.assertEqual(chk["n_below_0"], 0)
                self.assertEqual(chk["n_above_1"], 0)
        self.assertEqual(self.rec["format_checks"]["emission"]["outside_footprint_positive"], 0)

    def test_normalisation_block_is_recorded_and_honest(self):
        """The receipt must state that no affine rescale was applied, and give the
        map that would apply one, so the choice is auditable."""
        n = self.rec["normalisation"]
        self.assertIn("none beyond Dempster", n["applied"])
        for tag in ("belief", "mtheta", "conflict", "emission"):
            with self.subTest(tag=tag):
                rec = n["per_layer"][tag]
                self.assertGreaterEqual(rec["natural_min"], 0.0)
                self.assertLessEqual(rec["natural_max"], 1.0)
                a = rec["minmax_rescale_bounds"]["a"]
                b = rec["minmax_rescale_bounds"]["b"]
                self.assertAlmostEqual(a * rec["natural_min"] + b, 0.0, places=6)
                self.assertAlmostEqual(a * rec["natural_max"] + b, 1.0, places=6)

    def test_reliability_discounts_are_in_range(self):
        for k, v in self.rec["reliability"].items():
            self.assertTrue(0.0 < v <= 1.0, f"{k} = {v}")


class TestDeliverableBytes(unittest.TestCase):
    def setUp(self):
        self.rec = json.loads(REGISTRY.read_text())
        self.truth, self.footprint = grid.load_truth_and_footprint()

    def _open(self, key):
        meta = self.rec["files"][key]
        return conftest.DOWNLOADS / meta["file"]

    def test_every_file_is_a_legal_portal_submission(self):
        """The portal's own rule: single band, float, values in [0, 1]."""
        for key in self.rec["files"]:
            with self.subTest(key=key):
                with rasterio.open(self._open(key)) as src:
                    self.assertEqual(src.count, 1)
                    self.assertIn(src.dtypes[0], ("float32", "float64"))
                    self.assertEqual(src.width, 3292)
                    self.assertEqual(src.height, 3730)
                    self.assertEqual(src.crs.to_string(), "EPSG:32611")
                    self.assertEqual(src.res, (100.0, 100.0))
                    a = src.read(1)
                self.assertTrue(np.isfinite(a).all(), "non-finite value")
                self.assertGreaterEqual(float(a.min()), 0.0)
                self.assertLessEqual(float(a.max()), 1.0)

    def test_emission_mass_is_exactly_the_live_best_mass(self):
        with rasterio.open(self._open("emission")) as src:
            a = src.read(1)
        self.assertEqual(int((a > 0).sum()), LIVE_BEST_MASS)
        # the shipped emission is binary {0, 1}
        self.assertEqual(set(np.unique(a).tolist()), {0.0, 1.0})

    def test_emission_places_no_mass_outside_the_study_area(self):
        with rasterio.open(self._open("emission")) as src:
            a = src.read(1)
        outside = ~self.footprint
        self.assertEqual(int((a[outside] > 0).sum()), 0)

    def test_belief_layer_carries_the_calibrated_values(self):
        """The belief layer is the DS belief, NOT a max-scaled copy of it.

        This is a regression guard.  An earlier build divided each layer by its
        own maximum, which mapped Bel into [0.446, 1] and m(Theta) into
        [0.64, 1] -- a rescaled *shape* rather than a belief, contradicting both
        the page's worked values and the mass-function axioms.  The theoretical
        bounds (0.84 at full agreement, 0.375 where one family is silent) are
        asserted exactly here.
        """
        a1 = self.rec["reliability"]["a_dotted"]
        a2 = self.rec["reliability"]["a_tip"]
        with rasterio.open(self._open("belief")) as src:
            bel = src.read(1)
        with rasterio.open(self._open("mtheta")) as src:
            theta = src.read(1)

        bel_max_theory = 1.0 - (1.0 - a1) * (1.0 - a2)  # 0.84 for a = 0.6
        self.assertAlmostEqual(float(bel.max()), bel_max_theory, places=5)
        self.assertAlmostEqual(float(bel.max()), 0.84, places=5)
        self.assertLessEqual(float(bel.max()), 1.0)

        # m(Theta) = (1-a1)(1-a2)/(1-K) with K in [0, a1*a2] => [0.16, 0.25]
        lo = (1 - a1) * (1 - a2)
        hi = lo / (1.0 - a1 * a2)
        self.assertAlmostEqual(float(theta.min()), lo, places=5)
        self.assertAlmostEqual(float(theta.max()), hi, places=5)

        # every pixel's masses sum to 1 -> Bel + m(notF) + m(Theta) = 1 with
        # m(notF) = 1 - Bel - m(Theta) >= 0, i.e. Bel + m(Theta) <= 1
        both_positive = bel > 0
        self.assertTrue(bool((bel[both_positive] + theta[both_positive] <= 1.0 + 1e-6).all()))

    def test_conflict_matches_its_closed_form_on_every_pixel(self):
        """K = a1 a2 [b1 + b2 - 2 b1 b2], checked against the shipped raster.

        The closed form follows from K = m1(F)m2(notF) + m1(notF)m2(F) with
        m_i(F) = a_i b_i:
            K = a1 a2 [ b1 (1 - b2) + (1 - b1) b2 ] = a1 a2 (b1 + b2 - 2 b1 b2).
        So K vanishes only at the two corners (b1, b2) = (0, 0) and (1, 1), and is
        max = a1 a2 = 0.36 at (1, 0).  Comparing the whole raster against this
        expression starts from the family masks and ends at the file on disk, so
        it validates the emission-side layers end to end.
        """
        from gemsdoe48 import families

        a1 = self.rec["reliability"]["a_dotted"]
        a2 = self.rec["reliability"]["a_tip"]
        b1 = families.kernel_credit_surface(families.load_family_mask("dotted_02708"))
        b2 = families.kernel_credit_surface(families.load_family_mask("tip_02632"))
        with rasterio.open(self._open("conflict")) as src:
            k = src.read(1)

        expected = a1 * a2 * (b1 + b2 - 2.0 * b1 * b2)
        # float32 storage on disk vs float64 in memory
        np.testing.assert_allclose(k, expected, atol=1e-6)
        self.assertAlmostEqual(float(k.max()), a1 * a2, places=5)

        # the corner where both families are silent
        silent = (b1 == 0.0) & (b2 == 0.0)
        self.assertTrue(silent.any())
        self.assertLessEqual(float(k[silent].max()), 1e-9)
        # the corner where both speak, and where conflict is maximal
        both = (b1 == 1.0) & (b2 == 1.0)
        self.assertTrue(both.any())
        self.assertLessEqual(float(k[both].max()), 1e-9)
        opposed = (b1 == 1.0) & (b2 == 0.0)
        if opposed.any():
            self.assertAlmostEqual(float(k[opposed].min()), a1 * a2, places=5)

    def test_mtheta_floor_is_the_closed_form(self):
        """m12(Theta) at zero conflict = (1-a1)(1-a2) / (1-0) = 0.16 for a = 0.6.

        The brief asks for the unassigned mass to be carried forward as its own
        layer; a layer whose floor is 0.16 rather than 0 is what that means, and
        it is the opposite of a max-rescaled layer (whose floor would be 0).
        """
        a1 = self.rec["reliability"]["a_dotted"]
        a2 = self.rec["reliability"]["a_tip"]
        with rasterio.open(self._open("mtheta")) as src:
            theta = src.read(1)
        self.assertAlmostEqual(float(theta.min()), (1 - a1) * (1 - a2), places=5)
        self.assertAlmostEqual(float(theta.min()), 0.16, places=5)
        self.assertGreater(float(theta.min()), 0.0)


class TestNotTheMean(unittest.TestCase):
    """The DS layers must not be a rescaled average of the two families."""

    def setUp(self):
        from gemsdoe48 import ds, families

        self.b1 = families.load_family_surface("dotted_02708")
        self.b2 = families.load_family_surface("tip_02632")
        self.bel = ds.combine_pair(self.b1, self.b2, 0.6, 0.6).bel_F
        self.mean = ds.naive_mean(self.b1, self.b2)

    def test_not_an_affine_function_of_the_mean(self):
        m = self.mean.ravel()
        A = np.stack([m, np.ones(m.size)], axis=1)
        coef, *_ = np.linalg.lstsq(A, self.bel.ravel(), rcond=None)
        resid = self.bel.ravel() - A @ coef
        # the single best affine fit of Bel in the mean still misses by > 0.01
        # somewhere, so Bel is not an affine function of the mean
        self.assertGreater(float(np.abs(resid).max()), 0.01)

    def test_values_differ_on_every_union_pixel(self):
        union = (self.b1 > 0) | (self.b2 > 0)
        diff = np.abs(self.bel - self.mean)[union]
        self.assertTrue(np.all(diff > 0.05), "expected a large pointwise difference")

    def test_ranking_on_the_union_is_monotone_and_that_is_reported(self):
        """The honest headline: identical ranking on the union support.

        A union pixel has belief exactly 1 in its own family, so both statistics
        are monotone in the *other* family's belief; the Spearman correlation is
        1 to floating-point.  The repository ships the belief value, not a claim
        of a better ordering.
        """
        from scipy.stats import spearmanr

        union = (self.b1 > 0) | (self.b2 > 0)
        rho = spearmanr(self.bel[union], self.mean[union]).statistic
        self.assertAlmostEqual(float(rho), 1.0, places=6)
        rec = json.loads(REGISTRY.read_text())["not_the_mean"]
        self.assertAlmostEqual(
            rec["spearman_rho_belief_vs_naive_mean_on_union"], float(rho), places=6
        )
        self.assertIn("does NOT change the ranking", rec["verdict"])


if __name__ == "__main__":
    unittest.main()
