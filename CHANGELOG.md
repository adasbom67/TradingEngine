# Changelog

## Unreleased — 2026-08-20

### Added
- Bear call credit-spread construction using short lower-strike calls and protective calls $2, $3, or $5 higher.
- Independent Bull Put, Bear Call, or combined recommendation scans.
- Bearish trend, market-regime, probability, quote-audit, and pipeline diagnostics.
- Strategy-aware recommendation history, saved profiles, and paper positions.
- Live call-chain marking for simulated bear call positions.
- Session-aware recommendation scans that label off-hours results provisional and do not hard-reject short legs on current-session volume outside regular hours.
- Separate protective-leg liquidity defaults: minimum OI 25, no daily-volume requirement, and midpoint-relative quote-quality checks.
- Recommendations strategy navigation with Credit Spreads and Long Straddle sub-tabs; Critical Events is now nested under the Long Straddle strategy.
- Long Straddle contract selection across multiple nearby-ATM pairs and expirations, with open-interest, regular-hours volume, quote-freshness, and combined-spread gates.
- A true 10-point Critical Events score using compression, cost-buffered expiration expected value, same-time intraday pressure, ignition, and liquidity; the unavailable event calendar no longer contributes a placeholder point.
- Contract-specific two-scan alert confirmation so a changing expiration or strike cannot inherit another contract's streak.
- Look-ahead-safe Critical Events validation using a distinct 0–6 daily proxy score, modeled 1/3/5/10/20-session Long Straddle outcomes, score-bucket calibration, and a chronological 70/30 holdout.
- Bounded local SQLite quote collection for evaluated and tracked Long Straddle contracts, with 15-minute deduplication, 730-day retention, a default 1 GB cap, compressed feature snapshots, and visible storage telemetry.
- Removed the extra 2% Long Straddle execution penalty: live economics now use displayed asks plus commissions, while historical modeled results show no-spread, $0.02-per-leg, and $0.05-per-leg sensitivity cases.

### Validation
- 241 Python tests passing.
- Live five-year Critical Events validation completed for SPY, QQQ, IWM, and DIA with zero data errors.
- Live archive validation stored 72 evaluated contracts across four deduplicated snapshots at an initial annualized run rate of approximately 156 MB before tracked-contract accumulation.
- TypeScript/Vite production build passing.
- Live read-only SPY dual-strategy validation produced 44 eligible short puts, 23 eligible short calls, and 66 evaluated spreads without broker or pipeline errors.

### Safety
- Bear calls are always risk-defined; naked short calls are not constructed.
- Live broker-order submission remains unavailable.

## [0.9.3] — 2026-08-08

### Added
- Electron desktop workstation
- Windows installer and portable executable builds
- Packaged Python/FastAPI backend
- Automatic private-backend startup, health waiting, and shutdown
- Single-window workflow for recommendations, backtesting, dashboards, and paper trading
- Same-origin production UI/API hosting and Vite development proxy
- Reproducible desktop build script and packaging documentation

### Validation
- 191 Python tests passing
- Vite production build passing
- Packaged API and UI return HTTP 200 from the private loopback service
- Constrained live SPY scan completed with one symbol succeeded, zero failed, and three candidates
- Desktop shutdown confirmed to terminate the owned backend process

### Safety
- Backend binds only to a dynamically allocated `127.0.0.1` port
- Electron renderer has Node integration disabled, context isolation enabled, and sandboxing enabled
- Schwab secrets and OAuth tokens are not embedded in desktop artifacts
- Live broker-order submission remains disabled

## [0.9.0] — 2026-08-04

### Added
- React Operator Console
- Command Center Intelligence
- Backtesting workspace
- Recommendation workspace
- Optional recommendation constraints
- Trading profiles
- Recommendation history
- Quote audit
- Recommendation diagnostics
- Recommendation pipeline validation
- FastAPI operator-console endpoints
- Expanded automated test coverage

### Validation
- 185 Python tests passing
- Vite production build passing

### Safety
- Research Mode
- Read-only execution
- Paper and live order submission disabled
