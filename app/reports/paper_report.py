from app.paper.automation import PaperAutomationResult
from app.paper.manager import PaperManagementResult
from app.paper.models import PaperAccount, PaperPosition
from app.paper.workflow import PaperDailyWorkflowResult


class PaperReport:
    def format_account(self, account: PaperAccount) -> str:
        lines = [
            "Paper Trading Account",
            "",
            f"Initial cash: ${account.initial_cash:,.2f}",
            f"Equity: ${account.equity:,.2f}",
            f"Realized P/L: ${account.realized_pnl:,.2f}",
            f"Unrealized P/L: ${account.unrealized_pnl:,.2f}",
            f"Committed risk: ${account.committed_risk:,.2f}",
            f"Available buying power: ${account.available_buying_power:,.2f}",
            f"Open positions: {len(account.open_positions)}",
            f"Closed positions: {len(account.closed_positions)}",
            f"Win rate: {account.win_rate:.1%}",
            f"Maximum drawdown: ${account.maximum_drawdown:,.2f}",
            f"Recorded observations: {len(account.observations)}",
        ]
        if account.positions:
            lines.extend(["", "Positions:"])
            for position in account.positions:
                status = "OPEN" if position.is_open else position.exit_reason or "CLOSED"
                pnl = position.unrealized_pnl if position.is_open else position.realized_pnl
                lines.append(
                    f"{position.position_id}  {position.symbol:<6} "
                    f"{position.short_strike:g}/{position.long_strike:g} x{position.quantity} "
                    f"{status:<14} P/L ${pnl:>8,.2f} exp {position.expiration}"
                )
        if account.observations:
            lines.extend(["", "Recent observations:"])
            for item in account.observations[-10:]:
                selection = ""
                if item.selected_short_strike is not None:
                    selection = (
                        f" {item.selected_short_strike:g}/"
                        f"{item.selected_long_strike:g}"
                    )
                lines.append(
                    f"{item.observed_on}  {item.symbol:<6} "
                    f"{item.decision:<12}{selection}  {item.reason}"
                )
        return "\n".join(lines)

    def format_dashboard(self, account: PaperAccount) -> str:
        lines = [
            "Paper Portfolio Dashboard",
            "",
            f"Equity:                 ${account.equity:>12,.2f}",
            f"Total return:           ${(account.equity-account.initial_cash):>12,.2f}",
            f"Realized P/L:           ${account.realized_pnl:>12,.2f}",
            f"Unrealized P/L:         ${account.unrealized_pnl:>12,.2f}",
            f"Committed risk:         ${account.committed_risk:>12,.2f}",
            f"Buying power:           ${account.available_buying_power:>12,.2f}",
            f"Maximum drawdown:       ${account.maximum_drawdown:>12,.2f}",
            f"Open / closed positions: {len(account.open_positions)} / {len(account.closed_positions)}",
            f"Win rate:                {account.win_rate:>12.1%}",
        ]
        if account.open_positions:
            lines.extend(["", "Open exposure:"])
            for position in sorted(account.open_positions, key=lambda item: item.expiration):
                lines.append(
                    f"{position.symbol:<6} {position.short_strike:g}/{position.long_strike:g} "
                    f"x{position.quantity} exp {position.expiration} "
                    f"risk ${position.maximum_risk:,.2f} P/L ${position.unrealized_pnl:,.2f}"
                )
        return "\n".join(lines)

    @staticmethod
    def format_position(position: PaperPosition) -> str:
        action = "Opened" if position.is_open else "Closed"
        pnl = position.unrealized_pnl if position.is_open else position.realized_pnl
        return (
            f"{action} paper position {position.position_id}: {position.symbol} "
            f"{position.short_strike:g}/{position.long_strike:g} x{position.quantity}, "
            f"credit ${position.entry_credit:.2f}, P/L ${pnl:,.2f}"
        )

    @staticmethod
    def format_automation(results: list[PaperAutomationResult]) -> str:
        lines = ["Automatic Paper Scan", ""]
        for result in results:
            if result.position:
                position = result.position
                lines.append(
                    f"{result.symbol:<6} OPENED  {position.short_strike:g}/"
                    f"{position.long_strike:g} x{position.quantity} "
                    f"credit ${position.entry_credit:.2f} exp {position.expiration}"
                )
            else:
                lines.append(
                    f"{result.symbol:<6} NO TRADE  {result.decision}: {result.reason}"
                )
        return "\n".join(lines)

    @staticmethod
    def format_management(results: list[PaperManagementResult]) -> str:
        lines = ["Paper Position Management", ""]
        if not results:
            lines.append("No open positions to manage.")
        for result in results:
            debit = "n/a" if result.current_debit is None else f"${result.current_debit:.2f}"
            lines.append(
                f"{result.symbol:<6} {result.action:<7} {result.position_id} "
                f"debit {debit:<7} P/L ${result.pnl:,.2f}  {result.reason}"
            )
        return "\n".join(lines)

    def format_daily(self, result: PaperDailyWorkflowResult, account: PaperAccount) -> str:
        return "\n\n".join(
            [
                self.format_management(result.management),
                self.format_automation(result.scans),
                self.format_dashboard(account),
            ]
        )
