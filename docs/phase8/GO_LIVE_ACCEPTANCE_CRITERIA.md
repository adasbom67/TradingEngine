# Go-Live Acceptance Criteria

Live trading remains prohibited until every mandatory item passes.

## Engineering

- full automated suite passes
- broker contract tests pass
- no secrets tracked in Git
- live mode defaults off
- kill switch tested
- submission idempotency tested
- recovery from simulated network loss tested
- partial-fill path tested
- reconciliation mismatch tested
- audit trail verified

## Broker and account

- selected Schwab account verified
- option-spread permissions verified
- account identifiers masked in output
- buying power verified
- order reads verified
- position reads verified
- cancellation verified in a safe environment where possible

## Operational

- startup reconciliation passes
- health checks pass
- diagnostics archived
- single-instance lock verified
- runtime backup completed
- rollback instructions tested
- manual intervention procedure understood
- emergency contact and broker access available

## Trading policy

- approved symbol universe documented
- maximum one contract
- maximum one live position initially
- risk limits lower than paper limits
- approved entry window defined
- prohibited dates/events policy defined
- every order manually approved
- first pilot trade reviewed before submission

## Pilot success

Before unattended automation:

- minimum controlled pilot period completed
- no unresolved reconciliation differences
- order/fill lifecycle matches broker records
- exits handled correctly
- audit trail complete
- paper/live slippage comparison reviewed
