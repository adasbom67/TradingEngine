from app.config.strategy_config import PutSpreadConfig
from app.evaluation.trade_decision import TradeDecision, TradeDecisionEngine
from app.models.trades.bull_put_spread import BullPutSpread
from app.models.trades.trade_candidate import TradeCandidate
from tests.helpers import create_option


def candidate(**overrides):
    values = {
        "spread": BullPutSpread(create_option(500), create_option(495)),
        "score": 85,
        "probability_of_profit": 0.80,
        "return_on_risk": 0.15,
        "managed_expected_value": 10.0,
        "market_regime": "bullish",
    }
    values.update(overrides)
    return TradeCandidate(**values)


def test_trade_decision_when_all_thresholds_pass():
    result = TradeDecisionEngine().evaluate(candidate(), PutSpreadConfig())
    assert result.decision == TradeDecision.TRADE


def test_watch_for_neutral_regime_without_hard_failure():
    result = TradeDecisionEngine().evaluate(
        candidate(market_regime="neutral"),
        PutSpreadConfig(),
    )
    assert result.decision == TradeDecision.WATCH


def test_pass_for_negative_managed_expected_value():
    result = TradeDecisionEngine().evaluate(
        candidate(managed_expected_value=-1),
        PutSpreadConfig(),
    )
    assert result.decision == TradeDecision.PASS
