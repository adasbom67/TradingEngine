# Live Trading Architecture

## New bounded contexts

### 1. Trading domain — `app/trading`

Owns broker-independent intent and lifecycle models.

Suggested modules:

```text
app/trading/
    models.py
    order_plan.py
    state_machine.py
    service.py
    reconciliation.py
    approvals.py
```

Core objects:

- `TradeIntent`
- `OrderLeg`
- `OrderPlan`
- `OrderRecord`
- `FillRecord`
- `LivePosition`
- `ReconciliationResult`
- `ApprovalRecord`

### 2. Broker execution — `app/brokers/schwab_trading`

Contains the Schwab-specific adapter only.

```text
app/brokers/schwab_trading/
    client.py
    mapper.py
    orders.py
    accounts.py
    errors.py
```

The rest of the application must depend on a broker protocol, not directly on Schwab SDK order objects.

### 3. Live risk — `app/risk/live_risk.py`

Extends existing portfolio constraints with:

- broker buying power
- live account value
- daily realized and unrealized loss
- duplicate and overlapping exposure
- order-notional and spread-risk limits
- stale quote rejection
- market-hours policy
- pending-order exposure
- kill-switch state

### 4. Persistence — `app/trading/store.py`

Initial implementation may use atomic JSON files, consistent with the current recovery architecture. The store must preserve:

- intents
- approvals
- submitted orders
- broker order IDs
- fills
- reconciled positions
- state transitions
- last synchronization marker

A database is deferred until scale or concurrency requires it.

### 5. Operations integration

Existing production-readiness components remain authoritative for:

- structured logs
- audit logs
- retry policy
- instance lock
- recovery checkpoints
- diagnostics
- startup validation
- configuration service

## Dependency direction

```text
CLI / Scheduler
      ↓
Application Services
      ↓
Trading Domain + Risk Domain
      ↓
Broker Protocol
      ↓
Schwab Adapter
```

Broker SDK types must not leak into strategy, risk, or reporting modules.

## Command/query separation

Commands mutate state:

- create intent
- approve intent
- preview order
- submit order
- cancel order
- reconcile account
- activate/deactivate kill switch

Queries do not mutate state:

- show intent
- show orders
- show positions
- show reconciliation status
- show risk status
