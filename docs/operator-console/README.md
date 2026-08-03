# TradingEngine Operator Console v1 Alpha

This additive release introduces a FastAPI application boundary and responsive React/TypeScript console while preserving the existing CLI and Flask console for rollback.

## Safety boundary

The API exposes health, masked account selection, backtesting, and recommendations. The live-order submission endpoint is deliberately blocked and returns HTTP 403.

## Start backend

```powershell
pip install -r requirements-operator-console.txt
python operator_api.py
```

## Start frontend

```powershell
cd operator-console
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Included workflows

- responsive command-center shell
- masked Schwab account selection
- backtest inputs for symbol, capital, minimum/maximum DTE, and spread width
- structured backtest metrics and recent trades
- multi-symbol recommendations
- expiration, DTE, both leg deltas, net position delta, credit, risk, POP, and managed EV
- health checks

## Deferred

- live-order submission
- authentication for non-local deployment
- persistent research-run history
- interactive chart library integration
- dry-run intent persistence
