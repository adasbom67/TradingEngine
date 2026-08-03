from __future__ import annotations

import os

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template_string, request, url_for

from app.backtesting.engine import HistoricalBacktester
from app.backtesting.models import BacktestConfig
from app.brokers.schwab_auth import create_schwab_client
from app.brokers.schwab_market_data import SchwabMarketDataClient
from app.brokers.schwab_trading.client import SchwabTradingClient
from app.config.strategy_config import DEFAULT_STRATEGIES
from app.evaluation.default_pipeline import create_default_candidate_pipeline
from app.indicators.market_analysis import MarketAnalysisBuilder
from app.operations.health import HealthChecker
from app.paper.ledger import PaperLedger
from app.paper.service import PaperTradingService
from app.reports.backtest_report import BacktestReport
from app.scanners.live_candidate_scanner import LiveCandidateScanner
from app.trading.account_selection import AccountSelectionRequired, select_account
from app.trading.order_plan import BullPutOrderPlanBuilder
from app.trading.validation import OrderPlanValidator
from app.web.settings import LocalSettingsStore

STYLE = """
:root{--bg:#0b1220;--card:#151f32;--line:#293650;--text:#e8edf7;--muted:#9aabc5;--good:#6bd89b;--warn:#ffd166}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:Segoe UI,Arial,sans-serif}
nav{background:#10192a;padding:14px 24px;border-bottom:1px solid var(--line)}nav a{color:var(--muted);text-decoration:none;margin-right:20px}
main{max-width:1180px;margin:24px auto;padding:0 18px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;margin-bottom:16px}.metric{font-size:28px;font-weight:700}.muted{color:var(--muted)}
input,button{background:#0e1728;color:var(--text);border:1px solid #40506b;border-radius:7px;padding:10px;margin:5px 4px 5px 0}button{background:#1f6feb;cursor:pointer}.secondary{background:#26354d}.danger{color:#ff8a8a}.good{color:var(--good)}.warning{color:var(--warn)}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:10px;border-bottom:1px solid var(--line)}pre{white-space:pre-wrap;background:#09101d;padding:14px;border-radius:8px}.flash{padding:12px;background:#483d17;border-radius:8px;margin-bottom:12px}label{display:block;color:var(--muted);margin-top:8px}.pill{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:4px 9px;color:var(--muted)}
"""
BASE = """<!doctype html><html><head><title>{{title}} - TradingEngine</title><style>""" + STYLE + """</style></head><body>
<nav><strong>TradingEngine v0.10.3</strong>&nbsp;&nbsp;<a href='/'>Dashboard</a><a href='/accounts'>Accounts</a><a href='/backtest'>Backtest</a><a href='/recommendations'>Recommendations</a><a href='/paper'>Paper</a><a href='/health'>Health</a></nav>
<main>{% with messages=get_flashed_messages() %}{% for m in messages %}<div class='flash'>{{m}}</div>{% endfor %}{% endwith %}__BODY__</main></body></html>"""


def page(title: str, body: str, **context):
    return render_template_string(BASE.replace("__BODY__", body), title=title, **context)


