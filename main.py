from __future__ import annotations

import argparse

from dotenv import load_dotenv

from app.brokers.schwab_auth import create_schwab_client
from app.brokers.schwab_market_data import SchwabMarketDataClient
from app.config.strategy_config import DEFAULT_STRATEGIES, PutSpreadConfig
from app.evaluation.default_pipeline import create_default_candidate_pipeline
from app.indicators.market_analysis import MarketAnalysisBuilder
from app.models.portfolio.portfolio_state import PortfolioState
from app.reports.opportunity_report import OpportunityReport
from app.scanners.live_candidate_scanner import LiveCandidateScanner
from app.backtesting.engine import HistoricalBacktester
from app.backtesting.models import BacktestConfig
from app.reports.backtest_report import BacktestReport
from app.backtesting.optimizer import BacktestOptimizer
from app.reports.backtest_optimization_report import BacktestOptimizationReport
from app.backtesting.portfolio import PortfolioBacktester
from app.backtesting.walk_forward import WalkForwardTester
from app.reports.portfolio_backtest_report import PortfolioBacktestReport
from app.reports.walk_forward_report import WalkForwardReport
from app.paper.ledger import PaperLedger
from app.paper.service import PaperTradingService
from app.paper.automation import PaperTradeAutomation
from app.paper.manager import PaperPositionManager
from app.paper.exporter import PaperTradingExporter
from app.paper.workflow import PaperDailyWorkflow
from app.reports.paper_report import PaperReport
from datetime import date
from app.watchlists.manager import WatchlistManager
from app.daily.service import DailyRecommendationService
from app.reports.daily_recommendation_report import DailyRecommendationReport
from app.scheduling.scheduler import DailyScheduler, ScheduledJob
from app.config.runtime_config import RuntimeConfigLoader
from app.operations.health import HealthChecker
from app.operations.startup import StartupValidator
from app.operations.diagnostics import DiagnosticCollector
from app.operations.deployment import DeploymentVerifier
from app.operations.lifecycle import RecoveryCheckpoint

