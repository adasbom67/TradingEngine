from __future__ import annotations

from dataclasses import replace
from collections import Counter
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.brokers.schwab_auth import create_schwab_client
from app.brokers.schwab_market_data import SchwabMarketDataClient
from app.config.strategy_config import DEFAULT_STRATEGIES
from app.evaluation.default_pipeline import create_default_candidate_pipeline
from app.indicators.market_analysis import MarketAnalysisBuilder
from app.scanners.live_candidate_scanner import LiveCandidateScanner


class RecommendationConstraints(BaseModel):
    # Structure
    minimum_dte: int | None = Field(default=None, ge=0, le=365)
    maximum_dte: int | None = Field(default=None, ge=0, le=365)
    allowed_spread_widths: list[float] | None = None
    maximum_results_per_symbol: int | None = Field(default=None, ge=1, le=100)

    # Credit and return
    minimum_credit_per_contract: float | None = Field(default=None, ge=0)
    minimum_credit_percent_of_width: float | None = Field(default=None, ge=0, le=1)
    minimum_return_on_risk: float | None = Field(default=None, ge=0)
    minimum_probability_of_profit: float | None = Field(default=None, ge=0, le=1)
    minimum_expected_value: float | None = None
    minimum_managed_expected_value: float | None = None

    # Greeks
    minimum_short_delta: float | None = Field(default=None, ge=0, le=1)
    maximum_short_delta: float | None = Field(default=None, ge=0, le=1)
    maximum_absolute_net_delta: float | None = Field(default=None, ge=0, le=2)

    # Risk and liquidity
    maximum_loss_per_contract: float | None = Field(default=None, gt=0)
    minimum_open_interest: int | None = Field(default=None, ge=0)
    minimum_volume: int | None = Field(default=None, ge=0)
    maximum_bid_ask_spread: float | None = Field(default=None, ge=0)

    # Trend and decision quality
    require_20_sma_above_200_sma: bool | None = None
    require_price_above_200_sma: bool | None = None
    price_vs_20_sma: Literal["ANY", "ABOVE", "BELOW"] = "ANY"
    minimum_score: float | None = Field(default=None, ge=0, le=100)
    include_decisions: list[Literal["TRADE", "WATCH", "PASS"]] | None = None
    exclude_candidates_with_warnings: bool = False
    require_positive_managed_expected_value: bool = False

    # Quote and pricing controls
    pricing_method: Literal["SCORING", "NATURAL", "MIDPOINT", "CONSERVATIVE"] = "SCORING"

    @field_validator("allowed_spread_widths")
    @classmethod
    def validate_widths(cls, values: list[float] | None) -> list[float] | None:
        if values is None:
            return None
        normalized = sorted({float(value) for value in values})
        if not normalized or any(value <= 0 for value in normalized):
            raise ValueError("Allowed spread widths must contain positive values.")
        return normalized

    @model_validator(mode="after")
    def validate_ranges(self) -> "RecommendationConstraints":
        if (
            self.minimum_dte is not None
            and self.maximum_dte is not None
            and self.maximum_dte < self.minimum_dte
        ):
            raise ValueError("Maximum DTE must be greater than or equal to minimum DTE.")
        if (
            self.minimum_short_delta is not None
            and self.maximum_short_delta is not None
            and self.maximum_short_delta < self.minimum_short_delta
        ):
            raise ValueError(
                "Maximum short Delta must be greater than or equal to minimum short Delta."
            )
        return self


class RecommendationRequest(BaseModel):
    symbols: list[str] = Field(min_length=1, max_length=20)
    constraints: RecommendationConstraints = Field(default_factory=RecommendationConstraints)

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            symbol = value.strip().upper()
            if symbol and symbol not in normalized:
                normalized.append(symbol)
        if not normalized:
            raise ValueError("At least one valid symbol is required.")
        return normalized


