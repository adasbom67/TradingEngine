# Trading Engine Architecture

## 1. Purpose

The Trading Engine is a modular Python application for researching, scanning, backtesting, paper trading, and eventually executing options strategies.

The first supported strategy is a bullish put credit spread, but the architecture is designed to support additional strategies without rewriting the scanner, backtester, portfolio manager, reporting system, or user interface.

## 2. Core Architecture

```text
User Interface
      |
      v
Strategy Configuration
      |
      v
Strategy Engine
      |
      +-------------------+
      |                   |
      v                   v
Market Scanner       Backtesting Engine
      |                   |
      +---------+---------+
                |
                v
        Portfolio and Risk
                |
        +-------+-------+
        |               |
        v               v
  Paper Trading    Live Execution
        |
        v
 Reports and Analytics
```

## 3. Architectural Principles

### 3.1 Separation of concerns

Each module should have one clear responsibility.

Examples:

* Broker modules communicate with external broker APIs.
* Strategy modules make trading decisions.
* Backtesting modules simulate historical trades.
* Risk modules approve or reject proposed trades.
* UI modules collect inputs and display results.

### 3.2 Shared strategy logic

The scanner, backtester, paper trader, and live trader must use the same strategy rules.

Strategy logic must not be copied into multiple modules.

### 3.3 Configuration-driven behavior

Trading rules should be represented by configuration objects rather than hardcoded values.

Examples include:

* Delta range.
* Days to expiration.
* Spread width.
* Minimum credit.
* Profit target.
* Stop-loss rule.
* Risk per trade.

### 3.4 Safe defaults

Live order execution must remain disabled unless it is explicitly enabled through a controlled configuration and passes all required safety checks.

### 3.5 Testability

Core trading logic must not depend directly on the user interface.

Functions and classes should accept ordinary Python objects so they can be tested independently.

## 4. Module Responsibilities

## 4.1 `app/brokers`

### Purpose

Provide a common interface for broker and market-data services.

### Inputs

* API credentials.
* Authentication tokens.
* Symbols.
* Account identifiers.
* Market-data requests.
* Order requests.

### Outputs

* Historical price data.
* Current quotes.
* Option chains.
* Account balances.
* Positions.
* Order statuses.
* Broker responses.

### Dependencies

* Schwab API client.
* Application configuration.
* Logging utilities.

### Rules

* Broker-specific response formats should be converted into internal models.
* Strategy modules should not directly call broker-library methods.
* Authentication failures should raise clear errors.
* Sensitive credentials must not be committed to Git.

## 4.2 `app/data`

### Purpose

Retrieve, normalize, validate, cache, and store market data.

### Inputs

* Broker responses.
* Historical data files.
* Symbols.
* Date ranges.
* Data frequency.

### Outputs

* Standardized price records.
* Standardized option records.
* Validated datasets.
* Cached historical data.

### Dependencies

* Broker layer.
* Configuration.
* Internal data models.

### Rules

* Data must be validated before use.
* Missing values must be handled explicitly.
* Dates and times must use consistent timezone rules.
* Historical and live data must be distinguishable.

## 4.3 `app/indicators`

### Purpose

Calculate technical indicators from standardized price data.

### Inputs

* Historical price records.
* Indicator parameters.

### Outputs

* Simple moving averages.
* Exponential moving averages.
* RSI.
* ATR.
* MACD.
* Other derived market indicators.

### Dependencies

* Data models.
* Numerical or dataframe libraries.

### Rules

* Indicator functions should not retrieve market data themselves.
* Indicator calculations should be deterministic.
* Insufficient historical data should produce a clear result or error.

## 4.4 `app/config`

### Purpose

Define and validate strategy and application settings.

### Inputs

* Default values.
* User-interface inputs.
* Saved strategy files.
* Environment variables.

### Outputs

* Validated configuration objects.
* Strategy presets.
* Application settings.

### Dependencies

* Python standard library.
* Optional serialization utilities.

### Rules

* Configurations store values, not trading behavior.
* Every configuration object must support validation.
* Invalid settings must fail before a scan or order is attempted.
* Sensitive values must come from environment variables or secure storage.

## 4.5 `app/options`

### Purpose

Normalize option-chain data and perform reusable option calculations.

### Inputs

* Raw or normalized option-chain data.
* Expiration dates.
* Strikes.
* Bid and ask prices.
* Greeks.
* Underlying price.

### Outputs

* Flattened option records.
* Spread pricing.
* Maximum profit.
* Maximum loss.
* Breakeven.
* Liquidity measurements.

### Dependencies

* Data models.
* Date utilities.
* Configuration where appropriate.

### Rules

* This module provides reusable calculations.
* It should not decide whether a complete strategy should trade.
* Bid, ask, midpoint, and estimated fill prices must remain distinct.

## 4.6 `app/strategies`

### Purpose

Apply strategy rules and produce trade candidates.

### Inputs

* Strategy configuration.
* Underlying market data.
* Indicator values.
* Option-chain data.
* Portfolio context when required.

### Outputs

* Qualified option candidates.
* Constructed spreads.
* Candidate scores.
* Rejection reasons.
* Trade explanations.