from datetime import datetime, timedelta, timezone
from app.brokers.schwab_trading.client import SchwabTradingClient
from app.trading.order_plan import BullPutOrderPlanBuilder
from app.trading.reconciliation import ReadOnlyReconciliationService
from app.trading.service import DryRunTradingService
from app.trading.validation import OrderPlanValidator
from app.trading.account_selection import AccountSelectionRequired, select_account
from app.reports.trading_report import TradingReport


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TradingEngine live scanner")
    subparsers = parser.add_subparsers(dest="command")

    scan = subparsers.add_parser("scan", help="Scan one or more symbols")
    scan.add_argument(
        "symbols",
        nargs="+",
        help="Underlying symbols, for example SPY QQQ IWM",
    )
    scan.add_argument(
        "--strategy",
        choices=tuple(DEFAULT_STRATEGIES),
        default="Balanced",
    )
    scan.add_argument("--limit", type=int, default=5)
    scan.add_argument("--account-value", type=float)
    scan.add_argument("--buying-power", type=float)
    scan.add_argument("--open-positions", type=int, default=0)
    scan.add_argument("--committed-risk", type=float, default=0.0)
    scan.add_argument("--daily-loss", type=float, default=0.0)
    backtest = subparsers.add_parser("backtest", help="Backtest a symbol using daily history")
    backtest.add_argument("symbol")
    backtest.add_argument("--initial-capital", type=float, default=100000.0)
    backtest.add_argument("--limit", type=int, default=10)
    optimize = subparsers.add_parser(
        "backtest-optimize",
        help="Compare exit-management parameter combinations",
    )
    optimize.add_argument("symbol")
    optimize.add_argument("--initial-capital", type=float, default=100000.0)
    optimize.add_argument("--limit", type=int, default=15)

    portfolio = subparsers.add_parser(
        "portfolio-backtest",
        help="Backtest multiple symbols under shared position constraints",
    )
    portfolio.add_argument("symbols", nargs="+")
    portfolio.add_argument("--initial-capital", type=float, default=100000.0)
    portfolio.add_argument("--max-open-positions", type=int, default=5)
    portfolio.add_argument("--max-risk-per-trade", type=float, default=500.0)

    walk = subparsers.add_parser(
        "walk-forward",
        help="Optimize rolling training windows and test on unseen data",
    )
    walk.add_argument("symbol")
    walk.add_argument("--initial-capital", type=float, default=100000.0)
    walk.add_argument("--training-bars", type=int, default=504)
    walk.add_argument("--testing-bars", type=int, default=126)

    paper = subparsers.add_parser("paper", help="Manage the local paper-trading ledger")
    paper.add_argument("--ledger", default="data/paper_account.json")
    paper_sub = paper.add_subparsers(dest="paper_command")
    paper_init = paper_sub.add_parser("init")
    paper_init.add_argument("--cash", type=float, default=100000.0)
    paper_init.add_argument("--overwrite", action="store_true")
    paper_sub.add_parser("status")
    paper_open = paper_sub.add_parser("open")
    paper_open.add_argument("symbol")
    paper_open.add_argument("--expiration", required=True)
    paper_open.add_argument("--short", type=float, required=True)
    paper_open.add_argument("--long", type=float, required=True)
    paper_open.add_argument("--credit", type=float, required=True)
    paper_open.add_argument("--quantity", type=int, default=1)
    paper_mark = paper_sub.add_parser("mark")
    paper_mark.add_argument("position_id")
    paper_mark.add_argument("--debit", type=float, required=True)
    paper_close = paper_sub.add_parser("close")
    paper_close.add_argument("position_id")
    paper_close.add_argument("--debit", type=float, required=True)
    paper_close.add_argument("--reason", required=True)
    paper_scan = paper_sub.add_parser(
        "scan",
        help="Scan symbols and automatically open qualifying TRADE candidates",
    )
    paper_scan.add_argument("symbols", nargs="+")
    paper_scan.add_argument(
        "--strategy",
        choices=tuple(DEFAULT_STRATEGIES),
        default="Balanced",
    )
    paper_scan.add_argument("--quantity", type=int, default=1)

    paper_manage = paper_sub.add_parser(
        "manage", help="Mark open positions and apply automatic exit rules"
    )
    paper_manage.add_argument(
        "--strategy", choices=tuple(DEFAULT_STRATEGIES), default="Balanced"
    )

    paper_sub.add_parser("dashboard", help="Show paper portfolio dashboard")

    paper_export = paper_sub.add_parser("export", help="Export paper activity to CSV")
    paper_export.add_argument("--directory", default="reports/paper")

    paper_daily = paper_sub.add_parser(
        "daily", help="Manage open positions, then scan symbols for new trades"
    )
    paper_daily.add_argument("symbols", nargs="+")
    paper_daily.add_argument(
        "--strategy", choices=tuple(DEFAULT_STRATEGIES), default="Balanced"
    )
    paper_daily.add_argument("--quantity", type=int, default=1)

    watchlist = subparsers.add_parser("watchlist", help="Manage named symbol watchlists")
    watchlist.add_argument("--file", default="config/watchlists.json")
    watch_sub = watchlist.add_subparsers(dest="watchlist_command")
    watch_init = watch_sub.add_parser("init")
    watch_init.add_argument("--overwrite", action="store_true")
    watch_sub.add_parser("list")
    watch_show = watch_sub.add_parser("show")
    watch_show.add_argument("name", nargs="?")
    watch_create = watch_sub.add_parser("create")
    watch_create.add_argument("name")
    watch_create.add_argument("symbols", nargs="+")
    watch_create.add_argument("--default", action="store_true")
    watch_add = watch_sub.add_parser("add")
    watch_add.add_argument("name")
    watch_add.add_argument("symbols", nargs="+")
    watch_remove = watch_sub.add_parser("remove")
    watch_remove.add_argument("name")
    watch_remove.add_argument("symbols", nargs="+")
    watch_default = watch_sub.add_parser("default")
    watch_default.add_argument("name")

    daily = subparsers.add_parser("daily-report", help="Scan a watchlist and write a daily recommendation report")
    daily.add_argument("--watchlist", default=None)
    daily.add_argument("--watchlist-file", default="config/watchlists.json")
    daily.add_argument("--strategy", choices=tuple(DEFAULT_STRATEGIES), default="Balanced")
    daily.add_argument("--output-directory", default="reports/daily")
    daily.add_argument("--detail-limit", type=int, default=3)

    scheduler = subparsers.add_parser("scheduler", help="Run scheduled daily recommendation reports")
    scheduler.add_argument("--config", default="config/schedule.json")
    scheduler.add_argument("--state", default="data/scheduler_state.json")
    scheduler.add_argument("--watchlist", default=None)
    scheduler.add_argument("--watchlist-file", default="config/watchlists.json")
    scheduler.add_argument("--strategy", choices=tuple(DEFAULT_STRATEGIES), default="Balanced")
    scheduler.add_argument("--output-directory", default="reports/daily")
    schedule_sub = scheduler.add_subparsers(dest="scheduler_command")
    schedule_init = schedule_sub.add_parser("init")
    schedule_init.add_argument("--overwrite", action="store_true")
    schedule_sub.add_parser("status")
    schedule_sub.add_parser("run-due")
    schedule_loop = schedule_sub.add_parser("loop")
    schedule_loop.add_argument("--poll-seconds", type=int, default=60)

    config_cmd = subparsers.add_parser("config", help="Validate centralized runtime configuration")
    config_cmd.add_argument("--file", default="config/runtime.json")
    config_sub = config_cmd.add_subparsers(dest="config_command")
    config_sub.add_parser("validate")

    health = subparsers.add_parser("health", help="Run production-readiness health checks")
    health.add_argument("--config", default="config/runtime.json")

    version = subparsers.add_parser("version", help="Show the TradingEngine version")
    version.add_argument("--file", default="VERSION")

    diagnostics = subparsers.add_parser("diagnostics", help="Write an operational diagnostics snapshot")
    diagnostics.add_argument("--config", default="config/runtime.json")
    diagnostics.add_argument("--output-directory", default="reports/diagnostics")

    recovery = subparsers.add_parser("recovery", help="Inspect or clear the recovery checkpoint")
    recovery.add_argument("--config", default="config/runtime.json")
    recovery_sub = recovery.add_subparsers(dest="recovery_command")
    recovery_sub.add_parser("status")
    recovery_sub.add_parser("clear")

    verify = subparsers.add_parser("verify-deployment", help="Compile the application and run the test suite")
    verify.add_argument("--project-root", default=".")
    verify.add_argument("--skip-tests", action="store_true")

    trade = subparsers.add_parser("trade", help="Read-only Schwab trading and dry-run order planning")
    trade.add_argument("--config", default="config/runtime.json")
    trade_sub = trade.add_subparsers(dest="trade_command")
    trade_sub.add_parser("account")
    trade_sub.add_parser("positions")
    trade_orders = trade_sub.add_parser("orders")
    trade_orders.add_argument("--days", type=int, default=30)
    trade_sub.add_parser("reconcile")
    trade_plan = trade_sub.add_parser("plan")
    trade_plan.add_argument("symbol")
    trade_plan.add_argument("--strategy", choices=tuple(DEFAULT_STRATEGIES), default="Balanced")
    trade_plan.add_argument("--quantity", type=int, default=1)
    trade_validate = trade_sub.add_parser("validate")
    trade_validate.add_argument("symbol")
    trade_validate.add_argument("--strategy", choices=tuple(DEFAULT_STRATEGIES), default="Balanced")
    trade_validate.add_argument("--quantity", type=int, default=1)
    return parser


