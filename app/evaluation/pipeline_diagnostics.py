from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PipelineDiagnostics:
    total_contracts: int = 0
    total_puts: int = 0
    expiration_count: int = 0
    price_history_bars: int = 0
    filter_input_puts: int = 0
    eligible_puts: int = 0
    filter_rejections: dict[str, int] = field(default_factory=dict)
    pair_attempts: int = 0
    same_expiration_pairs: int = 0
    ordered_strike_pairs: int = 0
    allowed_width_pairs: int = 0
    minimum_credit_pairs: int = 0
    valid_credit_pairs: int = 0
    risk_approved_pairs: int = 0
    candidates_built: int = 0
    builder_rejections: dict[str, int] = field(default_factory=dict)
    candidates_evaluated: int = 0
    portfolio_rejections: int = 0
    candidates_ranked: int = 0

    def increment_filter_rejection(self, reason: str) -> None:
        self.filter_rejections[reason] = self.filter_rejections.get(reason, 0) + 1

    def increment_builder_rejection(self, reason: str) -> None:
        self.builder_rejections[reason] = self.builder_rejections.get(reason, 0) + 1

    def first_zero_stage(self) -> str | None:
        stages = [
            ("option_contracts", self.total_contracts),
            ("put_contracts", self.total_puts),
            ("eligible_puts", self.eligible_puts),
            ("same_expiration_pairs", self.same_expiration_pairs),
            ("ordered_strike_pairs", self.ordered_strike_pairs),
            ("allowed_width_pairs", self.allowed_width_pairs),
            ("minimum_credit_pairs", self.minimum_credit_pairs),
            ("valid_credit_pairs", self.valid_credit_pairs),
            ("risk_approved_pairs", self.risk_approved_pairs),
            ("candidates_built", self.candidates_built),
            ("candidates_evaluated", self.candidates_evaluated),
            ("candidates_ranked", self.candidates_ranked),
        ]
        positive_indexes = [
            index for index, (_, value) in enumerate(stages) if value > 0
        ]
        if not positive_indexes:
            return stages[0][0]

        start_index = min(positive_indexes)
        for name, value in stages[start_index:]:
            if value == 0:
                return name
        return None

    def primary_bottleneck(self) -> dict[str, Any] | None:
        combined = {
            **{f"filter:{key}": value for key, value in self.filter_rejections.items()},
            **{f"builder:{key}": value for key, value in self.builder_rejections.items()},
        }
        if not combined:
            return None
        reason, count = max(combined.items(), key=lambda item: item[1])
        return {"reason": reason, "count": count}

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["first_zero_stage"] = self.first_zero_stage()
        payload["primary_bottleneck"] = self.primary_bottleneck()
        return payload
