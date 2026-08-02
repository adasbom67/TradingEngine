TradingEngine Change Set 04 — Automatic Market Analysis
=======================================================

What is included
----------------
- Daily Schwab price-history retrieval (preserves your local addition)
- Automatic .env loading in Schwab authentication
- TechnicalIndicators:
  - SMA(20)
  - SMA(200)
  - Wilder RSI(14)
  - Wilder ATR(14)
- MarketAnalysisBuilder:
  - Creates PriceSnapshot from Schwab candles
  - Creates TrendAnalysis from PutSpreadConfig rules
- LiveCandidateScanner.scan_live():
  - Retrieves daily price history
  - Builds market analysis automatically
  - Retrieves the live option chain
  - Runs the existing candidate pipeline
- Automated tests for all new behavior

Safety
------
The ZIP does not contain .env or token.json. Keep your existing local copies.

Installation
------------
1. Back up your current TradingEngine folder.
2. Extract this ZIP.
3. Copy the contents into C:\Users\Anil Das\TradingEngine and replace matching files.
4. Confirm your existing .env and token.json remain in your local project.
5. Run:

   python -m pytest -q

Expected local result
---------------------
78 passed, with the existing harmless websockets deprecation warning possible.

New scanner method
------------------
LiveCandidateScanner now has:

   scan_live(symbol, config, as_of=None, price_history_years=2)

It automatically creates PriceSnapshot and TrendAnalysis before running the
existing live option-chain candidate pipeline.