def _portfolio_from_args(args: argparse.Namespace) -> PortfolioState | None:
    supplied = (args.account_value, args.buying_power)
    if supplied == (None, None):
        return None
    if None in supplied:
        raise ValueError(
            "--account-value and --buying-power must be supplied together."
        )
    return PortfolioState(
        account_value=args.account_value,
        available_buying_power=args.buying_power,
        open_positions=args.open_positions,
        committed_risk=args.committed_risk,
        daily_realized_loss=args.daily_loss,
    )


def _scan_symbol(
    symbol: str,
    config: PutSpreadConfig,
    market_data: SchwabMarketDataClient,
    scanner: LiveCandidateScanner,
    analysis_builder: MarketAnalysisBuilder,
    portfolio: PortfolioState | None,
) -> tuple[list, object]:
    price_history = market_data.get_daily_price_history(symbol)
    snapshot, trend = analysis_builder.build(symbol, price_history, config)
    candidates = scanner.scan(
        symbol=symbol,
        price_snapshot=snapshot,
        trend_analysis=trend,
        config=config,
        portfolio_state=portfolio,
    )
    return candidates, snapshot


def run_scan(args: argparse.Namespace) -> int:
    if args.limit <= 0:
        raise ValueError("--limit must be greater than zero.")

    load_dotenv()
    symbols = [symbol.strip().upper() for symbol in args.symbols]
    if any(not symbol for symbol in symbols):
        raise ValueError("Symbols cannot be blank.")

    config: PutSpreadConfig = DEFAULT_STRATEGIES[args.strategy]
    portfolio = _portfolio_from_args(args)

    market_data = SchwabMarketDataClient(create_schwab_client())
    analysis_builder = MarketAnalysisBuilder()
    scanner = LiveCandidateScanner(
        market_data=market_data,
        pipeline=create_default_candidate_pipeline(),
        market_analysis=analysis_builder,
    )
    report = OpportunityReport()

    results: dict[str, list] = {}
    snapshots: dict[str, object] = {}
    for symbol in symbols:
        candidates, snapshot = _scan_symbol(
            symbol,
            config,
            market_data,
            scanner,
            analysis_builder,
            portfolio,
        )
        results[symbol] = candidates
        snapshots[symbol] = snapshot

    if len(symbols) > 1:
        print(report.format_summary(results))
        return 0

    symbol = symbols[0]
    print(report.format_ranked(results[symbol], snapshots[symbol], args.limit))
    return 0