def _quote_payload(short_put: Any, long_put: Any, scoring_credit: float) -> dict[str, Any]:
    short_midpoint = round((short_put.bid + short_put.ask) / 2, 2)
    long_midpoint = round((long_put.bid + long_put.ask) / 2, 2)
    natural_credit = round(max(short_put.bid - long_put.ask, 0.0), 2)
    midpoint_credit = round(max(short_midpoint - long_midpoint, 0.0), 2)
    scoring_credit = round(scoring_credit, 2)

    scoring_vs_natural = round(scoring_credit - natural_credit, 2)
    scoring_vs_midpoint = round(scoring_credit - midpoint_credit, 2)
    material_threshold = round(max(0.05, abs(midpoint_credit) * 0.10), 2)
    audit_status = (
        "REVIEW"
        if abs(scoring_vs_midpoint) > material_threshold
        else "ALIGNED"
    )

    return {
        "short_bid": short_put.bid,
        "short_ask": short_put.ask,
        "short_midpoint": short_midpoint,
        "short_volume": short_put.volume,
        "short_open_interest": short_put.open_interest,
        "long_bid": long_put.bid,
        "long_ask": long_put.ask,
        "long_midpoint": long_midpoint,
        "long_volume": long_put.volume,
        "long_open_interest": long_put.open_interest,
        "natural_credit": natural_credit,
        "midpoint_credit": midpoint_credit,
        "conservative_credit": natural_credit,
        "scoring_credit": scoring_credit,
        "quote_timestamp": None,
        "quote_timestamp_status": "NOT_PROVIDED_BY_NORMALIZED_CONTRACT",
        "scoring_vs_natural": scoring_vs_natural,
        "scoring_vs_midpoint": scoring_vs_midpoint,
        "material_difference_threshold": material_threshold,
        "audit_status": audit_status,
        "audit_message": (
            "Scoring credit differs materially from Schwab-derived natural or midpoint credit."
            if audit_status == "REVIEW"
            else "Scoring credit is reasonably aligned with the derived quote references."
        ),
    }


def _candidate_payload(symbol: str, candidate: Any) -> dict[str, Any]:
    spread = candidate.spread
    short_put = spread.short_put
    long_put = spread.long_put

    short_delta = short_put.delta
    long_delta = long_put.delta
    net_position_delta = None
    if short_delta is not None and long_delta is not None:
        net_position_delta = (-short_delta) + long_delta

    width = abs(short_put.strike - long_put.strike)
    quote = _quote_payload(short_put, long_put, spread.credit)

    return {
        "symbol": symbol,
        "rank": candidate.rank,
        "decision": candidate.decision,
        "score": candidate.score,
        "expiration": short_put.expiration_date.isoformat(),
        "dte": short_put.days_to_expiration,
        "short_strike": short_put.strike,
        "long_strike": long_put.strike,
        "spread_width": width,
        "short_delta": short_delta,
        "long_delta": long_delta,
        "net_position_delta": net_position_delta,
        "credit": spread.credit,
        "maximum_profit": spread.max_profit,
        "maximum_risk": spread.max_loss,
        "breakeven": spread.breakeven,
        "return_on_risk": candidate.return_on_risk or spread.return_on_risk,
        "probability_of_profit": candidate.probability_of_profit,
        "expected_value": candidate.expected_value,
        "managed_expected_value": candidate.managed_expected_value,
        "market_regime": candidate.market_regime,
        "decision_reasons": candidate.decision_reasons,
        "reasons": candidate.reasons,
        "warnings": candidate.warnings,
        "score_breakdown": candidate.score_breakdown,
        "quote": quote,
    }


def _selected_credit(candidate: dict[str, Any], method: str) -> float:
    quote = candidate["quote"]
    return {
        "SCORING": quote["scoring_credit"],
        "NATURAL": quote["natural_credit"],
        "MIDPOINT": quote["midpoint_credit"],
        "CONSERVATIVE": quote["conservative_credit"],
    }[method]


