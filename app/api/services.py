from __future__ import annotations
import math
from app.backtesting.engine import HistoricalBacktester
from app.backtesting.models import BacktestConfig
from app.brokers.schwab_auth import create_schwab_client
from app.brokers.schwab_market_data import SchwabMarketDataClient
from app.brokers.schwab_trading.client import SchwabTradingClient
from app.config.runtime_config import RuntimeConfigLoader
from app.config.strategy_config import DEFAULT_STRATEGIES
from app.evaluation.default_pipeline import create_default_candidate_pipeline
from app.indicators.market_analysis import MarketAnalysisBuilder
from app.operations.health import HealthChecker
from app.scanners.live_candidate_scanner import LiveCandidateScanner
from app.web.settings import LocalSettingsStore


def finite(value: float):
    return value if math.isfinite(value) else None

def health_payload():
    cfg=RuntimeConfigLoader().load(); report=HealthChecker(cfg).run()
    return {'version': cfg.version, 'healthy': report.healthy,
            'checks':[{'name':c.name,'status':c.status.value,'message':c.message} for c in report.checks]}

def list_accounts(settings_path='data/local_settings.json'):
    broker=SchwabTradingClient(create_schwab_client()); linked=broker.get_accounts(); local=LocalSettingsStore(settings_path).load()
    return linked, local

def save_account(last_four: str, settings_path='data/local_settings.json'):
    linked,_=list_accounts(settings_path)
    matches=[a for a in linked if a.account_id.endswith(last_four)]
    if len(matches) != 1: raise ValueError('Account selection must match exactly one linked Schwab account.')
    a=matches[0]; LocalSettingsStore(settings_path).save_account(a.account_hash, a.account_id[-4:]); return a

def run_backtest(request):
    market=SchwabMarketDataClient(create_schwab_client())
    history=market.get_daily_price_history(request.symbol, period_years=5)
    cfg=BacktestConfig(initial_capital=request.initial_capital,
        minimum_entry_dte=request.minimum_entry_dte,
        maximum_entry_dte=request.maximum_entry_dte,
        spread_width=request.spread_width)
    result=HistoricalBacktester().run(request.symbol, history, cfg)
    equity=[request.initial_capital]; value=request.initial_capital
    for trade in result.trades:
        value += trade.pnl; equity.append(round(value,2))
    groups=lambda rows:[{'name':g.name,'trade_count':g.trade_count,'win_rate':g.win_rate,
        'total_pnl':g.total_pnl,'average_pnl':g.average_pnl,'profit_factor':finite(g.profit_factor)} for g in rows]
    return {'symbol':result.symbol,'initial_capital':result.initial_capital,'ending_capital':result.ending_capital,
        'total_pnl':result.total_pnl,'trade_count':len(result.trades),'win_rate':result.win_rate,
        'profit_factor':finite(result.profit_factor),'maximum_drawdown':result.maximum_drawdown,
        'average_pnl':result.average_pnl,'average_winner':result.average_winner,'average_loser':result.average_loser,
        'minimum_entry_dte':request.minimum_entry_dte,'maximum_entry_dte':request.maximum_entry_dte,
        'spread_width':request.spread_width,'by_regime':groups(result.by_regime()),
        'by_exit_reason':groups(result.by_exit_reason()),
        'recent_trades':[{'entry_date':t.entry_date.isoformat(),'exit_date':t.exit_date.isoformat(),
            'short_strike':t.short_strike,'long_strike':t.long_strike,'entry_dte':t.entry_dte,
            'pnl':t.pnl,'exit_reason':t.exit_reason} for t in result.trades[-10:]], 'equity_curve':equity}

def run_recommendations(request):
    if request.strategy not in DEFAULT_STRATEGIES: raise ValueError(f'Unknown strategy: {request.strategy}')
    market=SchwabMarketDataClient(create_schwab_client())
    scanner=LiveCandidateScanner(market_data=market,pipeline=create_default_candidate_pipeline(),market_analysis=MarketAnalysisBuilder())
    config=DEFAULT_STRATEGIES[request.strategy]; output=[]
    for symbol in request.symbols:
        try:
            candidates=scanner.scan_live(symbol=symbol,config=config)
            rows=[]
            for c in candidates:
                s=c.spread
                short_delta=float(s.short_put.delta or 0.0); long_delta=float(s.long_put.delta or 0.0)
                rows.append({'symbol':symbol,'rank':c.rank,'decision':c.decision,'score':c.score,
                    'expiration':s.short_put.expiration_date.isoformat(),'dte':s.short_put.days_to_expiration,
                    'short_strike':s.short_put.strike,'long_strike':s.long_put.strike,
                    'short_delta':short_delta,'long_delta':long_delta,
                    'net_position_delta':round((-short_delta)+long_delta,4),
                    'credit':s.credit,'max_profit':s.max_profit,'max_loss':s.max_loss,'breakeven':s.breakeven,
                    'probability_of_profit':c.probability_of_profit,'return_on_risk':c.return_on_risk,
                    'managed_expected_value':c.managed_expected_value,'market_regime':c.market_regime,
                    'reasons':c.reasons,'warnings':c.warnings})
            message=f'{len(rows)} candidates returned.' if rows else 'Scan completed; no eligible candidates were constructed.'
            output.append({'symbol':symbol,'status':'ok','message':message,'recommendations':rows})
        except Exception as exc:
            output.append({'symbol':symbol,'status':'error','message':str(exc),'recommendations':[]})
    return {'strategy':request.strategy,'results':output,'live_submission_available':False}
