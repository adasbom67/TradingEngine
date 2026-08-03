# TradingEngine

TradingEngine is a modular options research and trading platform focused initially on bull put credit spreads. It supports live Schwab market data, strategy evaluation, backtesting, portfolio research, walk-forward validation, automated paper trading, watchlists, scheduling, and daily recommendation reports.

## Current version

- Stable release: `v0.9.0`
- Active release candidate: `v0.9.1`
- Active branch: `develop`
- Active phase: Production Readiness

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
python main.py version
python main.py config validate
python main.py health
```

Schwab credentials remain local in `.env` and OAuth state remains local in `token.json`. Neither file may be committed.

## Common commands

```powershell
python main.py scan SPY
python main.py backtest SPY
python main.py portfolio-backtest SPY QQQ IWM DIA
python main.py walk-forward SPY
python main.py paper dashboard
python main.py daily-report --watchlist core
python main.py scheduler status
```

## Project continuity

Future sessions should begin with:

1. `PROJECT_STATUS.md`
2. `ROADMAP.md`
3. `DEVELOPMENT_METHODOLOGY.md`
4. `CHANGELOG.md`

## Safety status

Live order execution is not enabled. Backtest option prices are modeled estimates and are not reconstructed historical fills.


## Schwab account selection

When more than one Schwab account is linked, set `SCHWAB_LIVE_ACCOUNT_HASH` in the local `.env` file. The environment value takes precedence over the blank repository default in `config/runtime.json`. Account identifiers are masked in CLI output. Never commit `.env` or a full account hash.

## Web operations console

Run `python web.py` and open `http://127.0.0.1:8000`. The console supports account selection, backtests, recommendations, dry-run review, paper status, and health checks. Live submission is unavailable.
