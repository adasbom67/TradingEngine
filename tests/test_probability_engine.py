from app.config.strategy_config import PutSpreadConfig
from app.evaluation.probability_engine import ProbabilityEngine
from app.models.trades.bull_put_spread import BullPutSpread
from tests.helpers import create_option


def _spread():
    return BullPutSpread(
        create_option(500, bid=1.50, ask=1.60, delta=-0.20),
        create_option(495, bid=0.70, ask=0.80, delta=-0.10),
    )


def test_probability_engine_calculates_delta_proxy_and_unmanaged_ev():
    result = ProbabilityEngine().evaluate(_spread())

    assert result.probability_of_profit == 0.80
    assert result.probability_of_loss == 0.20
    assert round(result.unmanaged_expected_value, 2) == -30.0


def test_probability_engine_models_profit_target_and_stop_loss():
    config = PutSpreadConfig(
        profit_target_percent=50,
        stop_loss_percent=200,
    )

    result = ProbabilityEngine().evaluate(_spread(), config)

    assert result.profit_target_amount == 35.0
    assert result.stop_loss_amount == 140.0
    assert round(result.managed_expected_value, 2) == 0.0
    assert result.expected_value == result.managed_expected_value
