TradingEngine Phase 3C - Research Diagnostics
==============================================

Changes
-------
- Uses each daily bar's high and low to detect target and stop touches.
- Applies a conservative stop-first assumption when both thresholds are touched.
- Caps adverse stop-gap execution with a configurable maximum debit increment.
- Records entry SMA20, SMA200, RSI, market regime, underlying return, MFE, and MAE.
- Adds average holding period and longest losing streak metrics.
- Reports performance grouped by market regime and exit reason.

Caution
-------
Historical option prices remain model approximations. Results are for strategy
research and must not be treated as reconstructed executable fills.
