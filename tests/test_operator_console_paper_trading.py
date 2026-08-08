from datetime import date, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.paper_trading import create_paper_trading_router

def client(tmp_path):
    app=FastAPI();app.include_router(create_paper_trading_router(tmp_path/"paper_account.json"));return TestClient(app)

def test_paper_account_starts_uninitialized_and_simulation_only(tmp_path):
    payload=client(tmp_path).get("/api/paper/account").json();assert payload["initialized"] is False;assert payload["execution_mode"]=="SIMULATION_ONLY";assert payload["safeguards"]["broker_orders_enabled"] is False

def test_paper_account_lifecycle(tmp_path):
    api=client(tmp_path);assert api.post("/api/paper/initialize",json={"initial_cash":50000}).status_code==200
    opened=api.post("/api/paper/positions",json={"symbol":"SPY","expiration":(date.today()+timedelta(days=30)).isoformat(),"short_strike":500,"long_strike":495,"entry_credit":1.0,"quantity":1});assert opened.status_code==200
    pid=opened.json()["position"]["position_id"];assert opened.json()["account"]["summary"]["committed_risk"]==400
    marked=api.post(f"/api/paper/positions/{pid}/mark",json={"current_debit":0.5});assert marked.json()["position"]["unrealized_pnl"]==50
    closed=api.post(f"/api/paper/positions/{pid}/close",json={"exit_debit":0.5,"reason":"PROFIT_TARGET"});assert closed.json()["account"]["summary"]["realized_pnl"]==50

def test_paper_entry_preserves_recommendation_context_and_blocks_pass(tmp_path):
    api=client(tmp_path);api.post("/api/paper/initialize",json={"initial_cash":50000})
    expiration=(date.today()+timedelta(days=30)).isoformat()
    blocked=api.post("/api/paper/positions",json={"symbol":"SPY","expiration":expiration,"short_strike":500,"long_strike":495,"entry_credit":1.0,"entry_decision":"PASS"})
    assert blocked.status_code==400;assert "PASS recommendations" in blocked.json()["detail"]
    watch_without_approval=api.post("/api/paper/positions",json={"symbol":"SPY","expiration":expiration,"short_strike":500,"long_strike":495,"entry_credit":1.0,"entry_decision":"WATCH"})
    assert watch_without_approval.status_code==400
    opened=api.post("/api/paper/positions",json={"symbol":"SPY","expiration":expiration,"short_strike":500,"long_strike":495,"entry_credit":1.0,"entry_decision":"WATCH","allow_watch_simulation":True,"entry_score":82.5,"entry_thesis":["Strong liquidity; regime requires caution."],"entry_constraints":{"minimum_score":80},"market_regime":"high_volatility","source_scan_reference":"2026-08-08T15:00:00+00:00","selected_pricing_method":"NATURAL","quote_audit_status":"ALIGNED"})
    assert opened.status_code==200
    position=opened.json()["position"]
    assert position["entry_decision"]=="WATCH";assert position["experimental"] is True
    assert position["entry_score"]==82.5;assert position["entry_constraints"]["minimum_score"]==80

def test_legacy_ledger_positions_receive_safe_metadata_defaults(tmp_path):
    api=client(tmp_path);api.post("/api/paper/initialize",json={"initial_cash":50000})
    expiration=(date.today()+timedelta(days=30)).isoformat()
    opened=api.post("/api/paper/positions",json={"symbol":"SPY","expiration":expiration,"short_strike":500,"long_strike":495,"entry_credit":1.0})
    assert opened.json()["position"]["entry_decision"]=="MANUAL"
