# TradingEngine Workstation — Backtesting Workspace

## Included
- Functional React navigation
- Backtesting form
- Ticker and starting capital
- Minimum and maximum DTE
- Spread width presets: 1, 2, 3, 5, and 10
- Custom spread width
- Historical-period selection
- Structured metrics and recent trades
- Responsive desktop, tablet, and phone layouts
- FastAPI validation and tests

## Current DTE behavior
The existing historical engine accepts one entry DTE. The workstation uses the
midpoint of the selected range as a clearly disclosed representative entry DTE.
This is not a full expiration sweep.

## Safety
This slice is research-only. It adds no live-order placement, replacement,
cancellation, account mutation, or broker mutation routes.
