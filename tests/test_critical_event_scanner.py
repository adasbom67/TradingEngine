from datetime import date, datetime, timedelta, timezone

import pytest

from app.models.market.option_contract import OptionContract
from app.scanners.critical_event_scanner import CriticalEventScanner


def contract(
    option_type: str,
    strike: float = 100,
    *,
    bid: float = 3.8,
    ask: float = 4.2,
    open_interest: int = 500,
    volume: int = 100,
    quote_time: datetime | None = None,
) -> OptionContract:
    return OptionContract(
        symbol=f"XYZ-{option_type}-{strike}",
        expiration_date=date.today() + timedelta(days=32),
        strike=strike,
        option_type=option_type,
        bid=bid,
        ask=ask,
        last=(bid + ask) / 2,
        delta=0.5 if option_type == "CALL" else -0.5,
        volume=volume,
        open_interest=open_interest,
        days_to_expiration=32,
        implied_volatility=20.0,
        quote_time=quote_time or datetime.now(timezone.utc),
    )


def daily_bars() -> list[dict[str, float]]:
    bars = []
    for index in range(70):
        close = 98 + index * 0.02 + (0.25 if index % 2 else -0.25)
        width = 0.55 if index < 65 else 0.20
        bars.append({
            "open": close,
            "high": close + width,
            "low": close - width,
            "close": close,
            "volume": 1000,
        })
    return bars


def parsed_intraday_bars(*, latest_volume: float = 2200, latest_width: float = 1.5):
    bars = []
    eastern_offset = timezone(timedelta(hours=-4))
    start = date(2026, 7, 20)
    for index in range(20):
        instant = datetime.combine(start + timedelta(days=index), datetime.min.time(), eastern_offset).replace(hour=15, minute=30)
        if instant.weekday() >= 5:
            continue
        bars.append({
            "datetime": instant,
            "open": 100,
            "high": 100.20,
            "low": 99.80,
            "close": 100,
            "volume": 500,
        })
    bars.append({
        "datetime": datetime(2026, 8, 17, 15, 30, tzinfo=eastern_offset),
        "open": 100,
        "high": 103 + latest_width,
        "low": 103 - latest_width,
        "close": 103,
        "volume": latest_volume,
    })
    return bars


def test_selects_multiple_executable_nearby_atm_pairs():
    contracts = [
        contract(kind, strike, bid=3.9, ask=4.1)
        for strike in (99, 100, 101, 110)
        for kind in ("CALL", "PUT")
    ]
    saturday = datetime(2026, 8, 22, 14, tzinfo=timezone.utc)

    pairs = CriticalEventScanner._select_candidate_pairs(
        contracts, 100.4, observed_at=saturday
    )

    assert [pair[0].strike for pair in pairs] == [100, 101, 99]


def test_contract_selection_rejects_weak_open_interest_and_wide_quotes():
    contracts = [
        contract("CALL", open_interest=99),
        contract("PUT", open_interest=99),
        contract("CALL", 101, bid=1.0, ask=2.0),
        contract("PUT", 101, bid=1.0, ask=2.0),
    ]
    saturday = datetime(2026, 8, 22, 14, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="No executable"):
        CriticalEventScanner._select_candidate_pairs(
            contracts, 100, observed_at=saturday
        )


def test_contract_selection_rejects_stale_quotes_during_regular_hours():
    observed_at = datetime(2026, 8, 17, 15, 0, tzinfo=timezone.utc)
    stale = observed_at - timedelta(minutes=21)
    contracts = [
        contract("CALL", quote_time=stale),
        contract("PUT", quote_time=stale),
    ]

    with pytest.raises(ValueError, match="No executable"):
        CriticalEventScanner._select_candidate_pairs(
            contracts, 100, observed_at=observed_at
        )


def test_incomplete_intraday_candle_is_excluded():
    observed_at = datetime(2026, 8, 17, 15, 40, tzinfo=timezone.utc)
    payload = {"candles": [
        {"datetime": int(datetime(2026, 8, 17, 15, 15, tzinfo=timezone.utc).timestamp() * 1000),
         "open": 100, "high": 101, "low": 99, "close": 100, "volume": 100},
        {"datetime": int(datetime(2026, 8, 17, 15, 30, tzinfo=timezone.utc).timestamp() * 1000),
         "open": 100, "high": 101, "low": 99, "close": 100, "volume": 100},
    ]}

    bars = CriticalEventScanner._intraday_bars(payload, observed_at=observed_at)

    assert len(bars) == 1
    assert bars[0]["datetime"].minute == 15


def test_score_reaches_true_ten_point_maximum_and_exposes_economics():
    result = CriticalEventScanner._score(
        "XYZ",
        100,
        daily_bars(),
        (
            contract("CALL", bid=0.68, ask=0.70),
            contract("PUT", bid=0.68, ask=0.70),
        ),
        parsed_intraday_bars(),
    )

    assert result["total_score"] == 10
    assert result["score_maximum"] == 10
    assert set(result["scores"]) == {
        "compression", "option_value", "pressure", "ignition", "liquidity"
    }
    assert result["metrics"]["expected_net_value"] > 0
    assert 0 <= result["metrics"]["probability_of_profit"] <= 1
    assert result["option"]["modeled_entry_debit"] == pytest.approx(result["option"]["natural_debit"] + 0.03)
    assert result["option"]["estimated_fees"] == pytest.approx(0.03)
    assert "2%" not in result["model_target"]
    assert result["data_quality"]["event_calendar"] == "NOT_INTEGRATED"


def test_intraday_pressure_is_compared_with_same_time_of_day():
    signals = CriticalEventScanner._intraday_signals(
        parsed_intraday_bars(latest_volume=750, latest_width=0.2),
        daily_bars(),
    )

    assert signals["volume_ratio"] == pytest.approx(1.5)
    assert signals["sample_count"] >= 5
    assert signals["slot"] == "15:30 ET"


def test_expected_payoff_and_breakeven_probability_are_bounded():
    payoff = CriticalEventScanner._expected_absolute_normal_payoff(0, 10)
    probability = CriticalEventScanner._probability_outside_breakevens(0, 10, 8)

    assert payoff == pytest.approx(10 * (2 / 3.141592653589793) ** 0.5)
    assert 0 < probability < 1


def test_universe_is_restricted_to_four_supported_etfs():
    assert CriticalEventScanner._normalize_symbols(["aapl", "spy", "DIA", "TSLA"]) == ["SPY", "DIA"]
    assert CriticalEventScanner._normalize_symbols(["AAPL"]) == ["SPY", "QQQ", "IWM", "DIA"]
