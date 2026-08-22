from datetime import date, datetime, timedelta, timezone

from app.data.critical_event_archive import CriticalEventArchive
from app.models.market.option_contract import OptionContract


def option(symbol, strike=100, dte=32):
    return OptionContract(
        symbol=symbol,
        expiration_date=date(2026, 9, 18),
        strike=strike,
        option_type="CALL" if "C" in symbol else "PUT",
        bid=1.0,
        ask=1.1,
        last=1.05,
        delta=0.5,
        volume=100,
        open_interest=500,
        days_to_expiration=dte,
        implied_volatility=20.0,
        quote_time=datetime(2026, 8, 20, 15, tzinfo=timezone.utc),
    )


def scored():
    return [{
        "symbol": "SPY",
        "total_score": 6,
        "option": {"call_symbol": "SPY-C-100", "put_symbol": "SPY-P-100"},
    }]


def test_archive_deduplicates_interval_and_reports_storage(tmp_path):
    archive = CriticalEventArchive(tmp_path / "archive.sqlite3", maximum_mib=16)
    observed = datetime(2026, 8, 20, 15, tzinfo=timezone.utc)
    contracts = [option("SPY-C-100"), option("SPY-P-100")]

    first = archive.capture("SPY", 100, contracts, scored(), daily_bar_count=500, intraday_bar_count=200, captured_at=observed)
    duplicate = archive.capture("SPY", 100, contracts, scored(), daily_bar_count=500, intraday_bar_count=200, captured_at=observed + timedelta(minutes=5))
    status = archive.status()

    assert first["stored"] is True
    assert duplicate == {"stored": False, "reason": "INTERVAL_DEDUPLICATED"}
    assert status["snapshot_count"] == 1
    assert status["contract_count"] == 2
    assert status["physical_bytes"] > 0
    assert status["projected_annual_bytes"] > 0


def test_archive_retains_selected_contract_outside_surface(tmp_path):
    archive = CriticalEventArchive(tmp_path / "archive.sqlite3")
    observed = datetime(2026, 8, 20, 15, tzinfo=timezone.utc)
    contracts = [option("SPY-C-100", strike=130), option("SPY-P-100", strike=130)]

    result = archive.capture("SPY", 100, contracts, scored(), daily_bar_count=500, intraday_bar_count=200, captured_at=observed)

    assert result["contracts"] == 2


def test_archive_does_not_store_contracts_the_scanner_did_not_evaluate(tmp_path):
    archive = CriticalEventArchive(tmp_path / "archive.sqlite3")
    observed = datetime(2026, 8, 20, 15, tzinfo=timezone.utc)
    contracts = [option("SPY-C-100"), option("SPY-P-100"), option("SPY-C-101", strike=101)]

    result = archive.capture("SPY", 100, contracts, scored(), daily_bar_count=500, intraday_bar_count=200, captured_at=observed)

    assert result["contracts"] == 2


def test_disabled_archive_does_not_create_database(tmp_path):
    path = tmp_path / "archive.sqlite3"
    archive = CriticalEventArchive(path, enabled=False)

    assert archive.capture("SPY", 100, [], [], daily_bar_count=0, intraday_bar_count=0)["reason"] == "DISABLED"
    assert not path.exists()
