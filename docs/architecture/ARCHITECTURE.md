# TradingEngine Architecture

## Architectural style

TradingEngine uses a layered, modular architecture. Domain logic is separated from broker integrations, operational workflows, persistence, and presentation.

## Major layers

- `app/brokers`: Schwab authentication and market data.
- `app/indicators`: technical indicators and market analysis.
- `app/strategies`: bull put spread construction.
- `app/evaluation`: scoring, probability estimates, decisions, and ranking.
- `app/scanners`: live candidate orchestration.
- `app/backtesting`: historical simulation, optimization, portfolio, and walk-forward research.
- `app/paper`: persistent paper ledger, automation, management, and exports.
- `app/daily`: multi-symbol daily recommendation workflow.
- `app/watchlists`: named symbol universes.
- `app/scheduling`: weekday job execution and persistent scheduler state.
- `app/operations`: runtime configuration, logging, audit, health, and startup validation.
- `app/reports`: human-readable and exported outputs.

## Primary live-analysis flow

Schwab market data → market analysis → candidate scanner → strategy builder → evaluators → decision and ranking → report or paper workflow.

## Research flow

Historical equity bars → indicator state → modeled spread pricing → trade simulator → portfolio aggregation → optimization and walk-forward reports.

## Operational flow

Runtime configuration → startup validation → health checks → structured logs and audit trail → scheduled daily workflow.

## Architectural decisions

- The same evaluation pipeline is reused across scanning and paper trading.
- Backtests are explicitly labeled as modeled estimates.
- Paper state is persisted locally and excluded from Git.
- Live order execution is separated into a future phase.
- Operational configuration and health checks are isolated from strategy logic.
