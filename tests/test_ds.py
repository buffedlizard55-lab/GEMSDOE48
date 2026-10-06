"""Dempster-Shafer algebra, verified against closed forms.

Every expected number here is derived by hand in the docstring of the test that
uses it, from Dempster's rule of combination (Dempster 1967; Shafer 1976, ch. 3)
applied to the two-sided simple support function

    m({F}) = a * b,  m({notF}) = a * (1 - b),  m(Theta) = 1 - a

with `a` the Shafer (1976) sec. 11.2 discount and `b` the detector's belief that
a fault is present at this pixel.  The three masses sum to 1 for every pixel by
construction, which is itself asserted.
"""
from __future__ import annotations

import unittest

import numpy as np

import conftest  # noqa: F401  (path bootstrap)
from gemsdoe48 import ds


class TestMassFunction(unittest.TestCase):
    def test_masses_sum_to_one_everywhere(self):
        b = np.linspace(0.0, 1.0, 101).reshape(1, -1)
        for a in (0.05, 0.6, 1.0):
            m = ds.mass_function(b, a)
            np.testing.assert_allclose(m.sum(axis=0), 1.0, atol=1e-15)

    def test_components(self):
        b = np.array([[0.25]])
        m = ds.mass_function(b, 0.6)
        self.assertAlmostEqual(m[ds.NF, 0, 0], 0.15)
        self.assertAlmostEqual(m[ds.NN, 0, 0], 0.45)
        self.assertAlmostEqual(m[ds.NT, 0, 0], 0.40)

    def test_belief_is_clipped(self):
        b = np.array([[-3.0, 2.0]])
        m = ds.mass_function(b, 1.0)
        self.assertAlmostEqual(m[ds.NF, 0, 0], 0.0)
        self.assertAlmostEqual(m[ds.NF, 0, 1], 1.0)

    def test_reliability_bounds(self):
        b = np.array([[0.5]])
        for bad in (0.0, -0.1, 1.5):
            with self.assertRaises(ValueError):
                ds.mass_function(b, bad)
        ds.mass_function(b, 1.0)  # 1.0 is legal


class TestWorkedExamples(unittest.TestCase):
    """The three exact numbers quoted in the repository documentation."""

    A = 0.6

    def test_full_agreement_bel_084_theta_016(self):
        """b1 = b2 = 1, a = 0.6.

        m_i(F) = 0.6, m_i(notF) = 0, m_i(Theta) = 0.4.
        K = 0.6*0 + 0*0.6 = 0.
        m12(F) = 0.6*0.6 + 0.6*0.4 + 0.4*0.6 = 0.36 + 0.24 + 0.24 = 0.84.
        m12(Theta) = 0.4*0.4 / (1 - 0) = 0.16.
        """
        r = ds.combine_pair(np.array([[1.0]]), np.array([[1.0]]), self.A, self.A)
        self.assertAlmostEqual(r.conflict[0, 0], 0.0, places=15)
        self.assertAlmostEqual(r.bel_F[0, 0], 0.84, places=15)
        self.assertAlmostEqual(r.m_theta[0, 0], 0.16, places=15)

    def test_total_disagreement_bel_0375_K_036_theta_025(self):
        """b1 = 1, b2 = 0, a = 0.6.

        m1(F) = 0.6, m1(notF) = 0,  m1(Theta) = 0.4
        m2(F) = 0,   m2(notF) = 0.6, m2(Theta) = 0.4
        K = 0.6*0.6 + 0*0 = 0.36;  1 - K = 0.64.
        m12(F)     = (0 + 0.6*0.4 + 0.4*0) / 0.64 = 0.24 / 0.64 = 0.375.
        m12(Theta) = (0.4 * 0.4)         / 0.64 = 0.16 / 0.64 = 0.25.
        """
        r = ds.combine_pair(np.array([[1.0]]), np.array([[0.0]]), self.A, self.A)
        self.assertAlmostEqual(r.conflict[0, 0], 0.36, places=15)
        self.assertAlmostEqual(r.bel_F[0, 0], 0.375, places=15)
        self.assertAlmostEqual(r.m_theta[0, 0], 0.25, places=15)

    def test_total_disagreement_is_the_maximum_conflict(self):
        """K = a1*a2*[b1(1-b2) + (1-b1)b2], maximised at (b1,b2) = (1,0) => a1*a2."""
        b1 = np.linspace(0, 1, 51).reshape(1, -1)
        b2 = np.linspace(0, 1, 51).reshape(-1, 1)
        r = ds.combine_pair(np.broadcast_to(b1, (51, 51)), np.broadcast_to(b2, (51, 51)),
                            self.A, self.A)
        self.assertAlmostEqual(r.conflict.max(), self.A * self.A, places=12)

    def test_half_belief_both_sides_bel_04024(self):
        """b1 = b2 = 0.5, a = 0.6.

        m_i(F) = m_i(notF) = 0.3, m_i(Theta) = 0.4.
        K = 0.3*0.3 + 0.3*0.3 = 0.18;  1 - K = 0.82.
        m12(F) = (0.09 + 0.12 + 0.12) / 0.82 = 0.33 / 0.82 = 0.402439024...
        """
        r = ds.combine_pair(np.array([[0.5]]), np.array([[0.5]]), self.A, self.A)
        self.assertAlmostEqual(r.conflict[0, 0], 0.18, places=15)
        self.assertAlmostEqual(r.bel_F[0, 0], 0.33 / 0.82, places=15)
        self.assertAlmostEqual(r.bel_F[0, 0], 0.4024390243902439, places=15)


