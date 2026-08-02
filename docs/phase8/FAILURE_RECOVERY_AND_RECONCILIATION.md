# Failure Recovery and Reconciliation

## Broker truth principle

Schwab is the source of truth for live orders, fills, positions, and account balances. Local persistence is an operational journal and recovery aid.

## Startup sequence in live-capable modes

1. acquire instance lock
2. validate runtime configuration
3. validate credentials and selected account
4. read recovery checkpoint
5. load local trading journal
6. fetch broker account snapshot
7. fetch recent and open orders
8. fetch broker positions
9. reconcile local and broker state
10. activate kill switch on material mismatch
11. permit new intents only after successful reconciliation

## Submission uncertainty

When a network failure occurs after submission begins:

1. set state to `SUBMISSION_UNKNOWN`
2. save recovery checkpoint
3. do not resubmit
4. query broker orders using account, time window, contracts, quantity, and price
5. match one unique broker order
6. attach broker order ID and continue monitoring
7. if no unique match exists, require manual resolution

## Reconciliation categories

- `MATCHED`
- `LOCAL_MISSING`
- `BROKER_MISSING`
- `QUANTITY_MISMATCH`
- `PRICE_MISMATCH`
- `STATE_MISMATCH`
- `UNMATCHED_ORDER`
- `UNMATCHED_POSITION`

Material discrepancies activate the kill switch.

## Partial-fill response

A partially filled multi-leg order is high risk. The engine must:

- surface an immediate alert
- stop new entries
- continue polling
- avoid automatic compensating orders in the initial release
- require manual intervention if the broker does not complete or cancel the remaining quantity

## Recovery checkpoints

Checkpoints should cover:

- account reconciliation
- submission
- cancellation
- exit management
- daily live workflow

A completed and reconciled operation clears its checkpoint.