def run_backtest(args: argparse.Namespace) -> int:
    load_dotenv()
    symbol = args.symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol cannot be blank.")
    market_data = SchwabMarketDataClient(create_schwab_client())
    history = market_data.get_daily_price_history(symbol, period_years=5)
    config = BacktestConfig(initial_capital=args.initial_capital)
    result = HistoricalBacktester().run(symbol, history, config)
    print(BacktestReport().format(result, args.limit))
    return 0


def run_backtest_optimize(args: argparse.Namespace) -> int:
    if args.limit <= 0:
        raise ValueError("--limit must be greater than zero.")
    load_dotenv()
    symbol = args.symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol cannot be blank.")
    market_data = SchwabMarketDataClient(create_schwab_client())
    history = market_data.get_daily_price_history(symbol, period_years=5)
    base = BacktestConfig(initial_capital=args.initial_capital)
    optimization = BacktestOptimizer().run(symbol, history, base)
    print(BacktestOptimizationReport().format(optimization, args.limit))
    return 0

def run_portfolio_backtest(args: argparse.Namespace) -> int:
    load_dotenv()
    symbols = [symbol.strip().upper() for symbol in args.symbols]
    if any(not symbol for symbol in symbols):
        raise ValueError("Symbols cannot be blank.")
    market_data = SchwabMarketDataClient(create_schwab_client())
    histories = {
        symbol: market_data.get_daily_price_history(symbol, period_years=5)
        for symbol in symbols
    }
    config = BacktestConfig(initial_capital=args.initial_capital)
    result = PortfolioBacktester().run(
        histories,
        config,
        max_open_positions=args.max_open_positions,
        max_risk_per_trade=args.max_risk_per_trade,
    )
    print(PortfolioBacktestReport().format(result))
    return 0


def run_walk_forward(args: argparse.Namespace) -> int:
    load_dotenv()
    symbol = args.symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol cannot be blank.")
    market_data = SchwabMarketDataClient(create_schwab_client())
    print("Running walk-forward analysis (compact grid)...", flush=True)
    history = market_data.get_daily_price_history(symbol, period_years=5)
    config = BacktestConfig(initial_capital=args.initial_capital)
    result = WalkForwardTester().run(
        symbol,
        history,
        config,
        training_bars=args.training_bars,
        testing_bars=args.testing_bars,
    )
    print(WalkForwardReport().format(result))
    return 0


