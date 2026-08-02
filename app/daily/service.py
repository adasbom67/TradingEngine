from __future__ import annotations

from datetime import datetime

from app.config.strategy_config import PutSpreadConfig
from app.daily.models import DailyRecommendationResult, DailySymbolResult
from app.scanners.live_candidate_scanner import LiveCandidateScanner


class DailyRecommendationService:
    """Scan a watchlist while isolating failures to individual symbols."""

    def __init__(self, scanner: LiveCandidateScanner) -> None:
        self._scanner = scanner

    def run(
        self,
        symbols: list[str],
        config: PutSpreadConfig,
        *,
        strategy_name: str,
        watchlist_name: str,
        generated_at: datetime | None = None,
    ) -> DailyRecommendationResult:
        results: list[DailySymbolResult] = []
        for raw_symbol in symbols:
            symbol = raw_symbol.strip().upper()
            if not symbol:
                continue
            try:
                candidates = self._scanner.scan_live(symbol, config)
                results.append(DailySymbolResult(symbol=symbol, candidates=candidates))
            except Exception as exc:
                results.append(DailySymbolResult(symbol=symbol, error=str(exc)))
        return DailyRecommendationResult(
            generated_at=generated_at or datetime.now().astimezone(),
            strategy=strategy_name,
            watchlist=watchlist_name,
            symbols=results,
        )
