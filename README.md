# Trading Engine

A modular Python platform for researching, backtesting, paper trading, and eventually executing options-trading strategies through the Charles Schwab API.

> **Project status:** Early development
> **Current milestone:** Strategy framework
> **Live trading:** Disabled

## Project Vision

The goal of this project is to build a maintainable options-trading platform that can:

* Retrieve market and account data from Charles Schwab.
* Analyze underlying securities using technical indicators.
* Scan stocks and ETFs for strategy opportunities.
* Construct and rank options trades.
* Backtest configurable trading strategies.
* Simulate trades in a paper-trading portfolio.
* Track risk, positions, and performance.
* Present strategy settings and results through a local user interface.
* Support live order execution only after extensive testing and validation.

## Initial Strategy

The first strategy being developed is a bullish put credit spread.

Its configurable rules may include:

* Price relative to the 20-day and 200-day simple moving averages.
* Relationship between the 20-day and 200-day moving averages.
* Minimum and maximum days to expiration.
* Short-put delta range.
* Minimum bid price.
* Minimum volume and open interest.
* Maximum bid-ask spread.
* Spread width.
* Minimum credit.
* Profit target.
* Stop-loss threshold.
* Exit days to expiration.
* Maximum risk per trade.
* Maximum number of open positions.

The same strategy definition will eventually be used by the scanner, backtester, paper trader, user interface, and live execution engine.

## Core Design Principle

Strategy rules must be implemented once and reused everywhere.

```text
Strategy Configuration
          |
          v
    Strategy Engine
          |
          +--> Market Scanner
          +--> Backtester
          +--> Paper Trader
          +--> Live Trader
          +--> Reports and UI
```

The user interface will collect settings and display results. It will not contain trading logic.

## Planned Modules

```text
app/
├── backtesting/     Historical strategy simulation
├── brokers/         Broker integrations
├── config/          Strategy and application settings
├── data/            Market-data retrieval and storage
├── execution/       Order preparation and submission
├── indicators/      Technical indicators
├── options/         Option-chain processing and spread construction
├── papertrading/    Simulated positions and orders
├── portfolio/       Portfolio state and position sizing
├── reports/         Trade logs and performance reports
├── risk/            Portfolio and trade-level risk controls
├── scanners/        Multi-symbol opportunity scanning
├── strategies/      Strategy behavior and decision rules
├── ui/              Local user interface
└── utils/           Shared utility functions
```

## Development Roadmap

### Version 0.1 — Foundation

* Project structure
* Python environment
* Schwab authentication
* Historical price retrieval
* Current option-chain retrieval
* Moving-average calculations
* Basic strategy configuration

### Version 0.2 — Strategy Engine

* Validated strategy configuration
* Bull put spread strategy class
* Option candidate filtering
* Spread construction
* Candidate scoring
* Trade-selection explanations
* Strategy presets

### Version 0.3 — Scanner

* Multi-symbol scanning
* Trend filtering
* Ranked trade opportunities
* Rejection reasons
* Scan reports

### Version 0.4 — Backtester

* Historical signal testing
* Historical options-data integration
* Position simulation
* Transaction costs and slippage
* Exit-rule simulation
* Performance metrics
* Trade logs and equity curves

### Version 0.5 — Dashboard

* Strategy editor
* Saved strategy library
* Scanner controls
* Backtest controls
* Results tables
* Performance charts

### Version 1.0 — Paper Trading

* Simulated orders
* Virtual portfolio
* Position monitoring
* Daily profit-and-loss tracking
* Risk-limit enforcement

### Version 2.0 — Live Trading

* Broker account integration
* Order previews
* Explicit execution safeguards
* Position reconciliation
* Monitoring and alerts
* Emergency trading controls

## Development Principles

The project follows these rules:

1. Build and test one small component at a time.
2. Keep configuration separate from strategy behavior.
3. Keep user-interface code separate from trading logic.
4. Reuse the same strategy logic across all operating modes.
5. Validate external data before using it.
6. Apply risk controls before creating an order.
7. Record important decisions and errors through logging.
8. Use type hints and descriptive names.
9. Avoid duplicated business logic.
10. Never enable live execution by default.

## Backtesting Policy

A strategy must not be considered ready for live execution based only on a technical signal or a high win rate.

Evaluation should include:

* Net profit and return on capital.
* Expectancy per trade.
* Average gain and average loss.
* Profit factor.
* Maximum drawdown.
* Consecutive losses.
* Capital utilization.
* Holding period.
* Slippage and transaction costs.
* Results across different market regimes.
* Out-of-sample and paper-trading performance.

Historical underlying-price tests and historical option-spread tests must be clearly distinguished. Estimated option prices must never be presented as actual historical fills.

## Safety

This project is for research and software development. Trading involves financial risk.

Before live execution is considered, the platform must include:

* Configuration validation.
* Position-size limits.
* Maximum trade-risk limits.
* Portfolio exposure limits.
* Duplicate-order protection.
* Market-hours checks.
* Order previews.
* Explicit paper-versus-live account selection.
* Confirmation safeguards.
* Detailed order and error logs.
* A global mechanism that disables order submission.

## Current Development Focus

The immediate development sequence is:

1. Finalize and test `PutSpreadConfig`.
2. Create the bull put spread strategy class.
3. Connect option candidate selection to the strategy configuration.
4. Test candidate selection with current Schwab option-chain data.
5. Build the first underlying-signal backtest.
6. Add a local Streamlit user interface after the core logic is tested.
