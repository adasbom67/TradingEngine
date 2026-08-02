from app.backtesting.optimizer import OptimizationResult, OptimizationRun


class BacktestOptimizationReport:
    def format(self, optimization: OptimizationResult, limit: int = 15) -> str:
        if limit <= 0:
            raise ValueError("Limit must be greater than zero.")
        lines = [
            f"Backtest optimization: {optimization.symbol}",
            "",
            "Ranking: profit factor, then total P/L, then lower drawdown.",
            "Historical option values remain model-based approximations.",
            "",
            "Rank Exit Target Stop Trend Strike Trades  Win%      P/L     PF   Max DD",
        ]
        for rank, run in enumerate(optimization.ranked[:limit], start=1):
            lines.append(self._line(rank, run))
        best = optimization.best
        if best is not None:
            p = best.parameters
            lines.extend([
                "",
                "Best configuration:",
                f"Exit DTE: {p.exit_dte}",
                f"Profit target: {p.profit_target_percent:.0f}%",
                f"Stop loss: {p.stop_loss_percent:.0f}%",
                f"Trend exit: {'ON' if p.enable_trend_exit else 'OFF'}",
                f"Strike-threat exit: {'ON' if p.enable_strike_threat_exit else 'OFF'}",
            ])
        return "\n".join(lines)

    @staticmethod
    def _line(rank: int, run: OptimizationRun) -> str:
        p = run.parameters
        r = run.result
        return (
            f"{rank:>4} {p.exit_dte:>4} {p.profit_target_percent:>6.0f}% "
            f"{p.stop_loss_percent:>4.0f}% "
            f"{'Y' if p.enable_trend_exit else 'N':>5} "
            f"{'Y' if p.enable_strike_threat_exit else 'N':>6} "
            f"{len(r.trades):>6} {r.win_rate:>6.1%} "
            f"${r.total_pnl:>8,.0f} {r.profit_factor:>6.2f} "
            f"${r.maximum_drawdown:>7,.0f}"
        )
