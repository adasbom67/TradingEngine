TradingEngine Phase 2 - Decision and Managed Trade Model
========================================================

Added
-----
- Managed expected value using configured profit target and stop loss.
- Separate unmanaged expiration/max-loss expected value.
- Explicit TRADE / WATCH / PASS decisions with rationale.
- Multi-width spread evaluation: $2, $3, $5, and $10 defaults.
- Decision-aware candidate ranking.
- Multi-symbol command-line scanning.
- Watchlist summary output.
- Correct schwab-py daily price-history arguments for version 1.5.1.

Commands
--------
Single symbol:
    python main.py scan SPY

Multiple symbols:
    python main.py scan SPY QQQ IWM DIA

Tests
-----
    python -m pytest -q

Expected result in the packaged source: 98 passed.

Important
---------
Keep your existing .env and token.json. They are not included.
The probability model remains delta-based and should be treated as a
screening estimate, not a guarantee or personalized investment advice.
