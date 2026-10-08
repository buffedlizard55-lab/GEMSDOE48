"""The metric is tested against its own naive transcription, not against itself.

The fast implementation in ``gemsdoe48.metric`` collapses the two ``max``
operators of the official equations onto 25 shifted-array operations.  These
tests prove that collapse is exact by comparing against an independent O(|G| * N)
loop written straight from the published equations, on random rasters where the
``max`` is genuinely contested (many candidates inside the 300 m reach).
"""
from __future__ import annotations

import unittest

import numpy as np

import conftest  # noqa: F401  (path bootstrap)
from gemsdoe48 import metric


class TestKernel(unittest.TestCase):
    def test_offset_count_and_weights(self):
        # 300 m reach on a 100 m grid => integer offsets with hypot < 3.
        self.assertEqual(len(metric.OFFSETS), 25)
        ks = sorted(k for _, _, k in metric.OFFSETS)
        self.assertAlmostEqual(ks[0], 1.0 - 2.0 * np.sqrt(2.0) / 3.0)  # (2,2)
        self.assertAlmostEqual(ks[-1], 1.0)  # (0,0)
        for dr, dc, k in metric.OFFSETS:
            self.assertGreater(k, 0.0)
            self.assertLessEqual(k, 1.0)
            self.assertLess(np.hypot(dr, dc), 3.0)

    def test_no_duplicate_offsets(self):
        seen = {(dr, dc) for dr, dc, _ in metric.OFFSETS}
        self.assertEqual(len(seen), 25)

    def test_kernel_is_symmetric(self):
        d = {(dr, dc): k for dr, dc, k in metric.OFFSETS}
        for (dr, dc), k in d.items():
            self.assertAlmostEqual(d[(-dr, -dc)], k)

    def test_max_credit_at_own_pixel_is_the_value(self):
        f = np.zeros((9, 9))
        f[4, 4] = 0.7
        out = metric.max_credit_field(f)
        self.assertAlmostEqual(out[4, 4], 0.7)  # k = 1 on the diagonal
        self.assertAlmostEqual(out[4, 7], 0.0)  # exactly at the reach
        self.assertAlmostEqual(out[4, 6], 0.7 * (1.0 - 2.0 / 3.0))


class TestIdentities(unittest.TestCase):
    def test_fpw_identity_and_mass(self):
        rng = np.random.default_rng(11)
        p = (rng.random((80, 90)) < 0.02).astype(np.float64)
        t = rng.random((80, 90)) < 0.01
        r = metric.dti(p, t)
        # FPw = S - M exactly, by construction of the arrays
        self.assertAlmostEqual(r.fpw, r.mass - r.self_credit, places=9)
        # FNw = |G| - TPw exactly, because p <= 1 and k <= 1
        self.assertAlmostEqual(r.fnw, r.n_truth - r.tpw, places=9)

    def test_dti_formula_is_the_published_one(self):
        rng = np.random.default_rng(3)
        p = rng.random((60, 60)) * (rng.random((60, 60)) < 0.05)
        t = rng.random((60, 60)) < 0.02
        r = metric.dti(p, t)
        manual = r.tpw / (r.tpw + 0.2 * r.fpw + 0.8 * r.fnw + metric.EPS)
        self.assertAlmostEqual(r.dti, manual, places=12)


