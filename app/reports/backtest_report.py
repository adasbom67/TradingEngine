from app.backtesting.models import BacktestGroupMetrics, BacktestResult


class BacktestReport:
    def format(self, result: BacktestResult, limit: int = 10) -> str:
        lines = [
            f"Backtest: {result.symbol}",
            "",
            "IMPORTANT: historical option prices are approximated with an",
            "ATR-volatility Black-Scholes spread model. Daily-bar high/low values",
            "are used for target and stop detection. This is not a reconstruction",
            "of executable historical fills.",
            "",
            f"Trades: {len(result.trades)}",
            f"Win rate: {result.win_rate:.1%}",
            f"Total P/L: ${result.total_pnl:,.2f}",
            f"Average P/L: ${result.average_pnl:,.2f}",
            f"Average winner: ${result.average_winner:,.2f}",
            f"Average loser: ${result.average_loser:,.2f}",
            f"Average days held: {result.average_days_held:.1f}",
            f"Profit factor: {result.profit_factor:.2f}",
            f"Maximum drawdown: ${result.maximum_drawdown:,.2f}",
            f"Longest losing streak: {result.longest_losing_streak}",
            f"Ending capital: ${result.ending_capital:,.2f}",
        ]
        self._append_groups(lines, "Performance by market regime:", result.by_regime())
        self._append_groups(lines, "Performance by exit reason:", result.by_exit_reason())

        if result.trades:
            lines.extend(["", "Recent trades:"])
            for trade in result.trades[-limit:]:
                lines.append(
                    f"{trade.entry_date}  {trade.short_strike:.0f}/{trade.long_strike:.0f}  "
                    f"{trade.exit_reason:<13} P/L ${trade.pnl:>8,.2f}  "
                    f"credit {trade.entry_credit:.2f}  exit {trade.exit_debit:.2f}  "
                    f"DTE {trade.entry_dte}->{trade.exit_dte}  {trade.market_regime}"
                )
                lines.append(
                    f"  underlying {trade.entry_price:.2f}->{trade.exit_price:.2f} "
                    f"({trade.underlying_return_percent:+.1f}%)  "
                    f"RSI {trade.entry_rsi:.1f}  ATR {trade.entry_atr:.2f}  "
                    f"MFE ${trade.maximum_favorable_excursion:.2f}  "
                    f"MAE ${trade.maximum_adverse_excursion:.2f}"
                )
        return "\n".join(lines)

    @staticmethod
    def _append_groups(
        lines: list[str],
        heading: str,
        groups: list[BacktestGroupMetrics],
    ) -> None:
        if not groups:
            return
        lines.extend(["", heading])
        for group in groups:
            lines.append(
                f"{group.name:<18} trades {group.trade_count:>4}  "
                f"win {group.win_rate:>6.1%}  avg ${group.average_pnl:>8,.2f}  "
                f"total ${group.total_pnl:>10,.2f}  PF {group.profit_factor:.2f}"
            )
