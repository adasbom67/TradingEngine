from math import isclose

from app.config.strategy_config import PutSpreadConfig
from app.models.market.option_contract import OptionContract
from app.models.trades.bull_put_spread import BullPutSpread
from app.models.trades.trade_candidate import TradeCandidate


class BullPutSpreadBuilder:
    """Construct valid bull put spread candidates from eligible puts."""

    def build(
        self,
        puts: list[OptionContract],
        config: PutSpreadConfig,
    ) -> list[TradeCandidate]:
        config.validate()
        candidates: list[TradeCandidate] = []

        for short_put in puts:
            for long_put in puts:
                if not self._same_expiration(short_put, long_put):
                    continue
                if long_put.strike >= short_put.strike:
                    continue

                width = short_put.strike - long_put.strike
                if not self._allowed_width(width, config.allowed_spread_widths):
                    continue

                spread = BullPutSpread(short_put=short_put, long_put=long_put)
                if spread.credit < config.minimum_credit:
                    continue
                if spread.credit <= 0 or spread.credit >= spread.width:
                    continue
                if spread.max_loss > config.maximum_risk_per_trade:
                    continue

                candidates.append(TradeCandidate(spread=spread))

        return sorted(
            candidates,
            key=lambda candidate: (
                candidate.spread.short_put.expiration_date,
                -candidate.spread.short_put.strike,
                candidate.spread.width,
            ),
        )

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
