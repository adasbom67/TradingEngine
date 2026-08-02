# Phase 8 Architecture and Design Sprint

## Purpose

This package defines the architecture for adding safe live trading to TradingEngine after the verified v0.9.3 production-readiness release.

It is a design deliverable. It does **not** enable live order submission.

## Deployment

Copy the package contents into the TradingEngine repository while working on the `develop` branch. The files are additive and belong under `docs/`.

## Required reading order

1. `docs/phase8/PHASE_8_EXECUTIVE_DESIGN.md`
2. `docs/phase8/LIVE_TRADING_ARCHITECTURE.md`
3. `docs/phase8/ORDER_LIFECYCLE_STATE_MACHINE.md`
4. `docs/phase8/RISK_AND_SAFETY_MODEL.md`
5. `docs/phase8/BROKER_CONTRACTS.md`
6. `docs/phase8/FAILURE_RECOVERY_AND_RECONCILIATION.md`
7. `docs/phase8/IMPLEMENTATION_PLAN.md`
8. `docs/phase8/GO_LIVE_ACCEPTANCE_CRITERIA.md`
9. `docs/phase8/OPERATIONAL_RUNBOOK.md`

## Result of the sprint

Phase 8 will be implemented in four gated increments:

- **8A — Broker Readiness and Dry Run**
- **8B — Order Submission and Monitoring**
- **8C — Live Portfolio Reconciliation**
- **8D — Safety Controls and Controlled Go-Live**

No increment may place a real order until its preceding gates pass.
