from datetime import date

from app.config.strategy_config import PutSpreadConfig
from app.paper.ledger import PaperLedger
from app.paper.manager import PaperPositionManager
from app.paper.service import PaperTradingService


class FakeMarketData:
    def __init__(self, payload):
        self.payload = payload

    def get_put_option_chain(self, symbol, from_date=None, to_date=None):
        return self.payload

    def get_call_option_chain(self, symbol, from_date=None, to_date=None):
        return self.payload


def payload(short_ask: float, long_bid: float):
    expiration = "2027-01-15:30"
    return {
        "symbol": "SPY",
        "underlyingPrice": 720.0,
        "putExpDateMap": {
            expiration: {
                "700.0": [{
                    "symbol": "SPY270115P00700000", "putCall": "PUT",
                    "strikePrice": 700.0, "bid": short_ask - 0.05,
                    "ask": short_ask, "last": short_ask,
                    "delta": -0.20, "totalVolume": 100,
                    "openInterest": 1000, "daysToExpiration": 30,
                }],
                "695.0": [{
                    "symbol": "SPY270115P00695000", "putCall": "PUT",
                    "strikePrice": 695.0, "bid": long_bid,
                    "ask": long_bid + 0.05, "last": long_bid,
                    "delta": -0.15, "totalVolume": 100,
                    "openInterest": 1000, "daysToExpiration": 30,
                }],
            }
        },
    }


def call_payload(short_ask: float, long_bid: float):
    expiration = "2027-01-15:30"
    return {
        "symbol": "SPY",
        "underlyingPrice": 600.0,
        "callExpDateMap": {
            expiration: {
                "605.0": [{
                    "symbol": "SPY270115C00605000", "putCall": "CALL",
                    "strikePrice": 605.0, "bid": short_ask - 0.05,
                    "ask": short_ask, "last": short_ask,
                    "delta": 0.20, "totalVolume": 100,
                    "openInterest": 1000, "daysToExpiration": 30,
                }],
                "608.0": [{
                    "symbol": "SPY270115C00608000", "putCall": "CALL",
                    "strikePrice": 608.0, "bid": long_bid,
                    "ask": long_bid + 0.05, "last": long_bid,
                    "delta": 0.12, "totalVolume": 100,
                    "openInterest": 1000, "daysToExpiration": 30,
                }],
            }
        },
    }


def make_service(tmp_path):
    service = PaperTradingService(PaperLedger(tmp_path / "paper.json"))
    service.initialize(100_000)
    position = service.open_position(
        "SPY", date(2027, 1, 15), 700, 695, 1.0,
        opened_on=date(2026, 12, 1),
    )
    return service, position


def test_manager_closes_profit_target(tmp_path):
    service, position = make_service(tmp_path)
    manager = PaperPositionManager(service, FakeMarketData(payload(0.60, 0.20)))
    result = manager.manage_all(PutSpreadConfig(), as_of=date(2026, 12, 16))[0]
    assert result.action == "CLOSED"
    assert result.reason == "PROFIT_TARGET"
    assert not service.status().open_positions


def test_manager_marks_open_position(tmp_path):
    service, position = make_service(tmp_path)
    manager = PaperPositionManager(service, FakeMarketData(payload(1.05, 0.20)))
    result = manager.manage_all(PutSpreadConfig(), as_of=date(2026, 12, 16))[0]
    assert result.action == "MARKED"
    assert service.status().open_positions[0].current_debit == 0.85
    assert service.status().snapshots


def test_manager_closes_at_exit_dte(tmp_path):
    service, position = make_service(tmp_path)
    manager = PaperPositionManager(service, FakeMarketData(payload(1.05, 0.20)))
    result = manager.manage_all(PutSpreadConfig(exit_dte=7), as_of=date(2027, 1, 10))[0]
    assert result.action == "CLOSED"
    assert result.reason == "EXIT_DTE"


def test_manager_can_recommend_exit_without_auto_closing(tmp_path):
    service, position = make_service(tmp_path)
    manager = PaperPositionManager(service, FakeMarketData(payload(0.60, 0.20)))
    result = manager.manage_all(
        PutSpreadConfig(), as_of=date(2026, 12, 16), auto_close=False
    )[0]
    assert result.action == "EXIT_RECOMMENDED"
    assert result.reason == "PROFIT_TARGET"
    assert service.status().open_positions[0].current_debit == 0.40


def test_manager_marks_bear_call_from_live_call_chain(tmp_path):
    service = PaperTradingService(PaperLedger(tmp_path / "paper.json"))
    service.initialize(100_000)
    position = service.open_position(
        "SPY", date(2027, 1, 15), 605, 608, 1.0,
        opened_on=date(2026, 12, 1), strategy_type="BEAR_CALL",
    )
    manager = PaperPositionManager(
        service, FakeMarketData(call_payload(1.05, 0.20))
    )
    result = manager.manage_all(
        PutSpreadConfig(), as_of=date(2026, 12, 16), auto_close=False
    )[0]
    assert result.position_id == position.position_id
    assert result.action == "MARKED"
    assert service.status().open_positions[0].current_debit == 0.85
