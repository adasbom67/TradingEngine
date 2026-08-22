from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.api.backtesting import BacktestRequest, run_backtest
from app.api.critical_events import CriticalEventScanRequest, run_critical_event_scan
from app.api.critical_event_research import (
    CriticalEventBacktestRequest,
    critical_event_archive_status,
    run_critical_event_backtest,
)
from app.api.paper_trading import create_paper_trading_router
from app.api.recommendation_history import RecommendationHistoryStore
from app.api.recommendations import RecommendationRequest, run_recommendation_scan
from app.api.trading_profiles import (
    ProfileDuplicateRequest,
    ProfileRenameRequest,
    TradingProfile,
    TradingProfileStore,
)
from app.brokers.schwab_connection import (
    SchwabConnectionError,
    begin_schwab_authorization,
    complete_schwab_authorization,
    is_schwab_authentication_error,
    schwab_connection_status,
)
from app.config.service import ConfigService
from app.operations.health import HealthChecker
from app.monitoring.critical_event_monitor import CriticalEventMonitor, ETF_UNIVERSE, MonitorConfiguration


class SchwabAuthorizationCompleteRequest(BaseModel):
    redirect_url: str


def _read_version() -> str:
    path = Path("VERSION")
    return path.read_text(encoding="utf-8").strip() if path.exists() else "unknown"


def _operator_console_directory() -> Path | None:
    """Return the built Operator Console directory when it is available.

    The desktop host sets ``TRADINGENGINE_UI_DIR`` to its packaged UI. Local
    builds fall back to ``operator-console/dist`` so a single backend process
    can serve both the API and the production frontend.
    """
    configured = os.getenv("TRADINGENGINE_UI_DIR")
    directory = Path(configured) if configured else Path("operator-console/dist")
    index = directory / "index.html"
    return directory.resolve() if index.is_file() else None


