from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any


HORIZONS = (1, 3, 5, 10, 20)


@dataclass(frozen=True)
class CriticalEventBacktestConfig:
    minimum_signal_score: int = 4
    entry_dte: int = 32
    implied_volatility_markup: float = 1.15
    fees_per_transaction: float = 3.0
    modest_cost_per_leg: float = 0.02
    conservative_cost_per_leg: float = 0.05

    def validate(self) -> None:
        if not 0 <= self.minimum_signal_score <= 6:
            raise ValueError("Minimum historical signal score must be between 0 and 6.")
        if not 21 <= self.entry_dte <= 45:
            raise ValueError("Entry DTE must be between 21 and 45.")
        if self.implied_volatility_markup <= 0:
            raise ValueError("Implied-volatility markup must be positive.")
        if self.fees_per_transaction < 0:
            raise ValueError("Fees cannot be negative.")
        if self.modest_cost_per_leg < 0 or self.conservative_cost_per_leg < 0:
            raise ValueError("Per-leg execution costs cannot be negative.")
        if self.conservative_cost_per_leg < self.modest_cost_per_leg:
            raise ValueError("Conservative execution cost cannot be below modest cost.")


class CriticalEventHistoricalBacktester:
    """Look-ahead-safe daily proxy backtest for the Critical Events thesis.

    The live scanner's intraday pressure and executable option-liquidity inputs
    cannot be reconstructed from daily candles. This engine deliberately uses
    daily pressure/ignition proxies and reports a six-point historical signal
    score instead of presenting it as the live ten-point score.
    """

    def run(
        self,
        symbol: str,
        price_history: dict[str, Any],
        config: CriticalEventBacktestConfig | None = None,
    ) -> dict[str, Any]:
        cfg = config or CriticalEventBacktestConfig()
        cfg.validate()
        candles = self._normalize(price_history)
        observations: list[dict[str, Any]] = []
        for index in range(60, len(candles) - max(HORIZONS)):
            history = candles[: index + 1]
            scores, metrics = self._signal(history)
            score = sum(scores.values())
            if score < cfg.minimum_signal_score:
                continue
            observations.append(
                self._observe(symbol.upper(), candles, index, score, scores, metrics, cfg)
            )

        return self._summarize(symbol.upper(), candles, observations, cfg)

    @classmethod
    def _signal(cls, history: list[dict[str, Any]]) -> tuple[dict[str, int], dict[str, float | bool]]:
        recent = history[-21:]
        normalized_ranges = [
            (bar["high"] - bar["low"]) / max(bar["close"], 0.01)
            for bar in recent
        ]
        baseline_range = statistics.mean(normalized_ranges[:-1])
        compression_ratio = statistics.mean(normalized_ranges[-6:-1]) / max(baseline_range, 0.0001)
        compression = 2 if compression_ratio < 0.65 else 1 if compression_ratio < 0.85 else 0

        current = recent[-1]
        prior = recent[:-1]
        volume_ratio = current["volume"] / max(statistics.mean(item["volume"] for item in prior), 1.0)
        pressure = 2 if volume_ratio > 1.8 else 1 if volume_ratio > 1.2 else 0

        current_range = normalized_ranges[-1]
        expansion_ratio = current_range / max(baseline_range, 0.0001)
        breakout = current["close"] > max(item["high"] for item in prior) or current["close"] < min(item["low"] for item in prior)
        ignition = 2 if breakout and expansion_ratio > 1.6 else 1 if breakout or expansion_ratio > 1.3 else 0
        return (
            {"compression": compression, "daily_pressure_proxy": pressure, "daily_ignition_proxy": ignition},
            {
                "compression_ratio": compression_ratio,
                "volume_ratio": volume_ratio,
                "expansion_ratio": expansion_ratio,
                "breakout": breakout,
            },
        )

    @classmethod
    def _observe(cls, symbol, candles, index, score, scores, metrics, cfg):
        entry = candles[index]
        spot = entry["close"]
        strike = round(spot)
        forecast_volatility = cls._forecast_volatility(candles[: index + 1])
        entry_iv = min(max(forecast_volatility * cfg.implied_volatility_markup, 0.05), 2.0)
        theoretical_entry = cls._straddle_value(spot, strike, cfg.entry_dte, entry_iv)
        fee_per_share = cfg.fees_per_transaction / 100
        scenario_costs = {
            "ZERO_SPREAD": 0.0,
            "MODEST_2C_PER_LEG": cfg.modest_cost_per_leg,
            "CONSERVATIVE_5C_PER_LEG": cfg.conservative_cost_per_leg,
        }
        entry_debits = {
            name: theoretical_entry + cost_per_leg * 2 + fee_per_share
            for name, cost_per_leg in scenario_costs.items()
        }
        primary_scenario = "MODEST_2C_PER_LEG"
        entry_debit = entry_debits[primary_scenario]
        outcomes: dict[str, Any] = {}
        for horizon in HORIZONS:
            exit_index = index + horizon
            exit_bar = candles[exit_index]
            elapsed_days = max((exit_bar["date"] - entry["date"]).days, horizon)
            remaining_dte = max(cfg.entry_dte - elapsed_days, 0)
            exit_volatility = cls._forecast_volatility(candles[: exit_index + 1])
            exit_iv = min(max(exit_volatility * cfg.implied_volatility_markup, 0.05), 2.0)
            theoretical_exit = cls._straddle_value(exit_bar["close"], strike, remaining_dte, exit_iv)
            window = candles[index + 1: exit_index + 1]
            maximum_excursion = max(
                max(abs(item["high"] / spot - 1), abs(item["low"] / spot - 1))
                for item in window
            )
            scenarios = {}
            for name, cost_per_leg in scenario_costs.items():
                exit_credit = max(theoretical_exit - cost_per_leg * 2 - fee_per_share, 0.0)
                pnl = (exit_credit - entry_debits[name]) * 100
                scenarios[name] = {
                    "entry_debit": entry_debits[name],
                    "exit_credit": exit_credit,
                    "modeled_pnl": pnl,
                    "profitable": pnl > 0,
                }
            primary = scenarios[primary_scenario]
            outcomes[str(horizon)] = {
                "absolute_return": abs(exit_bar["close"] / spot - 1),
                "maximum_excursion": maximum_excursion,
                "breakeven_reached": maximum_excursion >= entry_debit / spot,
                "modeled_pnl": primary["modeled_pnl"],
                "profitable": primary["profitable"],
                "remaining_dte": remaining_dte,
                "execution_scenarios": scenarios,
            }
        return {
            "symbol": symbol,
            "date": entry["date"].isoformat(),
            "price": spot,
            "strike": strike,
            "signal_score": score,
            "scores": scores,
            "metrics": metrics,
            "forecast_volatility": forecast_volatility,
            "modeled_entry_iv": entry_iv,
            "modeled_entry_debit": entry_debit,
            "modeled_entry_debits": entry_debits,
            "breakeven_move": entry_debit / spot,
            "outcomes": outcomes,
        }

    @classmethod
    def _summarize(cls, symbol, candles, observations, cfg):
        horizon_metrics = {str(h): cls._aggregate_horizon(observations, h) for h in HORIZONS}
        by_score = []
        for score in sorted({item["signal_score"] for item in observations}):
            group = [item for item in observations if item["signal_score"] == score]
            by_score.append({
                "score": score,
                "count": len(group),
                "horizons": {str(h): cls._aggregate_horizon(group, h) for h in HORIZONS},
            })
        split = math.floor(len(observations) * 0.7)
        training, testing = observations[:split], observations[split:]
        return {
            "symbol": symbol,
            "period": {"start": candles[60]["date"].isoformat(), "end": candles[-1]["date"].isoformat(), "daily_bars": len(candles)},
            "configuration": {
                "minimum_signal_score": cfg.minimum_signal_score,
                "historical_score_maximum": 6,
                "entry_dte": cfg.entry_dte,
                "implied_volatility_markup": cfg.implied_volatility_markup,
                "fees_per_transaction": cfg.fees_per_transaction,
                "primary_execution_scenario": "MODEST_2C_PER_LEG",
                "execution_cost_per_leg": {
                    "ZERO_SPREAD": 0.0,
                    "MODEST_2C_PER_LEG": cfg.modest_cost_per_leg,
                    "CONSERVATIVE_5C_PER_LEG": cfg.conservative_cost_per_leg,
                },
            },
            "signal_count": len(observations),
            "horizons": horizon_metrics,
            "by_score": by_score,
            "walk_forward": {
                "method": "CHRONOLOGICAL_70_30_HOLDOUT",
                "training": {"count": len(training), "horizon_20": cls._aggregate_horizon(training, 20)},
                "testing": {"count": len(testing), "horizon_20": cls._aggregate_horizon(testing, 20)},
            },
            "recent_signals": observations[-20:],
        }

    @staticmethod
    def _aggregate_horizon(observations, horizon):
        scenario_names = ("ZERO_SPREAD", "MODEST_2C_PER_LEG", "CONSERVATIVE_5C_PER_LEG")
        if not observations:
            empty = {"modeled_win_rate": 0.0, "average_modeled_pnl": 0.0}
            return {"count": 0, "average_absolute_return": 0.0, "average_maximum_excursion": 0.0, "breakeven_rate": 0.0, "modeled_win_rate": 0.0, "average_modeled_pnl": 0.0, "execution_sensitivity": {name: dict(empty) for name in scenario_names}}
        values = [item["outcomes"][str(horizon)] for item in observations]
        sensitivity = {}
        for name in scenario_names:
            scenarios = [item["execution_scenarios"][name] for item in values]
            sensitivity[name] = {
                "modeled_win_rate": statistics.mean(item["profitable"] for item in scenarios),
                "average_modeled_pnl": statistics.mean(item["modeled_pnl"] for item in scenarios),
            }
        return {
            "count": len(values),
            "average_absolute_return": statistics.mean(item["absolute_return"] for item in values),
            "average_maximum_excursion": statistics.mean(item["maximum_excursion"] for item in values),
            "breakeven_rate": statistics.mean(item["breakeven_reached"] for item in values),
            "modeled_win_rate": statistics.mean(item["profitable"] for item in values),
            "average_modeled_pnl": statistics.mean(item["modeled_pnl"] for item in values),
            "execution_sensitivity": sensitivity,
        }

    @staticmethod
    def _forecast_volatility(candles):
        def realized(lookback):
            closes = [item["close"] for item in candles[-(lookback + 1):]]
            returns = [math.log(current / previous) for previous, current in zip(closes, closes[1:])]
            return statistics.pstdev(returns) * math.sqrt(252)
        return realized(20) * 0.65 + realized(60) * 0.35

    @staticmethod
    def _straddle_value(spot, strike, dte, volatility, rate=0.04):
        if dte <= 0:
            return abs(spot - strike)
        years = dte / 365
        denominator = volatility * math.sqrt(years)
        d1 = (math.log(spot / strike) + (rate + volatility * volatility / 2) * years) / denominator
        d2 = d1 - denominator
        cdf = lambda value: 0.5 * (1 + math.erf(value / math.sqrt(2)))
        call = spot * cdf(d1) - strike * math.exp(-rate * years) * cdf(d2)
        put = strike * math.exp(-rate * years) * cdf(-d2) - spot * cdf(-d1)
        return max(call + put, 0.0)

    @staticmethod
    def _normalize(payload):
        raw = payload.get("candles") if isinstance(payload, dict) else None
        if not isinstance(raw, list) or len(raw) < 82:
            raise ValueError("Critical Events backtesting requires at least 82 daily candles.")
        candles = []
        for item in raw:
            timestamp = float(item["datetime"])
            if timestamp > 10_000_000_000:
                timestamp /= 1000
            candles.append({
                "date": datetime.fromtimestamp(timestamp, tz=timezone.utc).date(),
                "open": float(item["open"]), "high": float(item["high"]),
                "low": float(item["low"]), "close": float(item["close"]),
                "volume": float(item["volume"]),
            })
        candles.sort(key=lambda item: item["date"])
        return candles
