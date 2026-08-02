# TradingEngine v0.9.1 Release Notes

## Purpose

This release begins Phase 7 and establishes the operational foundation required before live trading.

## New capabilities

- Central runtime configuration
- Configuration validation
- JSONL application logs
- Append-only audit events
- Health and startup checks
- Version command
- Formal project continuity and release documentation

## Verification commands

```powershell
pytest -q
python main.py version
python main.py config validate
python main.py health
```

## Known limitations

- Health checks validate local readiness but do not yet perform a live Schwab API call.
- Restart orchestration and deployment automation are planned for v0.9.2.
- Live order execution remains disabled.

## Next milestone

v0.9.2 will focus on restart recovery, deployment tooling, operational metrics, and notification adapters.
