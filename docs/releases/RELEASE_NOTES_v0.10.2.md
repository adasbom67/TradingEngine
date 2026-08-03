# TradingEngine v0.10.2 — Explicit Live and Paper Account Model

## Changes

- Live Schwab account selection now uses only `SCHWAB_LIVE_ACCOUNT_HASH` from the local `.env`.
- Account hashes are no longer supported in tracked `config/runtime.json`.
- Paper trading remains an independent simulated account backed by `data/paper_account.json`.
- Tracked paper defaults now define initial cash, ledger path, and capital source.
- Multi-account guidance remains masked and does not print complete identifiers.
- Live order submission remains unavailable.

## Local configuration

```dotenv
SCHWAB_LIVE_ACCOUNT_HASH=<full selected Schwab account hash>
```

The `.env` file must remain excluded from Git.
