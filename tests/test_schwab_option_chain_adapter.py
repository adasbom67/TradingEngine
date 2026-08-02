from datetime import date
import pytest
from app.data.schwab_option_chain_adapter import SchwabOptionChainAdapter, SchwabOptionChainFormatError


def test_adapter_flattens_schwab_put_map():
    payload={"symbol":"SPY","underlyingPrice":605.25,"putExpDateMap":{"2026-09-04:35":{"500.0":[{"symbol":"SPY   260904P00500000","putCall":"PUT","strikePrice":500.0,"bid":1.5,"ask":1.6,"last":1.55,"delta":-0.2,"totalVolume":125,"openInterest":2500,"daysToExpiration":35}]}}}
    chain=SchwabOptionChainAdapter().to_option_chain(payload)
    assert chain.underlying_symbol=="SPY"
    assert chain.underlying_price==605.25
    assert chain.contract_count()==1
    c=chain.contracts[0]
    assert c.expiration_date==date(2026,9,4)
    assert c.strike==500.0
    assert c.option_type=="PUT"
    assert c.delta==-0.2
    assert c.volume==125
    assert c.open_interest==2500


def test_adapter_uses_requested_symbol_when_payload_omits_it():
    chain=SchwabOptionChainAdapter().to_option_chain({"underlyingPrice":605.25,"putExpDateMap":{}}, requested_symbol="spy")
    assert chain.underlying_symbol=="SPY"


def test_adapter_rejects_payload_without_underlying_price():
    with pytest.raises(SchwabOptionChainFormatError, match="underlying price"):
        SchwabOptionChainAdapter().to_option_chain({"putExpDateMap":{}}, requested_symbol="SPY")
