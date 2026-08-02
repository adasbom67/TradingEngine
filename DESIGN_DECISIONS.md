# Design Decisions

## ADR-001: Begin with bull put credit spreads

A single strategy reduces implementation and validation complexity. Additional strategies will be introduced only after the platform is operationally stable.

## ADR-002: Research and paper trading precede live execution

The system must demonstrate technically correct and operationally reliable behavior before it can submit real orders.

## ADR-003: Reuse one candidate evaluation pipeline

Live scans and paper trading share the same scoring and decision logic to reduce behavioral drift.

## ADR-004: Use walk-forward validation

Walk-forward testing reduces reliance on a single optimized historical period and exposes unstable parameter behavior.

## ADR-005: Preserve modeled-backtest disclaimers

Schwab daily history does not provide historical option chains. Modeled option prices must not be represented as reconstructed fills.

## ADR-006: Keep `main` stable and develop on `develop`

Stable releases remain recoverable while active development can proceed without destabilizing the latest tagged checkpoint.

## ADR-007: Add production readiness before live trading

Structured logging, audit records, health checks, configuration validation, and recovery controls are mandatory prerequisites for live execution.

## ADR-008: Bounded retries only

Transient external failures may be retried with a configured maximum attempt count and capped exponential backoff. Infinite retries are prohibited because they hide outages and can leave workflows stalled indefinitely.

## ADR-009: Atomic local recovery checkpoints

Operational workflows use an atomic JSON checkpoint to record in-progress and completed states. This keeps recovery transparent and inspectable without introducing a database before it is necessary.

## ADR-010: Single-instance protection

Long-running operational workflows support a lock file so that two scheduler or daily-operation processes cannot modify shared paper state concurrently.
