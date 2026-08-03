from fastapi.testclient import TestClient
from app.api.app import create_api

def test_live_submission_is_blocked():
    response=TestClient(create_api()).post('/api/orders/submit')
    assert response.status_code == 403

def test_backtest_request_validation():
    response=TestClient(create_api()).post('/api/backtests',json={'symbol':'SPY','initial_capital':100000,'minimum_entry_dte':45,'maximum_entry_dte':30,'spread_width':5})
    assert response.status_code == 422
