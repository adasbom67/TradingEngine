from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.backtesting.critical_events import (
    CriticalEventBacktestConfig,
    CriticalEventHistoricalBacktester,
)
from app.brokers.schwab_auth import create_schwab_client
from app.brokers.schwab_market_data import SchwabMarketDataClient
from app.data.critical_event_archive import CriticalEventArchive
from app.scanners.critical_event_scanner import SUPPORTED_SYMBOLS


class CriticalEventBacktestRequest(BaseModel):
    symbols: list[str] = Field(default_factory=lambda: list(SUPPORTED_SYMBOLS), min_length=1, max_length=4)
    period_years: int = Field(default=5, ge=2, le=20)
    minimum_signal_score: int = Field(default=4, ge=0, le=6)
    entry_dte: int = Field(default=32, ge=21, le=45)
    implied_volatility_markup: float = Field(default=1.15, ge=0.5, le=3.0)

    @model_validator(mode="after")
    def normalize_symbols(self) -> "CriticalEventBacktestRequest":
        normalized = []
        for value in self.symbols:
            symbol = value.strip().upper()
            if symbol not in SUPPORTED_SYMBOLS:
                raise ValueError(f"Unsupported Critical Events symbol: {symbol}")
            if symbol not in normalized:
                normalized.append(symbol)
        self.symbols = normalized
        return self


def run_critical_event_backtest(request: CriticalEventBacktestRequest) -> dict:
    market_data = SchwabMarketDataClient(create_schwab_client())
    backtester = CriticalEventHistoricalBacktester()
    config = CriticalEventBacktestConfig(
        minimum_signal_score=request.minimum_signal_score,
        entry_dte=request.entry_dte,
        implied_volatility_markup=request.implied_volatility_markup,
    )
    results = []
    diagnostics = []
    for symbol in request.symbols:
        try:
            history = market_data.get_daily_price_history(symbol, period_years=request.period_years)
            results.append(backtester.run(symbol, history, config))
            diagnostics.append({"symbol": symbol, "status": "OK", "message": "Historical proxy completed."})
        except Exception as exc:
            diagnostics.append({"symbol": symbol, "status": "ERROR", "message": str(exc)})
    return {
        "results": results,
        "diagnostics": diagnostics,
        "methodology": {
            "look_ahead_safe": True,
            "score_scale": "0-6 daily proxy",
            "live_score_comparability": "NOT_DIRECTLY_COMPARABLE",
            "option_prices": "BLACK_SCHOLES_WITH_REALIZED_VOLATILITY_PROXY",
            "intraday_inputs": "DAILY_VOLUME_AND_RANGE_PROXIES",
            "event_calendar": "NOT_INTEGRATED",
            "sample_overlap": "Daily observations overlap across forward horizons.",
            "execution_sensitivity": "ZERO_SPREAD, MODEST_2C_PER_LEG, CONSERVATIVE_5C_PER_LEG; commissions included",
        },
        "disclosure": (
            "This validates whether historical compression, daily pressure, and daily ignition "
            "preceded movement. Option P/L is modeled, not reconstructed from historical quotes. "
            "The live 10-point score also includes intraday and executable-liquidity evidence that "
            "daily history cannot reproduce. Modeled option results are shown under three fixed "
            "top-of-book cost assumptions rather than one asserted slippage estimate."
        ),
    }


def critical_event_archive_status() -> dict:
    return CriticalEventArchive.from_environment().status()
