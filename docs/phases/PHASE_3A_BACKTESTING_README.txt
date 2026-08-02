TradingEngine Phase 3A - Historical Backtesting Foundation

Adds:
- app/backtesting/models.py
- app/backtesting/engine.py
- app/reports/backtest_report.py
- python main.py backtest SYMBOL
- four focused backtesting tests

Important limitation:
Schwab daily equity history does not provide historical option chains. This
foundation therefore approximates option spread values from the underlying's
daily bars, ATR, configured spread width, and configured credit percentage.
The CLI and report disclose this limitation. Do not treat results as historical
executable fills.

Validation performed in the packaging environment:
- Python compilation succeeded for all new/modified files.
- 4 focused backtesting tests passed.
- Full-suite collection could not be run in the packaging environment because
  schwab-py was not installed there. Run the complete suite in your existing
  Windows virtual environment, where schwab-py is installed.

Commands:
  pytest -q
  python main.py backtest SPY
