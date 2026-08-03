from app.web import create_app
from app.web.settings import LocalSettingsStore


def test_web_console_is_local_operator_console(tmp_path):
    app=create_app(testing=True, settings_path=str(tmp_path / "local.json"))
    response=app.test_client().get("/")
    assert response.status_code == 200
    assert b"Operations Console" in response.data
    assert b"Submission disabled" in response.data


def test_live_submission_route_is_forbidden(tmp_path):
    app=create_app(testing=True, settings_path=str(tmp_path / "local.json"))
    response=app.test_client().post("/trade/submit")
    assert response.status_code == 405


def test_local_settings_store_is_atomic(tmp_path):
    store=LocalSettingsStore(tmp_path / "local.json")
    store.save_account("HASH-SECRET-1234", "1234")
    assert store.load().schwab_live_account_hash == "HASH-SECRET-1234"
    assert not (tmp_path / "local.json.tmp").exists()


def test_backtest_form_renders_without_broker_call(tmp_path):
    app=create_app(testing=True, settings_path=str(tmp_path / "local.json"))
    response=app.test_client().get("/backtest")
    assert response.status_code == 200
    assert b"Run backtest" in response.data


def test_recommendations_form_renders_without_broker_call(tmp_path):
    app=create_app(testing=True, settings_path=str(tmp_path / "local.json"))
    response=app.test_client().get("/recommendations")
    assert response.status_code == 200
    assert b"Create top TRADE dry-run" in response.data


def test_recommendations_uses_balanced_strategy(monkeypatch, tmp_path):
    from app.config.strategy_config import DEFAULT_STRATEGIES
    captured = {}

    class FakeScanner:
        def __init__(self, *args, **kwargs):
            pass

        def scan_live(self, *, symbol, config, **kwargs):
            captured["symbol"] = symbol
            captured["config"] = config
            return []

    monkeypatch.setattr("app.web.app.create_schwab_client", lambda: object())
    monkeypatch.setattr("app.web.app.SchwabMarketDataClient", lambda client: object())
    monkeypatch.setattr("app.web.app.LiveCandidateScanner", FakeScanner)
    monkeypatch.setattr("app.web.app.create_default_candidate_pipeline", lambda: object())
    monkeypatch.setattr("app.web.app.MarketAnalysisBuilder", lambda: object())

    app = create_app(testing=True, settings_path=str(tmp_path / "settings.json"))
    response = app.test_client().post("/recommendations", data={"symbol": "SPY", "action": "scan"})

    assert response.status_code == 200
    assert captured["symbol"] == "SPY"
    assert captured["config"] is DEFAULT_STRATEGIES["Balanced"]
    assert b"bull_put_spread" not in response.data


def test_recommendations_wires_market_analysis_by_keyword(monkeypatch, tmp_path):
    captured = {}

    class FakeScanner:
        def __init__(self, *args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs

        def scan_live(self, *, symbol, config, **kwargs):
            return []

    fake_market_data = object()
    fake_pipeline = object()
    fake_market_analysis = object()

    monkeypatch.setattr("app.web.app.create_schwab_client", lambda: object())
    monkeypatch.setattr(
        "app.web.app.SchwabMarketDataClient",
        lambda client: fake_market_data,
    )
    monkeypatch.setattr("app.web.app.LiveCandidateScanner", FakeScanner)
    monkeypatch.setattr(
        "app.web.app.create_default_candidate_pipeline",
        lambda: fake_pipeline,
    )
    monkeypatch.setattr(
        "app.web.app.MarketAnalysisBuilder",
        lambda: fake_market_analysis,
    )

    app = create_app(
        testing=True,
        settings_path=str(tmp_path / "settings.json"),
    )
    response = app.test_client().post(
        "/recommendations",
        data={"symbol": "SPY", "action": "scan"},
    )

    assert response.status_code == 200
    assert captured["args"] == ()
    assert captured["kwargs"]["market_data"] is fake_market_data
    assert captured["kwargs"]["pipeline"] is fake_pipeline
    assert captured["kwargs"]["market_analysis"] is fake_market_analysis


def test_recommendations_renders_real_bull_put_spread_fields(monkeypatch, tmp_path):
    from datetime import date

    from app.models.market.option_contract import OptionContract
    from app.models.trades.bull_put_spread import BullPutSpread
    from app.models.trades.trade_candidate import TradeCandidate

    short_put = OptionContract(
        symbol="SPY  260918P00720000",
        expiration_date=date(2026, 9, 18),
        strike=720.0,
        option_type="PUT",
        bid=1.10,
        ask=1.15,
        last=1.12,
        delta=-0.20,
        volume=100,
        open_interest=1000,
        days_to_expiration=47,
    )
    long_put = OptionContract(
        symbol="SPY  260918P00715000",
        expiration_date=date(2026, 9, 18),
        strike=715.0,
        option_type="PUT",
        bid=0.50,
        ask=0.55,
        last=0.52,
        delta=-0.16,
        volume=80,
        open_interest=900,
        days_to_expiration=47,
    )
    candidate = TradeCandidate(
        spread=BullPutSpread(short_put=short_put, long_put=long_put),
        score=91.5,
        decision="TRADE",
    )

    class FakeScanner:
        def __init__(self, *args, **kwargs):
            pass

        def scan_live(self, *, symbol, config, **kwargs):
            return [candidate]

    monkeypatch.setattr("app.web.app.create_schwab_client", lambda: object())
    monkeypatch.setattr("app.web.app.SchwabMarketDataClient", lambda client: object())
    monkeypatch.setattr("app.web.app.LiveCandidateScanner", FakeScanner)

    app = create_app(
        testing=True,
        settings_path=str(tmp_path / "settings.json"),
    )
    response = app.test_client().post(
        "/recommendations",
        data={"symbol": "SPY", "action": "scan"},
    )

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "720 / 715" in body
    assert "91.5" in body
    assert "$0.55" in body
