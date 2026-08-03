from datetime import date, datetime, timezone, timedelta
from app.models.market.option_contract import OptionContract
from app.models.trades.bull_put_spread import BullPutSpread
from app.models.trades.trade_candidate import TradeCandidate
from app.trading.models import BrokerAccount, BrokerAccountSnapshot, BrokerOrder, BrokerPosition
from app.trading.order_plan import BullPutOrderPlanBuilder
from app.trading.validation import OrderPlanValidator
from app.trading.service import DryRunTradingService
from app.trading.reconciliation import ReadOnlyReconciliationService


def candidate(decision="TRADE"):
    exp=date.today()+timedelta(days=35)
    short=OptionContract("SPY",exp,700,"PUT",1.5,1.6,1.55,-.2,100,1000,35)
    long=OptionContract("SPY",exp,695,"PUT",.7,.8,.75,-.15,100,1000,35)
    return TradeCandidate(BullPutSpread(short,long),score=92,decision=decision)

def test_builder_creates_credit_vertical():
    plan=BullPutOrderPlanBuilder().build_entry(candidate(),quantity=2)
    assert plan.symbol=="SPY" and plan.quantity==2 and plan.limit_price==.7
    assert plan.maximum_risk==860

def test_validator_accepts_valid_plan():
    plan=BullPutOrderPlanBuilder().build_entry(candidate())
    assert OrderPlanValidator().validate(plan).valid

def test_validator_rejects_expired_plan():
    c=candidate(); plan=BullPutOrderPlanBuilder().build_entry(c)
    assert not OrderPlanValidator().validate(plan,today=plan.legs[0].expiration).valid

class FakeBroker:
    def get_accounts(self): return [BrokerAccount("12345678","hash")]
    def get_account(self,h): return BrokerAccountSnapshot(self.get_accounts()[0],100000,50000)
    def get_positions(self,h): return [BrokerPosition("SPY",1)]
    def get_orders(self,h,**kw): return [BrokerOrder("1","FILLED")]
    def preview_order(self,h,o): return {"submission_enabled":False,"plan_id":o.plan_id}

def test_dry_run_never_submits_and_returns_preview():
    plan=BullPutOrderPlanBuilder().build_entry(candidate())
    result=DryRunTradingService(FakeBroker()).execute("hash",plan)
    assert result.validation.valid and result.preview["submission_enabled"] is False

def test_read_only_reconciliation():
    result=ReadOnlyReconciliationService().reconcile(FakeBroker(),"hash")
    assert result.successful and len(result.positions)==1 and len(result.orders)==1
