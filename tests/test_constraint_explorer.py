from datetime import date
from app.config.strategy_config import PutSpreadConfig
from app.models.market.option_chain import OptionChain
from app.models.market.option_contract import OptionContract
from app.selection.option_chain_filter import OptionChainFilter, delta_bucket

def c(strike, delta):
    return OptionContract(symbol=f"SPY-{strike}", expiration_date=date(2026,9,18), strike=strike,
        option_type="PUT", bid=1.0, ask=1.1, last=1.05, delta=delta, volume=100,
        open_interest=500, days_to_expiration=45)

def test_delta_bucket_boundaries():
    assert delta_bucket(-0.03) == "<0.05"
    assert delta_bucket(-0.07) == "0.05-0.10"
    assert delta_bucket(-0.12) == "0.10-0.15"
    assert delta_bucket(-0.17) == "0.15-0.20"
    assert delta_bucket(-0.22) == "0.20-0.25"
    assert delta_bucket(-0.27) == "0.25-0.30"
    assert delta_bucket(-0.35) == "0.30-0.40"
    assert delta_bucket(-0.45) == ">=0.40"
    assert delta_bucket(None) == "missing"

def test_filter_diagnostics_capture_delta_distribution():
    chain = OptionChain(underlying_symbol="SPY", underlying_price=700,
        contracts=[c(690,-0.07),c(685,-0.12),c(680,-0.17),c(675,-0.22),c(670,-0.35)])
    _, d = OptionChainFilter().filter_puts_with_diagnostics(chain, PutSpreadConfig())
    assert sum(d.delta_distribution.values()) == 5
    assert d.delta_distribution["0.05-0.10"] == 1
    assert d.delta_distribution["0.30-0.40"] == 1
