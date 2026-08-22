from __future__ import annotations

import os
import smtplib
import threading
from dataclasses import dataclass
from datetime import datetime, time, timezone
from email.message import EmailMessage
from typing import Any, Callable
from uuid import uuid4
from zoneinfo import ZoneInfo


ETF_UNIVERSE = ["SPY", "QQQ", "IWM", "DIA"]


def is_high_confidence(candidate: dict[str, Any], minimum_score: int = 8) -> bool:
    scores = candidate.get("scores", {})
    return (
        candidate.get("phase") == "IGNITION"
        and int(candidate.get("total_score", 0)) >= minimum_score
        and scores.get("option_value") == 2
        and scores.get("ignition") == 2
        and scores.get("liquidity") == 2
    )


def is_regular_market_hours(now: datetime | None = None) -> bool:
    eastern = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo("America/New_York"))
    return eastern.weekday() < 5 and time(9, 30) <= eastern.time().replace(tzinfo=None) <= time(16, 0)


@dataclass
class MonitorConfiguration:
    interval_minutes: int = 15
    minimum_score: int = 8
    confirmations_required: int = 2
    market_hours_only: bool = True


class CriticalEventMonitor:
    """Background, read-only scanner with consecutive-signal confirmation."""

    def __init__(self, scan: Callable[[], dict[str, Any]]) -> None:
        self._scan = scan
        self._configuration = MonitorConfiguration()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()
        self._streaks: dict[str, int] = {}
        self._alerted_contracts: set[str] = set()
        self._alerts: list[dict[str, Any]] = []
        self._latest_candidates: list[dict[str, Any]] = []
        self._latest_diagnostics: list[dict[str, Any]] = []
        self._last_scan_at: str | None = None
        self._next_scan_at: str | None = None
        self._state = "STOPPED"
        self._message = "Monitor is stopped."

    def start(self, configuration: MonitorConfiguration | None = None) -> dict[str, Any]:
        with self._lock:
            if configuration is not None:
                self._configuration = configuration
            if self._thread and self._thread.is_alive():
                return self.status()
            self._stop_event.clear()
            self._state = "STARTING"
            self._message = "Starting the 15-minute monitor."
            self._thread = threading.Thread(target=self._run, name="critical-event-monitor", daemon=True)
            self._thread.start()
        return self.status()

    def stop(self) -> dict[str, Any]:
        self._stop_event.set()
        with self._lock:
            self._state = "STOPPED"
            self._message = "Monitor is stopped."
            self._next_scan_at = None
        return self.status()

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "enabled": bool(self._thread and self._thread.is_alive() and not self._stop_event.is_set()),
                "state": self._state,
                "message": self._message,
                "configuration": vars(self._configuration),
                "last_scan_at": self._last_scan_at,
                "next_scan_at": self._next_scan_at,
                "latest_candidates": list(self._latest_candidates),
                "diagnostics": list(self._latest_diagnostics),
                "alerts": list(self._alerts[-20:]),
                "email_configured": _email_is_configured(),
            }

    def _run(self) -> None:
        while not self._stop_event.is_set():
            now = datetime.now(timezone.utc)
            if self._configuration.market_hours_only and not is_regular_market_hours(now):
                with self._lock:
                    self._state = "WAITING_FOR_MARKET"
                    self._message = "Waiting for regular U.S. market hours."
                if self._stop_event.wait(60):
                    break
                continue
            self._execute_scan(now)
            seconds = self._configuration.interval_minutes * 60
            next_scan = datetime.fromtimestamp(now.timestamp() + seconds, tz=timezone.utc)
            with self._lock:
                self._next_scan_at = next_scan.isoformat()
            if self._stop_event.wait(seconds):
                break

    def _execute_scan(self, started_at: datetime) -> None:
        with self._lock:
            self._state = "SCANNING"
            self._message = "Scanning SPY, QQQ, IWM, and DIA through Schwab."
        try:
            result = self._scan()
            candidates = result.get("candidates", [])
            diagnostics = result.get("diagnostics", [])
            new_alerts = self._review(candidates, started_at)
            with self._lock:
                self._latest_candidates = candidates
                self._latest_diagnostics = diagnostics
                self._last_scan_at = datetime.now(timezone.utc).isoformat()
                self._state = "ALERT" if new_alerts else "MONITORING"
                self._message = f"{len(new_alerts)} confirmed high-confidence alert(s)." if new_alerts else "Scan complete; no newly confirmed high-confidence trade."
        except Exception as exc:
            with self._lock:
                self._last_scan_at = datetime.now(timezone.utc).isoformat()
                self._state = "ERROR"
                self._message = str(exc)

    def _review(self, candidates: list[dict[str, Any]], observed_at: datetime) -> list[dict[str, Any]]:
        qualifying: list[tuple[dict[str, Any], str]] = []
        for candidate in candidates:
            option = candidate.get("option", {})
            contract_key = (
                f"{candidate.get('symbol', '')}:"
                f"{option.get('expiration')}:{option.get('strike')}"
            )
            if is_high_confidence(candidate, self._configuration.minimum_score):
                qualifying.append((candidate, contract_key))
        qualifying_keys = {contract_key for _, contract_key in qualifying}
        for contract_key in list(self._streaks):
            if contract_key not in qualifying_keys:
                self._streaks[contract_key] = 0
        created: list[dict[str, Any]] = []
        for candidate, contract_key in qualifying:
            symbol = str(candidate.get("symbol", ""))
            self._streaks[contract_key] = self._streaks.get(contract_key, 0) + 1
            option = candidate.get("option", {})
            if self._streaks[contract_key] < self._configuration.confirmations_required or contract_key in self._alerted_contracts:
                continue
            alert = {"id": uuid4().hex, "created_at": observed_at.isoformat(), "symbol": symbol,
                     "score": candidate.get("total_score"), "phase": candidate.get("phase"),
                     "contract_key": contract_key, "option": option,
                     "reasons": candidate.get("reasons", []), "acknowledged": False}
            self._alerted_contracts.add(contract_key)
            self._alerts.append(alert)
            created.append(alert)
            _send_email_alert(alert)
        return created


