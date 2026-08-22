# TradingEngine Current Checkpoint

> **Last reviewed:** 2026-08-20
> **Canonical system description:** [docs/SYSTEM_OVERVIEW.md](docs/SYSTEM_OVERVIEW.md)

## Release and validation

- Active application version: `v0.9.3` release candidate.
- Operating mode: research and paper simulation.
- Live broker order submission: unavailable and disabled.
- Latest validated source baseline: 241 Python tests passing and TypeScript/Vite production build passing.
- Windows installer and portable artifacts were rebuilt successfully on 2026-08-17.

## Current working milestone

Complete and soak-test the paper-trading lifecycle, then harden all Schwab-facing workflows before implementing read-only broker reconciliation and dry-run order preview.

## Recently completed

- Standalone Electron desktop application and packaged Python backend.
- In-app Schwab connection status and reauthorization.
- Fixed-width $3/$5/$10 bull put hedge selection without a long-leg delta requirement.
- Bear call credit-spread recommendations with $2/$3/$5 higher-strike protective calls.
- Session-aware recommendation liquidity: provisional off-hours scans, short-leg regular-hours volume enforcement, reduced protective-leg OI, no protective-leg volume gate, and midpoint-relative quote checks.
- Persistent recommendation profiles, history, diagnostics, and quote audit.
- Persistent paper entry, live marking, closing, observations, and account snapshots.
- Experimental Critical Events scanner, 15-minute market-hours monitor, and visual/audio alerts.
- Unified Recommendations workspace with separate Credit Spreads and Long Straddle strategy sub-tabs.
- Long Straddle scoring based on displayed asks plus commissions, same-time intraday signals, executable quote gates, and contract-specific two-scan confirmation.
- Long Straddle historical validation with daily proxy scoring, modeled forward outcomes, chronological holdout results, and bounded prospective option-quote collection.

## Immediate priorities

1. Run the paper lifecycle through sustained real-market sessions.
2. Measure outcomes, slippage, calibration, and failure behavior.
3. Complete resilience, migration, backup, and data-freshness handling.
4. Add read-only Schwab account/position reconciliation.
5. Add exact multi-leg dry-run order previews and safety gates.

Detailed sequencing is maintained in [docs/TRADING_ENGINE_COMPLETION_PLAN.md](docs/TRADING_ENGINE_COMPLETION_PLAN.md). Future direction is summarized in [ROADMAP.md](ROADMAP.md).