class TestExactness(unittest.TestCase):
    """Fast path vs the deliberately naive transcription."""

    def _case(self, seed, shape=(40, 45), density=0.03, ndots=90):
        rng = np.random.default_rng(seed)
        p = np.zeros(shape)
        idx = rng.choice(shape[0] * shape[1], size=ndots, replace=False)
        p.flat[idx] = rng.random(ndots)
        t = rng.random(shape) < density
        return p, t

    def test_fast_equals_bruteforce_random(self):
        for seed in (1, 2, 3, 4, 5):
            with self.subTest(seed=seed):
                p, t = self._case(seed)
                fast = metric.dti(p, t, validate=True)
                slow = metric.dti_bruteforce(p, t)
                self.assertAlmostEqual(fast.tpw, slow.tpw, places=8)
                self.assertAlmostEqual(fast.fpw, slow.fpw, places=6)
                self.assertAlmostEqual(fast.fnw, slow.fnw, places=8)
                self.assertAlmostEqual(fast.dti, slow.dti, places=9)

    def test_fast_equals_bruteforce_with_a_cluster(self):
        # A dense cluster makes the argmax of several truth pixels contestable
        # at several kernel offsets -- the case where an off-by-one shift bug
        # would show up.
        p = np.zeros((40, 45))
        p[20:24, 20:25] = 1.0
        p[20, 24] = 0.5
        t = np.zeros((40, 45), dtype=bool)
        t[21:23, 21:24] = True
        fast = metric.dti(p, t)
        slow = metric.dti_bruteforce(p, t)
        self.assertAlmostEqual(fast.tpw, slow.tpw, places=10)
        self.assertAlmostEqual(fast.dti, slow.dti, places=10)

    def test_fast_equals_bruteforce_binary(self):
        rng = np.random.default_rng(77)
        p = (rng.random((50, 50)) < 0.06).astype(float)
        t = rng.random((50, 50)) < 0.03
        self.assertAlmostEqual(
            metric.dti(p, t).dti, metric.dti_bruteforce(p, t).dti, places=10
        )

    def test_shift_convention_is_pinned(self):
        """The shift moves `a` by (+dr, +dc): `out[r, c] = a[r - dr, c - dc]`.

        The sign is immaterial to the metric (the offset set and the kernel are
        both symmetric), but it must not drift silently, so it is pinned here.
        """
        a = np.zeros((7, 7))
        a[3, 3] = 1.0
        for dr, dc in ((0, 0), (2, 0), (-2, 0), (0, 3), (0, -3), (2, -2)):
            got = metric._shift(a, dr, dc)
            want = np.zeros_like(a)
            rr, cc = 3 + dr, 3 + dc
            if 0 <= rr < 7 and 0 <= cc < 7:
                want[rr, cc] = 1.0
            np.testing.assert_allclose(got, want, err_msg=f"dr={dr} dc={dc}")

    def test_shift_matches_an_explicit_o_n2_loop(self):
        a = np.arange(20, dtype=float).reshape(4, 5)
        for dr, dc in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, -2), (-3, 4)):
            got = metric._shift(a, dr, dc)
            want = np.zeros_like(a)
            for r in range(a.shape[0]):
                for c in range(a.shape[1]):
                    if 0 <= r - dr < a.shape[0] and 0 <= c - dc < a.shape[1]:
                        want[r, c] = a[r - dr, c - dc]
            np.testing.assert_allclose(got, want)

    @staticmethod
    def _shift_plus(a, dr, dc):
        """`out[r, c] = a[r + dr, c + dc]`, zero-filled (NOT circular)."""
        out = np.zeros_like(a)
        h, w = a.shape
        r0, r1 = max(-dr, 0), min(h, h - dr)
        c0, c1 = max(-dc, 0), min(w, w - dc)
        if r0 < r1 and c0 < c1:
            out[r0:r1, c0:c1] = a[r0 + dr : r1 + dr, c0 + dc : c1 + dc]
        return out

    def test_sign_convention_cannot_change_the_result(self):
        """Because OFFSETS and k are both symmetric, either sign gives the same
        `max` -- so the fast path is exact whichever convention is used."""
        rng = np.random.default_rng(5)
        f = rng.random((30, 30))
        plus = np.zeros_like(f)
        for dr, dc, k in metric.OFFSETS:  # out[r,c] = a[r+dr, c+dc]
            plus = np.maximum(plus, self._shift_plus(f, dr, dc) * k)
        np.testing.assert_allclose(metric.max_credit_field(f), plus, atol=1e-12)


