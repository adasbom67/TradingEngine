# Master Chat and Branch Handoff

## Source

This file preserves the project-relevant context from the ChatGPT tasks **“Options trading engine v1”** (the pinned, authoritative master task) and **“Branch · Options trading engine v1”** so future development can continue from this repository without depending on either task being open.

When task history and this file disagree, use this priority order:

1. Current repository code, tests, and Git state.
2. The newest messages in the pinned master task.
3. This handoff document and repository status documents.
4. The older branch task.

## Product objective

Build a safety-first options trading system that finds, explains, ranks, and manages high-quality bull put credit spreads. The initial strategy and primary reference symbol are SPY bull put spreads. The system should prove one strategy through automated tests, historical research, and sustained paper trading before controlled live trading is considered.

## Working principles agreed in the task

- Trade quality and safety take priority over feature speed.
- Every recommendation must be explainable with trend, liquidity, credit, probability, and risk evidence.
- Development should proceed autonomously; request user intervention only when credentials, broker authorization, a business/risk decision, or an external action is genuinely required.
- Keep user-facing communication concise and focused. Provide step-by-step guidance when the user must perform a technical action.
- Git is the source of truth. Preserve small, testable changes and keep the automated suite passing.
- Never expose `.env`, OAuth tokens, local ledgers, logs, or downloaded market data through Git.
- Live order submission must remain disabled until paper-trading, operational-readiness, approval, reconciliation, and kill-switch criteria are satisfied.

## Early implementation history

The branch task established the original engine foundation and then advanced through:

1. Domain models for option contracts, option chains, price snapshots, trend analysis, bull put spreads, and trade candidates.
2. `PutSpreadConfig` with validation and explicit strategy constraints.
3. A modular evaluation framework and trend evaluator.
4. Option filtering, bull put spread construction, spread evaluation, candidate ranking, and the end-to-end candidate pipeline.
5. Schwab OAuth and live market-data integration.
6. Schwab option-chain normalization into internal models.
7. Live SPY candidate scanning.
8. Daily price history, 20-day and 200-day SMA calculation, automatic market snapshots, and readable live scan output.

The task verified live, non-delayed Schwab SPY option-chain data and a passing suite at the time. Subsequent repository work significantly expanded the engine beyond that checkpoint.

## Current repository state supersedes the old checkpoint

Use `PROJECT_STATUS.md`, `ROADMAP.md`, `ARCHITECTURE.md`, and the current code/tests as the authoritative present state. At the time of this handoff:

- Stable release: v0.9.0 on `main`.
- Active development: v0.9.2 on `develop`.
- Current phase: production readiness.
- The repository includes live Schwab analysis, recommendation ranking, backtesting and optimization, portfolio/walk-forward research, automated paper trading, watchlists, scheduling, reports, operational health checks, logging, audit, retries, locking, checkpoints, diagnostics, and an operator console.
- Live order submission is not implemented or enabled.
- The complete local test suite passes: 189 tests.

## Pinned master-task checkpoint

The pinned master task is newer than the branch task. Its latest validated baseline is:

- Schwab OAuth and live quotes operational after converting the verified token into `schwab-py` 1.5.1's wrapped token format.
- Four-symbol recommendation scans complete through the Operator Console.
- A representative SPY scan processed 1,478 puts, found 57 eligible puts, built and ranked 27 candidates.
- The full Python suite passed with 189 tests and two dependency warnings.
- The Operator Console production build passed.
- Paper Trading API and workspace are present, simulation-only, and explicitly incapable of creating broker orders.
- The Constraint Explorer backend and component were installed, but the master-task UI check showed that the explorer had not actually been inserted into the Recommendations page at that time.

The current working tree contains uncommitted Constraint Explorer changes. Preserve and review them before further edits:

- modified recommendation API, diagnostics, filtering, Recommendations page, and frontend types
- new recommendation constraint component(s)
- new `test_constraint_explorer.py`
- local Schwab diagnostic/conversion scripts

## Proposed but not yet integrated master-task slice

The newest master-task deliverable is a proposed Paper Trading Slice 3 package. It was prepared, but the task stopped after asking the user to extract the ZIP. Treat it as **pending**, not installed.

The proposed behavior is:

- `TRADE` recommendations remain eligible for paper execution.
- `WATCH` recommendations may be deliberately simulated in paper while retaining their original `WATCH` classification.
- `PASS` recommendations remain blocked.
- Open paper positions receive live Schwab mark-to-market updates.
- Paper positions/journal entries preserve the entry decision, score, reasons, and thesis metadata.
- Closing a position archives realized P/L and the exit reason.
- No live Schwab order creation or submission is added.

Repository inspection confirms the pending slice is absent: current automation opens positions only for `TRADE`, `PaperPosition` has no entry decision/score/thesis fields, and the Paper Trading API supports manual mark/close but no live mark-to-market refresh endpoint.

## Canonical local location

All future development should occur in:

`C:\Users\Anil Das\Documents\Programming Projects\Options Trading Engine`

The former working copy at `C:\Users\Anil Das\TradingEngine` is retained as a backup and should not be used for new changes.

## Immediate engineering direction

Continue from the current `develop` branch and existing working-tree changes. Preserve those uncommitted changes. The master-task-aligned next sequence is:

1. Review and finish or intentionally remove the partially integrated Constraint Explorer work.
2. Implement the pending Paper Trading Slice 3 directly in this repository, with tests: controlled WATCH simulation, PASS blocking, live Schwab marks, preserved entry metadata, close/history/journal behavior, and simulation-only safeguards.
3. Integrate retry, locking, and recovery checkpoints into Schwab-facing daily operations and paper position management.
4. Run an extended paper-trading soak test and review operational results.
5. Begin controlled live-readiness work with read-only account reconciliation and order preview/validation.
6. Do not add order submission until the explicit live-readiness gates are met.
