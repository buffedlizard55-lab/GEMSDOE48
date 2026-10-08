"""Retired live-anchor inversion — INVALIDATED, forensic opt-in only.

The old anchor model treated ``FPw`` as ``S - TPw`` and inferred a hidden truth
count, numerator, break-even bar, and removal budget from owner-reported live
scores. That substitution is **not** a general identity under the official
metric: ``FPw = sum_x p(x) * (1 - max_g k(d(x,g)))``, while ``TPw`` sums a
per-truth-pixel maximum. The two totals need not match. The score rows also lack
organizer receipts linking local bytes to leaderboard entries.

The calculations below are retained only to reproduce historical diagnostics.
They raise unless ``legacy_audit_only=True`` is explicitly supplied, and all
returned values carry an invalidated/forensic-only status. Never use them as a
score estimate, promotion gate, truth-density estimate, or evidence of a local
file's leaderboard attribution.
"""

from __future__ import annotations

from dataclasses import dataclass

ALPHA = 0.2
INVALID_STATUS = "INVALIDATED_FORENSIC_ONLY_DO_NOT_USE_FOR_PROMOTION"
INVALIDATION_REASON = (
    "The historical inversion substitutes FPw=S-TPw, which is not a general "
    "identity under the official metric; local-file/leaderboard linkage is also unverified."
)


@dataclass
class LiveAnchor:
    """Historical owner-reported anchors; arithmetic requires forensic opt-in.

    ``truth_px`` is the old inversion-derived assumed value, not an observed or
    estimated private-label count. It remains only to reproduce the old receipt.
    """

    s_big: float = 0.2600  # owner-reported score; local bytes not linked by receipt
    n_big: int = 44090
    s_small: float = 0.2708  # owner-reported score; local bytes not linked by receipt
    n_small: int = 40199
    truth_px: int = 12632  # historical surrogate input; not a hidden-truth estimate
    legacy_audit_only: bool = False

    def _require_legacy_audit_only(self) -> None:
        if not self.legacy_audit_only:
            raise RuntimeError(
                "invalidated live-anchor inversion; construct LiveAnchor(legacy_audit_only=True) "
                "only for forensic reproduction"
            )

    def invert(self) -> dict:
        """Reproduce the invalid historical inversion for forensic comparison only."""
        self._require_legacy_audit_only()
        dn = self.n_big - self.n_small
        t_small = self.s_small * (ALPHA * self.n_small + (1 - ALPHA) * self.truth_px)
        t_big = self.s_big * (ALPHA * self.n_big + (1 - ALPHA) * self.truth_px)
        budget = self.s_small * ALPHA * dn
        return {
            "validity_status": INVALID_STATUS,
            "invalidation_reason": INVALIDATION_REASON,
            "dn_removed": dn,
            "assumed_truth_px_invalidated": self.truth_px,
            "implied_tpw_from_small_invalidated": t_small,
            "implied_tpw_from_big_invalidated": t_big,
            "tpw_consistency_rel_invalidated": abs(t_big - t_small) / t_small,
            "implied_credit_per_dot_invalidated": t_small / self.n_small,
            "break_even_bar_tau_live_invalidated": ALPHA * self.s_small,
            "credit_loss_budget_numerator_units_invalidated": budget,
        }

    def assess_removal(self, n_removed: int, measured_credit_loss: float = 0.0) -> dict:
        """Reproduce the retired removal heuristic; it is not a promotion gate."""
        self._require_legacy_audit_only()
        budget = self.s_small * ALPHA * n_removed
        cost = measured_credit_loss
        safety = float("inf") if cost <= 0 else budget / cost
        if cost <= 0:
            safety = 99.0  # historical encoding; not evidence of a safe removal
        return {
            "validity_status": INVALID_STATUS,
            "invalidation_reason": INVALIDATION_REASON,
            "n_removed": int(n_removed),
            "budget_invalidated": budget,
            "measured_credit_loss_proxy": cost,
            "safety_invalidated": safety,
            "tau_live_invalidated": ALPHA * self.s_small,
            "legacy_rule_passes_not_promotion": safety >= 2.0,
        }
