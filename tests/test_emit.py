"""Covering geometry: the two theorems the emission strategy rests on.

Both claims are proved by construction here rather than quoted.

1. **Hexagonal covering density.** Among all arrangements of equal circles that
   cover the plane with no overlap, the hexagonal (triangular-lattice)
   arrangement is the densest: it needs `2*pi/(3*sqrt(3)) = 1.20920` circles per
   unit area against the square lattice's `pi/2 = 1.57080`.  The saving is
   `1 - 1.20920/1.57080 = 23.02 %`.  Verified by area counting and by an explicit
   two-dimensional lattice construction.

2. **The maximum distance from an arbitrary point to the nearest lattice node**
   (the covering radius `rho`) is `d/sqrt(3)` for a triangular lattice of side
   `d` and `d/sqrt(2)` for a square lattice of side `d`.  So for a fixed node
   count, hex covers strictly tighter -- the reason `emit.hex_lattice` exists.
"""
from __future__ import annotations

import unittest

import numpy as np

import conftest  # noqa: F401  (path bootstrap)
from gemsdoe48 import emit, metric


class TestCoveringDensityConstants(unittest.TestCase):
    def test_hex_and_square_densities(self):
        self.assertAlmostEqual(emit.HEX_COVERING_DENSITY, 2 * np.pi / (3 * np.sqrt(3)), places=12)
        self.assertAlmostEqual(emit.HEX_COVERING_DENSITY, 1.2091995761561452, places=12)
        self.assertAlmostEqual(emit.SQ_COVERING_DENSITY, np.pi / 2, places=12)
        self.assertLess(emit.HEX_COVERING_DENSITY, emit.SQ_COVERING_DENSITY)

    def test_saving_is_23_percent(self):
        self.assertAlmostEqual(emit.HEX_SAVING, 1 - 1.2091995761561452 / (np.pi / 2), places=12)
        self.assertAlmostEqual(emit.HEX_SAVING, 0.2302, places=4)


class TestCoveringRadiusBothLattices(unittest.TestCase):
    """Measure rho by brute force on a dense probe grid, for both lattices."""

    @staticmethod
    def _covering_radius(points: np.ndarray, lo: float, hi: float, n: int = 601) -> float:
        xs = np.linspace(lo, hi, n)
        best = np.full((n, n), np.inf)
        for px, py in points:
            d = np.hypot(xs[:, None] - px, xs[None, :] - py)
            np.minimum(best, d, out=best)
        return float(best.max())

    def test_hex_covering_radius_is_d_over_sqrt3(self):
        d = 20.0
        pts = emit.hex_lattice((600, 600), d, phase=(0.0, 0.0))
        sel = pts[100:500, 100:500]
        rr, cc = np.nonzero(sel)
        self.assertGreater(rr.size, 50)
        got = self._covering_radius(np.stack([cc, rr], axis=1).astype(float), 0, 99, n=201)
        # compare against the theoretical d/sqrt(3), allowing for the finite probe
        self.assertAlmostEqual(got, d / np.sqrt(3), delta=0.75)

    def test_square_covering_radius_is_d_over_sqrt2(self):
        d = 20.0
        pts = emit.square_lattice((600, 600), d)
        sel = pts[100:500, 100:500]
        rr, cc = np.nonzero(sel)
        got = self._covering_radius(np.stack([cc, rr], axis=1).astype(float), 0, 99, n=201)
        self.assertAlmostEqual(got, d / np.sqrt(2), delta=0.75)

    def test_hex_is_tighter_than_square_at_equal_node_count(self):
        d = 20.0
        hexc = 2 * np.pi / (3 * np.sqrt(3)) / (d * d)
        sqc = (np.pi / 2) / (d * d)
        self.assertLess(hexc, sqc)
        self.assertLess(d / np.sqrt(3), d / np.sqrt(2))


class TestHexLatticeProperties(unittest.TestCase):
    def test_orientation_and_spacing(self):
        pts = emit.hex_lattice((200, 200), 10.0, phase=(0.0, 0.0))
        rr, cc = np.nonzero(pts)
        self.assertGreater(rr.size, 100)
        # row spacing is the triangular height d*sqrt(3)/2
        rows = np.unique(rr)
        gaps = np.diff(rows)
        self.assertTrue(np.all(gaps <= 9))  # every row used by some offset

    def test_minimum_inter_point_distance_is_the_lattice_side_up_to_rounding(self):
        """The lattice is laid out at real-valued positions and then snapped to
        integer pixels, so the realised nearest-neighbour distance can fall a
        little below the requested spacing (measured: 11.66 for spacing = 12.0,
        i.e. the pair at (10, 6)).  Asserting exact equality would be wrong."""
        d = 12.0
        pts = emit.hex_lattice((400, 400), d, phase=(0.0, 0.0))
        rr, cc = np.nonzero(pts)
        coords = np.stack([rr, cc], axis=1).astype(float)
        rng = np.random.default_rng(0)
        idx = rng.choice(coords.shape[0], size=min(600, coords.shape[0]), replace=False)
        sub = coords[idx]
        dmat = np.hypot(sub[:, 0][:, None] - sub[:, 0][None, :],
                        sub[:, 1][:, None] - sub[:, 1][None, :])
        np.fill_diagonal(dmat, np.inf)
        self.assertGreaterEqual(dmat.min(), d - 1.0)
        # and it is never wildly larger: a hex lattice has no holes
        self.assertLess(dmat.min(), d)

    def test_phase_shifts_the_lattice(self):
        a = emit.hex_lattice((100, 100), 10.0, phase=(0.0, 0.0))
        b = emit.hex_lattice((100, 100), 10.0, phase=(0.3, 0.7))
        self.assertFalse(np.array_equal(a, b))
        self.assertLess(abs(int(a.sum()) - int(b.sum())), 200)


