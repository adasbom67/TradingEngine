from datetime import date
from app.config.strategy_config import PutSpreadConfig
from app.models.market.option_chain import OptionChain
from app.models.market.trend_analysis import TrendAnalysis
from app.scanners.live_candidate_scanner import LiveCandidateScanner
from tests.helpers import create_price_snapshot

class FakeMarketData:
    def __init__(self): self.request=None
    def get_put_option_chain(self,symbol,from_date=None,to_date=None,strike_count=None):
        self.request={"symbol":symbol,"from_date":from_date,"to_date":to_date}; return {"raw":"chain"}
class FakeAdapter:
    def to_option_chain(self,payload,requested_symbol=None):
        assert payload=={"raw":"chain"}; assert requested_symbol=="SPY"; return OptionChain("SPY",605.0,[])
class FakePipeline:
    def __init__(self): self.received=None
    def run(self,chain,price_snapshot,trend_analysis,config):
        self.received=(chain,price_snapshot,trend_analysis,config); return ["ranked-candidate"]

def test_live_scanner_fetches_normalizes_and_runs_pipeline():
    market=FakeMarketData(); pipeline=FakePipeline(); scanner=LiveCandidateScanner(market,pipeline,FakeAdapter())
    config=PutSpreadConfig(minimum_dte=30,maximum_dte=45)
    result=scanner.scan("spy",create_price_snapshot(),TrendAnalysis(passed=True,score=100),config,as_of=date(2026,7,31))
    assert result==["ranked-candidate"]
    assert market.request=={"symbol":"SPY","from_date":date(2026,8,30),"to_date":date(2026,9,14)}
    assert pipeline.received[0].underlying_symbol=="SPY"

class FakeLiveMarketData(FakeMarketData):
    def __init__(self):
        super().__init__()
        self.history_request = None

    def get_daily_price_history(self, symbol, period_years=2):
        self.history_request = (symbol, period_years)
        return {"candles": [{"close": 1.0}]}


class FakeMarketAnalysis:
    def build(self, symbol, payload, config):
        assert symbol == "SPY"
        assert payload == {"candles": [{"close": 1.0}]}
        return create_price_snapshot(), TrendAnalysis(passed=True, score=100)


def test_scan_live_builds_analysis_and_runs_existing_scan():
    market = FakeLiveMarketData()
    pipeline = FakePipeline()
    scanner = LiveCandidateScanner(
        market,
        pipeline,
        FakeAdapter(),
        FakeMarketAnalysis(),
    )
    config = PutSpreadConfig(minimum_dte=30, maximum_dte=45)

    result = scanner.scan_live(
        "spy",
        config,
        as_of=date(2026, 7, 31),
        price_history_years=3,
    )

    assert result == ["ranked-candidate"]
    assert market.history_request == ("SPY", 3)
