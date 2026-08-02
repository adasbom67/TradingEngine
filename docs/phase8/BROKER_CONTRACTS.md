# Broker Contracts

## Broker protocol

The Schwab adapter should implement a broker-neutral interface similar to:

```python
class TradingBroker(Protocol):
    def get_accounts(self) -> list[BrokerAccount]: ...
    def get_account(self, account_id: str) -> BrokerAccountSnapshot: ...
    def get_orders(self, account_id: str, *, from_time, to_time) -> list[BrokerOrder]: ...
    def get_positions(self, account_id: str) -> list[BrokerPosition]: ...
    def preview_order(self, account_id: str, order: OrderPlan) -> OrderPreview: ...
    def place_order(self, account_id: str, order: OrderPlan) -> BrokerSubmission: ...
    def cancel_order(self, account_id: str, broker_order_id: str) -> BrokerOrder: ...
    def get_order(self, account_id: str, broker_order_id: str) -> BrokerOrder: ...
```

The exact Schwab SDK capability for preview must be verified during Phase 8A. If the SDK/API does not expose a true preview endpoint, `OrderPreview` becomes an internal deterministic validation result and live submission remains disabled until the limitation is documented and accepted.

## Normalized broker models

Broker responses are mapped into internal immutable models:

- `BrokerAccount`
- `BrokerAccountSnapshot`
- `BrokerOrder`
- `BrokerOrderLeg`
- `BrokerFill`
- `BrokerPosition`
- `BrokerSubmission`
- `BrokerError`

## Error taxonomy

- `BrokerAuthenticationError`
- `BrokerConfigurationError`
- `BrokerValidationError`
- `BrokerRateLimitError`
- `BrokerTransientError`
- `BrokerSubmissionError`
- `BrokerUnknownSubmissionState`
- `BrokerReconciliationError`

Only explicitly transient read operations may be retried automatically. Submission retries require reconciliation first.

## Order mapping

A bull put credit spread is represented as one vertical order with two legs:

- short put: `SELL_TO_OPEN`
- long put: `BUY_TO_OPEN`

Exit order:

- short put: `BUY_TO_CLOSE`
- long put: `SELL_TO_CLOSE`

Order mapping validates:

- same underlying
- same expiration
- put contracts
- short strike above long strike
- positive quantity
- supported duration and session
- limit credit/debit sign and rounding