def _rejection_reasons(
    candidate: dict[str, Any],
    constraints: RecommendationConstraints,
) -> list[str]:
    reasons: list[str] = []
    selected_credit = _selected_credit(candidate, constraints.pricing_method)
    credit_per_contract = selected_credit * 100
    width = candidate["spread_width"]
    raw_short_delta = candidate.get("short_delta")
    short_delta = abs(raw_short_delta) if raw_short_delta is not None else None

    if (
        constraints.minimum_short_delta is not None
        and short_delta is not None
        and short_delta < constraints.minimum_short_delta
    ):
        reasons.append("Short-leg absolute Delta is below the minimum.")
    if (
        constraints.maximum_short_delta is not None
        and short_delta is not None
        and short_delta > constraints.maximum_short_delta
    ):
        reasons.append("Short-leg absolute Delta exceeds the maximum.")

    if (
        constraints.minimum_credit_per_contract is not None
        and credit_per_contract < constraints.minimum_credit_per_contract
    ):
        reasons.append(
            f"Credit per contract ${credit_per_contract:.2f} is below "
            f"${constraints.minimum_credit_per_contract:.2f}."
        )
    if (
        constraints.minimum_credit_percent_of_width is not None
        and width > 0
        and selected_credit / width < constraints.minimum_credit_percent_of_width
    ):
        reasons.append("Credit as a percentage of spread width is below the minimum.")
    if (
        constraints.minimum_return_on_risk is not None
        and candidate["return_on_risk"] < constraints.minimum_return_on_risk
    ):
        reasons.append("Return on risk is below the minimum.")
    if (
        constraints.minimum_probability_of_profit is not None
        and candidate["probability_of_profit"] < constraints.minimum_probability_of_profit
    ):
        reasons.append("Probability of profit is below the minimum.")
    if (
        constraints.minimum_expected_value is not None
        and candidate["expected_value"] < constraints.minimum_expected_value
    ):
        reasons.append("Expected value is below the minimum.")
    if (
        constraints.minimum_managed_expected_value is not None
        and candidate["managed_expected_value"]
        < constraints.minimum_managed_expected_value
    ):
        reasons.append("Managed expected value is below the minimum.")
    if (
        constraints.maximum_absolute_net_delta is not None
        and candidate["net_position_delta"] is not None
        and abs(candidate["net_position_delta"])
        > constraints.maximum_absolute_net_delta
    ):
        reasons.append("Absolute net position Delta exceeds the maximum.")
    if (
        constraints.maximum_loss_per_contract is not None
        and candidate["maximum_risk"] > constraints.maximum_loss_per_contract
    ):
        reasons.append("Maximum loss per contract exceeds the maximum.")
    if (
        constraints.minimum_score is not None
        and candidate["score"] < constraints.minimum_score
    ):
        reasons.append("Score is below the minimum.")
    if (
        constraints.include_decisions
        and candidate["decision"] not in constraints.include_decisions
    ):
        reasons.append("Decision is not included.")
    if constraints.exclude_candidates_with_warnings and candidate["warnings"]:
        reasons.append("Candidate contains evaluation warnings.")
    if (
        constraints.require_positive_managed_expected_value
        and candidate["managed_expected_value"] <= 0
    ):
        reasons.append("Managed expected value is not positive.")

    quote = candidate["quote"]
    if constraints.minimum_open_interest is not None:
        if min(quote["short_open_interest"], quote["long_open_interest"]) < constraints.minimum_open_interest:
            reasons.append("One or both legs have insufficient open interest.")
    if constraints.minimum_volume is not None:
        if min(quote["short_volume"], quote["long_volume"]) < constraints.minimum_volume:
            reasons.append("One or both legs have insufficient volume.")
    if constraints.maximum_bid_ask_spread is not None:
        short_spread = quote["short_ask"] - quote["short_bid"]
        long_spread = quote["long_ask"] - quote["long_bid"]
        if max(short_spread, long_spread) > constraints.maximum_bid_ask_spread:
            reasons.append("One or both leg bid-ask spreads exceed the maximum.")

    return reasons


def _strategy_for_constraints(constraints: RecommendationConstraints):
    strategy = DEFAULT_STRATEGIES["Balanced"]
    changes: dict[str, Any] = {}

    # Only universe and trend controls are applied before candidate creation.
    # Qualification controls remain post-pipeline so rejected candidates and
    # their reasons stay visible in diagnostics.
    mappings = {
        "minimum_dte": constraints.minimum_dte,
        "maximum_dte": constraints.maximum_dte,
        "require_20_sma_above_200_sma": constraints.require_20_sma_above_200_sma,
        "require_price_above_200_sma": constraints.require_price_above_200_sma,
    }
    for field_name, value in mappings.items():
        if value is not None:
            changes[field_name] = value

    if constraints.allowed_spread_widths:
        changes["allowed_spread_widths"] = tuple(constraints.allowed_spread_widths)
    if constraints.price_vs_20_sma == "ABOVE":
        changes["require_price_below_20_sma"] = False
    elif constraints.price_vs_20_sma == "BELOW":
        changes["require_price_below_20_sma"] = True

    configured = replace(strategy, **changes)
    configured.validate()
    return configured



