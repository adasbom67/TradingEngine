TradingEngine Update 05 — Opportunity Intelligence
==================================================

Included
--------
- OpportunityEvaluator: delta-based probability proxy, return-on-risk,
  liquidity, and credit-quality scoring.
- Configurable opportunity scoring thresholds and weights.
- BullPutSpread breakeven and return-on-risk properties.
- TradeCandidate probability and return-on-risk fields.
- Default production pipeline using TrendEvaluator + OpportunityEvaluator.
- Human-readable OpportunityReport for ranked recommendations.
- Correct schwab-py daily price-history arguments for version 1.5.1.
- Five new tests.

Install
-------
Copy the contents of this ZIP into the root of your existing TradingEngine
folder and replace matching files. Keep your local .env and token.json files.

Test
----
python -m pytest -q

Expected
--------
83 passed

Important
---------
The probability-of-profit value is a transparent heuristic calculated as
1 - absolute short-put delta. It is not a guarantee or a broker-calculated
probability model.
