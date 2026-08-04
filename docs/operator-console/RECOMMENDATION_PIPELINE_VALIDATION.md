# Recommendation Pipeline Validation — Slice 5

This slice instruments the live recommendation path without changing its
qualification rules.

The API and UI now expose normalized contracts, puts, expirations, eligible
puts, spread-pair stages, credit checks, risk checks, candidates built,
evaluated, and ranked. Contract-filter and spread-builder removals are counted
by reason, and the first zero stage is highlighted for each symbol.

No market-data, pricing, scoring, paper-trading, or live-order rule changes.
