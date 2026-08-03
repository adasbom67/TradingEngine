from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models.trades.trade_candidate import TradeCandidate
from app.trading.models import AssetType, Instruction, OrderLeg, OrderPlan, OrderSide


class BullPutOrderPlanBuilder:
    def build_entry(self, candidate: TradeCandidate, *, quantity: int = 1) -> OrderPlan:
        if quantity <= 0:
            raise ValueError("quantity must be greater than zero.")
        spread = candidate.spread
        short = spread.short_put
        long = spread.long_put
        return OrderPlan(
            plan_id=str(uuid4()),
            symbol=short.symbol.strip().upper(),
            quantity=quantity,
            side=OrderSide.CREDIT,
            limit_price=round(spread.credit, 2),
            duration="DAY",
            session="NORMAL",
            created_at=datetime.now(timezone.utc),
            source_candidate_score=candidate.score,
            source_decision=candidate.decision,
            legs=(
                OrderLeg(
                    symbol=self._option_symbol(short.symbol, short.expiration_date, short.strike),
                    asset_type=AssetType.OPTION,
                    instruction=Instruction.SELL_TO_OPEN,
                    quantity=quantity,
                    underlying=short.symbol.strip().upper(),
                    expiration=short.expiration_date,
                    strike=short.strike,
                ),
                OrderLeg(
                    symbol=self._option_symbol(long.symbol, long.expiration_date, long.strike),
                    asset_type=AssetType.OPTION,
                    instruction=Instruction.BUY_TO_OPEN,
                    quantity=quantity,
                    underlying=long.symbol.strip().upper(),
                    expiration=long.expiration_date,
                    strike=long.strike,
                ),
            ),
            metadata={"strategy": "BULL_PUT_CREDIT_SPREAD"},
        )

    @staticmethod
    def _option_symbol(underlying: str, expiration, strike: float) -> str:
        root = underlying.strip().upper()
        strike_code = f"{int(round(strike * 1000)):08d}"
        return f"{root}  {expiration:%y%m%d}P{strike_code}"