def _email_is_configured() -> bool:
    return all(os.getenv(name) for name in ("CRITICAL_EVENT_SMTP_HOST", "CRITICAL_EVENT_EMAIL_FROM", "CRITICAL_EVENT_EMAIL_TO"))


def _send_email_alert(alert: dict[str, Any]) -> None:
    if not _email_is_configured():
        return
    message = EmailMessage()
    message["Subject"] = f"TradingEngine critical event: {alert['symbol']} score {alert['score']}/10"
    message["From"] = os.environ["CRITICAL_EVENT_EMAIL_FROM"]
    message["To"] = os.environ["CRITICAL_EVENT_EMAIL_TO"]
    option = alert.get("option", {})
    message.set_content(f"Confirmed high-confidence research signal\n\nETF: {alert['symbol']}\nScore: {alert['score']}/10\nPhase: {alert['phase']}\nExpiration: {option.get('expiration')}\nStrike: {option.get('strike')}\nModeled entry debit: {option.get('modeled_entry_debit')}\n\nNo order was submitted. Review live quotes before making any decision.")
    try:
        with smtplib.SMTP(os.environ["CRITICAL_EVENT_SMTP_HOST"], int(os.getenv("CRITICAL_EVENT_SMTP_PORT", "587")), timeout=15) as server:
            if os.getenv("CRITICAL_EVENT_SMTP_STARTTLS", "1") == "1":
                server.starttls()
            username, password = os.getenv("CRITICAL_EVENT_SMTP_USERNAME"), os.getenv("CRITICAL_EVENT_SMTP_PASSWORD")
            if username and password:
                server.login(username, password)
            server.send_message(message)
    except Exception:
        return
