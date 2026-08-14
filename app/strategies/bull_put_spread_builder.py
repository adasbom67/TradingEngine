from math import isclose

from app.config.strategy_config import PutSpreadConfig
from app.evaluation.pipeline_diagnostics import PipelineDiagnostics
from app.models.market.option_contract import OptionContract
from app.models.trades.bull_put_spread import BullPutSpread
from app.models.trades.trade_candidate import TradeCandidate


class BullPutSpreadBuilder:
    """Construct valid bull put spread candidates from eligible puts."""

    def build(
        self,
        puts: list[OptionContract],
        config: PutSpreadConfig,
        *,
        long_puts: list[OptionContract] | None = None,
    ) -> list[TradeCandidate]:
        candidates, _ = self.build_with_diagnostics(
            puts, config, long_puts=long_puts
        )
        return candidates

    def build_with_diagnostics(
        self,
        puts: list[OptionContract],
        config: PutSpreadConfig,
        diagnostics: PipelineDiagnostics | None = None,
        *,
        long_puts: list[OptionContract] | None = None,
    ) -> tuple[list[TradeCandidate], PipelineDiagnostics]:
        config.validate()
        diagnostics = diagnostics or PipelineDiagnostics()
        candidates: list[TradeCandidate] = []

        hedge_universe = puts if long_puts is None else long_puts
        for short_put in puts:
            for long_put in hedge_universe:
                diagnostics.pair_attempts += 1
                if not self._same_expiration(short_put, long_put):
                    diagnostics.increment_builder_rejection("different_expiration")
                    continue
                diagnostics.same_expiration_pairs += 1
                if long_put.strike >= short_put.strike:
                    diagnostics.increment_builder_rejection("invalid_strike_order")
                    continue
                diagnostics.ordered_strike_pairs += 1

                width = short_put.strike - long_put.strike
                if not self._allowed_width(width, config.allowed_spread_widths):
                    diagnostics.increment_builder_rejection("spread_width_not_allowed")
                    continue
                diagnostics.allowed_width_pairs += 1

                spread = BullPutSpread(short_put=short_put, long_put=long_put)
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
                candidate.spread.short_put.expiration_date,
                -candidate.spread.short_put.strike,
                candidate.spread.width,
            ),
        )
        return candidates, diagnostics

    @staticmethod
    def _same_expiration(
        short_put: OptionContract,
        long_put: OptionContract,
    ) -> bool:
        return short_put.expiration_date == long_put.expiration_date

    @staticmethod
    def _allowed_width(
        width: float,
        allowed_widths: tuple[float, ...],
    ) -> bool:
        return any(isclose(width, allowed, abs_tol=1e-9) for allowed in allowed_widths)
