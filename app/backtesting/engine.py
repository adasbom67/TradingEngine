from __future__ import annotations

from datetime import date, datetime, timezone
from math import floor
from typing import Any

from app.backtesting.models import BacktestConfig, BacktestResult, BacktestTrade
from app.backtesting.pricing import ApproximateSpreadPricer
from app.indicators.technical_indicators import TechnicalIndicators


class HistoricalBacktester:
    """Daily-bar backtester with strict no-look-ahead signal generation.

    Historical option values are estimated with a Black-Scholes vertical-spread
    model using ATR-derived volatility. Daily high and low values are used to
    detect target and stop touches. When both are touched on the same daily bar,
    the simulator uses the conservative assumption that the stop occurred first.
    """

    def __init__(self, pricer: ApproximateSpreadPricer | None = None) -> None:
        self._pricer = pricer or ApproximateSpreadPricer()

    def run(
        self,
        symbol: str,
        price_history: dict[str, Any],
        config: BacktestConfig | None = None,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> BacktestResult:
        cfg = config or BacktestConfig()
        cfg.validate()
        candles = self._normalize(price_history)
        result = BacktestResult(symbol=symbol.upper(), initial_capital=cfg.initial_capital)
        last_entry_index = -10_000

        for index in range(cfg.lookback_days, len(candles) - cfg.entry_dte):
            entry_date = candles[index]["date"]
            if start_date is not None and entry_date < start_date:
                continue
            if end_date is not None and entry_date > end_date:
                continue
            if index - last_entry_index < cfg.minimum_days_between_entries:
                continue
            history = candles[: index + 1]
            closes = [c["close"] for c in history]
            sma20 = sum(closes[-20:]) / 20
            sma200 = sum(closes[-200:]) / 200
            current = closes[-1]
            atr = TechnicalIndicators.atr(history, 14)
            if not (sma20 > sma200 and current > sma200):
                continue

            trade = self._simulate_trade(
                symbol.upper(), candles, index, sma20, sma200, atr, cfg
            )
            if trade is None:
                continue
            result.trades.append(trade)
            last_entry_index = index
        return result

    def _simulate_trade(self, symbol, candles, entry_index, sma20, sma200, atr, cfg):
        entry = candles[entry_index]
        entry_price = entry["close"]
        short_strike = floor(entry_price - cfg.short_strike_distance_atr * atr)
        long_strike = short_strike - cfg.spread_width

        entry_valuation = self._pricer.value(
            entry_price,
            short_strike,
            long_strike,
            cfg.entry_dte,
            atr,
            cfg.risk_free_rate,
            cfg.volatility_floor,
            cfg.volatility_ceiling,
        )
        maximum_credit = cfg.spread_width * cfg.maximum_entry_credit_percent_of_width
        credit = min(entry_valuation.debit - cfg.entry_slippage, maximum_credit)
        if credit < cfg.minimum_entry_credit:
            return None

        target_debit = credit * (1 - cfg.profit_target_percent / 100)
        stop_debit = min(
            cfg.spread_width,
            credit * (1 + cfg.stop_loss_percent / 100),
        )
        max_debit = cfg.spread_width
        planned_exit_index = entry_index + cfg.entry_dte - cfg.exit_dte
        exit_index = planned_exit_index
        exit_reason = "EXIT_DTE"
        exit_debit = 0.0
        exit_theoretical_value = 0.0
        exit_remaining_dte = cfg.exit_dte
        min_theoretical_debit = entry_valuation.debit
        max_theoretical_debit = entry_valuation.debit

        for i in range(entry_index + 1, planned_exit_index + 1):
            history = candles[: i + 1]
            current_atr = TechnicalIndicators.atr(history, 14)
            remaining = max(entry_index + cfg.entry_dte - i, 0)
            candle = candles[i]

            high_value = self._pricer.value(
                candle["high"], short_strike, long_strike, remaining, current_atr,
                cfg.risk_free_rate, cfg.volatility_floor, cfg.volatility_ceiling,
            ).debit
            low_value = self._pricer.value(
                candle["low"], short_strike, long_strike, remaining, current_atr,
                cfg.risk_free_rate, cfg.volatility_floor, cfg.volatility_ceiling,
            ).debit
            close_value = self._pricer.value(
                candle["close"], short_strike, long_strike, remaining, current_atr,
                cfg.risk_free_rate, cfg.volatility_floor, cfg.volatility_ceiling,
            ).debit

            daily_min = min(high_value, low_value, close_value)
            daily_max = max(high_value, low_value, close_value)
            min_theoretical_debit = min(min_theoretical_debit, daily_min)
            max_theoretical_debit = max(max_theoretical_debit, daily_max)

            target_touched = daily_min <= target_debit
            stop_touched = daily_max >= stop_debit

            # Optional defensive exits are evaluated before the normal target.
            # Stop-loss remains first because it is the most conservative same-bar
            # assumption when multiple conditions are touched.
            current_closes = [c["close"] for c in history]
            current_sma20 = sum(current_closes[-20:]) / 20
            trend_deteriorated = (
                cfg.enable_trend_exit
                and candle["close"] < current_sma20
                and current_sma20 < sma20
            )
            strike_threatened = (
                cfg.enable_strike_threat_exit
                and candle["low"] <= short_strike + cfg.strike_threat_buffer_atr * current_atr
            )

            if stop_touched:
                exit_index = i
                exit_theoretical_value = daily_max
                gap_beyond_stop = min(
                    max(daily_max - stop_debit, 0.0),
                    cfg.maximum_stop_gap_debit,
                )
                exit_debit = min(
                    max_debit,
                    stop_debit + gap_beyond_stop + cfg.exit_slippage,
                )
                exit_reason = "STOP_LOSS"
                exit_remaining_dte = remaining
                break

            if strike_threatened:
                exit_index = i
                exit_theoretical_value = close_value
                exit_debit = min(max_debit, close_value + cfg.exit_slippage)
                exit_reason = "STRIKE_THREAT"
                exit_remaining_dte = remaining
                break

            if trend_deteriorated:
                exit_index = i
                exit_theoretical_value = close_value
                exit_debit = min(max_debit, close_value + cfg.exit_slippage)
                exit_reason = "TREND_EXIT"
                exit_remaining_dte = remaining
                break

            if target_touched:
                exit_index = i
                exit_theoretical_value = daily_min
                exit_debit = min(max_debit, target_debit + cfg.exit_slippage)
                exit_reason = "PROFIT_TARGET"
                exit_remaining_dte = remaining
                break
        else:
            history = candles[: planned_exit_index + 1]
            current_atr = TechnicalIndicators.atr(history, 14)
            valuation = self._pricer.value(
                candles[planned_exit_index]["close"],
                short_strike,
                long_strike,
                cfg.exit_dte,
                current_atr,
                cfg.risk_free_rate,
                cfg.volatility_floor,
                cfg.volatility_ceiling,
            )
            exit_theoretical_value = valuation.debit
            min_theoretical_debit = min(min_theoretical_debit, valuation.debit)
            max_theoretical_debit = max(max_theoretical_debit, valuation.debit)
            exit_debit = min(max_debit, valuation.debit + cfg.exit_slippage)

        exit_price = candles[exit_index]["close"]
        pnl = (credit - exit_debit) * 100
        entry_rsi = TechnicalIndicators.rsi(
            [c["close"] for c in candles[: entry_index + 1]], 14
        )
        regime = self._classify_regime(entry_price, sma20, sma200, atr, cfg)
        return BacktestTrade(
            symbol=symbol,
            entry_date=entry["date"],
            exit_date=candles[exit_index]["date"],
            short_strike=float(short_strike),
            long_strike=float(long_strike),
            entry_credit=credit,
            exit_debit=exit_debit,
            pnl=pnl,
            exit_reason=exit_reason,
            days_held=exit_index - entry_index,
            entry_price=entry_price,
            exit_price=exit_price,
            reasons=("20-day SMA above 200-day SMA", "Price above 200-day SMA"),
            entry_dte=cfg.entry_dte,
            exit_dte=exit_remaining_dte,
            entry_atr=atr,
            entry_volatility=entry_valuation.annualized_volatility,
            target_debit=target_debit,
            stop_debit=stop_debit,
            maximum_loss=(cfg.spread_width - credit) * 100,
            theoretical_entry_value=entry_valuation.debit,
            exit_theoretical_value=exit_theoretical_value,
            entry_sma20=sma20,
            entry_sma200=sma200,
            entry_rsi=entry_rsi,
            market_regime=regime,
            underlying_return_percent=(exit_price / entry_price - 1.0) * 100,
            maximum_favorable_excursion=(credit - min_theoretical_debit) * 100,
            maximum_adverse_excursion=(credit - max_theoretical_debit) * 100,
        )

    @staticmethod
    def _classify_regime(price, sma20, sma200, atr, cfg) -> str:
        if atr / price >= cfg.high_volatility_atr_percent:
            return "HIGH_VOLATILITY"
        if sma20 > sma200 and price > sma20:
            return "BULLISH"
        if price < sma200 and sma20 <= sma200:
            return "BEARISH"
        return "NEUTRAL"

    @staticmethod
    def _normalize(payload):
        raw = payload.get("candles") if isinstance(payload, dict) else None
        if not isinstance(raw, list) or not raw:
            raise ValueError("Price history must contain candles.")
        candles = []
        for item in raw:
            dt = datetime.fromtimestamp(item["datetime"] / 1000, tz=timezone.utc).date()
            candles.append({
                "date": dt,
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"]),
            })
        candles.sort(key=lambda c: c["date"])
        return candles
