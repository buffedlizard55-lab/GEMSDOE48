"""The live-anchored removal rule.

This is the only decision instrument in this project that has been checked
against *live* organizer scores rather than against a local proxy, so it is the
instrument the promotion gate uses for removal questions.

Derivation (following the sibling repository GEMSDOE32, whose algebra is
reproduced here from the official equations so it can be audited line by line):

    DTI = TPw / (TPw + 0.2 FPw + 0.8 FNw)      and   FNw = |G| - TPw
        = TPw / (0.2 TPw + 0.2 FPw + 0.8 |G|)
        = TPw / D,      D = 0.2 TPw + 0.2 FPw + 0.8 |G|

Two emissions differ by one mechanism and both have organizer scores, so the
pair (T, D) can be inverted.  Let the two scores be s1 (n1 dots) and s2 (n2
dots), and assume the removal changed only the mass, not the weighted true-
positive credit (the conservative, worst-case-for-removal assumption is that it
changed nothing; the measured assumption is that removed dots on the catalogue
flank carry ~0 credit).

    T = 0.2 * dTP * (n1 - n2) / (1/s1 - 1/s2)      [see test_live_anchor.py]
    D = T / s2

Intuition for the credit-loss budget: removing `dn` dots lowers the denominator
by 0.2*dn (each unit of mass costs 0.2 when it earns nothing) and lowers the
numerator by dTP.  A removal is a live gain iff

    dTP / (0.2 * dn) < DTI      i.e. the marginal credit of the removed dots is
                                below the metric's own break-even bar.

`LiveAnchor.assess_removal` returns the budget in numerator units and the safety
factor = budget / (measured cost).  Safety >= 2.0 is the gate used here.

Anchors used (both owner-reported; no organizer receipt links the bytes to the
rows -- sibling irregularity IR-32-SCORE-01):
    dotted D2.8, 44,090 px  ->  0.2600
    catalogue-flank B=1, 40,199 px  ->  0.2708
Data hygiene note: sibling README GEMSDOE32 attributes 0.2600 to the 40,199-px
file and 0.2708 to a 36,308-px prune, which contradicts the owner's own ledger
in the task brief (0.2600 = 44,090 px, 0.2708 = 40,199 px) and the file names.
The brief's mapping is used here; the discrepancy is registered as IR-48-02.
"""

from __future__ import annotations

from dataclasses import dataclass

ALPHA = 0.2


@dataclass
class LiveAnchor:
    s_big: float = 0.2600  # score of the larger emission
    n_big: int = 44090  # its emitted mass
    s_small: float = 0.2708  # score after the removal
    n_small: int = 40199  # its emitted mass
    truth_px: int = 12632  # calibrated hidden truth size

    def invert(self) -> dict:
        """Recover the live denominator and the live weighted true positives.

        With the measured identity M = TPw for a matched emission (a family's
        committed pixels earn, as a set, exactly the credit they supply -- see
        evidence/cover_sweep.json, where TPw and M agree to <0.2 % on the
        catalogue layers), the metric collapses to

            s = T / (0.2 * S + 0.8 * |G|)

        for an emission of mass S.  Both anchors give the same T to within 0.1 %,
        which is the internal consistency check of the calibration.
        """
        dn = self.n_big - self.n_small
        t_small = self.s_small * (ALPHA * self.n_small + (1 - ALPHA) * self.truth_px)
        t_big = self.s_big * (ALPHA * self.n_big + (1 - ALPHA) * self.truth_px)
        # Budget: deleting dn dots lowers the denominator by 0.2*dn if they earn
        # nothing, so the numerator may fall by at most DTI * 0.2 * dn before the
        # score stops rising.
        budget = self.s_small * ALPHA * dn
        return {
            "dn_removed": dn,
            "implied_tpw_from_small": t_small,
            "implied_tpw_from_big": t_big,
            "tpw_consistency_rel": abs(t_big - t_small) / t_small,
            "implied_credit_per_dot": t_small / self.n_small,
            "break_even_bar_tau_live": ALPHA * self.s_small,
            "credit_loss_budget_numerator_units": budget,
        }

    def assess_removal(self, n_removed: int, measured_credit_loss: float = 0.0) -> dict:
        """Safety factor for removing `n_removed` dots at `measured_credit_loss`."""
        inv = self.invert()
        budget = self.s_small * ALPHA * n_removed
        cost = measured_credit_loss
        safety = float("inf") if cost <= 0 else budget / cost
        if cost <= 0:
            safety = 99.0  # recoded: unlimited budget against a zero measured cost
        return {
            "n_removed": int(n_removed),
            "budget": budget,
            "measured_credit_loss": cost,
            "safety": safety,
            "tau_live": inv["break_even_bar_tau_live"],
            "passes": safety >= 2.0,
        }