class TestAlgebraicProperties(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(42)
        self.b1 = rng.random((40, 40))
        self.b2 = rng.random((40, 40))

    def test_masses_sum_to_one_after_combination(self):
        r = ds.combine_pair(self.b1, self.b2, 0.6, 0.6)
        total = r.m_F + r.m_notF + r.m_theta
        np.testing.assert_allclose(total, 1.0, atol=1e-12)

    def test_commutative(self):
        ab = ds.combine_pair(self.b1, self.b2, 0.6, 0.7)
        ba = ds.combine_pair(self.b2, self.b1, 0.7, 0.6)
        np.testing.assert_allclose(ab.m_F, ba.m_F, atol=1e-14)
        np.testing.assert_allclose(ab.m_notF, ba.m_notF, atol=1e-14)
        np.testing.assert_allclose(ab.m_theta, ba.m_theta, atol=1e-14)
        np.testing.assert_allclose(ab.conflict, ba.conflict, atol=1e-14)

    def test_associative_across_three_sources(self):
        b3 = np.random.default_rng(7).random((40, 40))
        m1 = ds.mass_function(self.b1, 0.6)
        m2 = ds.mass_function(self.b2, 0.7)
        m3 = ds.mass_function(b3, 0.55)
        left = ds.combine_two(ds.result_to_mass(ds.combine_two(m1, m2)), m3)
        right = ds.combine_two(m1, ds.result_to_mass(ds.combine_two(m2, m3)))
        np.testing.assert_allclose(left.m_F, right.m_F, atol=1e-12)
        np.testing.assert_allclose(left.m_theta, right.m_theta, atol=1e-12)

    def test_reliability_one_and_no_conflict_reduces_to_normalised_product(self):
        """a1 = a2 = 1: m = b1 b2 / [b1 b2 + (1 - b1)(1 - b2)], i.e. Bayes."""
        for b1v, b2v in ((0.9, 0.2), (0.5, 0.5), (1.0, 1.0), (0.0, 0.0)):
            b1 = np.array([[b1v]])
            b2 = np.array([[b2v]])
            r = ds.combine_pair(b1, b2, 1.0, 1.0)
            num = b1v * b2v
            den = b1v * b2v + (1 - b1v) * (1 - b2v)
            if den == 0:
                continue
            self.assertAlmostEqual(r.bel_F[0, 0], num / den, places=12)
            self.assertAlmostEqual(r.m_theta[0, 0], 0.0, places=15)

    def test_null_source_leaves_the_other_unchanged(self):
        """A source with b = 0.5 and a = 1 is uninformative: m(F) = m(notF) = 0.5,
        so K = 0.5*m2(notF) + 0.5*m2(F) = 0.5 and the normalised result is m2."""
        b2 = np.array([[0.8]])
        r = ds.combine_pair(np.array([[0.5]]), b2, 1.0, 1.0)
        self.assertAlmostEqual(r.bel_F[0, 0], 0.8, places=12)

    def test_belief_never_exceeds_plausibility(self):
        r = ds.combine_pair(self.b1, self.b2, 0.6, 0.6)
        self.assertTrue(np.all(r.bel_F <= r.pl_F + 1e-15))
        np.testing.assert_allclose(r.pl_F, r.bel_F + r.m_theta, atol=1e-15)

    def test_result_stays_in_unit_interval(self):
        r = ds.combine_pair(self.b1, self.b2, 0.6, 0.6)
        for arr in (r.m_F, r.m_notF, r.m_theta, r.conflict, r.bel_F, r.pl_F):
            self.assertGreaterEqual(float(arr.min()), -1e-15)
            self.assertLessEqual(float(arr.max()), 1.0 + 1e-15)

    def test_m_theta_is_monotone_in_conflict(self):
        """At fixed a, m12(Theta) = m1(Theta) m2(Theta) / (1 - K) rises with K."""
        b1 = np.linspace(0.0, 1.0, 200)
        b2 = np.linspace(1.0, 0.0, 200)
        r = ds.combine_pair(b1.reshape(1, -1), b2.reshape(1, -1), 0.6, 0.6)
        order = np.argsort(r.conflict[0])
        theta = r.m_theta[0][order]
        self.assertTrue(np.all(np.diff(theta) >= -1e-12))

    def test_equal_belief_is_not_idempotent_and_is_deflationary(self):
        """Dempster's rule is NOT idempotent, and with a discount it deflates.

        For b1 = b2 = b and a1 = a2 = a:
            K      = 2 a^2 b (1 - b)
            Bel    = [a^2 b^2 + 2 a b (1 - a)] / (1 - K)
        At b = 1 this is the 0.84 of the worked example, i.e. below 1; at b = 0.5
        it is 0.402439, i.e. below 0.5.  Combining two equally-discounted and
        identical opinions therefore moves belief *towards* the frame, never away
        from it.  That is the behaviour the submission's m(Theta) layer exposes,
        so the direction is asserted here rather than assumed.
        """
        b = np.linspace(0.0, 1.0, 101)
        r = ds.combine_pair(b.reshape(1, -1), b.reshape(1, -1), 0.6, 0.6)
        bel = r.bel_F[0]
        self.assertFalse(np.allclose(bel, b))
        # monotone increasing in b ...
        self.assertTrue(np.all(np.diff(bel) >= -1e-12))
        # ... and never above b (equality only at b = 0)
        self.assertTrue(np.all(bel <= b + 1e-12))
        self.assertAlmostEqual(bel[0], 0.0, places=15)
        self.assertAlmostEqual(bel[-1], 0.84, places=15)
        # closed form, checked at a few points including b = 0.5
        for bv in (0.25, 0.5, 0.75, 1.0):
            K = 2 * 0.36 * bv * (1 - bv)
            want = (0.36 * bv * bv + 2 * 0.6 * bv * 0.4) / (1 - K)
            self.assertAlmostEqual(
                float(ds.combine_pair(np.array([[bv]]), np.array([[bv]]), 0.6, 0.6).bel_F[0, 0]),
                want, places=12)

    def test_shape_mismatch_and_bad_shape_rejected(self):
        with self.assertRaises(ValueError):
            ds.combine_two(np.zeros((2, 5, 5)), np.zeros((2, 5, 5)))

    def test_total_conflict_falls_back_and_does_not_divide_by_zero(self):
        m1 = np.zeros((3, 2, 2))
        m2 = np.zeros((3, 2, 2))
        m1[ds.NF] = 1.0
        m2[ds.NN] = 1.0
        r = ds.combine_two(m1, m2)  # K = 1 everywhere
        self.assertTrue(np.isfinite(r.m_F).all())
        self.assertTrue(np.isfinite(r.m_theta).all())
        np.testing.assert_allclose(r.m_theta, 0.0, atol=1e-9)


class TestAgainstNaiveMean(unittest.TestCase):
    """What DS adds over an average, measured rather than asserted."""

    def setUp(self):
        rng = np.random.default_rng(0)
        self.b1 = rng.random((60, 60))
        self.b2 = rng.random((60, 60))

    def test_values_differ(self):
        r = ds.combine_pair(self.b1, self.b2, 0.6, 0.6)
        mean = ds.naive_mean(self.b1, self.b2)
        self.assertGreater(float(np.abs(r.bel_F - mean).mean()), 0.01)

    def test_on_the_union_support_ranking_is_monotone_in_the_other_belief(self):
        """The honest statement: on pixels where one family is 1, Bel is monotone
        in the other family's belief, so the *ranking* matches the mean's."""
        b2 = np.linspace(0.0, 1.0, 400).reshape(1, -1)
        b1 = np.ones_like(b2)
        r = ds.combine_pair(b1, b2, 0.6, 0.6)
        self.assertTrue(np.all(np.diff(r.bel_F[0]) >= -1e-12))
        from scipy.stats import spearmanr

        rho = spearmanr(r.bel_F[0], ds.naive_mean(b1, b2)[0]).statistic
        self.assertAlmostEqual(rho, 1.0, places=12)

    def test_ds_is_not_the_mean_and_is_not_a_rescaled_mean(self):
        r = ds.combine_pair(self.b1, self.b2, 0.6, 0.6)
        mean = ds.naive_mean(self.b1, self.b2)
        # no affine map of the mean reproduces Bel
        A = np.stack([mean.ravel(), np.ones(mean.size)], axis=1)
        coef, *_ = np.linalg.lstsq(A, r.bel_F.ravel(), rcond=None)
        resid = r.bel_F.ravel() - A @ coef
        self.assertGreater(float(np.abs(resid).max()), 1e-3)

    def test_conflict_and_mtheta_have_no_counterpart_in_an_average(self):
        r = ds.combine_pair(self.b1, self.b2, 0.6, 0.6)
        mean = ds.naive_mean(self.b1, self.b2)
        # both diagnostic layers carry variation the mean cannot express
        for layer in (r.conflict, r.m_theta):
            self.assertGreater(float(layer.std()), 0.0)
            A = np.stack([mean.ravel(), np.ones(mean.size)], axis=1)
            coef, *_ = np.linalg.lstsq(A, layer.ravel(), rcond=None)
            self.assertGreater(float(np.abs(layer.ravel() - A @ coef).max()), 1e-3)

    def test_result_to_mass_round_trip(self):
        r = ds.combine_pair(self.b1, self.b2, 0.6, 0.6)
        m = ds.result_to_mass(r)
        self.assertEqual(m.shape, (3, 60, 60))
        np.testing.assert_allclose(m.sum(axis=0), 1.0, atol=1e-12)

    def test_weighted_mean_extremes(self):
        a = ds.weighted_mean(self.b1, self.b2, 1.0)
        np.testing.assert_allclose(a, self.b1)
        a = ds.weighted_mean(self.b1, self.b2, 0.0)
        np.testing.assert_allclose(a, self.b2)


if __name__ == "__main__":
    unittest.main()
