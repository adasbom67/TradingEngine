TradingEngine Phase 3B - Backtest Calibration
==============================================

Changes
-------
- Replaces fixed-credit/time-decay pricing with an isolated Black-Scholes
  vertical-spread approximation.
- Derives annualized volatility from ATR and clamps it to configurable bounds.
- Entry credits now vary with spot, strikes, DTE, and volatility.
- Stop-loss fills execute at the configured stop plus slippage instead of
  automatically jumping to maximum loss.
- Maximum loss is reserved for a close at or below the long strike.
- Adds entry/exit diagnostics to each BacktestTrade.
- Expands reports with average winner/loser, credit, exit debit, and DTE.

Verification
------------
Run:

    pytest -q
    python main.py backtest SPY

Compare the new results with the Phase 3A baseline:
154 trades, 64.3% win rate, -$16,052.29 total P/L, profit factor 0.17.

Important
---------
This remains an approximate research model. It is not a substitute for
historical option-chain data.
