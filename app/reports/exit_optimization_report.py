from app.backtesting.models import ExitOptimizationResult


class ExitOptimizationReport:
    def format(self, optimization: ExitOptimizationResult, limit: int = 10) -> str:
        if limit <= 0:
            raise ValueError("Limit must be greater than zero.")
        baseline = optimization.baseline
        lines = [
            f"Exit optimization: {optimization.symbol}",
            "",
            "IMPORTANT: all results use the approximate ATR-volatility",
            "Black-Scholes spread model, not historical executable option fills.",
            "",
            "Baseline:",
            self._metrics_line(baseline),
            "",
            f"Top {min(limit, len(optimization.runs))} configurations:",
        ]
        for run in optimization.runs[:limit]:
            cfg = run.config
            flags = []
            if cfg.exit_on_trend_deterioration:
                flags.append("trend")
            if cfg.exit_on_short_strike_threat:
                flags.append("threat")
            defensive = "+".join(flags) if flags else "none"
            lines.append(
                f"{run.rank:>2}. exit {cfg.exit_dte:>2} DTE  target {cfg.profit_target_percent:>4.0f}%  "
                f"stop {cfg.stop_loss_percent:>4.0f}%  defensive {defensive:<12}  "
                f"{self._metrics_line(run.result)}"
            )
        if optimization.best:
            best = optimization.best
            improvement = best.result.total_pnl - baseline.total_pnl
            lines.extend([
                "",
                "Best versus baseline:",
                f"P/L improvement: ${improvement:,.2f}",
                f"Drawdown change: ${best.result.maximum_drawdown - baseline.maximum_drawdown:,.2f}",
            ])
        return "\n".join(lines)

    @staticmethod
    def _metrics_line(result) -> str:
        return (
            f"trades {len(result.trades):>3}  win {result.win_rate:>6.1%}  "
            f"P/L ${result.total_pnl:>10,.2f}  PF {result.profit_factor:>4.2f}  "
            f"DD ${result.maximum_drawdown:>9,.2f}"
        )
