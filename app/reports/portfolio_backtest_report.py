from app.backtesting.portfolio import PortfolioBacktestResult


class PortfolioBacktestReport:
    def format(self, result: PortfolioBacktestResult) -> str:
        lines = [
            "Portfolio Backtest",
            "",
            f"Symbols: {', '.join(sorted(result.symbol_results))}",
            f"Accepted trades: {len(result.trades)}",
            f"Rejected trades: {len(result.rejected)}",
            f"Win rate: {result.win_rate:.1%}",
            f"Total P/L: ${result.total_pnl:,.2f}",
            f"Profit factor: {result.profit_factor:.2f}",
            f"Maximum drawdown: ${result.maximum_drawdown:,.2f}",
            f"Maximum concurrent positions: {result.max_concurrent_positions}",
            f"Ending capital: ${result.ending_capital:,.2f}",
            "",
            "P/L by symbol:",
        ]
        for symbol, pnl in result.pnl_by_symbol().items():
            lines.append(f"{symbol:<8} ${pnl:>10,.2f}")
        if result.rejected:
            reasons: dict[str, int] = {}
            for rejected in result.rejected:
                reasons[rejected.reason] = reasons.get(rejected.reason, 0) + 1
            lines.extend(["", "Rejected by reason:"])
            for reason, count in sorted(reasons.items()):
                lines.append(f"{reason:<18} {count}")
        return "\n".join(lines)
