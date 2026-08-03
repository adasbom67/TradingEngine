# TradingEngine v0.10.1

## Phase 8A Account Selection Hardening

- `SCHWAB_LIVE_ACCOUNT_HASH` is now the preferred account-selection mechanism.
- Environment configuration takes precedence over the legacy runtime JSON value.
- Multiple linked accounts produce friendly masked guidance instead of a traceback.
- Full account hashes are never printed by the selection workflow.
- Single-account installations continue to select automatically.
- `config/runtime.json` remains safe to commit with a blank `account_hash`.
- Live submission remains unavailable.