### Dependencies

* Configuration.
* Indicators.
* Options utilities.
* Internal models.
* Risk checks where required.

### Rules

* Strategy decisions belong here.
* Strategies should not display UI elements.
* Strategies should not directly submit orders.
* Every recommendation should explain why it was selected or rejected.

## 4.7 `app/scanners`

### Purpose

Run one or more strategies across multiple symbols.

### Inputs

* Symbol lists.
* Strategy objects.
* Current market data.
* Scan settings.

### Outputs

* Ranked opportunities.
* Symbols with no valid trades.
* Rejection reasons.
* Scan summaries.

### Dependencies

* Strategy engine.
* Data layer.
* Broker layer.
* Reporting utilities.

### Rules

* The scanner coordinates work but does not duplicate strategy logic.
* Failures for one symbol should not necessarily stop the entire scan.
* Results should include timestamps.

## 4.8 `app/backtesting`

### Purpose

Simulate strategy behavior using historical data.

### Inputs

* Strategy configuration.
* Historical price data.
* Historical option data when available.
* Starting capital.
* Slippage assumptions.
* Transaction costs.
* Date range.

### Outputs

* Historical trades.
* Daily portfolio values.
* Equity curve.
* Performance metrics.
* Rejected signals.
* Backtest assumptions.

### Dependencies

* Strategy engine.
* Historical data layer.
* Portfolio simulator.
* Risk module.
* Reporting module.

### Rules

* The backtester must not access future data.
* Historical option data and estimated option prices must be clearly distinguished.
* Entry and exit fills must include configurable slippage.
* Results must identify all important assumptions.
* Open positions must be tracked through time.

## 4.9 `app/papertrading`

### Purpose

Simulate trading using current market data without submitting live broker orders.

### Inputs

* Approved trade candidates.
* Current quotes.
* Virtual account balance.
* Position and risk settings.

### Outputs

* Simulated orders.
* Virtual positions.
* Profit-and-loss records.
* Position history.

### Dependencies

* Strategy engine.
* Portfolio module.
* Risk module.
* Market-data layer.
* Reporting module.

### Rules

* Paper trades must use realistic estimated fills.
* Paper and live positions must never be mixed.
* Every simulated order must be timestamped and logged.

## 4.10 `app/portfolio`

### Purpose

Track capital, positions, exposure, and position sizing.

### Inputs

* Account balance.
* Existing positions.
* Proposed trades.
* Trade risk.
* Portfolio limits.

### Outputs

* Position sizes.
* Capital usage.
* Portfolio exposure.
* Position records.
* Available buying power.

### Dependencies

* Internal models.
* Risk configuration.
* Broker account data or paper account state.

### Rules

* Position sizing should be centralized.
* Strategies should not independently calculate final contract quantities.
* Portfolio state must be updated consistently after orders or simulated fills.

## 4.11 `app/risk`

### Purpose

Determine whether a proposed trade is permitted.

### Inputs

* Proposed trade.
* Maximum loss.
* Portfolio state.
* Account balance.
* Open positions.
* Risk configuration.

### Outputs

* Approval or rejection.
* Maximum allowed quantity.
* Risk warnings.
* Rejection reasons.

### Dependencies

* Portfolio module.
* Strategy configuration.
* Internal trade models.

### Rules

* Risk checks must occur before order creation.
* Rejected trades must include a reason.
* Live execution may not bypass risk controls.
* Portfolio-level and trade-level risk must both be evaluated.

## 4.12 `app/execution`

### Purpose

Convert approved trade instructions into broker orders.

### Inputs

* Approved trade.
* Account identifier.
* Quantity.
* Limit price.
* Execution mode.
* Broker configuration.

### Outputs

* Order preview.
* Broker order request.
* Order confirmation.
* Order status.
* Execution errors.

### Dependencies

* Broker layer.
* Risk module.
* Portfolio state.
* Logging.

### Rules

* Execution must support paper and live modes distinctly.
* Live orders require explicit safeguards.
* Duplicate-order protection is required.
* Orders should be previewed and validated before submission.
* Broker responses must be logged without exposing secrets.

## 4.13 `app/reports`

### Purpose

Create human-readable and machine-readable results.

### Inputs

* Scan results.
* Backtest results.
* Trades.
* Positions.
* Portfolio history.
* Performance metrics.

### Outputs

* Tables.
* CSV files.
* Charts.
* Trade logs.
* Performance summaries.
* Strategy comparison reports.

### Dependencies

* Internal models.
* Dataframe and charting libraries.
* File utilities.

### Rules

* Reports should not contain trading logic.
* Every report should identify the strategy and configuration used.
* Backtest reports should include assumptions and date ranges.

## 4.14 `app/ui`

### Purpose

Allow users to configure and operate the platform through a local interface.

### Inputs

* User-entered symbols.
* Strategy parameters.
* Saved strategies.
* Date ranges.
* Operating mode.

### Outputs

* Validated configuration objects.
* Scan requests.
* Backtest requests.
* Results tables.
* Charts.
* User-facing errors.

### Dependencies

