# ADR-012: Broker State Is Authoritative

## Status

Accepted for Phase 8 design.

## Decision

For live trading, broker orders, fills, positions, account balances, and buying power are authoritative. Local state is reconciled against broker state at startup and after material operations.

## Consequences

- Restart recovery is deterministic.
- Local corruption cannot silently create a false portfolio.
- Material mismatches stop new trading and activate the kill switch.