def run_paper(args: argparse.Namespace) -> int:
    service = PaperTradingService(PaperLedger(args.ledger))
    report = PaperReport()
    if args.paper_command == "init":
        account = service.initialize(args.cash, overwrite=args.overwrite)
        print(report.format_account(account))
        return 0
    if args.paper_command == "status":
        print(report.format_account(service.status()))
        return 0
    if args.paper_command == "open":
        position = service.open_position(
            symbol=args.symbol,
            expiration=date.fromisoformat(args.expiration),
            short_strike=args.short,
            long_strike=args.long,
            entry_credit=args.credit,
            quantity=args.quantity,
        )
        print(report.format_position(position))
        return 0
    if args.paper_command == "mark":
        position = service.mark_position(args.position_id, args.debit)
        print(report.format_position(position))
        return 0
    if args.paper_command == "close":
        position = service.close_position(args.position_id, args.debit, args.reason)
        print(report.format_position(position))
        return 0
    if args.paper_command == "scan":
        if args.quantity <= 0:
            raise ValueError("--quantity must be greater than zero.")

        load_dotenv()
        symbols = [symbol.strip().upper() for symbol in args.symbols]
        if any(not symbol for symbol in symbols):
            raise ValueError("Symbols cannot be blank.")

        config: PutSpreadConfig = DEFAULT_STRATEGIES[args.strategy]
        market_data = SchwabMarketDataClient(create_schwab_client())
        analysis_builder = MarketAnalysisBuilder()
        scanner = LiveCandidateScanner(
            market_data=market_data,
            pipeline=create_default_candidate_pipeline(),
            market_analysis=analysis_builder,
        )
        automation = PaperTradeAutomation(service, config)
        results = []

        for symbol in symbols:
            account = service.status()
            portfolio = PortfolioState(
                account_value=account.equity,
                available_buying_power=account.available_buying_power,
                open_positions=len(account.open_positions),
                committed_risk=account.committed_risk,
                daily_realized_loss=0.0,
            )
            candidates = scanner.scan_live(
                symbol=symbol,
                config=config,
                portfolio_state=portfolio,
            )
            results.append(
                automation.process(
                    symbol,
                    candidates,
                    quantity=args.quantity,
                )
            )

        print(report.format_automation(results))
        return 0
    if args.paper_command == "manage":
        load_dotenv()
        config: PutSpreadConfig = DEFAULT_STRATEGIES[args.strategy]
        market_data = SchwabMarketDataClient(create_schwab_client())
        manager = PaperPositionManager(service, market_data)
        results = manager.manage_all(config)
        print(report.format_management(results))
        return 0
    if args.paper_command == "dashboard":
        print(report.format_dashboard(service.status()))
        return 0
    if args.paper_command == "export":
        paths = PaperTradingExporter().export(service.status(), args.directory)
        print("Paper trading exports:")
        for path in paths:
            print(path)
        return 0
    if args.paper_command == "daily":
        if args.quantity <= 0:
            raise ValueError("--quantity must be greater than zero.")
        load_dotenv()
        symbols = [symbol.strip().upper() for symbol in args.symbols]
        if any(not symbol for symbol in symbols):
            raise ValueError("Symbols cannot be blank.")
        config: PutSpreadConfig = DEFAULT_STRATEGIES[args.strategy]
        market_data = SchwabMarketDataClient(create_schwab_client())
        scanner = LiveCandidateScanner(
            market_data=market_data,
            pipeline=create_default_candidate_pipeline(),
            market_analysis=MarketAnalysisBuilder(),
        )
        manager = PaperPositionManager(service, market_data)
        automation = PaperTradeAutomation(service, config)
        workflow = PaperDailyWorkflow(
            service, manager, scanner, automation
        )
        result = workflow.run(symbols, config, quantity=args.quantity)
        print(report.format_daily(result, service.status()))
        return 0
    raise ValueError("A paper-trading subcommand is required.")



def _create_live_scanner() -> LiveCandidateScanner:
    market_data = SchwabMarketDataClient(create_schwab_client())
    return LiveCandidateScanner(
        market_data=market_data,
        pipeline=create_default_candidate_pipeline(),
        market_analysis=MarketAnalysisBuilder(),
    )


def run_watchlist(args: argparse.Namespace) -> int:
    manager = WatchlistManager(args.file)
    command = args.watchlist_command
    if command == "init":
        store = manager.initialize(overwrite=args.overwrite)
    elif command == "list":
        store = manager.load()
    elif command == "show":
        name = args.name or manager.load().default
        print(f"{name}: {' '.join(manager.symbols(name))}")
        return 0
    elif command == "create":
        store = manager.create(args.name, args.symbols, make_default=args.default)
    elif command == "add":
        store = manager.add(args.name, args.symbols)
    elif command == "remove":
        store = manager.remove(args.name, args.symbols)
    elif command == "default":
        store = manager.set_default(args.name)
    else:
        raise ValueError("A watchlist subcommand is required.")
    print(f"Default watchlist: {store.default}")
    for name in sorted(store.watchlists):
        marker = "*" if name == store.default else " "
        print(f"{marker} {name:<12} {' '.join(store.watchlists[name])}")
    return 0


