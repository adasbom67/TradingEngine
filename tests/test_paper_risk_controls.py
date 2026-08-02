from datetime import date

from app.config.strategy_config import PutSpreadConfig
from app.models.market.option_contract import OptionContract
from app.models.trades.bull_put_spread import BullPutSpread
from app.models.trades.trade_candidate import TradeCandidate
from app.paper.automation import PaperTradeAutomation
from app.paper.ledger import PaperLedger
from app.paper.service import PaperTradingService


def candidate():
    expiration = date(2027, 1, 15)
    short = OptionContract("S", expiration, 700, "PUT", 1.25, 1.30, 1.27, -0.2, 100, 1000, 45)
    long = OptionContract("L", expiration, 695, "PUT", 0.55, 0.60, 0.57, -0.15, 100, 1000, 45)
    item = TradeCandidate(BullPutSpread(short_put=short, long_put=long))
    item.decision = "TRADE"
    item.decision_reasons = ["Approved"]
    item.rank = 1
    item.score = 90
    item.maximum_quantity = 10
    return item


def test_automation_rejects_when_total_risk_room_is_insufficient(tmp_path):
    service = PaperTradingService(PaperLedger(tmp_path / "paper.json"))
    service.initialize(1_000)
    config = PutSpreadConfig(
        maximum_risk_per_trade=500,
        maximum_account_risk_percent=0.01,
        maximum_total_risk_percent=0.05,
    )
    result = PaperTradeAutomation(service, config).process(
        "SPY", [candidate()], observed_on=date(2026, 12, 1)
    )
    assert result.action == "NO_TRADE"
    assert result.decision == "PASS"
