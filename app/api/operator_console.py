from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.backtesting import BacktestRequest, run_backtest
from app.api.recommendations import RecommendationRequest, run_recommendation_scan
from app.api.trading_profiles import (
    ProfileDuplicateRequest,
    ProfileRenameRequest,
    TradingProfile,
    TradingProfileStore,
)
from app.api.recommendation_history import RecommendationHistoryStore
from app.config.service import ConfigService
from app.operations.health import HealthChecker


def _read_version() -> str:
    path = Path("VERSION")
    return path.read_text(encoding="utf-8").strip() if path.exists() else "unknown"


def create_app() -> FastAPI:
    profile_store = TradingProfileStore()
    history_store = RecommendationHistoryStore()
    app = FastAPI(
        title="TradingEngine Workstation API",
        version=_read_version(),
        docs_url="/api/docs",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @app.get("/api/version")
    def version() -> dict[str, str]:
        return {"version": _read_version(), "environment": "development"}

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
                    "status": "DISABLED",
                    "message": "Paper order submission is disabled in this slice.",
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
    def rename_trading_profile(
        profile_name: str,
        request: ProfileRenameRequest,
    ) -> dict:
        try:
            profile = profile_store.rename(profile_name, request.new_name)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if profile is None:
            raise HTTPException(status_code=404, detail="Trading profile not found.")
        return {"profile": profile}

    @app.post("/api/trading-profiles/{profile_name}/duplicate")
    def duplicate_trading_profile(
        profile_name: str,
        request: ProfileDuplicateRequest,
    ) -> dict:
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
        result = run_recommendation_scan(request)
        history = history_store.save(
            request.model_dump(mode="json"),
            result,
        )
        result["history_id"] = history["id"]
        return result

    return app


app = create_app()
