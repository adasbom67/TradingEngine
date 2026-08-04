from types import SimpleNamespace
from app.api.recommendations import _quote_payload
def contract(bid,ask): return SimpleNamespace(bid=bid,ask=ask,volume=100,open_interest=500)
def test_quote_audit_flags_material_difference():
    quote=_quote_payload(contract(2.00,2.10),contract(1.40,1.50),0.80)
    assert quote["natural_credit"]==0.50
    assert quote["midpoint_credit"]==0.60
    assert quote["audit_status"]=="REVIEW"
def test_quote_audit_accepts_aligned_credit():
    quote=_quote_payload(contract(2.00,2.10),contract(1.40,1.50),0.61)
    assert quote["audit_status"]=="ALIGNED"