class TestMetricProperties(unittest.TestCase):
    def test_perfect_prediction_is_one(self):
        t = np.zeros((30, 30), dtype=bool)
        t[10, 10] = True
        t[20, 20] = True
        p = t.astype(float)
        # DTI = T/(T + eps) for a perfect prediction, so 1 - 1e-9 with |G| = 2.
        T = float(t.sum())
        self.assertAlmostEqual(metric.dti(p, t).dti, T / (T + metric.EPS), places=15)

    def test_empty_prediction_is_zero(self):
        t = np.zeros((30, 30), dtype=bool)
        t[10, 10] = True
        r = metric.dti(np.zeros((30, 30)), t)
        self.assertAlmostEqual(r.dti, 0.0, places=12)
        self.assertEqual(r.n_emitted, 0)

    def test_nan_is_treated_as_absent(self):
        t = np.zeros((20, 20), dtype=bool)
        t[5, 5] = True
        p = np.full((20, 20), np.nan)
        p[5, 5] = 1.0
        r = metric.dti(p, t)
        # T/(T + eps) exactly: the official denominator carries a "+ eps".  A
        # perfect prediction therefore scores 1 - 1e-9, not 1.  This is a
        # property of the published formula, not a bug in the implementation.
        self.assertAlmostEqual(r.dti, 1.0 / (1.0 + metric.EPS), places=15)
        self.assertLess(r.dti, 1.0)
        self.assertEqual(r.mass, 1.0)

    def test_out_of_range_is_rejected(self):
        t = np.zeros((10, 10), dtype=bool)
        t[1, 1] = True
        p = np.zeros((10, 10))
        p[1, 1] = 1.5
        with self.assertRaises(ValueError):
            metric.dti(p, t)
        p[1, 1] = -0.5
        with self.assertRaises(ValueError):
            metric.dti(p, t)
        # the guard can be switched off explicitly
        p2 = np.zeros((10, 10))
        p2[1, 1] = 1.5
        self.assertEqual(metric.dti(p2, t, validate=False).n_emitted, 1)

    def test_shape_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            metric.dti(np.zeros((5, 5)), np.zeros((5, 6), dtype=bool))

    def test_score_is_monotone_in_extra_true_positive_mass(self):
        t = np.zeros((40, 40), dtype=bool)
        t[20, 20] = True
        base = metric.dti(np.zeros((40, 40)), t).dti
        p = np.zeros((40, 40))
        p[20, 20] = 1.0
        self.assertGreater(metric.dti(p, t).dti, base)

    def test_a_far_dot_is_pure_cost(self):
        """A dot with no truth within 300 m only adds FPw."""
        t = np.zeros((40, 40), dtype=bool)
        t[2, 2] = True
        p0 = np.zeros((40, 40))
        p0[2, 2] = 1.0
        r0 = metric.dti(p0, t)
        p1 = p0.copy()
        p1[35, 35] = 1.0
        r1 = metric.dti(p1, t)
        self.assertAlmostEqual(r1.tpw, r0.tpw, places=12)
        self.assertEqual(r1.n_emitted, r0.n_emitted + 1)
        self.assertAlmostEqual(r1.mass - r0.mass, 1.0, places=12)
        self.assertLess(r1.dti, r0.dti)


def cur_tpw(p, t):
    """Total weighted true-positive credit of `p` against `t`."""
    return metric.dti(p, t).tpw


