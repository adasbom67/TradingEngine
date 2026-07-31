import pytest

from app.config.strategy_config import PutSpreadConfig


def test_default_strategy_config_is_valid():
    config = PutSpreadConfig()

    config.validate()


def test_strategy_config_requires_at_least_one_spread_width():
    config = PutSpreadConfig(
        allowed_spread_widths=(),
    )

    with pytest.raises(
        ValueError,
        match="At least one spread width is required",
    ):
        config.validate()


def test_strategy_config_rejects_zero_spread_width():
    config = PutSpreadConfig(
        allowed_spread_widths=(0.0,),
    )

    with pytest.raises(
        ValueError,
        match="Spread widths must be greater than zero",
    ):
        config.validate()


def test_strategy_config_rejects_negative_spread_width():
    config = PutSpreadConfig(
        allowed_spread_widths=(5.0, -10.0),
    )

    with pytest.raises(
        ValueError,
        match="Spread widths must be greater than zero",
    ):
        config.validate()


def test_strategy_config_accepts_multiple_positive_widths():
    config = PutSpreadConfig(
        allowed_spread_widths=(1.0, 2.0, 5.0, 10.0),
    )

    config.validate()

    assert config.allowed_spread_widths == (
        1.0,
        2.0,
        5.0,
        10.0,
    )
def test_default_trend_weights_total_100():
    config = PutSpreadConfig()

    config.validate()

    total = (
        config.trend_weight_sma_alignment
        + config.trend_weight_price_above_200
        + config.trend_weight_price_above_20
        + config.trend_weight_trend_confirmation
    )

    assert total == 100


def test_invalid_trend_weight_total_raises_error():
    config = PutSpreadConfig(
        trend_weight_sma_alignment=50,
        trend_weight_price_above_200=25,
        trend_weight_price_above_20=20,
        trend_weight_trend_confirmation=15,
    )

    with pytest.raises(
        ValueError,
        match="Trend evaluation weights must total 100",
    ):
        config.validate()


def test_negative_trend_weight_raises_error():
    config = PutSpreadConfig(
        trend_weight_sma_alignment=-10,
        trend_weight_price_above_200=50,
        trend_weight_price_above_20=40,
        trend_weight_trend_confirmation=20,
    )

    with pytest.raises(
        ValueError,
        match="Trend evaluation weights cannot be negative",
    ):
        config.validate()