def _rejection_analysis(rejected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for candidate in rejected:
        counter.update(candidate.get("reasons", []))
    total = max(len(rejected), 1)
    return [
        {
            "reason": reason,
            "count": count,
            "candidate_percent": round(count / total * 100, 1),
        }
        for reason, count in counter.most_common()
    ]


def _what_if_hints(
    constraints: RecommendationConstraints,
    analysis: list[dict[str, Any]],
) -> list[dict[str, str]]:
    if not analysis:
        return []
    messages = {item["reason"]: item["count"] for item in analysis}
    hints: list[dict[str, str]] = []
    rules = [
        (
            "Credit per contract",
            "minimum_credit_per_contract",
            f"Review the minimum credit per contract of ${constraints.minimum_credit_per_contract:.0f}."
            if constraints.minimum_credit_per_contract is not None else "Review the minimum credit requirement.",
        ),
        (
            "Return on risk",
            "minimum_return_on_risk",
            f"Review the minimum return on risk of {constraints.minimum_return_on_risk * 100:.1f}%."
            if constraints.minimum_return_on_risk is not None else "Review the return-on-risk requirement.",
        ),
        (
            "Probability of profit",
            "minimum_probability_of_profit",
            f"Review the minimum POP of {constraints.minimum_probability_of_profit * 100:.1f}%."
            if constraints.minimum_probability_of_profit is not None else "Review the POP requirement.",
        ),
        (
            "Short-leg absolute Delta exceeds",
            "maximum_short_delta",
            f"Review the maximum short Delta of {constraints.maximum_short_delta:.2f}."
            if constraints.maximum_short_delta is not None else "Review the short-Delta range.",
        ),
        (
            "insufficient open interest",
            "minimum_open_interest",
            f"Review the minimum open interest of {constraints.minimum_open_interest}."
            if constraints.minimum_open_interest is not None else "Review the open-interest requirement.",
        ),
        (
            "insufficient volume",
            "minimum_volume",
            f"Review the minimum volume of {constraints.minimum_volume}."
            if constraints.minimum_volume is not None else "Review the volume requirement.",
        ),
        (
            "Managed expected value",
            "minimum_managed_expected_value",
            "Review the managed expected-value requirement.",
        ),
        (
            "Maximum loss",
            "maximum_loss_per_contract",
            f"Review the maximum loss per contract of ${constraints.maximum_loss_per_contract:.0f}."
            if constraints.maximum_loss_per_contract is not None else "Review the maximum-loss requirement.",
        ),
    ]
    for phrase, field, suggestion in rules:
        count = sum(value for reason, value in messages.items() if phrase in reason)
        if count:
            hints.append({"constraint": field, "affected_candidates": str(count), "suggestion": suggestion})
    return hints[:5]


def _scan_outcome(evaluated: int, included: int, rejected: int, failed: int) -> str:
    if failed and evaluated == 0:
        return "ERROR"
    if evaluated == 0:
        return "NO_PIPELINE_CANDIDATES"
    if included == 0 and rejected > 0:
        return "ALL_REJECTED"
    return "RESULTS"

def run_recommendation_scan(request: RecommendationRequest) -> dict[str, Any]:
    started = perf_counter()
    market_data = SchwabMarketDataClient(create_schwab_client())
    scanner = LiveCandidateScanner(
        market_data,
        create_default_candidate_pipeline(),
        market_analysis=MarketAnalysisBuilder(),
    )
    strategy = _strategy_for_constraints(request.constraints)

    included: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []

    for symbol in request.symbols:
        try:
            scanned, pipeline_diagnostics = scanner.scan_live_with_diagnostics(
                symbol=symbol,
                config=strategy,
            )
            symbol_candidates = [_candidate_payload(symbol, item) for item in scanned]
            accepted_for_symbol: list[dict[str, Any]] = []

            for candidate in symbol_candidates:
                reasons = _rejection_reasons(candidate, request.constraints)
                candidate["selected_pricing_method"] = request.constraints.pricing_method
                candidate["selected_credit"] = _selected_credit(
                    candidate, request.constraints.pricing_method
                )
                candidate["selected_credit_per_contract"] = candidate["selected_credit"] * 100
                if reasons:
                    rejected.append({
                        "symbol": symbol,
                        "expiration": candidate["expiration"],
                        "short_strike": candidate["short_strike"],
                        "long_strike": candidate["long_strike"],
                        "reasons": reasons,
                    })
                else:
                    accepted_for_symbol.append(candidate)

            accepted_for_symbol.sort(
                key=lambda item: (item["decision"] != "TRADE", -item["score"])
            )
            if request.constraints.maximum_results_per_symbol is not None:
                accepted_for_symbol = accepted_for_symbol[
                    : request.constraints.maximum_results_per_symbol
                ]
            included.extend(accepted_for_symbol)

            pipeline_payload = pipeline_diagnostics.to_dict()
            diagnostics.append({
                "symbol": symbol,
                "status": "OK",
                "evaluated_count": len(symbol_candidates),
                "included_count": len(accepted_for_symbol),
                "rejected_count": len(symbol_candidates) - len(accepted_for_symbol),
                "pipeline": pipeline_payload,
                "message": (
                    f"{len(accepted_for_symbol)} candidate(s) met the active constraints."
                    if accepted_for_symbol
                    else (
                        f"Pipeline stopped at {pipeline_payload['first_zero_stage']}."
                        if not symbol_candidates and pipeline_payload["first_zero_stage"]
                        else "No candidates met all active constraints."
                    )
                ),
            })
        except Exception as exc:
            diagnostics.append({
                "symbol": symbol,
                "status": "ERROR",
                "evaluated_count": 0,
                "included_count": 0,
                "rejected_count": 0,
                "pipeline": None,
                "message": str(exc),
            })

    included.sort(key=lambda item: (item["decision"] != "TRADE", -item["score"]))
    evaluated_count = sum(item["evaluated_count"] for item in diagnostics)
    failed_symbols = sum(item["status"] == "ERROR" for item in diagnostics)
    successful_symbols = len(diagnostics) - failed_symbols
    rejection_analysis = _rejection_analysis(rejected)
    elapsed_ms = round((perf_counter() - started) * 1000)
    outcome = _scan_outcome(evaluated_count, len(included), len(rejected), failed_symbols)
    pipeline_fields = [
        "total_contracts", "total_puts", "expiration_count",
        "price_history_bars", "filter_input_puts", "eligible_puts",
        "hedge_input_puts", "eligible_hedge_puts",
        "pair_attempts", "same_expiration_pairs", "ordered_strike_pairs",
        "allowed_width_pairs", "minimum_credit_pairs", "valid_credit_pairs",
        "risk_approved_pairs", "candidates_built", "candidates_evaluated",
        "portfolio_rejections", "candidates_ranked",
    ]
    pipeline_totals = {
        field: sum(
            int(item["pipeline"].get(field, 0))
            for item in diagnostics
            if item.get("pipeline")
        )
        for field in pipeline_fields
    }
    delta_distribution: dict[str, int] = {}
    for item in diagnostics:
        pipeline = item.get("pipeline") or {}
        for bucket, count in pipeline.get("delta_distribution", {}).items():
            delta_distribution[bucket] = delta_distribution.get(bucket, 0) + int(count)

    filter_rejections: dict[str, int] = {}
    builder_rejections: dict[str, int] = {}
    for item in diagnostics:
        pipeline = item.get("pipeline") or {}
        for reason, count in pipeline.get("filter_rejections", {}).items():
            filter_rejections[reason] = filter_rejections.get(reason, 0) + int(count)
        for reason, count in pipeline.get("builder_rejections", {}).items():
            builder_rejections[reason] = builder_rejections.get(reason, 0) + int(count)

    return {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "symbols": request.symbols,
        "constraints": request.constraints.model_dump(),
        "candidates": included,
        "rejected_candidates": rejected,
        "diagnostics": diagnostics,
        "pipeline_validation": {
            "totals": pipeline_totals,
            "delta_distribution": delta_distribution,
            "filter_rejections": dict(
                sorted(filter_rejections.items(), key=lambda item: item[1], reverse=True)
            ),
            "builder_rejections": dict(
                sorted(builder_rejections.items(), key=lambda item: item[1], reverse=True)
            ),
        },
        "summary": {
            "candidate_count": len(included),
            "rejected_count": len(rejected),
            "evaluated_count": evaluated_count,
            "symbols_requested": len(request.symbols),
            "symbols_succeeded": successful_symbols,
            "symbols_failed": failed_symbols,
            "elapsed_ms": elapsed_ms,
            "outcome": outcome,
            "trade_count": sum(item["decision"] == "TRADE" for item in included),
            "watch_count": sum(item["decision"] == "WATCH" for item in included),
            "pass_count": sum(item["decision"] == "PASS" for item in included),
        },
        "rejection_analysis": rejection_analysis,
        "constraint_impact": rejection_analysis[:5],
        "what_if_hints": _what_if_hints(request.constraints, rejection_analysis),
        "diagnostics_disclosure": (
            "Evaluated count represents candidates returned by the existing Balanced "
            "strategy pipeline. The current pipeline does not expose raw option-contract "
            "or pre-strategy spread-generation counts, so those figures are not inferred."
        ),
        "execution_mode": "READ_ONLY",
        "pricing_disclosure": (
            "Natural credit is short bid minus long ask. Midpoint credit is the "
            "difference between each leg midpoint. Conservative credit currently "
            "equals natural credit. Scoring credit is the value used by the existing "
            "spread model. Contract quote timestamps are not present in the normalized "
            "option model and are therefore reported as unavailable."
        ),
    }

