# TradingEngine

TradingEngine is a modular options research and trading platform focused initially on bull put credit spreads. It supports live Schwab market data, strategy evaluation, backtesting, portfolio research, walk-forward validation, automated paper trading, watchlists, scheduling, and daily recommendation reports.

## Current version

- Stable release: `v0.9.0`
- Active release candidate: `v0.9.3`
- Active branch: `develop`
- Active phase: Production Readiness

## Desktop quick start

Normal use no longer requires VS Code or a terminal. Open either Windows artifact in:

```text
operator-console\release
```

- `TradingEngine-0.9.3-x64-Setup.exe` installs the application and creates shortcuts.
- `TradingEngine-0.9.3-x64-Portable.exe` runs directly without installation.

The desktop application starts and stops its private API automatically. See `docs/DESKTOP_APPLICATION.md` for build and runtime details.

## Developer quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
python main.py version
python main.py config validate
python main.py health
```

Build the Windows desktop artifacts with:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build_desktop.ps1
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
