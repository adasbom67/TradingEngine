TradingEngine Phase 3D - Exit Optimization
===========================================

New command:

    python main.py backtest-optimize SPY

Optional report limit:

    python main.py backtest-optimize SPY --limit 20

The optimizer compares:
- Exit DTE: 7, 10, 14, 21
- Profit target: 40%, 50%, 60%
- Stop loss: 150%, 175%, 200%
- Trend deterioration exit: off/on
- Short-strike threat exit: off/on

Ranking order:
1. Profit factor
2. Total P/L
3. Lower maximum drawdown

Existing command remains available:

    python main.py backtest SPY

Verification in packaging environment:
- Python compilation passed
- 113 tests passed using a temporary schwab-py import stub

After copying this update into your local TradingEngine project, run:

    pytest -q
    python main.py backtest-optimize SPY

Keep your local .env and token.json. They are not included.
