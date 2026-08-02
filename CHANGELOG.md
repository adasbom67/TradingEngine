# Changelog

## [0.9.1] - Unreleased

### Added

- Centralized runtime configuration in `config/runtime.json`.
- Runtime configuration validation.
- Structured JSONL logging.
- Append-only operational audit trail.
- Startup and health-check framework.
- `config validate`, `health`, and `version` CLI commands.
- Project status, roadmap, methodology, release, architecture, and design-decision documentation.

## [0.9.0] - 2026-08-02

### Added

- Live Schwab market-data integration.
- Technical indicators and market-regime analysis.
- Bull put spread evaluation and ranking.
- Backtesting, calibration, portfolio testing, and walk-forward validation.
- Automated paper trading and risk controls.
- Watchlists, scheduler, and daily recommendation reports.
- 137 locally verified passing tests.

## [0.9.2] - 2026-08-02

### Added
- Retry policy with bounded exponential backoff.
- Single-instance process lock and graceful shutdown controller.
- Atomic recovery checkpoints.
- Rotating JSONL logging.
- Operational diagnostics and deployment verification commands.

### Changed
- Runtime configuration now includes resilience and log-rotation settings.

## 0.9.3
- Completed Phase 7 production readiness.
- Added centralized configuration service and execution metrics.
- Added installation, upgrade, backup, and deployment workflows.
- Consolidated long-term project documentation under `docs/`.
