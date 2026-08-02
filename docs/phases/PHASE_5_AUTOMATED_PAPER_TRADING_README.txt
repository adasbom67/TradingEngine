TradingEngine Phase 5 - Automated Paper Trading
================================================

New capabilities
----------------
1. Automatic paper scan
   python main.py paper scan SPY QQQ IWM DIA

   Opens only top-ranked TRADE candidates. WATCH, PASS, duplicate-symbol,
   no-candidate, and risk-limit outcomes are written to the paper ledger.

2. Daily position management
   python main.py paper manage

   Marks every open position using a conservative natural close estimate:
       short put ask - long put bid

   Automatically closes positions at the configured:
   - profit target
   - stop loss
   - exit DTE

3. Daily workflow
   python main.py paper daily SPY QQQ IWM DIA

   Manages existing positions first, then scans for new qualifying trades.

4. Portfolio dashboard
   python main.py paper dashboard

   Shows equity, realized/unrealized P/L, buying power, committed risk,
   drawdown, win rate, and current open exposure.

5. CSV export
   python main.py paper export --directory reports/paper

   Produces:
   - paper_positions.csv
   - paper_observations.csv
   - paper_equity_curve.csv

6. Risk controls
   The automatic workflow enforces:
   - maximum open positions
   - maximum risk per trade
   - maximum account risk percentage per trade
   - maximum total portfolio risk percentage
   - duplicate-symbol prevention

Verification
------------
132 tests passed in the packaging environment using a temporary schwab-py
import stub. Run the complete suite in the existing Windows virtual environment:

    pytest -q

Expected result:

    132 passed

Deployment
----------
Copy the contents of this ZIP into the existing TradingEngine folder and allow
Windows to merge folders and replace matching source/test files.

Do not replace or delete the existing:
- .env
- token.json
- data/paper_account.json

The paper ledger is intentionally not included in this ZIP.
