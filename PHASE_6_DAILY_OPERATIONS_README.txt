TradingEngine Phase 6 - Daily Operations
========================================

Adds the first three Phase 6 capabilities:

1. Scheduler
   - Persistent local schedule configuration
   - Weekday-only jobs
   - Idempotent once-per-day execution
   - Status, run-due, and continuous loop commands
   - Default Eastern Time schedule at 09:45 and 15:45

2. Watchlist Manager
   - Named JSON watchlists
   - Default watchlist selection
   - Create, add, remove, show, list, and set-default commands
   - Initial core and sector watchlists

3. Daily Recommendation Reporting
   - Scans an entire named watchlist
   - Isolates symbol-specific market-data failures
   - Ranks TRADE, WATCH, PASS, and ERROR outcomes
   - Writes timestamped Markdown reports to reports/daily
   - Provides concise summary and selected candidate details

Verification in packaging environment
-------------------------------------
137 tests passed using a temporary schwab-py import stub.
Python compileall passed.

Local deployment verification
-----------------------------
Run in the existing Windows virtual environment:

    pytest -q

Expected:

    137 passed

Suggested first-run commands
----------------------------

    python main.py watchlist init
    python main.py watchlist list
    python main.py daily-report --watchlist core
    python main.py scheduler init
    python main.py scheduler status
    python main.py scheduler run-due

To run continuously in a terminal:

    python main.py scheduler loop --poll-seconds 60

Press Ctrl+C to stop the loop.

Notes
-----
- Keep the existing .env, token.json, and data/paper_account.json files.
- The scheduler is a local foreground process. Windows Task Scheduler can later
  be used to launch it automatically after login or reboot.
- Schedule settings are stored in config/schedule.json.
- Watchlists are stored in config/watchlists.json.
- Scheduler execution state is stored in data/scheduler_state.json.
