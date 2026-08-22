# Trading Engine Completion Plan

Last reviewed: 2026-08-08

> **Role:** Detailed delivery stages and live-trading gates.
> **Canonical current implementation:** [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)
> If the current-state language here becomes stale, the system overview and code take precedence.

## Product objective

Build a safety-first options trading engine that takes a SPY bull put credit spread through the complete lifecycle:

1. Live market scan.
2. Explainable TRADE, WATCH, or PASS recommendation.
3. Human review and paper execution.
4. Live marking and position management.
5. Exit, adjustment, or roll recommendation.
6. Complete journal and performance analysis.
7. Dry-run broker validation.
8. Manually approved live execution.
9. Carefully limited automation after a successful controlled-live history.

## Current state

The engine is a functional research, recommendation, and paper-trading application for bull put credit spreads. It has live Schwab market data, constrained and explainable recommendations, backtesting and walk-forward research, persistent paper trading, operational safety foundations, and a standalone Windows desktop application.

Live order submission is intentionally unavailable. The remaining work is to complete and validate the paper lifecycle, harden all Schwab-facing operations, then introduce broker execution through gated dry-run and manual-approval stages.

## Delivery milestones

### 1. Paper Trading Complete and Soak Ready

- Permit deliberate WATCH simulations with an explicit experimental label.
- Block PASS recommendations in both the UI and backend.
- Preserve entry decision, score, thesis, constraints, quote quality, pricing method, market regime, and scan reference.
- Refresh open positions from live Schwab option quotes.
- Complete closing, expiration, exit-reason, and realized-P/L records.
- Provide adjustment and roll proposals without automatic execution.
- Preserve all positions and history across application restarts.

Completion test: scan, select, paper enter, restart, live mark, receive an exit recommendation, close, and review a complete journal record without losing context.

### 2. Extended paper-trading soak test

- Operate through several weeks of real market sessions.
- Record recommendations, rejections, entries, marks, exits, and data failures.
- Compare estimated and realized slippage.
- Evaluate results by volatility and market regime.
- Validate profit target, stop loss, expiration, and assignment-risk behavior.
- Determine whether recommendation scores predict outcomes.

### 3. Operational hardening

- Apply retries, locks, and recovery checkpoints to every live scan and position update.
- Test expired authentication, stale quotes, partial responses, rate limits, network loss, and crashes.
- Add durable schema migration and backup handling.
- Add secure desktop credential and account settings.
- Display health, data freshness, and degraded-mode warnings in the desktop UI.
- Reconcile documentation and release versions.
- Add Windows application signing and a controlled update path.

### 4. Read-only broker reconciliation and dry-run execution

- Read Schwab accounts, positions, working orders, and buying power.
- Add broker-neutral account, order, fill, and position models.
- Build and validate an exact multi-leg order plan.
- Enforce quote freshness, duplicate exposure, risk, buying-power, and portfolio gates.
- Display an order preview without making submission reachable.
- Reconcile engine state against Schwab and report drift.
- Add persistent PAPER, DRY_RUN, and LIVE modes plus a safe-default kill switch.

### 5. Manually approved live submission

- Persist a trade intent before submission.
- Require explicit approval for every order.
- Prevent duplicate submissions with idempotency controls.
- Submit, monitor, cancel, and reconcile multi-leg orders.
- Handle rejection, partial fills, timeouts, and unknown submission outcomes safely.
- Audit every decision, approval, request, response, fill, and state transition.

### 6. Controlled live pilot

- SPY bull put spreads only.
- One contract and one open position.
- No 0DTE and no unattended submission.
- Strict market-time and event restrictions.
- Manual approval for entries, adjustments, and exits.
- Daily Schwab reconciliation and immediate persistent kill-switch access.

### 7. Post-v1 expansion

- Assisted rolling and adjustments.
- Approval-based scheduled entries.
- Portfolio capital and correlation controls.
- Bear call spreads, then iron condors.
- Regime-aware strategy selection and multi-strategy allocation.
- Unattended execution only after substantial controlled-live evidence.

## Mandatory live-trading gates

Before a live order can be approved, all of the following must pass: candidate decision, quote freshness, allowed market session, valid configuration, current account synchronization, duplicate-exposure check, per-trade risk, total risk, buying power, daily-loss limit, maximum positions, inactive kill switch, accepted preview, and explicit approval.

## Initial live limits

The first live pilot remains restricted to approved ETFs, one position, one contract, no 0DTE, configured market-time exclusions, and manual approval. Live functionality must remain disabled by default.

## Current working milestone

Milestone 1: Paper Trading Complete and Soak Ready.