def create_app(*, testing: bool = False, settings_path: str = "data/local_settings.json") -> Flask:
    app = Flask(__name__)
    app.secret_key = os.getenv("TRADINGENGINE_WEB_SECRET", "local-development-only")
    app.config.update(TESTING=testing)
    store = LocalSettingsStore(settings_path)

    @app.get("/")
    def dashboard():
        paper = None
        try:
            paper = PaperTradingService(PaperLedger("data/paper_account.json")).status()
        except Exception:
            pass
        local = store.load()
        return page("Dashboard", """
        <h1>Operations Console</h1><p class='muted'>Local-only, read-only broker console. Live submission is not implemented.</p>
        <div class='grid'><div class='card'><div class='muted'>Execution</div><div class='metric'>DRY RUN</div><span class='pill'>Submission disabled</span></div>
        <div class='card'><div class='muted'>Selected live account</div><div class='metric'>{{('****'+local.selected_account_last_four) if local.selected_account_last_four else 'Not selected'}}</div></div>
        <div class='card'><div class='muted'>Paper equity</div><div class='metric'>{{('$%.2f'|format(paper.equity)) if paper else 'Not initialized'}}</div></div>
        <div class='card'><div class='muted'>Paper positions</div><div class='metric'>{{paper.open_positions|length if paper else 0}}</div></div></div>
        <div class='card'><h2>Safety boundary</h2><p class='good'>PASS: Account and order reads only</p><p class='good'>PASS: Dry-run plans and validation</p><p class='danger'>BLOCKED: No submit, cancel, or replace route</p></div>
        """, paper=paper, local=local)

    @app.route("/accounts", methods=["GET", "POST"])
    def accounts():
        load_dotenv(); error = None; linked = []; snapshot = None
        try:
            broker = SchwabTradingClient(create_schwab_client()); linked = broker.get_accounts()
            if request.method == "POST":
                selected = request.form.get("account_hash", "")
                account = next((a for a in linked if a.account_hash == selected), None)
                if account is None:
                    raise ValueError("Select a linked Schwab account.")
                store.save_account(account.account_hash, account.account_id[-4:])
                flash(f"Live account ****{account.account_id[-4:]} selected locally.")
                return redirect(url_for("accounts"))
            try:
                selection = select_account(linked)
                snapshot = broker.get_account(selection.account.account_hash)
            except AccountSelectionRequired:
                pass
        except Exception as exc:
            error = str(exc)
        local = store.load()
        return page("Accounts", """
        <h1>Accounts</h1><div class='card'><h2>Schwab live account</h2><p class='muted'>Selection is stored only in a Git-ignored local file. Identifiers are masked.</p>
        {% if error %}<p class='danger'>{{error}}</p>{% endif %}<form method='post'>{% for a in linked %}<label><input type='radio' name='account_hash' value='{{a.account_hash}}' {% if local.selected_account_last_four==a.account_id[-4:] %}checked{% endif %}> Account ****{{a.account_id[-4:]}} ({{a.account_type}})</label>{% endfor %}<button type='submit'>Save selection</button></form></div>
        {% if snapshot %}<div class='grid'><div class='card'><div class='muted'>Account</div><div class='metric'>{{snapshot.account.masked_id}}</div></div><div class='card'><div class='muted'>Value</div><div class='metric'>${{'%.2f'|format(snapshot.account_value)}}</div></div><div class='card'><div class='muted'>Buying power</div><div class='metric'>${{'%.2f'|format(snapshot.buying_power)}}</div></div></div>{% endif %}
        <div class='card'><h2>Paper account</h2><p>Independent simulated ledger: <code>data/paper_account.json</code></p></div>
        """, linked=linked, local=local, snapshot=snapshot, error=error)

    @app.route("/backtest", methods=["GET", "POST"])
    def backtest():
        output = None; error = None
        symbol = request.form.get("symbol", "SPY").strip().upper()
        try:
            capital = float(request.form.get("capital", "100000") or 100000)
        except ValueError:
            capital = 100000.0; error = "Starting capital must be numeric."
        if request.method == "POST" and error is None:
            try:
                market_data = SchwabMarketDataClient(create_schwab_client())
                history = market_data.get_daily_price_history(symbol, period_years=5)
                result = HistoricalBacktester().run(symbol, history, BacktestConfig(initial_capital=capital))
                output = BacktestReport().format(result, 10)
            except Exception as exc:
                error = str(exc)
        return page("Backtest", """
        <h1>Backtesting</h1><div class='card'><form method='post'><label>Ticker</label><input name='symbol' value='{{symbol}}' required><label>Starting capital</label><input name='capital' type='number' min='1' step='1000' value='{{capital}}'><br><button>Run backtest</button></form></div>
        {% if error %}<div class='card danger'>{{error}}</div>{% endif %}{% if output %}<div class='card'><h2>Results</h2><pre>{{output}}</pre></div>{% endif %}
        """, symbol=symbol, capital=capital, output=output, error=error)

    @app.route("/recommendations", methods=["GET", "POST"])
    def recommendations():
        symbol = request.values.get("symbol", "SPY").strip().upper(); candidates = []; error = None; plan = None; validation = None
        if request.method == "POST":
            try:
                market_data = SchwabMarketDataClient(create_schwab_client())
                scanner = LiveCandidateScanner(
                    market_data=market_data,
                    pipeline=create_default_candidate_pipeline(),
                    market_analysis=MarketAnalysisBuilder(),
                )
                candidates = scanner.scan_live(symbol=symbol, config=DEFAULT_STRATEGIES["Balanced"])
                if request.form.get("action") == "dry_run":
                    eligible = [c for c in candidates if c.decision == "TRADE"]
                    if not eligible:
                        raise ValueError("No TRADE candidate is currently available.")
                    plan = BullPutOrderPlanBuilder().build_entry(eligible[0], quantity=1)
                    validation = OrderPlanValidator().validate(plan)
            except Exception as exc:
                error = str(exc)
        return page("Recommendations", """
        <h1>Recommendations</h1><div class='card'><form method='post'><input name='symbol' value='{{symbol}}'><button name='action' value='scan'>Scan</button><button class='secondary' name='action' value='dry_run'>Create top TRADE dry-run</button></form></div>
        {% if error %}<div class='card danger'>{{error}}</div>{% endif %}
        {% if candidates %}<div class='card'><table><tr><th>Rank</th><th>Decision</th><th>Score</th><th>Spread</th><th>Credit</th></tr>{% for c in candidates %}<tr><td>{{loop.index}}</td><td>{{c.decision}}</td><td>{{'%.1f'|format(c.score)}}</td><td>{{c.spread.short_put.strike|int}} / {{c.spread.long_put.strike|int}}</td><td>${{'%.2f'|format(c.spread.credit)}}</td></tr>{% endfor %}</table></div>{% endif %}
        {% if plan %}<div class='card'><h2>Dry-run order plan</h2><p class='warning'>No order can be submitted from this console.</p><pre>Symbol: {{plan.symbol}}\nQuantity: {{plan.quantity}}\nLimit credit: ${{'%.2f'|format(plan.limit_price)}}\nMaximum risk: ${{'%.2f'|format(plan.maximum_risk)}}\nValidation: {{'PASS' if validation.valid else 'FAIL'}}\n{% for leg in plan.legs %}{{leg.instruction.value}} {{leg.symbol}}\n{% endfor %}</pre></div>{% endif %}
        """, symbol=symbol, candidates=candidates, error=error, plan=plan, validation=validation)

    @app.get("/paper")
    def paper():
        try:
            account = PaperTradingService(PaperLedger("data/paper_account.json")).status(); error = None
        except Exception as exc:
            account = None; error = str(exc)
        return page("Paper", """
        <h1>Paper Portfolio</h1>{% if error %}<div class='card danger'>{{error}}</div>{% elif account %}<div class='grid'><div class='card'><div class='muted'>Equity</div><div class='metric'>${{'%.2f'|format(account.equity)}}</div></div><div class='card'><div class='muted'>Realized P/L</div><div class='metric'>${{'%.2f'|format(account.realized_pnl)}}</div></div><div class='card'><div class='muted'>Unrealized P/L</div><div class='metric'>${{'%.2f'|format(account.unrealized_pnl)}}</div></div><div class='card'><div class='muted'>Open positions</div><div class='metric'>{{account.open_positions|length}}</div></div></div>{% endif %}
        """, account=account, error=error)

    @app.get("/health")
    def health():
        from app.config.runtime_config import RuntimeConfigLoader
        config = RuntimeConfigLoader("config/runtime.json").load()
        result = HealthChecker(config).run()
        return page("Health", """
        <h1>Health & Diagnostics</h1><div class='card'><table><tr><th>Status</th><th>Check</th><th>Message</th></tr>{% for c in result.checks %}<tr><td class='{{"good" if c.status.value=="PASS" else "warning"}}'>{{c.status.value}}</td><td>{{c.name}}</td><td>{{c.message}}</td></tr>{% endfor %}</table></div>
        """, result=result)

    @app.post("/trade/submit")
    def forbidden_submit():
        return {"error": "Live order submission is not implemented in v0.10.3."}, 405

    return app
