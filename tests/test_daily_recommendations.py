from datetime import date, datetime, timezone

from app.config.strategy_config import PutSpreadConfig
from app.daily.service import DailyRecommendationService
from app.models.market.option_contract import OptionContract
from app.models.trades.bull_put_spread import BullPutSpread
from app.models.trades.trade_candidate import TradeCandidate
from app.reports.daily_recommendation_report import DailyRecommendationReport


class FakeScanner:
    def scan_live(self, symbol, config):
        if symbol == "BAD":
            raise RuntimeError("market data unavailable")
        if symbol == "EMPTY":
            return []
        short = OptionContract(symbol=f"{symbol} P", expiration_date=date(2026, 9, 18), strike=700, option_type="PUT", bid=1.2, ask=1.3, last=1.25, delta=-0.2, volume=100, open_interest=1000, days_to_expiration=40)
        long = OptionContract(symbol=f"{symbol} P", expiration_date=date(2026, 9, 18), strike=695, option_type="PUT", bid=.6, ask=.7, last=.65, delta=-0.15, volume=100, open_interest=1000, days_to_expiration=40)
        candidate = TradeCandidate(BullPutSpread(short, long))
        candidate.decision = "TRADE"
        candidate.score = 92
        candidate.probability_of_profit = .8
        candidate.managed_expected_value = 12
        return [candidate]


def test_daily_service_isolates_symbol_errors_and_report_writes(tmp_path):
    result = DailyRecommendationService(FakeScanner()).run(
        ["SPY", "EMPTY", "BAD"], PutSpreadConfig(), strategy_name="Balanced",
        watchlist_name="core", generated_at=datetime(2026, 8, 3, 9, 45, tzinfo=timezone.utc),
    )
    assert result.symbols[0].best.decision == "TRADE"
    assert result.symbols[1].best is None
    assert "unavailable" in result.symbols[2].error
    report = DailyRecommendationReport()
    text = report.format(result)
    assert "SPY" in text and "TRADE" in text and "ERROR" in text
    path = report.write(result, tmp_path)
    assert path.exists()