def _generate_daily_report(
    *,
    watchlist_name: str | None,
    watchlist_file: str,
    strategy_name: str,
    output_directory: str,
    detail_limit: int = 3,
) -> str:
    load_dotenv()
    manager = WatchlistManager(watchlist_file)
    store = manager.load()
    name = (watchlist_name or store.default).strip().lower()
    config: PutSpreadConfig = DEFAULT_STRATEGIES[strategy_name]
    result = DailyRecommendationService(_create_live_scanner()).run(
        manager.symbols(name),
        config,
        strategy_name=strategy_name,
        watchlist_name=name,
    )
    report = DailyRecommendationReport()
    text = report.format(result, detail_limit=detail_limit)
    path = report.write(result, output_directory)
    print(text)
    print(f"\nSaved report: {path}")
    return str(path)


def run_daily_report(args: argparse.Namespace) -> int:
    if args.detail_limit <= 0:
        raise ValueError("--detail-limit must be greater than zero.")
    _generate_daily_report(
        watchlist_name=args.watchlist,
        watchlist_file=args.watchlist_file,
        strategy_name=args.strategy,
        output_directory=args.output_directory,
        detail_limit=args.detail_limit,
    )
    return 0


def run_scheduler(args: argparse.Namespace) -> int:
    scheduler = DailyScheduler(args.config, args.state)
    if args.scheduler_command == "init":
        jobs = scheduler.initialize(overwrite=args.overwrite)
        print("Scheduler initialized.")
        for job in jobs:
            print(f"{job.name:<20} {job.at}")
        return 0
    if args.scheduler_command == "status":
        jobs = scheduler.load_jobs()
        due = {job.name for job in scheduler.due_jobs()}
        print("Scheduled jobs:")
        for job in jobs:
            state = "DUE" if job.name in due else "WAITING"
            print(f"{job.name:<20} {job.at}  {state}")
        return 0

    def runner(job: ScheduledJob) -> None:
        print(f"Running scheduled job: {job.name}", flush=True)
        _generate_daily_report(
            watchlist_name=args.watchlist,
            watchlist_file=args.watchlist_file,
            strategy_name=args.strategy,
            output_directory=args.output_directory,
        )

    if args.scheduler_command == "run-due":
        executed = scheduler.run_due(runner)
        print("Executed: " + (", ".join(executed) if executed else "none"))
        return 0
    if args.scheduler_command == "loop":
        print("Scheduler loop started. Press Ctrl+C to stop.", flush=True)
        scheduler.loop(runner, poll_seconds=args.poll_seconds)
        return 0
    raise ValueError("A scheduler subcommand is required.")



def run_config(args: argparse.Namespace) -> int:
    if args.config_command != "validate":
        raise ValueError("A config subcommand is required.")
    config = RuntimeConfigLoader(args.file).load()
    print("Runtime configuration is valid.")
    print(f"Environment: {config.environment}")
    print(f"Version: {config.version}")
    print(f"Maximum open positions: {config.risk.maximum_open_positions}")
    return 0


def run_health(args: argparse.Namespace) -> int:
    load_dotenv()
    result = StartupValidator(args.config).run()
    print(f"TradingEngine Health Check (v{result.config.version})")
    for check in result.health.checks:
        print(f"{check.status.value:<5} {check.name:<24} {check.message}")
    print(f"Log: {result.log_path}")
    print(f"Audit: {result.audit_path}")
    return result.health.exit_code


def run_version(args: argparse.Namespace) -> int:
    from pathlib import Path
    path = Path(args.file)
    if not path.exists():
        raise ValueError(f"Version file not found: {path}")
    print(path.read_text(encoding="utf-8").strip())
    return 0


def run_diagnostics(args: argparse.Namespace) -> int:
    config = RuntimeConfigLoader(args.config).load()
    collector = DiagnosticCollector()
    report = collector.collect(config)
    path = collector.write(report, args.output_directory)
    print(report.to_json())
    print(f"Saved diagnostics: {path}")
    return 0


