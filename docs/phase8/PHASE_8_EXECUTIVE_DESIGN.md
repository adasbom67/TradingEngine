# Phase 8 Executive Design

## Objective

Extend TradingEngine from a production-ready research and paper-trading platform into a controlled live-trading system for bull put credit spreads.

## Non-negotiable principles

1. Live execution is disabled by default.
2. The system must support `paper`, `dry_run`, and `live` modes.
3. A candidate recommendation is not an order authorization.
4. Risk approval, order validation, and operator approval are separate gates.
5. Every broker mutation receives an idempotency key.
6. Local state never overrides broker truth.
7. After uncertainty or restart, reconciliation occurs before new submissions.
8. Automated exits use the same safety gates as entries.
9. The kill switch blocks new risk immediately.
10. All decisions and broker responses are auditable.

## Existing foundation reused

Phase 8 builds on:

- Schwab authentication and market-data client
- candidate evaluation and ranking
- account-level portfolio constraints
- paper position lifecycle
- structured logging and audit trail
- runtime configuration
- bounded retry policies
- single-instance protection
- atomic recovery checkpoints
- health, diagnostics, installation, and verification tooling

## Target operating model

```text
Market Data
    ↓
Candidate Evaluation
    ↓
Trade Intent
    ↓
Risk Approval
    ↓
Order Plan
    ↓
Broker Preview / Validation
    ↓
Operator Approval or Policy Approval
    ↓
Order Submission
    ↓
Order Monitoring
    ↓
Fill Reconciliation
    ↓
Live Position
    ↓
Exit Intent and Order Lifecycle
```

## Explicitly out of scope for initial live release

- uncovered option selling
- multi-account routing
- complex allocation algorithms
- high-frequency execution
- intraday market-making
- automatic strategy expansion beyond bull put spreads
- broker-independent smart order routing
