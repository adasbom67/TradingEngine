from datetime import date
import pytest
from app.brokers.schwab_market_data import SchwabMarketDataClient, SchwabMarketDataError

class FakeResponse:
    def __init__(self,payload,status_code=200,text=""):
        self._payload=payload; self.status_code=status_code; self.text=text
    def raise_for_status(self):
        if self.status_code>=400: raise RuntimeError("HTTP failure")
    def json(self): return self._payload

class FakeSchwabClient:
    def __init__(self,response): self.response=response; self.calls=[]
    def get_option_chain(self,symbol,**kwargs): self.calls.append((symbol,kwargs)); return self.response

def test_market_data_client_requests_put_chain():
    raw={"symbol":"SPY","underlyingPrice":605.0}; fake=FakeSchwabClient(FakeResponse(raw))
    result=SchwabMarketDataClient(fake).get_put_option_chain("spy",from_date=date(2026,9,1),to_date=date(2026,9,15),strike_count=20)
    assert result==raw
    assert fake.calls[0][0]=="SPY"
    assert fake.calls[0][1]["strike_count"]==20
    assert fake.calls[0][1]["include_underlying_quote"] is True

def test_market_data_client_raises_clear_error():
    fake=FakeSchwabClient(FakeResponse({"error":"bad"},400,"bad request"))
    with pytest.raises(SchwabMarketDataError,match="SPY"):
        SchwabMarketDataClient(fake).get_put_option_chain("SPY")

class FakePriceHistoryClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get_price_history_every_day(self, symbol, **kwargs):
        self.calls.append((symbol, kwargs))
        return self.response


def test_market_data_client_requests_daily_history():
    payload = {"candles": [{"close": 100.0}]}
    fake = FakePriceHistoryClient(FakeResponse(payload))

    result = SchwabMarketDataClient(fake).get_daily_price_history(
        "spy",
        period_years=2,
    )

    assert result == payload
    assert fake.calls[0][0] == "SPY"
    assert "start_datetime" in fake.calls[0][1]
    assert "end_datetime" in fake.calls[0][1]
    assert fake.calls[0][1]["need_previous_close"] is True


def test_daily_history_rejects_empty_candles():
    fake = FakePriceHistoryClient(FakeResponse({"candles": []}))

    with pytest.raises(SchwabMarketDataError, match="no daily candles"):
        SchwabMarketDataClient(fake).get_daily_price_history("SPY")
