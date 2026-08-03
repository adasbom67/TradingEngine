# TradingEngine v0.10.3 - Web Operations Console

Added a local-only Flask console for masked Schwab account selection, backtest inputs/results, recommendations, dry-run order review, paper portfolio status, and health checks.

Safety: no submit, cancel, or replace implementation exists. `/trade/submit` returns HTTP 405. The selected account hash is stored only in `data/local_settings.json` or `.env`.

Start with `python web.py`, then open `http://127.0.0.1:8000`.
