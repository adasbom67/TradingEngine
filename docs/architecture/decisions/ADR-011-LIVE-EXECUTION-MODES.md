# ADR-011: Separate Paper, Dry-Run, and Live Execution Modes

## Status

Accepted for Phase 8 design.

## Decision

TradingEngine will expose three explicit execution modes: `paper`, `dry_run`, and `live`.

`paper` cannot call broker mutation endpoints. `dry_run` may read broker data and build or validate orders but cannot submit. `live` requires configuration enablement, safety checks, and explicit approval.

## Consequences

- Accidental live submission is harder.
- Code paths can be exercised before risk is introduced.
- Tests can assert that broker mutations are unreachable outside live mode.
