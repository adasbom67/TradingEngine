from datetime import date

from app.backtesting.models import BacktestResult, BacktestTrade
from app.backtesting.portfolio import PortfolioBacktester
from app.reports.portfolio_backtest_report import PortfolioBacktestReport


def trade(symbol, start, end, pnl=50, risk=400):
    return BacktestTrade(
        symbol=symbol,
        entry_date=date(2025, 1, start),
        exit_date=date(2025, 1, end),
        short_strike=100,
        long_strike=95,
        entry_credit=1,
        exit_debit=0.5,
        pnl=pnl,
        exit_reason="PROFIT_TARGET" if pnl > 0 else "STOP_LOSS",
        days_held=end-start,
        entry_price=110,
        exit_price=111,
        maximum_loss=risk,
    )


class FakeBacktester:
    def run(self, symbol, history, config):
        return BacktestResult(symbol, history["trades"], config.initial_capital)


def test_portfolio_enforces_position_and_risk_limits():
    histories = {
        "SPY": {"trades": [trade("SPY", 1, 10)]},
        "QQQ": {"trades": [trade("QQQ", 2, 8), trade("QQQ", 12, 15, risk=700)]},
    }
    result = PortfolioBacktester(FakeBacktester()).run(
        histories,
        max_open_positions=1,
        max_risk_per_trade=500,
    )
    assert len(result.trades) == 1
    assert {item.reason for item in result.rejected} == {"POSITION_LIMIT", "RISK_LIMIT"}
    assert result.max_concurrent_positions == 1


def test_portfolio_report_contains_symbol_breakdown():
    histories = {"SPY": {"trades": [trade("SPY", 1, 5, 75)]}}
    result = PortfolioBacktester(FakeBacktester()).run(histories)
    text = PortfolioBacktestReport().format(result)
    assert "Portfolio Backtest" in text
    assert "P/L by symbol:" in text
    assert "SPY" in text
