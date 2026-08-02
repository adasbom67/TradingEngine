# ADR-013: Never Blindly Retry an Order Submission

## Status

Accepted for Phase 8 design.

## Decision

If submission outcome is uncertain, the order enters `SUBMISSION_UNKNOWN`. The engine reconciles with the broker before any further submission attempt.

## Consequences

- Duplicate orders are less likely.
- Recovery is slower but safer.
- Broker-order matching and operator resolution are mandatory capabilities.