def run_recovery(args: argparse.Namespace) -> int:
    config = RuntimeConfigLoader(args.config).load()
    checkpoint = RecoveryCheckpoint(config.resilience.recovery_checkpoint_file)
    if args.recovery_command == "status":
        payload = checkpoint.load()
        print("No recovery checkpoint." if payload is None else __import__("json").dumps(payload, indent=2, sort_keys=True))
        return 0
    if args.recovery_command == "clear":
        checkpoint.clear()
        print("Recovery checkpoint cleared.")
        return 0
    raise ValueError("A recovery subcommand is required.")


def run_verify_deployment(args: argparse.Namespace) -> int:
    result = DeploymentVerifier().verify(args.project_root, run_tests=not args.skip_tests)
    print(f"Compilation: {'PASS' if result.compilation_ok else 'FAIL'}")
    print(f"Tests: {'PASS' if result.tests_ok else 'FAIL'}")
    if result.test_output:
        print(result.test_output)
    return 0 if result.successful else 1



def _select_trade_account(broker: SchwabTradingClient):
    selection = select_account(broker.get_accounts())
    return selection.account

def _build_live_trade_plan(symbol: str, strategy: str, quantity: int):
    if quantity <= 0:
        raise ValueError("--quantity must be greater than zero.")
    config = DEFAULT_STRATEGIES[strategy]
    market_data = SchwabMarketDataClient(create_schwab_client())
    scanner = LiveCandidateScanner(market_data=market_data, pipeline=create_default_candidate_pipeline(), market_analysis=MarketAnalysisBuilder())
    candidates = scanner.scan_live(symbol=symbol.strip().upper(), config=config)
    eligible = [c for c in candidates if c.decision == "TRADE"]
    if not eligible:
        raise ValueError(f"No TRADE candidate is currently available for {symbol.strip().upper()}.")
    return BullPutOrderPlanBuilder().build_entry(eligible[0], quantity=quantity)

def run_trade(args: argparse.Namespace) -> int:
    load_dotenv()
    runtime = RuntimeConfigLoader(args.config).load()
    broker = SchwabTradingClient(create_schwab_client())
    report = TradingReport()
    try:
        account = _select_trade_account(broker)
    except AccountSelectionRequired as exc:
        print(exc.user_message())
        return 2
    if args.trade_command == "account":
        print(report.account(broker.get_account(account.account_hash))); return 0
    if args.trade_command == "positions":
        print(report.positions(broker.get_positions(account.account_hash))); return 0
    if args.trade_command == "orders":
        if args.days <= 0: raise ValueError("--days must be greater than zero.")
        now = datetime.now(timezone.utc)
        print(report.orders(broker.get_orders(account.account_hash, from_time=now-timedelta(days=args.days), to_time=now))); return 0
    if args.trade_command == "reconcile":
        print(report.reconciliation(ReadOnlyReconciliationService().reconcile(broker, account.account_hash))); return 0
    if args.trade_command in {"plan", "validate"}:
        symbol=args.symbol.strip().upper()
        if symbol not in runtime.trading.approved_symbols:
            raise ValueError(f"{symbol} is not in trading.approved_symbols.")
        plan=_build_live_trade_plan(symbol,args.strategy,args.quantity)
        if args.trade_command == "plan": print(report.plan(plan)); return 0
        result=DryRunTradingService(broker,OrderPlanValidator()).execute(account.account_hash,plan)
        print(report.dry_run(result)); return 0 if result.validation.valid else 1
    raise ValueError("A trade subcommand is required.")

def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "scan":
        return run_scan(args)
    if args.command == "backtest":
        return run_backtest(args)
    if args.command == "backtest-optimize":
        return run_backtest_optimize(args)
    if args.command == "portfolio-backtest":
        return run_portfolio_backtest(args)
    if args.command == "walk-forward":
        return run_walk_forward(args)
    if args.command == "paper":
        return run_paper(args)
    if args.command == "watchlist":
        return run_watchlist(args)
    if args.command == "daily-report":
        return run_daily_report(args)
    if args.command == "scheduler":
        return run_scheduler(args)
    if args.command == "config":
        return run_config(args)
    if args.command == "health":
        return run_health(args)
    if args.command == "version":
        return run_version(args)
    if args.command == "diagnostics":
        return run_diagnostics(args)
    if args.command == "recovery":
        return run_recovery(args)
    if args.command == "verify-deployment":
        return run_verify_deployment(args)
    if args.command == "trade":
        return run_trade(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