* Strategy configuration.
* Scanner.
* Backtester.
* Reports.
* Paper trading.
* Execution controls.

### Rules

* The UI must not contain trading calculations.
* User input must be validated before execution.
* Paper and live modes must be visually distinct.
* Live trading actions must require explicit confirmation.

## 4.15 `app/utils`

### Purpose

Provide small reusable utilities that do not belong to a business-specific module.

### Inputs

* Dates.
* File paths.
* Logging settings.
* General application values.

### Outputs

* Formatted values.
* Date calculations.
* Logging configuration.
* File operations.

### Dependencies

* Python standard library.

### Rules

* Utilities should remain small and general.
* Trading decisions must not be hidden inside utility functions.

## 5. Core Domain Objects

The platform will gradually introduce internal models for common concepts.

Planned models include:

```text
PriceBar
OptionContract
OptionQuote
OptionChain
TradeCandidate
OptionLeg
CreditSpread
TradeDecision
Position
OrderRequest
OrderResult
PortfolioState
BacktestTrade
PerformanceMetrics
```

These models will provide a stable interface between modules.

For example, a strategy should receive a standardized `OptionChain` rather than a raw Schwab response.

## 6. Strategy Interface

All strategies should eventually follow a common structure.

A strategy may provide methods such as:

```python
validate_config()
analyze_underlying()
find_candidates()
construct_trades()
score_trade()
explain_trade()
evaluate_exit()
```

The exact interface will be introduced gradually rather than all at once.

The initial implementation will focus on the bull put spread strategy.

## 7. Data Flow

A typical live scan should follow this sequence:

```text
1. User selects a strategy and symbols.
2. The configuration is validated.
3. The data layer retrieves price and option data.
4. Indicators are calculated.
5. The strategy evaluates the underlying trend.
6. The strategy filters option candidates.
7. Spreads are constructed and scored.
8. Risk checks are applied.
9. Results are displayed and recorded.
```

A backtest should follow a similar sequence using historical data:

```text
1. Load the strategy configuration.
2. Load historical data for the selected period.
3. Advance through dates in chronological order.
4. Evaluate entry signals without using future data.
5. Construct simulated trades.
6. Apply position sizing and risk limits.
7. Track open positions.
8. Apply exit rules.
9. Record portfolio value and trade results.
10. Calculate performance statistics.
```

## 8. Dependency Direction

Dependencies should generally flow inward toward business logic and shared models.

Preferred direction:

```text
UI
 |
 v
Application Services
 |
 +--> Scanner
 +--> Backtester
 +--> Paper Trader
 +--> Execution
          |
          v
      Strategies
          |
          +--> Indicators
          +--> Options
          +--> Configuration
          +--> Domain Models
```

Strategy logic should not depend on Streamlit, command-line prompts, or report formatting.

## 9. Testing Strategy

Testing will be added incrementally.

### Unit tests

Used for:

* Configuration validation.
* Indicator calculations.
* Option-chain normalization.
* Spread calculations.
* Candidate filtering.
* Risk calculations.
* Exit rules.

### Integration tests

Used for:

* Schwab market-data retrieval.
* Option-chain processing.
* Scanner workflows.
* Backtest workflows.
* Paper-trading workflows.

### Safety tests

Used for:

* Live trading disabled by default.
* Invalid configurations rejected.
* Excessive risk rejected.
* Duplicate orders blocked.
* Paper and live accounts separated.

## 10. Logging

The application should record:

* Startup and shutdown.
* Authentication events.
* Market-data requests.
* Data-validation failures.
* Strategy decisions.
* Trade rejection reasons.
* Backtest assumptions.
* Paper orders.
* Live order previews and submissions.
* Broker errors.
* Unexpected exceptions.

Sensitive values such as access tokens, refresh tokens, client secrets, and full credentials must never be logged.

## 11. Configuration Storage

Initially, configurations will be created in Python.

Later, strategy configurations may be stored as JSON files, for example:

```text
config/strategies/
├── bull_put_conservative.json
├── bull_put_balanced.json
└── spy_income.json
```

Saved files should contain settings only. They should not contain executable Python code.

## 12. Safety Boundaries

The following boundaries are mandatory:

* Scanner output is not an order.
* Strategy approval is not risk approval.
* Risk approval is not user authorization.
* Paper execution is not live execution.
* Live submission must be explicitly enabled.
* Broker order status must be confirmed after submission.
* Failed or uncertain orders must not be silently retried.

## 13. Current Implementation Sequence

The current development sequence is:

1. Validate `PutSpreadConfig`.
2. Create `BullPutSpreadStrategy`.
3. Update put-candidate selection to use the configuration.
4. Test current option-chain filtering.
5. Construct complete bull put spreads.
6. Add trade scoring and explanations.
7. Build the first historical underlying-signal backtest.
8. Add backtest performance metrics.
9. Create the Streamlit strategy editor and dashboard.
10. Begin paper-trading development.

## 14. Change Policy

Architecture may evolve as the project grows.

When a major decision changes, this document should be updated to explain:

* What changed.
* Why it changed.
* Which modules are affected.
* Whether migration is required.
