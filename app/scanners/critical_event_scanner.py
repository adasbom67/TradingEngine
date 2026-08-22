from __future__ import annotations

import math
import statistics
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from app.brokers.schwab_market_data import SchwabMarketDataClient
from app.data.schwab_option_chain_adapter import SchwabOptionChainAdapter
from app.data.critical_event_archive import CriticalEventArchive
from app.market_session import recommendation_market_session
from app.models.market.option_contract import OptionContract

SUPPORTED_SYMBOLS = ("SPY", "QQQ", "IWM", "DIA")
SCORE_MAXIMUM = 10
MINIMUM_OPEN_INTEREST = 100
MINIMUM_REGULAR_HOURS_VOLUME = 10
MINIMUM_BID = 0.05
MAXIMUM_PAIR_SPREAD_PERCENT = 15.0
ESTIMATED_FEES_PER_SPREAD = 3.00
MINIMUM_INTRADAY_SAMPLES = 5
EASTERN = ZoneInfo("America/New_York")


class CriticalEventScanner:
    """Rank research-grade, direction-neutral long-straddle opportunities."""

    def __init__(
        self,
        market_data: SchwabMarketDataClient,
        adapter: SchwabOptionChainAdapter | None = None,
        archive: CriticalEventArchive | None = None,
    ) -> None:
        self._market_data = market_data
        self._adapter = adapter or SchwabOptionChainAdapter()
        self._archive = archive

    def scan(self, symbols: list[str]) -> dict[str, Any]:
        candidates: list[dict[str, Any]] = []
        diagnostics: list[dict[str, str]] = []
        for symbol in self._normalize_symbols(symbols):
            try:
                candidates.append(self._scan_symbol(symbol))
                diagnostics.append({"symbol": symbol, "status": "OK", "message": "Analyzed."})
            except Exception as exc:
                diagnostics.append({"symbol": symbol, "status": "ERROR", "message": str(exc)})
        candidates.sort(
            key=lambda item: (
                item["total_score"],
                item["metrics"]["expected_net_value"],
                -item["option"]["spread_pct"],
            ),
            reverse=True,
        )
        return {"candidates": candidates, "diagnostics": diagnostics}

    @staticmethod
    def _normalize_symbols(symbols: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in symbols:
            symbol = value.strip().upper()
            if symbol in SUPPORTED_SYMBOLS and symbol not in normalized:
                normalized.append(symbol)
        return normalized or list(SUPPORTED_SYMBOLS)

    def _scan_symbol(self, symbol: str) -> dict[str, Any]:
        history = self._market_data.get_daily_price_history(symbol)
        intraday_history = self._market_data.get_intraday_price_history(symbol)
        bars = self._bars(history)
        intraday_bars = self._intraday_bars(intraday_history)
        chain_payload = self._market_data.get_option_chain(symbol, strike_count=60)
        chain = self._adapter.to_option_chain(chain_payload, requested_symbol=symbol)
        pairs = self._select_candidate_pairs(chain.contracts, chain.underlying_price)
        scored = [
            self._score(symbol, chain.underlying_price, bars, pair, intraday_bars)
            for pair in pairs
        ]
        scored.sort(
            key=lambda item: (
                item["total_score"],
                item["metrics"]["expected_net_value"],
                -item["option"]["spread_pct"],
            ),
            reverse=True,
        )
        selected = scored[0]
        selected["alternatives_evaluated"] = len(scored)
        if self._archive is not None:
            selected["archive_capture"] = self._archive.capture(
                symbol,
                chain.underlying_price,
                chain.contracts,
                scored,
                daily_bar_count=len(bars),
                intraday_bar_count=len(intraday_bars),
            )
        return selected

    @staticmethod
    def _bars(payload: dict[str, Any]) -> list[dict[str, float]]:
        candles = payload.get("candles", [])
        bars = [
            {
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"]),
                "volume": float(item["volume"]),
            }
            for item in candles
        ]
        if len(bars) < 61:
            raise ValueError("At least 61 daily candles are required for volatility forecasting.")
        return bars

    @staticmethod
    def _intraday_bars(
        payload: dict[str, Any], observed_at: datetime | None = None
    ) -> list[dict[str, Any]]:
        observed = observed_at or datetime.now(timezone.utc)
        if observed.tzinfo is None:
            observed = observed.replace(tzinfo=timezone.utc)
        observed_eastern = observed.astimezone(EASTERN)
        bars: list[dict[str, Any]] = []
        for item in payload.get("candles", []):
            try:
                timestamp = float(item["datetime"])
                if timestamp > 10_000_000_000:
                    timestamp /= 1000
                instant = datetime.fromtimestamp(timestamp, tz=timezone.utc).astimezone(EASTERN)
                if instant.weekday() >= 5 or not time(9, 30) <= instant.time() < time(16, 0):
                    continue
                if instant + timedelta(minutes=15) > observed_eastern:
                    continue
                bars.append({
                    "datetime": instant,
                    "open": float(item["open"]),
                    "high": float(item["high"]),
                    "low": float(item["low"]),
                    "close": float(item["close"]),
                    "volume": float(item["volume"]),
                })
            except (KeyError, TypeError, ValueError, OSError, OverflowError):
                continue
        bars.sort(key=lambda item: item["datetime"])
        if not bars:
            raise ValueError("No completed regular-hours 15-minute candles were returned.")
        return bars

    @classmethod
    def _select_candidate_pairs(
        cls,
        contracts: list[OptionContract],
        underlying_price: float,
        observed_at: datetime | None = None,
    ) -> list[tuple[OptionContract, OptionContract]]:
        session = recommendation_market_session(observed_at)
        regular_hours = session["is_regular_hours"]
        eligible = [
            item
            for item in contracts
            if cls._contract_is_eligible(item, regular_hours, observed_at)
        ]
        expirations = sorted(
            {item.expiration_date for item in eligible},
            key=lambda expiry: abs((expiry - date.today()).days - 32),
        )[:4]
        pairs: list[tuple[OptionContract, OptionContract]] = []
        for expiration in expirations:
            expiry_contracts = [item for item in eligible if item.expiration_date == expiration]
            calls = {item.strike: item for item in expiry_contracts if item.option_type == "CALL"}
            puts = {item.strike: item for item in expiry_contracts if item.option_type == "PUT"}
            common = sorted(set(calls) & set(puts), key=lambda strike: abs(strike - underlying_price))
            nearby = [
                strike for strike in common
                if abs(strike - underlying_price) / max(underlying_price, 0.01) <= 0.015
            ][:3]
            for strike in nearby:
                pair = (calls[strike], puts[strike])
                if cls._pair_spread_percent(pair) <= MAXIMUM_PAIR_SPREAD_PERCENT:
                    pairs.append(pair)
        if not pairs:
            raise ValueError(
                "No executable nearby-ATM straddles passed DTE, quote, OI, volume, and spread gates."
            )
        return pairs

    @classmethod
    def _select_atm_pair(
        cls, contracts: list[OptionContract], underlying_price: float
    ) -> tuple[OptionContract, OptionContract]:
        """Compatibility helper returning the best mechanically nearby pair."""
        return cls._select_candidate_pairs(contracts, underlying_price)[0]

    @staticmethod
    def _contract_is_eligible(
        contract: OptionContract,
        regular_hours: bool,
        observed_at: datetime | None,
    ) -> bool:
        if not 21 <= contract.days_to_expiration <= 45:
            return False
        if contract.bid < MINIMUM_BID or contract.ask < contract.bid:
            return False
        if contract.open_interest < MINIMUM_OPEN_INTEREST:
            return False
        if regular_hours and contract.volume < MINIMUM_REGULAR_HOURS_VOLUME:
            return False
        if regular_hours:
            if contract.quote_time is None:
                return False
            now = observed_at or datetime.now(timezone.utc)
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
            age_minutes = (now.astimezone(timezone.utc) - contract.quote_time.astimezone(timezone.utc)).total_seconds() / 60
            if age_minutes < -1 or age_minutes > 20:
                return False
        return True

    @staticmethod
    def _pair_spread_percent(pair: tuple[OptionContract, OptionContract]) -> float:
        call, put = pair
        midpoint = (call.bid + call.ask + put.bid + put.ask) / 2
        combined_width = (call.ask - call.bid) + (put.ask - put.bid)
        return combined_width / max(midpoint, 0.01) * 100

    @classmethod
    def _score(
        cls,
        symbol: str,
        underlying_price: float,
        bars: list[dict[str, float]],
        pair: tuple[OptionContract, OptionContract],
        intraday_bars: list[dict[str, Any]],
    ) -> dict[str, Any]:
        call, put = pair
        daily_ranges = [
            (bar["high"] - bar["low"]) / max(bar["close"], 0.01)
            for bar in bars[-21:]
        ]
        baseline_range = statistics.mean(daily_ranges[:-1])
        compression_ratio = statistics.mean(daily_ranges[-6:-1]) / max(baseline_range, 0.0001)
        compression = 2 if compression_ratio < 0.65 else 1 if compression_ratio < 0.85 else 0

        intraday = cls._intraday_signals(intraday_bars, bars)
        pressure = 2 if intraday["volume_ratio"] > 1.8 else 1 if intraday["volume_ratio"] > 1.2 else 0
        ignition = (
            2 if intraday["breakout"] and intraday["expansion_ratio"] > 1.6
            else 1 if intraday["breakout"] or intraday["expansion_ratio"] > 1.3
            else 0
        )

        call_mid = (call.bid + call.ask) / 2
        put_mid = (put.bid + put.ask) / 2
        straddle_mid = call_mid + put_mid
        natural_debit = call.ask + put.ask
        estimated_fees = ESTIMATED_FEES_PER_SPREAD / 100
        modeled_entry_debit = natural_debit + estimated_fees
        spread_pct = cls._pair_spread_percent(pair)

        short_volatility = cls._realized_volatility(bars, 20)
        long_volatility = cls._realized_volatility(bars, 60)
        forecast_volatility = short_volatility * 0.65 + long_volatility * 0.35
        horizon = math.sqrt(call.days_to_expiration / 365)
        forecast_standard_move = underlying_price * forecast_volatility * horizon
        expected_payoff = cls._expected_absolute_normal_payoff(
            underlying_price - call.strike,
            forecast_standard_move,
        )
        probability_of_profit = cls._probability_outside_breakevens(
            underlying_price - call.strike,
            forecast_standard_move,
            modeled_entry_debit,
        )
        expected_net_value = (expected_payoff - modeled_entry_debit) * 100
        expected_return = expected_payoff / max(modeled_entry_debit, 0.01) - 1
        option_value = 2 if expected_return >= 0.10 else 1 if expected_return >= 0 else 0
        liquidity = 2 if spread_pct <= 5 else 1 if spread_pct <= 10 else 0

        scores = {
            "compression": compression,
            "option_value": option_value,
            "pressure": pressure,
            "ignition": ignition,
            "liquidity": liquidity,
        }
        total_score = sum(scores.values())
        phase = "IGNITION" if ignition == 2 and total_score >= 6 else "WATCH"

        market_iv_values = [
            value / 100
            for value in (call.implied_volatility, put.implied_volatility)
            if value is not None and value > 0
        ]
        market_implied_volatility = statistics.mean(market_iv_values) if market_iv_values else None
        quote_times = [item.quote_time for item in pair if item.quote_time is not None]
        quote_time = min(quote_times).isoformat() if len(quote_times) == 2 else None
        session = recommendation_market_session()

        return {
            "symbol": symbol,
            "price": underlying_price,
            "total_score": total_score,
            "score_maximum": SCORE_MAXIMUM,
            "phase": phase,
            "scores": scores,
            "model_target": (
                "Expiration expected value of the same-strike long straddle bought at "
                "the displayed natural ask debit plus $3 estimated commissions."
            ),
            "option": {
                "expiration": call.expiration_date.isoformat(),
                "dte": call.days_to_expiration,
                "strike": call.strike,
                "call_symbol": call.symbol,
                "put_symbol": put.symbol,
                "call_bid": call.bid,
                "call_ask": call.ask,
                "put_bid": put.bid,
                "put_ask": put.ask,
                "straddle_mid": straddle_mid,
                "natural_debit": natural_debit,
                "modeled_entry_debit": modeled_entry_debit,
                "cost_buffer": estimated_fees,
                "estimated_fees": estimated_fees,
                "upper_breakeven": call.strike + modeled_entry_debit,
                "lower_breakeven": call.strike - modeled_entry_debit,
                "breakeven_move_pct": modeled_entry_debit / max(underlying_price, 0.01) * 100,
                "implied_move_pct": natural_debit / max(underlying_price, 0.01) * 100,
                "spread_pct": spread_pct,
                "quote_time": quote_time,
            },
            "metrics": {
                "compression_ratio": compression_ratio,
                "volume_ratio": intraday["volume_ratio"],
                "expansion_ratio": intraday["expansion_ratio"],
                "intraday_sample_count": intraday["sample_count"],
                "intraday_slot": intraday["slot"],
                "breakout": intraday["breakout"],
                "short_realized_volatility": short_volatility,
                "long_realized_volatility": long_volatility,
                "forecast_volatility": forecast_volatility,
                "market_implied_volatility": market_implied_volatility,
                "forecast_move_pct": forecast_standard_move / max(underlying_price, 0.01) * 100,
                "expected_payoff": expected_payoff,
                "expected_net_value": expected_net_value,
                "expected_return": expected_return,
                "probability_of_profit": probability_of_profit,
            },
            "data_quality": {
                "market_session": session["status"],
                "quotes_provisional": session["provisional"],
                "quote_time": quote_time,
                "event_calendar": "NOT_INTEGRATED",
            },
            "reasons": [
                f"Five-session range is {compression_ratio:.0%} of its 20-session baseline.",
                f"Forecast expiration payoff is ${expected_payoff:.2f} versus a ${modeled_entry_debit:.2f} modeled entry debit.",
                f"Same-time 15-minute volume is {intraday['volume_ratio']:.2f}x its historical average.",
                f"Latest completed 15-minute range is {intraday['expansion_ratio']:.2f}x its same-time baseline.",
                f"Combined quote width is {spread_pct:.1f}% of the straddle midpoint.",
            ],
        }

    @staticmethod
    def _intraday_signals(
        intraday_bars: list[dict[str, Any]],
        daily_bars: list[dict[str, float]],
    ) -> dict[str, Any]:
        latest = intraday_bars[-1]
        slot = (latest["datetime"].hour, latest["datetime"].minute)
        comparisons = [
            item for item in intraday_bars[:-1]
            if (item["datetime"].hour, item["datetime"].minute) == slot
            and item["datetime"].date() != latest["datetime"].date()
        ][-20:]
        if len(comparisons) < MINIMUM_INTRADAY_SAMPLES:
            raise ValueError(
                f"At least {MINIMUM_INTRADAY_SAMPLES} historical 15-minute bars at the same time of day are required."
            )
        average_volume = statistics.mean(item["volume"] for item in comparisons)
        comparison_ranges = [
            (item["high"] - item["low"]) / max(item["close"], 0.01)
            for item in comparisons
        ]
        latest_range = (latest["high"] - latest["low"]) / max(latest["close"], 0.01)
        prior_high = max(item["high"] for item in daily_bars[-21:-1])
        prior_low = min(item["low"] for item in daily_bars[-21:-1])
        return {
            "volume_ratio": latest["volume"] / max(average_volume, 1.0),
            "expansion_ratio": latest_range / max(statistics.mean(comparison_ranges), 0.0001),
            "breakout": latest["close"] > prior_high or latest["close"] < prior_low,
            "sample_count": len(comparisons),
            "slot": latest["datetime"].strftime("%H:%M ET"),
        }

    @staticmethod
    def _realized_volatility(bars: list[dict[str, float]], lookback: int) -> float:
        closes = [item["close"] for item in bars[-(lookback + 1):]]
        returns = [math.log(current / previous) for previous, current in zip(closes, closes[1:])]
        return statistics.pstdev(returns) * math.sqrt(252)

    @staticmethod
    def _expected_absolute_normal_payoff(mean: float, standard_deviation: float) -> float:
        if standard_deviation <= 0:
            return abs(mean)
        z = mean / standard_deviation
        return (
            standard_deviation * math.sqrt(2 / math.pi) * math.exp(-(z * z) / 2)
            + mean * (2 * CriticalEventScanner._normal_cdf(z) - 1)
        )

    @staticmethod
    def _probability_outside_breakevens(
        mean: float,
        standard_deviation: float,
        debit: float,
    ) -> float:
        if standard_deviation <= 0:
            return 1.0 if abs(mean) > debit else 0.0
        upper = (debit - mean) / standard_deviation
        lower = (-debit - mean) / standard_deviation
        return max(0.0, min(1.0, 1 - CriticalEventScanner._normal_cdf(upper) + CriticalEventScanner._normal_cdf(lower)))

    @staticmethod
    def _normal_cdf(value: float) -> float:
        return 0.5 * (1 + math.erf(value / math.sqrt(2)))
