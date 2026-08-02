# Risk and Safety Model

## Gate sequence

A live entry must pass all gates:

1. candidate is `TRADE`
2. quotes are fresh
3. market session is allowed
4. strategy configuration is valid
5. account synchronization is current
6. no duplicate live or pending symbol exposure
7. per-trade risk limit passes
8. total committed risk limit passes
9. buying-power limit passes
10. daily-loss limit passes
11. maximum positions limit passes
12. kill switch is inactive
13. order preview is accepted
14. required approval is present

## Three execution modes

### `paper`

No broker trading endpoints may be called.

### `dry_run`

Broker account queries and order construction are permitted. The system may preview or validate where supported, but submission is prohibited.

### `live`

Submission is permitted only when all live controls are enabled and verified.

## Dual-control activation

Moving to live mode requires two separate configuration values:

```json
{
  "environment": "live",
  "trading": {
    "live_submission_enabled": true
  }
}
```

A runtime CLI acknowledgement is also required for manual submission.

## Kill switch

The kill switch:

- is persistent
- defaults to active after invalid recovery state
- prevents all new entries
- may allow risk-reducing exits
- records actor, timestamp, and reason
- requires explicit reset

## Quote safety

Reject an order plan when:

- quote timestamp exceeds configured age
- bid/ask is missing or crossed
- spread exceeds configured limit
- computed credit differs materially from preview
- underlying or contract data is inconsistent
- option multiplier is unexpected

## Initial live limits

First controlled deployment should use stricter limits than paper mode:

- one open live position
- one contract
- approved ETF universe only
- no same-day expiration
- no entry during first or last configured market minutes
- manual approval for every order
- no unattended live submission
