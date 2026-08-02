TradingEngine Phase 1 Complete
==============================

This package completes the first live decision-engine phase.

Added in this release
---------------------
- Delta-based probability and expected-value engine
- Bullish, neutral, bearish, and high-volatility market regimes
- Market-regime scoring
- Portfolio-level position, buying-power, daily-loss, and risk constraints
- Trade quality score breakdown
- Expanded human-readable recommendation report
- Live command-line scan entry point

Run all tests
-------------
    python -m pytest -q

Run a live SPY scan
-------------------
    python main.py scan SPY

Use a preset and show the top 3
-------------------------------
    python main.py scan SPY --strategy Conservative --limit 3

Apply portfolio constraints
---------------------------
    python main.py scan SPY --account-value 100000 --buying-power 20000

Important
---------
Keep your existing .env and token.json files. They are intentionally excluded.
Probability and expected-value figures are transparent delta-based estimates,
not guarantees or broker-supplied probabilities.
