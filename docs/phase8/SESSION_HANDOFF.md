# Phase 8 Session Handoff

## Current stable baseline

- Version: `v0.9.3`
- Stable branch: `main`
- Verified tests: 157
- Phase 7: complete
- Live submission: not implemented and must remain disabled

## Active objective

Implement **Phase 8A — Broker Readiness and Dry Run**.

## Exact next engineering task

1. switch to `develop`
2. confirm `develop` contains v0.9.3
3. create broker-neutral models and protocol under `app/trading`
4. implement read-only Schwab trading/account adapter
5. implement bull-put `OrderPlan` builder and validator
6. add dry-run CLI commands
7. add fake-broker contract tests
8. run full regression suite
9. update Phase 8 documentation

## Mandatory constraints

- no live submission CLI in Phase 8A
- no automatic retries of order mutations
- broker state is authoritative
- account IDs must be masked in reports and logs
- every future state transition must be auditable
