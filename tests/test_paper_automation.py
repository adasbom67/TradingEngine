from datetime import date

from app.models.market.option_contract import OptionContract
from app.models.trades.bull_put_spread import BullPutSpread
from app.models.trades.trade_candidate import TradeCandidate
from app.paper.automation import PaperTradeAutomation
from app.paper.ledger import PaperLedger
from app.paper.service import PaperTradingService


def _candidate(decision: str, *, rank: int = 1, maximum_quantity: int = 1):
    expiration = date(2027, 1, 15)
    short = OptionContract(
        symbol="SPY270115P00700000",
        expiration_date=expiration,
        strike=700,
        option_type="PUT",
        bid=1.25,
        ask=1.30,
        last=1.27,
        delta=-0.20,
        volume=100,
        open_interest=1000,
        days_to_expiration=45,
    )
    long = OptionContract(
        symbol="SPY270115P00695000",
        expiration_date=expiration,
        strike=695,
        option_type="PUT",
        bid=0.55,
        ask=0.60,
        last=0.57,
        delta=-0.15,
        volume=100,
        open_interest=1000,
        days_to_expiration=45,
    )
    candidate = TradeCandidate(BullPutSpread(short_put=short, long_put=long))
    candidate.decision = decision
    candidate.decision_reasons = [f"Scanner decision: {decision}."]
    candidate.rank = rank
    candidate.score = 90
    candidate.maximum_quantity = maximum_quantity
    return candidate


def test_paper_automation_opens_only_trade_candidate(tmp_path):
    service = PaperTradingService(PaperLedger(tmp_path / "paper.json"))
    service.initialize(100_000)
    result = PaperTradeAutomation(service).process(
        "SPY", [_candidate("TRADE")], observed_on=date(2026, 12, 1)
    )

    assert result.action == "OPENED"
    assert result.position is not None
    assert len(service.status().open_positions) == 1
    assert service.status().observations[-1].decision == "TRADE"


def test_paper_automation_records_watch_without_opening(tmp_path):
    service = PaperTradingService(PaperLedger(tmp_path / "paper.json"))
    service.initialize(100_000)
    result = PaperTradeAutomation(service).process(
        "SPY", [_candidate("WATCH")], observed_on=date(2026, 12, 1)
    )

    assert result.action == "NO_TRADE"
    assert result.decision == "WATCH"
    assert not service.status().open_positions
    assert service.status().observations[-1].decision == "WATCH"


def test_paper_automation_prevents_duplicate_symbol(tmp_path):
    service = PaperTradingService(PaperLedger(tmp_path / "paper.json"))
    service.initialize(100_000)
    automation = PaperTradeAutomation(service)
    automation.process("SPY", [_candidate("TRADE")], observed_on=date(2026, 12, 1))
    result = automation.process(
        "SPY", [_candidate("TRADE")], observed_on=date(2026, 12, 2)
    )

    assert result.action == "NO_TRADE"
    assert result.decision == "SKIP"
    assert len(service.status().open_positions) == 1


def test_paper_automation_honors_candidate_maximum_quantity(tmp_path):
    service = PaperTradingService(PaperLedger(tmp_path / "paper.json"))
    service.initialize(100_000)
    result = PaperTradeAutomation(service).process(
        "SPY",
        [_candidate("TRADE", maximum_quantity=2)],
        quantity=5,
        observed_on=date(2026, 12, 1),
    )

    assert result.position is not None
    assert result.position.quantity == 2
