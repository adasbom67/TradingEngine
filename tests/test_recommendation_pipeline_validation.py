from datetime import date

from app.config.strategy_config import PutSpreadConfig
from app.evaluation.pipeline_diagnostics import PipelineDiagnostics
from app.models.market.option_chain import OptionChain
from app.models.market.option_contract import OptionContract
from app.selection.option_chain_filter import OptionChainFilter
from app.strategies.bull_put_spread_builder import BullPutSpreadBuilder


def contract(
    strike: float,
    *,
    delta: float = -0.20,
    bid: float = 1.00,
    ask: float = 1.10,
    volume: int = 100,
    open_interest: int = 500,
) -> OptionContract:
    return OptionContract(
        symbol=f"SPY-{strike}",
        expiration_date=date(2026, 9, 18),
        strike=strike,
        option_type="PUT",
        bid=bid,
        ask=ask,
        last=(bid + ask) / 2,
        delta=delta,
        volume=volume,
        open_interest=open_interest,
        days_to_expiration=45,
    )


def test_filter_diagnostics_identify_delta_and_liquidity_bottlenecks():
    chain = OptionChain(
        underlying_symbol="SPY",
        underlying_price=700,
        contracts=[
            contract(680),
            contract(675, delta=-0.40),
            contract(670, volume=0),
        ],
    )
    config = PutSpreadConfig()
    eligible, diagnostics = OptionChainFilter().filter_puts_with_diagnostics(
        chain, config
    )
    assert len(eligible) == 1
    assert diagnostics.total_puts == 3
    assert diagnostics.filter_rejections["delta_above_maximum"] == 1
    assert diagnostics.filter_rejections["volume_below_minimum"] == 1


def test_hedge_filter_ignores_delta_short_bid_and_daily_volume():
    chain = OptionChain(
        underlying_symbol="SPY",
        underlying_price=700,
        contracts=[
            contract(680, delta=None, bid=0.05, ask=0.10),
            contract(675, delta=-0.05, bid=0.05, ask=0.10, volume=0),
        ],
    )
    hedges, diagnostics = OptionChainFilter().filter_hedge_puts_with_diagnostics(
        chain, PutSpreadConfig()
    )

    assert [item.strike for item in hedges] == [680, 675]
    assert diagnostics.eligible_hedge_puts == 2
    assert "volume_below_minimum" not in diagnostics.hedge_filter_rejections


def test_hedge_filter_uses_reduced_open_interest_floor():
    chain = OptionChain(
        underlying_symbol="SPY",
        underlying_price=700,
        contracts=[contract(680, open_interest=25), contract(675, open_interest=24)],
    )
    hedges, diagnostics = OptionChainFilter().filter_hedge_puts_with_diagnostics(
        chain, PutSpreadConfig()
    )

    assert [item.strike for item in hedges] == [680]
    assert diagnostics.hedge_filter_rejections["open_interest_below_minimum"] == 1


def test_off_hours_policy_can_skip_short_leg_volume_gate():
    chain = OptionChain(
        underlying_symbol="SPY",
        underlying_price=700,
        contracts=[contract(680, volume=0)],
    )
    eligible, diagnostics = OptionChainFilter().filter_puts_with_diagnostics(
        chain, PutSpreadConfig(enforce_minimum_volume=False)
    )

    assert [item.strike for item in eligible] == [680]
    assert diagnostics.minimum_volume_enforced is False


def test_short_quote_width_is_relative_to_option_midpoint():
    chain = OptionChain(
        underlying_symbol="SPY",
        underlying_price=700,
        contracts=[
            contract(680, bid=2.00, ask=2.40),
            contract(675, bid=1.00, ask=1.40),
        ],
    )
    eligible, diagnostics = OptionChainFilter().filter_puts_with_diagnostics(
        chain, PutSpreadConfig()
    )

    assert [item.strike for item in eligible] == [680]
    assert diagnostics.filter_rejections["relative_bid_ask_spread_too_wide"] == 1


def test_builder_diagnostics_identify_width_bottleneck():
    config = PutSpreadConfig(allowed_spread_widths=(5.0,))
    puts = [contract(680), contract(670)]
    candidates, diagnostics = BullPutSpreadBuilder().build_with_diagnostics(
        puts, config
    )
    assert candidates == []
    assert diagnostics.ordered_strike_pairs == 1
    assert diagnostics.allowed_width_pairs == 0
    assert diagnostics.builder_rejections["spread_width_not_allowed"] == 1
    assert diagnostics.first_zero_stage() == "allowed_width_pairs"


def test_pipeline_diagnostics_payload_exposes_bottleneck():
    diagnostics = PipelineDiagnostics(
        total_contracts=100,
        total_puts=50,
        eligible_puts=0,
        filter_rejections={"open_interest_below_minimum": 50},
    )
    payload = diagnostics.to_dict()
    assert payload["first_zero_stage"] == "eligible_puts"
    assert payload["primary_bottleneck"]["reason"] == (
        "filter:open_interest_below_minimum"
    )
