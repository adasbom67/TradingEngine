# TradingEngine Roadmap

## Completed

1. Foundation and project architecture
2. Schwab market-data integration
3. Strategy evaluation and recommendation engine
4. Backtesting and calibration
5. Portfolio and walk-forward research
6. Automated paper trading
7. Daily scheduling, watchlists, and reports

## Active: Phase 7 — Production Readiness

### v0.9.1 — Operational foundation

- Central runtime configuration
- Configuration validation
- Structured logging
- Audit trail
- Health checks
- Startup validation
- Version and release documentation

### v0.9.2 — Recovery and deployment

- Restart-safe workflow orchestration
- State integrity and backup checks
- Windows launch scripts
- Operational metrics and run summaries
- Notification adapters

### v0.9.3 — Live-readiness validation

- Read-only Schwab account reconciliation
- Position comparison and drift detection
- Order-preview models
- Kill-switch design and dry-run controls

## Phase 8 — Controlled Live Trading

- Order preview
- Explicit user approval workflow
- Order submission
- Fill reconciliation
- Live position management
- Emergency kill switch
- Manual override and recovery

## Version 1.0 go-live criteria

- Sustained and reviewed paper-trading history
- Healthy production-readiness checks
- Full auditability
- Restart and recovery validation
- Live workflow tested in dry-run mode
- Explicit capital and risk limits
- Successful end-to-end order preview and reconciliation

## Active checkpoint: v0.9.2

Phase 7 reliability foundations are implemented: rotating logs, bounded retries, process locking, recovery checkpoints, diagnostics, and deployment verification.

### Next task

Wire retry/checkpoint/locking into live daily and paper workflows, perform sustained paper-trading soak tests, then begin Phase 8 with Schwab order preview only. No live order submission is enabled yet.
