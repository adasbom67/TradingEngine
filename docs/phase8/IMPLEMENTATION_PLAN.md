# Phase 8 Implementation Plan

## 8A — Broker Readiness and Dry Run

Target release: `v0.10.0`

Deliverables:

- broker-neutral execution protocol
- normalized account, order, fill, and position models
- Schwab account and order read adapter
- order-plan builder for bull put verticals
- deterministic order validator
- dry-run execution mode
- account-selection configuration
- reconciliation read-only report
- test doubles and contract tests
- CLI:
  - `trade account`
  - `trade positions`
  - `trade orders`
  - `trade plan`
  - `trade validate`
  - `trade reconcile`

Gate: no order submission method is reachable from CLI.

## 8B — Submission and Monitoring

Target release: `v0.11.0`

Deliverables:

- persistent trade-intent journal
- manual approval records
- live submission adapter
- order monitoring
- cancellation
- partial-fill detection
- submission-unknown recovery
- live-disabled-by-default controls
- CLI:
  - `trade approve`
  - `trade submit --confirm`
  - `trade order`
  - `trade cancel`

Gate: all submissions require explicit operator confirmation.

## 8C — Live Portfolio Reconciliation

Target release: `v0.12.0`

Deliverables:

- live position store
- fill-to-position aggregation
- buying-power and account-value synchronization
- live committed-risk calculation
- entry/exit reconciliation
- live dashboard and daily snapshots
- paper/live behavioral comparison

Gate: no unattended live workflow.

## 8D — Safety Controls and Controlled Go-Live

Target release: `v1.0.0-rc1`

Deliverables:

- persistent kill switch
- live health checks
- trading-hours policy
- stale-quote checks
- daily loss enforcement
- controlled scheduler integration
- operator runbook
- disaster-recovery drill
- controlled one-contract pilot

Gate: go-live acceptance checklist signed off.

## Development sequence

For every increment:

1. branch from stable `develop`
2. implement broker-independent domain first
3. add Schwab adapter behind protocol
4. use fake broker tests
5. run full regression suite
6. perform dry-run against live account reads
7. update design docs and ADRs
8. commit to `develop`
9. promote only after local verification
