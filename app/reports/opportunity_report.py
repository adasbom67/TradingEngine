from __future__ import annotations

from app.models.market.price_snapshot import PriceSnapshot
from app.models.trades.trade_candidate import TradeCandidate


class OpportunityReport:
    """Create concise, decision-oriented trade recommendations."""

    def format_candidate(
        self,
        candidate: TradeCandidate,
        snapshot: PriceSnapshot | None = None,
    ) -> str:
        spread = candidate.spread
        short_put = spread.short_put
        long_put = spread.long_put

        symbol = snapshot.symbol if snapshot else self._underlying(short_put.symbol)
        lines = [
            f"{symbol} Bull Put Credit Spread",
            f"Decision: {candidate.decision}",
        ]
        if snapshot:
            lines.append(f"Underlying: ${snapshot.current_price:.2f}")
        lines.extend([
            f"Market regime: {candidate.market_regime.replace('_', ' ').title()}",
            f"Expiration: {short_put.expiration_date}",
            f"Sell {short_put.strike:g} Put / Buy {long_put.strike:g} Put",
            f"Spread width: ${spread.width:.2f}",
            f"Credit: ${spread.credit:.2f}",
            f"Max profit: ${spread.max_profit:.2f}",
            f"Max risk: ${spread.max_loss:.2f}",
            f"Breakeven: ${spread.breakeven:.2f}",
            f"Return on risk: {candidate.return_on_risk:.1%}",
            f"Estimated probability of profit: {candidate.probability_of_profit:.1%}",
            f"Managed expected value: ${candidate.managed_expected_value:.2f}",
            f"Expiration max-loss expected value: ${candidate.unmanaged_expected_value:.2f}",
            f"Profit target amount: ${candidate.profit_target_amount:.2f}",
            f"Stop-loss amount: ${candidate.stop_loss_amount:.2f}",
            f"Overall score: {candidate.score:.1f}/100",
            f"Trade quality score: {candidate.score:.1f}/100",
            f"Rank: {candidate.rank}",
        ])
        if candidate.maximum_quantity:
            lines.append(f"Maximum approved quantity: {candidate.maximum_quantity}")
        if candidate.decision_reasons:
            lines.append("Decision rationale:")
            lines.extend(f"- {reason}" for reason in candidate.decision_reasons)
        if candidate.score_breakdown:
            lines.append("Score breakdown:")
            lines.extend(
                f"- {name}: {score:.1f}/100"
                for name, score in candidate.score_breakdown.items()
            )
        if candidate.reasons:
            lines.append("Reasons:")
            lines.extend(f"- {reason}" for reason in candidate.reasons)
        if candidate.warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in candidate.warnings)

        lines.append(
            "Probability and expected value are delta-based screening estimates, "
            "not guarantees of profit."
        )
        return "\n".join(lines)

    def format_ranked(
        self,
        candidates: list[TradeCandidate],
        snapshot: PriceSnapshot | None = None,
        limit: int = 5,
    ) -> str:
        if limit <= 0:
            raise ValueError("Report limit must be greater than zero.")
        if not candidates:
            return "No qualifying bull put spread candidates found."
        return "\n\n".join(
            self.format_candidate(candidate, snapshot)
            for candidate in candidates[:limit]
        )

    def format_summary(
        self,
        candidates_by_symbol: dict[str, list[TradeCandidate]],
    ) -> str:
        """Format one-line best-candidate summaries for a watchlist."""
        lines = ["Watchlist Summary"]
        for symbol, candidates in candidates_by_symbol.items():
            if not candidates:
                lines.append(f"{symbol:<6} PASS   No qualifying candidates")
                continue
            best = candidates[0]
            spread = best.spread
            lines.append(
                f"{symbol:<6} {best.decision:<5} "
                f"Score {best.score:5.1f}  "
                f"{spread.short_put.strike:g}/{spread.long_put.strike:g}  "
                f"Credit ${spread.credit:.2f}  "
                f"Managed EV ${best.managed_expected_value:.2f}"
            )
        return "\n".join(lines)

    @staticmethod
    def _underlying(option_symbol: str) -> str:
        return option_symbol.strip().split()[0] or "UNKNOWN"
