from app.models.trades.trade_candidate import TradeCandidate


class CandidateRanker:
    """Rank evaluated candidates using deterministic tie-breakers."""

    def rank(self, candidates: list[TradeCandidate]) -> list[TradeCandidate]:
        decision_priority = {"TRADE": 0, "WATCH": 1, "PASS": 2, "UNDECIDED": 3}
        ranked = sorted(
            candidates,
            key=lambda candidate: (
                decision_priority.get(candidate.decision, 3),
                -candidate.score,
                len(candidate.warnings),
                -candidate.spread.risk_reward_ratio,
                -candidate.spread.credit,
                candidate.spread.max_loss,
                -candidate.spread.short_leg.strike,
            ),
        )

        for index, candidate in enumerate(ranked, start=1):
            candidate.rank = index

        return ranked
