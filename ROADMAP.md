# TradingEngine Roadmap

> **Role:** Future-facing milestone sequence.
> **Current implementation:** [docs/SYSTEM_OVERVIEW.md](docs/SYSTEM_OVERVIEW.md)
> **Detailed delivery gates:** [docs/TRADING_ENGINE_COMPLETION_PLAN.md](docs/TRADING_ENGINE_COMPLETION_PLAN.md)

## Active

### 1. Paper lifecycle validation

- Complete remaining exit, adjustment, roll, and journal behavior.
- Conduct an extended real-market paper-trading soak test.
- Measure fill assumptions, slippage, score calibration, and regime behavior.

### 2. Operational hardening

- Exercise token expiry, stale data, partial responses, rate limits, network loss, and restart recovery.
- Complete durable schema migration, backup, and data-freshness handling.
- Extend health and degraded-mode visibility throughout the desktop UI.

## Next

### 3. Read-only broker reconciliation

- Synchronize Schwab accounts, balances, positions, working orders, and buying power.
- Compare broker state with engine state and report drift without changing broker state.

### 4. Dry-run execution

- Build exact broker-neutral multi-leg order plans.
- Enforce quote, session, duplication, risk, buying-power, and portfolio gates.
- Add persistent PAPER, DRY_RUN, and LIVE modes with a safe-default kill switch.

### 5. Manually approved live pilot

- Permit submission only after explicit review and approval.
- Begin with approved ETFs, one contract, one open position, no 0DTE, and no unattended execution.
- Add idempotency, fill reconciliation, cancellation, recovery, and complete auditability.

## Later

- Assisted adjustments and rolling.
- Portfolio-aware sizing and correlation limits.
- Bear call spreads, iron condors, and regime-aware strategy allocation.
- Carefully bounded automation only after substantial controlled-live evidence.

Live trading remains unavailable until the applicable validation and safety gates are complete.
