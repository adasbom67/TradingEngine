from __future__ import annotations

from dataclasses import asdict
from math import isfinite

from pydantic import BaseModel, Field, model_validator

from app.backtesting.engine import HistoricalBacktester
from app.backtesting.models import BacktestConfig
from app.brokers.schwab_auth import create_schwab_client
from app.brokers.schwab_market_data import SchwabMarketDataClient


class BacktestRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=10)
    initial_capital: float = Field(gt=0)
    minimum_dte: int = Field(ge=8, le=180)
    maximum_dte: int = Field(ge=8, le=180)
    spread_width: float = Field(gt=0, le=100)
    period_years: int = Field(default=5, ge=2, le=20)

    @model_validator(mode="after")
    def validate_request(self) -> "BacktestRequest":
        self.symbol = self.symbol.strip().upper()
        if not self.symbol:
            raise ValueError("Symbol cannot be blank.")
        if self.maximum_dte < self.minimum_dte:
            raise ValueError(
                "Maximum DTE must be greater than or equal to minimum DTE."
            )
        return self


def run_backtest(request: BacktestRequest) -> dict:
    # The current engine models one representative entry DTE.
    effective_dte = round((request.minimum_dte + request.maximum_dte) / 2)
    exit_dte = min(7, effective_dte - 1)

    config = BacktestConfig(
        initial_capital=request.initial_capital,
        entry_dte=effective_dte,
        exit_dte=exit_dte,
        spread_width=request.spread_width,
    )
    config.validate()

    market_data = SchwabMarketDataClient(create_schwab_client())
    history = market_data.get_daily_price_history(
        request.symbol,
        period_years=request.period_years,
    )
    result = HistoricalBacktester().run(request.symbol, history, config)

    def finite(value: float) -> float | None:
        return value if isfinite(value) else None

    return {
        "configuration": {
            "symbol": result.symbol,
            "initial_capital": request.initial_capital,
            "minimum_dte": request.minimum_dte,
            "maximum_dte": request.maximum_dte,
            "effective_entry_dte": effective_dte,
            "spread_width": request.spread_width,
            "period_years": request.period_years,
            "dte_method": "MIDPOINT_REPRESENTATIVE",
        },
        "summary": {
            "trade_count": len(result.trades),
            "win_rate": result.win_rate,
            "total_pnl": result.total_pnl,
            "ending_capital": result.ending_capital,
            "average_pnl": result.average_pnl,
            "profit_factor": finite(result.profit_factor),
            "maximum_drawdown": result.maximum_drawdown,
            "average_days_held": result.average_days_held,
            "longest_losing_streak": result.longest_losing_streak,
        },
        "by_regime": [
            asdict(item) | {"profit_factor": finite(item.profit_factor)}
            for item in result.by_regime()
        ],
        "by_exit_reason": [
            asdict(item) | {"profit_factor": finite(item.profit_factor)}
            for item in result.by_exit_reason()
        ],
        "recent_trades": [
            {
                **asdict(trade),
                "entry_date": trade.entry_date.isoformat(),
                "exit_date": trade.exit_date.isoformat(),
            }
            for trade in result.trades[-20:]
        ],
        "disclosure": (
            "Historical option prices are approximated by the existing "
            "ATR-volatility Black-Scholes spread model. The selected DTE range "
            "currently uses its midpoint as one representative entry DTE; "
            "this is not a full expiration sweep."
        ),
    }