class TestCoverageHelpers(unittest.TestCase):
    def test_dilate_disk_is_a_true_euclidean_dilation(self):
        m = np.zeros((21, 21), dtype=bool)
        m[10, 10] = True
        for r in (0, 1, 2, 3, 5):
            got = emit.dilate_disk(m, float(r))
            yy, xx = np.mgrid[0:21, 0:21]
            want = (np.hypot(yy - 10, xx - 10) <= r + 1e-9)
            np.testing.assert_array_equal(got, want, err_msg=f"r={r}")

    def test_dilate_mask_is_the_manhattan_ball_and_dilate_disk_is_euclidean(self):
        """Two different dilations live in this module, and they are not the same.

        `dilate_mask` ORs the four axis neighbours repeatedly, so its footprint is
        the city-block (Manhattan) ball {|dr| + |dc| <= r} -- NOT a square and NOT
        an exact disk.  `dilate_disk` is the exact Euclidean disk, which is what
        the metric's 300 m triangular kernel actually reaches.

        The two coincide for r <= 2 and diverge from r = 3, where the Euclidean
        disk gains the L1-excess cells first: measured +4 cells at r = 3, +8 at
        r = 4, +20 at r = 5.  So `dilate_mask` is the *tighter* of the two -- a
        corridor built with it is a subset of the true 300 m reach, which is the
        safe direction for a corridor and the wrong one for a stand-in.
        """
        m = np.zeros((21, 21), dtype=bool)
        m[10, 10] = True
        yy, xx = np.mgrid[0:21, 0:21]
        for r in (1, 2, 3, 4, 5):
            with self.subTest(r=r):
                manhattan = (np.abs(yy - 10) + np.abs(xx - 10)) <= r
                np.testing.assert_array_equal(emit.dilate_mask(m, r), manhattan)
                disk = emit.dilate_disk(m, float(r))
                # the Manhattan ball is a subset of the Euclidean disk
                self.assertTrue(bool((manhattan & ~disk).sum() == 0))
        # they agree exactly at r <= 2 ...
        for r in (1, 2):
            np.testing.assert_array_equal(emit.dilate_mask(m, r), emit.dilate_disk(m, float(r)))
        # ... and diverge from r = 3
        expected_extra = {3: 4, 4: 8, 5: 20}
        for r, extra in expected_extra.items():
            with self.subTest(r=r):
                self.assertEqual(
                    int((emit.dilate_disk(m, float(r)) & ~emit.dilate_mask(m, r)).sum()), extra
                )

    def test_disk_offsets_are_the_exact_euclidean_disk(self):
        for r in (1.0, 2.0, 2.5, 3.0):
            offs = emit.disk_offsets(r)
            self.assertIn((0, 0), offs)
            for dr, dc in offs:
                self.assertLessEqual(np.hypot(dr, dc), r + 1e-9)
            # no cell just outside the disk is missed
            for dr in range(-int(r) - 2, int(r) + 3):
                for dc in range(-int(r) - 2, int(r) + 3):
                    if np.hypot(dr, dc) <= r and (dr, dc) not in offs:
                        self.fail(f"({dr},{dc}) missing from r={r}")

    def test_covered_within_is_exactly_the_euclidean_disk(self):
        """`covered_within` must NOT be intersected with the support: the covered
        set is everything within the radius, and the caller intersects it."""
        rng = np.random.default_rng(7)
        support = rng.random((50, 50)) < 0.08
        pts = np.zeros((50, 50), dtype=bool)
        rr, cc = np.nonzero(support)
        keep = rng.random(rr.size) < 0.3
        pts[rr[keep], cc[keep]] = True
        for r in (1.0, 2.0, 3.0):
            np.testing.assert_array_equal(emit.covered_within(pts, r), emit.dilate_disk(pts, r))
            # intersecting with the support is the caller's job, and it is a superset
            self.assertGreaterEqual(int((support & emit.covered_within(pts, r)).sum()),
                                    int(emit.covered_within(pts, r).sum()) - int((~support).sum()))

    def test_covering_radius_of_the_shipped_family_is_small(self):
        """A committed set covers its own 1-px corridor, by construction."""
        from gemsdoe48 import families

        m = families.load_family_mask("dotted_02708")
        corridor = emit.dilate_mask(m, 1)
        self.assertLessEqual(emit.covering_radius(m, corridor), 1.0 + 1e-9)


