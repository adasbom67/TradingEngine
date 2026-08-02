from app.config.strategy_config import PutSpreadConfig
from app.models.portfolio.portfolio_state import PortfolioState
from app.models.trades.bull_put_spread import BullPutSpread
from app.models.trades.trade_candidate import TradeCandidate
from app.risk.portfolio_constraints import PortfolioConstraintService
from tests.helpers import create_option


def candidate():
    return TradeCandidate(BullPutSpread(
        create_option(500, bid=1.50, ask=1.60),
        create_option(495, bid=0.70, ask=0.80),
    ))


def test_approves_quantity_within_risk_budget():
    decision = PortfolioConstraintService().evaluate(
        candidate(),
        PortfolioState(100000, 10000),
        PutSpreadConfig(maximum_risk_per_trade=1000),
    )
    assert decision.approved is True
    assert decision.maximum_quantity == 2


def test_rejects_when_max_positions_reached():
    decision = PortfolioConstraintService().evaluate(
        candidate(),
        PortfolioState(100000, 10000, open_positions=5),
        PutSpreadConfig(maximum_open_positions=5),
    )
    assert decision.approved is False
