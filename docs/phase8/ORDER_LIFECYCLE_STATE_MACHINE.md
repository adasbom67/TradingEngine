# Order Lifecycle State Machine

## Trade intent states

```text
CREATED
  ├─→ REJECTED
  └─→ RISK_APPROVED
          ├─→ APPROVAL_REQUIRED
          │       ├─→ REJECTED
          │       └─→ APPROVED
          └─→ APPROVED
```

## Order states

```text
PLANNED
  ↓
PREVIEWED
  ↓
READY_TO_SUBMIT
  ↓
SUBMITTING
  ├─→ SUBMISSION_UNKNOWN
  ├─→ REJECTED
  └─→ SUBMITTED
          ├─→ WORKING
          ├─→ PARTIALLY_FILLED
          ├─→ FILLED
          ├─→ CANCEL_PENDING
          ├─→ CANCELLED
          ├─→ EXPIRED
          └─→ REJECTED
```

## Position states

```text
PENDING_ENTRY
  ↓
OPEN
  ├─→ EXIT_PENDING
  │       ├─→ OPEN
  │       └─→ CLOSED
  ├─→ ASSIGNMENT_RISK
  ├─→ RECONCILIATION_REQUIRED
  └─→ CLOSED
```

## Transition rules

- Only valid state transitions are accepted.
- Every transition stores UTC timestamp, actor, reason, and correlation ID.
- `SUBMISSION_UNKNOWN` blocks resubmission until broker reconciliation completes.
- A partially filled vertical is treated as an operational exception requiring immediate monitoring.
- A position is considered open only after broker-confirmed fills.
- Local cancellation does not mean broker cancellation; confirmation is required.
- No retry may blindly repeat an order submission.

## Idempotency

Every order submission is assigned:

- local order ID
- trade-intent ID
- idempotency key
- correlation ID

Before submission, the service checks both local history and broker open/recent orders for an equivalent order.