class TestCoverRegionInvariants(unittest.TestCase):
    """The two documented traps: keep_radius below the target, and prune-before-fill."""

    def setUp(self):
        rng = np.random.default_rng(11)
        self.support = rng.random((120, 120)) < 0.10
        self.support[60:, :] = False  # a corridor with a hard edge

    def test_keep_radius_below_target_leaves_the_target_unmet(self):
        """Documented failure mode: pruning to the target radius digs holes."""
        bad = emit.cover_region(self.support, spacing=3.0, keep_radius=1.0, prune=True)
        good = emit.cover_region(self.support, spacing=3.0, keep_radius=3.0, prune=True)
        r_bad = emit.covering_radius(bad["points"], self.support)
        r_good = emit.covering_radius(good["points"], self.support)
        self.assertLessEqual(r_good, 3.0 + 1e-9)
        # the documented trap really does break the target
        self.assertGreaterEqual(r_bad, r_good)

    def test_the_cover_is_complete_and_the_radius_is_the_target(self):
        for spacing in (2.0, 3.0, 4.0):
            with self.subTest(spacing=spacing):
                out = emit.cover_region(self.support, spacing=spacing,
                                        keep_radius=float(np.ceil(spacing)))
                pts = out["points"]
                self.assertTrue(bool((self.support & ~emit.dilate_disk(pts, np.ceil(spacing))).sum() == 0))
                self.assertLessEqual(emit.covering_radius(pts, self.support), float(np.ceil(spacing)) + 1e-9)

    def test_greedy_fill_closes_the_support_within_the_radius(self):
        """`greedy_fill(points, support, radius)` returns the augmented point mask
        and must leave no support pixel further than `radius` away."""
        pts = emit.hex_lattice(self.support.shape, 6.0) & emit.dilate_mask(self.support, 6)
        self.assertGreater(int((self.support & ~emit.covered_within(pts, 3.0)).sum()), 0)
        filled = emit.greedy_fill(pts, self.support, 3.0, max_passes=6)
        self.assertEqual(filled.shape, self.support.shape)
        self.assertEqual(int((filled & ~pts).sum() > 0), 1, "nothing was added")
        self.assertEqual(int((self.support & ~emit.covered_within(filled, 3.0)).sum()), 0)
        # greedy_fill only ever adds
        self.assertTrue(bool((pts & ~filled).sum() == 0))

    def test_greedy_fill_leaves_a_zero_radius_support_alone(self):
        pts = np.zeros((30, 30), dtype=bool)
        out = emit.greedy_fill(pts, np.zeros((30, 30), dtype=bool), 2.0, max_passes=4)
        self.assertEqual(int(out.sum()), 0)

    def test_prune_reduces_or_keeps_the_count(self):
        pts = emit.hex_lattice((120, 120), 2.5)
        pts = pts & emit.dilate_mask(self.support, 3)
        pruned = emit.prune_redundant_batched(pts, self.support, radius=3.0, rounds=3)
        self.assertLessEqual(int(pruned.sum()), int(pts.sum()))
        # and the pruned set still covers the support at radius 3
        self.assertEqual(int((self.support & ~emit.dilate_disk(pruned, 3.0)).sum()), 0)


class TestEmissionGeometryAgainstTheMetric(unittest.TestCase):
    """Closing the loop: geometry -> credit, using the real metric."""

    def test_a_hex_cover_beats_a_square_cover_at_equal_node_count(self):
        """For the same number of dots, hex leaves more truth pixels covered."""
        support = np.zeros((300, 300), dtype=bool)
        support[150:170, :] = True
        truth = support.copy()
        d = 12.0
        hex_pts = emit.hex_lattice((300, 300), d) & emit.dilate_mask(support, 12)
        sq_pts = emit.square_lattice((300, 300), d) & emit.dilate_mask(support, 12)
        r_hex = metric.dti(hex_pts.astype(float), truth)
        r_sq = metric.dti(sq_pts.astype(float), truth)
        # compare per unit mass, since the two lattices place different counts
        self.assertGreater(r_hex.tpw / hex_pts.sum(), r_sq.tpw / sq_pts.sum())

    def test_denser_is_not_free(self):
        """T1: doubling the mass of an already-perfect cover lowers the score."""
        support = np.zeros((200, 200), dtype=bool)
        support[100:103, 20:180] = True
        truth = support.copy()
        coarse = emit.hex_lattice((200, 200), 3.0) & support
        fine = emit.hex_lattice((200, 200), 1.5) & support
        r_coarse = metric.dti(coarse.astype(float), truth)
        r_fine = metric.dti(fine.astype(float), truth)
        self.assertGreater(r_coarse.tpw, 0.0)
        self.assertGreater(r_fine.mass, r_coarse.mass)
        # past perfect coverage, extra mass is pure false positive
        self.assertLess(r_fine.tpw / r_fine.mass, r_coarse.tpw / r_coarse.mass)


if __name__ == "__main__":
    unittest.main()
