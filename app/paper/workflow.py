from __future__ import annotations

from dataclasses import dataclass

from app.config.strategy_config import PutSpreadConfig
from app.models.portfolio.portfolio_state import PortfolioState
from app.paper.automation import PaperAutomationResult, PaperTradeAutomation
from app.paper.manager import PaperManagementResult, PaperPositionManager
from app.paper.service import PaperTradingService
from app.scanners.live_candidate_scanner import LiveCandidateScanner


@dataclass(frozen=True)
class PaperDailyWorkflowResult:
    management: list[PaperManagementResult]
    scans: list[PaperAutomationResult]


class PaperDailyWorkflow:
    """Manage existing positions, then scan for new qualifying paper trades."""

    def __init__(
        self,
        service: PaperTradingService,
        manager: PaperPositionManager,
        scanner: LiveCandidateScanner,
        automation: PaperTradeAutomation,
    ) -> None:
        self._service = service
        self._manager = manager
        self._scanner = scanner
        self._automation = automation

    def run(
        self,
        symbols: list[str],
        config: PutSpreadConfig,
        *,
        quantity: int = 1,
    ) -> PaperDailyWorkflowResult:
        management = self._manager.manage_all(config)
        scans: list[PaperAutomationResult] = []
        for symbol in symbols:
            account = self._service.status()
            portfolio = PortfolioState(
                account_value=account.equity,
                available_buying_power=account.available_buying_power,
                open_positions=len(account.open_positions),
                committed_risk=account.committed_risk,
                daily_realized_loss=0.0,
            )
            candidates = self._scanner.scan_live(
                symbol=symbol,
                config=config,
                portfolio_state=portfolio,
            )
            scans.append(
                self._automation.process(symbol, candidates, quantity=quantity)
            )
        self._service.record_snapshot()
        return PaperDailyWorkflowResult(management=management, scans=scans)
