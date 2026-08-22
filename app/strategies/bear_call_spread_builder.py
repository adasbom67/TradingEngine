from math import isclose

from app.config.strategy_config import PutSpreadConfig
from app.evaluation.pipeline_diagnostics import PipelineDiagnostics
from app.models.market.option_contract import OptionContract
from app.models.trades.bear_call_spread import BearCallSpread
from app.models.trades.trade_candidate import TradeCandidate


class BearCallSpreadBuilder:
    """Build short lower-strike calls hedged by higher-strike long calls."""

    def build(
        self,
        calls: list[OptionContract],
        config: PutSpreadConfig,
        *,
        long_calls: list[OptionContract] | None = None,
    ) -> list[TradeCandidate]:
        candidates, _ = self.build_with_diagnostics(
            calls, config, long_calls=long_calls
        )
        return candidates

    def build_with_diagnostics(
        self,
        calls: list[OptionContract],
        config: PutSpreadConfig,
        diagnostics: PipelineDiagnostics | None = None,
        *,
        long_calls: list[OptionContract] | None = None,
    ) -> tuple[list[TradeCandidate], PipelineDiagnostics]:
        config.validate()
        diagnostics = diagnostics or PipelineDiagnostics(strategy_type="BEAR_CALL")
        diagnostics.strategy_type = "BEAR_CALL"
        candidates: list[TradeCandidate] = []
        hedge_universe = calls if long_calls is None else long_calls

        for short_call in calls:
            for long_call in hedge_universe:
                diagnostics.pair_attempts += 1
                if short_call.expiration_date != long_call.expiration_date:
                    diagnostics.increment_builder_rejection("different_expiration")
                    continue
                diagnostics.same_expiration_pairs += 1
                if long_call.strike <= short_call.strike:
                    diagnostics.increment_builder_rejection("invalid_strike_order")
                    continue
                diagnostics.ordered_strike_pairs += 1
                width = long_call.strike - short_call.strike
                if not any(isclose(width, allowed, abs_tol=1e-9) for allowed in config.allowed_spread_widths):
                    diagnostics.increment_builder_rejection("spread_width_not_allowed")
                    continue
                diagnostics.allowed_width_pairs += 1

                spread = BearCallSpread(short_call=short_call, long_call=long_call)
                if spread.credit < config.minimum_credit:
                    diagnostics.increment_builder_rejection("credit_below_minimum")
                    continue
                diagnostics.minimum_credit_pairs += 1
                if spread.credit <= 0:
                    diagnostics.increment_builder_rejection("non_positive_credit")
                    continue
                if spread.credit >= spread.width:
                    diagnostics.increment_builder_rejection("credit_not_below_width")
                    continue
                diagnostics.valid_credit_pairs += 1
                if spread.max_loss > config.maximum_risk_per_trade:
                    diagnostics.increment_builder_rejection("maximum_risk_exceeded")
                    continue
                diagnostics.risk_approved_pairs += 1
                candidates.append(TradeCandidate(spread=spread))

        diagnostics.candidates_built = len(candidates)
        candidates.sort(
            key=lambda candidate: (
                candidate.spread.short_call.expiration_date,
                candidate.spread.short_call.strike,
                candidate.spread.width,
            )
        )
        return candidates, diagnostics
