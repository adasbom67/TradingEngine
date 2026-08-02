from app.backtesting.walk_forward import WalkForwardResult


class WalkForwardReport:
    def format(self, result: WalkForwardResult) -> str:
        lines = [
            f"Walk-Forward Test: {result.symbol}",
            "",
            f"Folds: {len(result.folds)}",
            f"Profitable folds: {result.profitable_folds}/{len(result.folds)}",
            f"Out-of-sample trades: {result.test_trade_count}",
            f"Out-of-sample win rate: {result.test_win_rate:.1%}",
            f"Out-of-sample total P/L: ${result.total_test_pnl:,.2f}",
        ]
        if result.folds:
            lines.extend(["", "Fold results:"])
            for index, fold in enumerate(result.folds, 1):
                p = fold.parameters
                lines.append(
                    f"{index:>2}. train {fold.training_start}->{fold.training_end}  "
                    f"test {fold.testing_start}->{fold.testing_end}  "
                    f"DTE {p.exit_dte} target {p.profit_target_percent:.0f}% "
                    f"stop {p.stop_loss_percent:.0f}%  "
                    f"trades {len(fold.testing_result.trades):>3}  "
                    f"P/L ${fold.testing_result.total_pnl:>9,.2f}  "
                    f"PF {fold.testing_result.profit_factor:.2f}"
                )
        return "\n".join(lines)
