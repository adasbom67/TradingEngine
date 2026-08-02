# Phase 8 Operational Runbook

## Before market

1. activate virtual environment
2. confirm branch and version
3. run `python main.py health`
4. run deployment verification
5. run live reconciliation in read-only mode
6. confirm kill-switch state
7. inspect account, positions, and open orders
8. review scheduled market events
9. confirm execution mode

## Before approving an order

- candidate decision is `TRADE`
- account state is synchronized
- no duplicate exposure
- credit and width match the recommendation
- risk and buying power pass
- quote is fresh
- broker validation/preview passes
- expiration and strikes are correct
- quantity is correct
- audit record exists

## After submission

- record broker order ID
- confirm broker acknowledgement
- monitor until terminal or working state
- verify any fills
- reconcile resulting position
- inspect committed risk
- retain audit and diagnostic records

## Emergency procedure

1. activate kill switch
2. stop scheduler or live workflow
3. inspect broker directly
4. cancel open entry orders where appropriate
5. do not assume local cancellation succeeded
6. reconcile positions and orders
7. create diagnostics snapshot
8. preserve logs and recovery checkpoint
9. document operator actions
10. resume only after root cause and reconciliation are complete

## End of day

- reconcile account
- review open orders
- review positions and expiration risk
- record account snapshot
- export audit summary
- verify no unresolved checkpoint
- back up runtime state