def create_app() -> FastAPI:
    profile_store = TradingProfileStore()
    history_store = RecommendationHistoryStore()
    critical_event_monitor = CriticalEventMonitor(
        lambda: run_critical_event_scan(CriticalEventScanRequest(symbols=ETF_UNIVERSE))
    )

    app = FastAPI(
        title="TradingEngine Workstation API",
        version=_read_version(),
        docs_url="/api/docs",
        redoc_url=None,
    )

    app.router.routes.extend(create_paper_trading_router().routes)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @app.get("/api/version")
    def version() -> dict[str, str]:
        return {
            "version": _read_version(),
            "environment": (
                "desktop" if os.getenv("TRADINGENGINE_DESKTOP") == "1" else "development"
            ),
        }

    @app.get("/api/health")
    def health() -> dict:
        runtime_config = ConfigService().load()
        report = HealthChecker(runtime_config).run()
        return {
            "healthy": report.healthy,
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "message": check.message,
                }
                for check in report.checks
            ],
        }

    @app.get("/api/schwab/status")
    def schwab_status() -> dict:
        return schwab_connection_status()

    @app.post("/api/schwab/authorize")
    def schwab_authorize() -> dict:
        try:
            return begin_schwab_authorization()
        except SchwabConnectionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/schwab/authorize/complete")
    def schwab_authorize_complete(
        request: SchwabAuthorizationCompleteRequest,
    ) -> dict:
        try:
            return complete_schwab_authorization(request.redirect_url)
        except SchwabConnectionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/dashboard")
    def dashboard() -> dict:
        from datetime import datetime, timezone

        runtime_config = ConfigService().load()
        health_report = HealthChecker(runtime_config).run()
        checks = [
            {
                "name": check.name,
                "status": check.status.value,
                "message": check.message,
            }
            for check in health_report.checks
        ]

        latest_items = history_store.list_entries(limit=1)
        latest = latest_items[0] if latest_items else None
        summary = latest.get("summary", {}) if latest else {}
        schwab = next(
            (check for check in checks if check["name"] == "schwab_environment"),
            None,
        )

        return {
            "refreshed_at": datetime.now(timezone.utc).isoformat(),
            "operating_mode": "RESEARCH",
            "execution_mode": "READ_ONLY",
            "workspace": "Trading Day",
            "platform": {
                "api": {
                    "status": "HEALTHY",
                    "message": "FastAPI workstation service is responding.",
                },
                "recommendation_engine": {
                    "status": "READY",
                    "message": "Recommendation scans are available.",
                },
                "broker": {
                    "status": (
                        "CONNECTED"
                        if schwab and schwab["status"] == "PASS"
                        else "NOT_CONFIGURED"
                    ),
                    "message": (
                        schwab["message"]
                        if schwab
                        else "Schwab environment check is unavailable."
                    ),
                },
                "market_data": {
                    "status": "AVAILABLE" if latest else "AWAITING_SCAN",
                    "message": (
                        "Live Schwab data was used by the latest recommendation scan."
                        if latest
                        else "Run a recommendation scan to validate live market data."
                    ),
                },
                "paper_trading": {
                    "status": "READY",
                    "message": (
                        "Local simulation ledger is available; "
                        "broker orders remain disabled."
                    ),
                },
                "live_trading": {
                    "status": "DISABLED",
                    "message": "Live order submission is intentionally disabled.",
                },
            },
            "health": {"healthy": health_report.healthy, "checks": checks},
            "latest_scan": (
                {
                    "id": latest.get("id"),
                    "scanned_at": latest.get("scanned_at"),
                    "symbols": latest.get("symbols", []),
                    "candidate_count": summary.get("candidate_count", 0),
                    "rejected_count": summary.get("rejected_count", 0),
                    "evaluated_count": summary.get("evaluated_count", 0),
                    "trade_count": summary.get("trade_count", 0),
                    "watch_count": summary.get("watch_count", 0),
                    "pass_count": summary.get("pass_count", 0),
                    "outcome": summary.get("outcome", "UNKNOWN"),
                }
                if latest
                else None
            ),
            "portfolio": {
                "status": "NOT_CONNECTED",
                "open_positions": None,
                "message": "Portfolio synchronization is not enabled in Research mode.",
            },
            "alerts": [
                {
                    "severity": "INFO",
                    "title": "Research mode",
                    "message": "Order submission remains disabled.",
                }
            ],
        }

    @app.post("/api/backtests")
    def backtest(request: BacktestRequest) -> dict:
        return run_backtest(request)

    @app.post("/api/critical-events/scan")
    def critical_event_scan(request: CriticalEventScanRequest) -> dict:
        connection = schwab_connection_status()
        if connection.get("requires_reconnect"):
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "SCHWAB_RECONNECT_REQUIRED",
                    "message": connection["message"],
                },
            )
        return run_critical_event_scan(request)

    @app.post("/api/critical-events/backtest")
    def critical_event_backtest(request: CriticalEventBacktestRequest) -> dict:
        connection = schwab_connection_status()
        if connection.get("requires_reconnect"):
            raise HTTPException(status_code=401, detail=connection["message"])
        return run_critical_event_backtest(request)

    @app.get("/api/critical-events/archive")
    def critical_event_archive() -> dict:
        return critical_event_archive_status()

    @app.get("/api/critical-events/monitor")
    def critical_event_monitor_status() -> dict:
        return critical_event_monitor.status()

    @app.post("/api/critical-events/monitor/start")
    def start_critical_event_monitor() -> dict:
        connection = schwab_connection_status()
        if connection.get("requires_reconnect"):
            raise HTTPException(status_code=401, detail=connection["message"])
        return critical_event_monitor.start(MonitorConfiguration())

    @app.post("/api/critical-events/monitor/stop")
    def stop_critical_event_monitor() -> dict:
        return critical_event_monitor.stop()

    @app.get("/api/trading-profiles")
    def list_trading_profiles() -> dict:
        return {"profiles": profile_store.list_profiles()}

    @app.post("/api/trading-profiles")
    def save_trading_profile(profile: TradingProfile) -> dict:
        return {"profile": profile_store.save(profile)}

    @app.delete("/api/trading-profiles/{profile_name}")
    def delete_trading_profile(profile_name: str) -> dict:
        if not profile_store.delete(profile_name):
            raise HTTPException(status_code=404, detail="Trading profile not found.")
        return {"deleted": profile_name}

    @app.put("/api/trading-profiles/{profile_name}/rename")
    def rename_trading_profile(profile_name: str, request: ProfileRenameRequest) -> dict:
        try:
            profile = profile_store.rename(profile_name, request.new_name)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if profile is None:
            raise HTTPException(status_code=404, detail="Trading profile not found.")
        return {"profile": profile}

    @app.post("/api/trading-profiles/{profile_name}/duplicate")
    def duplicate_trading_profile(profile_name: str, request: ProfileDuplicateRequest) -> dict:
        try:
            profile = profile_store.duplicate(profile_name, request.new_name)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if profile is None:
            raise HTTPException(status_code=404, detail="Trading profile not found.")
        return {"profile": profile}

    @app.put("/api/trading-profiles/{profile_name}/default")
    def set_default_trading_profile(profile_name: str) -> dict:
        profile = profile_store.set_default(profile_name)
        if profile is None:
            raise HTTPException(status_code=404, detail="Trading profile not found.")
        return {"profile": profile}

    @app.get("/api/recommendations/history")
    def list_recommendation_history(limit: int = 25) -> dict:
        safe_limit = min(max(limit, 1), 100)
        return {"history": history_store.list_entries(safe_limit)}

    @app.get("/api/recommendations/history/{history_id}")
    def get_recommendation_history(history_id: str) -> dict:
        entry = history_store.get(history_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Scan history not found.")
        return {"scan": entry}

    @app.post("/api/recommendations/scan")
    def recommendation_scan(request: RecommendationRequest) -> dict:
        connection = schwab_connection_status()
        if connection.get("requires_reconnect"):
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "SCHWAB_RECONNECT_REQUIRED",
                    "message": connection["message"],
                },
            )
        result = run_recommendation_scan(request)
        authentication_errors = [
            item.get("message", "")
            for item in result.get("diagnostics", [])
            if item.get("status") == "ERROR"
            and is_schwab_authentication_error(item.get("message", ""))
        ]
        if authentication_errors:
            raise HTTPException(
                status_code=401,
                detail={
                    "code": "SCHWAB_RECONNECT_REQUIRED",
                    "message": (
                        "Schwab rejected the saved credentials. Reconnect Schwab, "
                        "then run the scan again."
                    ),
                },
            )
        history = history_store.save(request.model_dump(mode="json"), result)
        result["history_id"] = history["id"]
        return result

    ui_directory = _operator_console_directory()
    if ui_directory is not None:
        app.mount(
            "/",
            StaticFiles(directory=ui_directory, html=True),
            name="operator-console",
        )

    return app


app = create_app()
