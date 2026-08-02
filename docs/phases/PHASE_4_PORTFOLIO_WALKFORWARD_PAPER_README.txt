TradingEngine Phase 4
Portfolio Backtesting, Walk-Forward Validation, and Paper Trading
=================================================================

VERIFICATION
------------
121 tests passed in the packaging environment using a temporary Schwab import
stub. Python compilation passed. Run the full suite in your existing Windows
virtual environment, which already contains schwab-py.

NEW COMMANDS
------------

1. Portfolio backtest

   python main.py portfolio-backtest SPY QQQ IWM DIA

Optional controls:

   --initial-capital 100000
   --max-open-positions 5
   --max-risk-per-trade 500

This combines symbol-level simulated trades under shared position and risk
constraints. It reports portfolio P/L, profit factor, drawdown, maximum
concurrency, rejected trades, and P/L by symbol.

2. Walk-forward validation

   python main.py walk-forward SPY

Optional controls:

   --initial-capital 100000
   --training-bars 504
   --testing-bars 126

Each fold optimizes on a rolling training window and evaluates the selected
parameters on the following unseen testing window. Historical option values
remain approximate.

3. Paper trading

Initialize:

   python main.py paper init --cash 100000

View status:

   python main.py paper status

Open a virtual spread:

   python main.py paper open SPY --expiration 2026-09-18 --short 730 --long 725 --credit 1.15

Mark its current debit:

   python main.py paper mark POSITION_ID --debit 0.70

Close it:

   python main.py paper close POSITION_ID --debit 0.55 --reason PROFIT_TARGET

Paper account state is stored locally at data/paper_account.json and is excluded
from Git. Use --ledger with the paper command to specify another file.

IMPORTANT LIMITATIONS
---------------------
- Backtesting uses ATR-volatility Black-Scholes approximations, not historical
  executable option-chain prices.
- Walk-forward testing reduces overfitting risk but does not eliminate it.
- Paper trading does not submit any orders to Schwab.
- Paper marks are entered manually in this release.

DEPLOYMENT
----------
Copy the app, tests, main.py, .gitignore, and this README into the root of your
TradingEngine project, allowing folders to merge. Keep your existing .env and
token.json.

Then run:

   pytest -q

Expected result:

   121 passed
