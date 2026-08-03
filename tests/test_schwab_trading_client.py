from datetime import datetime, timezone
from app.brokers.schwab_trading.client import SchwabTradingClient

class Response:
    status_code=200; text=""
    def __init__(self,p): self.p=p
    def raise_for_status(self): pass
    def json(self): return self.p
class Client:
    def get_account_numbers(self): return Response([{"accountNumber":"12345678","hashValue":"abc"}])
    def get_account(self,h,**kwargs): return Response({"securitiesAccount":{"accountNumber":"12345678","type":"MARGIN","currentBalances":{"liquidationValue":100000,"buyingPower":50000},"positions":[]}})
    def get_orders_for_account(self,h,**kwargs): return Response([])

def test_schwab_read_only_adapter_maps_account():
    b=SchwabTradingClient(Client()); a=b.get_accounts()[0]; snap=b.get_account(a.account_hash)
    assert a.masked_id=="****5678" and snap.account_value==100000

def test_schwab_read_only_adapter_reads_empty_positions_and_orders():
    b=SchwabTradingClient(Client())
    assert b.get_positions("abc")==[]
    assert b.get_orders("abc",from_time=datetime.now(timezone.utc),to_time=datetime.now(timezone.utc))==[]

def test_adapter_exposes_no_submission_method():
    assert not hasattr(SchwabTradingClient,"place_order")
