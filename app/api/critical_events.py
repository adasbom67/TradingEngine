from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.brokers.schwab_auth import create_schwab_client
from app.brokers.schwab_market_data import SchwabMarketDataClient
from app.data.critical_event_archive import CriticalEventArchive
from app.scanners.critical_event_scanner import CriticalEventScanner


class CriticalEventScanRequest(BaseModel):
    symbols: list[str] = Field(default_factory=lambda: ["SPY", "QQQ", "IWM", "DIA"])


def run_critical_event_scan(request: CriticalEventScanRequest) -> dict:
    archive = CriticalEventArchive.from_environment()
    scanner = CriticalEventScanner(
        SchwabMarketDataClient(create_schwab_client()),
        archive=archive,
    )
    result = scanner.scan(request.symbols)
    result.update(
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "Schwab market data",
            "execution_mode": "READ_ONLY",
            "archive": archive.status(),
            "disclosure": (
                "Research signal only. The value score estimates expiration expected "
                "payoff from a blended historical-volatility forecast against the natural "
                "ask debit plus estimated commissions. It is not a guarantee, event-calendar data "
                "is not integrated, and no order is submitted to Schwab."
            ),
        }
    )
    return result
