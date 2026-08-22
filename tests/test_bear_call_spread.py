from datetime import date

import pytest

from app.config.strategy_config import BearCallSpreadConfig
from app.evaluation.default_pipeline import create_default_candidate_pipeline
from app.models.market.option_chain import OptionChain
from app.models.market.option_contract import OptionContract
from app.models.market.price_snapshot import PriceSnapshot
from app.models.market.trend_analysis import TrendAnalysis
from app.models.trades.bear_call_spread import BearCallSpread
from app.paper.ledger import PaperLedger
from app.paper.service import PaperTradingService
from app.selection.option_chain_filter import OptionChainFilter
from app.strategies.bear_call_spread_builder import BearCallSpreadBuilder


def call(strike, bid, ask, delta, *, option_type="CALL"):
    return OptionContract(
        symbol=f"SPY270115C{int(strike * 1000):08d}",
        expiration_date=date(2027, 1, 15),
        strike=float(strike),
        option_type=option_type,
        bid=float(bid),
        ask=float(ask),
        last=(bid + ask) / 2,
        delta=delta,
        volume=200,
        open_interest=1000,
        days_to_expiration=35,
    )


def test_bear_call_payoff_is_risk_defined():
    spread = BearCallSpread(
        short_call=call(605, 1.50, 1.60, 0.20),
        long_call=call(608, 0.40, 0.50, 0.12),
    )
    assert spread.width == 3
    assert spread.credit == pytest.approx(1.0)
    assert spread.max_profit == pytest.approx(100)
    assert spread.max_loss == pytest.approx(200)
    assert spread.breakeven == pytest.approx(606)
    assert spread.direction == "BEARISH"


def test_bear_call_filter_and_builder_use_fixed_higher_strike_hedges():
    short = call(605, 1.50, 1.60, 0.20)
    hedge = call(608, 0.40, 0.50, 0.12)
    wrong_width = call(609, 0.30, 0.40, 0.10)
    chain = OptionChain("SPY", 600, [short, hedge, wrong_width])
    config = BearCallSpreadConfig(minimum_credit=0.50)
    option_filter = OptionChainFilter()

    shorts, diagnostics = option_filter.filter_calls_with_diagnostics(chain, config)
    hedges, diagnostics = option_filter.filter_hedge_calls_with_diagnostics(
        chain, config, diagnostics
    )
    candidates, diagnostics = BearCallSpreadBuilder().build_with_diagnostics(
        shorts, config, diagnostics, long_calls=hedges
    )

    assert candidates
    assert all(item.spread.long_call.strike > item.spread.short_call.strike for item in candidates)
    assert {item.spread.width for item in candidates} <= {2.0, 3.0, 5.0}
    assert diagnostics.strategy_type == "BEAR_CALL"
    assert diagnostics.total_calls == 3


def test_bear_call_pipeline_scores_bearish_market_as_favorable():
    chain = OptionChain(
        "SPY",
        600,
        [call(605, 1.50, 1.60, 0.20), call(608, 0.40, 0.50, 0.12)],
    )
    snapshot = PriceSnapshot(
        symbol="SPY", current_price=590, sma20=595, sma200=610, rsi=42, atr=7
    )
    candidates, diagnostics = create_default_candidate_pipeline("BEAR_CALL").run_with_diagnostics(
        chain,
        snapshot,
        TrendAnalysis(passed=True, score=100, reasons=["Bearish alignment passed."]),
        BearCallSpreadConfig(minimum_credit=0.50),
    )
    assert len(candidates) == 1
    assert candidates[0].market_regime == "bearish"
    assert candidates[0].score > 70
    assert diagnostics.candidates_ranked == 1


def test_paper_service_accepts_bear_call_and_preserves_strategy(tmp_path):
    service = PaperTradingService(PaperLedger(tmp_path / "paper.json"))
    position = service.open_position(
        "SPY",
        date(2027, 1, 15),
        605,
        608,
        1.0,
        strategy_type="BEAR_CALL",
    )
    assert position.width == 3
    assert position.maximum_risk == 200
    assert service.status().open_positions[0].strategy_type == "BEAR_CALL"


def test_bear_call_rejects_unhedged_strike_order(tmp_path):
    service = PaperTradingService(PaperLedger(tmp_path / "paper.json"))
    with pytest.raises(ValueError, match="below the long strike"):
        service.open_position(
            "SPY",
            date(2027, 1, 15),
            608,
            605,
            1.0,
            strategy_type="BEAR_CALL",
        )