class TestCreditBar(unittest.TestCase):
    """Test the alpha*DTI helper only in explicitly restricted local cases."""

    def test_bar_is_alpha_times_dti(self):
        for v in (0.0, 0.1, 0.2778, 0.3195, 1.0):
            self.assertAlmostEqual(metric.credit_bar(v), 0.2 * v)

    def test_bar_numeric_example_is_not_a_live_calibration(self):
        # This is arithmetic only; it does not infer a hidden-truth density or
        # establish a universal promotion threshold from the owner-reported 0.2708.
        self.assertAlmostEqual(metric.credit_bar(0.2708), 0.05416, places=9)

    def test_adding_a_dot_above_the_conditional_local_bar_raises_the_score(self):
        """Check the restricted one-truth case where delta TPw = self-credit.

        A second dot next to an *already perfectly covered* truth pixel adds no
        TPw at all, so it is not the case tested here. A dot that becomes the
        argmax for exactly one previously uncovered truth pixel has equal
        marginal TPw and prediction-centred self-credit; only in this geometry
        does ``k > alpha*DTI`` apply directly. This is not a general gate.
        """
        t = np.zeros((60, 60), dtype=bool)
        t[10, 10] = True  # covered perfectly
        t[40, 40] = True  # left uncovered
        p = np.zeros((60, 60))
        p[10, 10] = 1.0
        cur = metric.dti(p, t).dti
        # k at 2 px offset = 1 - 200/300 = 1/3, above the bar 0.2 * DTI
        k = 1.0 - 2.0 / 3.0
        self.assertGreater(k, metric.credit_bar(cur))
        p2 = p.copy()
        p2[40, 42] = 1.0
        self.assertGreater(metric.dti(p2, t).dti, cur)

    def test_adding_a_dot_below_the_bar_lowers_the_score(self):
        """Same construction, but the bar is raised above the available weight.

        With one truth pixel perfectly covered, DTI ~= 1 and the bar is 0.2.  A
        candidate dot 3 px from a second, uncovered truth pixel has k = 0 reading
        (the reach is 3 px, so k = 1 - 300/300 = 0) and is a pure loss.
        """
        t = np.zeros((60, 60), dtype=bool)
        t[10, 10] = True
        p = np.zeros((60, 60))
        p[10, 10] = 1.0
        cur = metric.dti(p, t).dti
        self.assertAlmostEqual(cur, 1.0, places=8)
        # a dot 3 px from the truth pixel earns exactly zero credit
        far = p.copy()
        far[10, 13] = 1.0
        r_far = metric.dti(far, t)
        self.assertAlmostEqual(r_far.tpw, cur_tpw(p, t), places=12)
        self.assertLess(r_far.dti, cur)

    def test_worked_credit_bar_arithmetic_in_single_truth_case(self):
        """One dot 2 px from one truth: the local marginal terms happen to match.

        Here TPw = self-credit = k = 1/3, S = 1, FPw = S-self-credit = 2/3,
        and FNw = |G|-TPw = 2/3. The denominator is 1, so DTI = 1/3. This
        example does not justify substituting FPw=S-TPw for arbitrary rasters.
        """
        t = np.zeros((60, 60), dtype=bool)
        t[30, 30] = True
        p = np.zeros((60, 60))
        p[30, 32] = 1.0
        r = metric.dti(p, t)
        k = 1.0 - 2.0 / 3.0
        self.assertAlmostEqual(r.tpw, k, places=12)
        self.assertAlmostEqual(r.mass, 1.0, places=12)
        self.assertAlmostEqual(r.self_credit, k, places=12)
        self.assertAlmostEqual(r.fpw, 2.0 / 3.0, places=12)
        self.assertAlmostEqual(r.fnw, 2.0 / 3.0, places=12)
        # DTI = k/(1 + eps) -- the official denominator's "+ eps" again
        self.assertAlmostEqual(r.dti, k / (1.0 + metric.EPS), places=15)
        self.assertAlmostEqual(metric.credit_bar(r.dti), 0.2 * k / (1.0 + metric.EPS), places=15)
        self.assertGreater(1.0, metric.credit_bar(r.dti))

        better = p.copy()
        better[30, 30] = 1.0
        self.assertGreater(metric.dti(better, t).dti, r.dti)

    def test_a_dot_that_earns_nothing_is_refused_by_the_bar(self):
        """At 3 px the kernel weight is exactly 0, and the bar is positive."""
        t = np.zeros((60, 60), dtype=bool)
        t[30, 30] = True
        p = np.zeros((60, 60))
        p[30, 30] = 1.0
        cur = metric.dti(p, t).dti
        self.assertGreater(metric.credit_bar(cur), 0.0)
        k_available = max(1.0 - 300.0 / 300.0, 0.0)
        self.assertLessEqual(k_available, metric.credit_bar(cur))
        worse = p.copy()
        worse[30, 33] = 1.0
        self.assertLess(metric.dti(worse, t).dti, cur)

    def test_conditional_single_pixel_derivative_identity(self):
        """Verify the local rational identity when delta TP=self-credit=k.

        The denominator increment is alpha*v only under that restricted
        one-variable condition; the official metric does not imply it generally.
        """
        T0, D0, k = 3.0, 9.0, 0.5
        dti_val = T0 / D0
        for v in (0.0, 0.25, 0.5, 1.0):
            # numeric derivative of the exact rational expression
            h = 1e-6
            f = lambda x: (T0 + x * k) / (D0 + 0.2 * x)  # noqa: E731
            num = (f(v + h) - f(v - h)) / (2 * h)
            expected_sign = np.sign(k - metric.ALPHA * dti_val)
            self.assertEqual(np.sign(num), expected_sign)
        self.assertEqual(
            metric.optimal_value_is_binary(),
            "conditional local endpoint result only; global binary optimality is not established",
        )


class TestFootprintHandling(unittest.TestCase):
    def test_outside_footprint_mass_is_ignored(self):
        t = np.zeros((20, 20), dtype=bool)
        t[5, 5] = True
        fp = np.zeros((20, 20), dtype=bool)
        fp[0:10, 0:10] = True
        p = np.zeros((20, 20))
        p[5, 5] = 1.0
        p[15, 15] = 1.0  # outside the footprint
        r_in = metric.dti(p, t, footprint=fp)
        r_all = metric.dti(p, t)
        self.assertAlmostEqual(r_in.mass, 1.0)
        self.assertAlmostEqual(r_all.mass, 2.0)
        self.assertGreater(r_in.dti, r_all.dti)

    def test_footprint_is_used_for_truth_too(self):
        t = np.zeros((20, 20), dtype=bool)
        t[15, 15] = True  # outside the footprint
        fp = np.zeros((20, 20), dtype=bool)
        fp[0:10, 0:10] = True
        r = metric.dti(np.ones((20, 20)), t, footprint=fp)
        self.assertEqual(r.n_truth, 0)


if __name__ == "__main__":
    unittest.main()
