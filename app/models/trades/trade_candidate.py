from dataclasses import dataclass, field

from app.models.trades.bull_put_spread import BullPutSpread


@dataclass
class TradeCandidate:
    """
    Represents an evaluated trade candidate.

    A TradeCandidate wraps a BullPutSpread and stores the
    evaluation results produced by the evaluation pipeline.
    """

    spread: BullPutSpread

    score: float = 0.0

    rank: int = 0

    probability_of_profit: float = 0.0

    return_on_risk: float = 0.0

    expected_value: float = 0.0

    unmanaged_expected_value: float = 0.0

    managed_expected_value: float = 0.0

    profit_target_amount: float = 0.0

    stop_loss_amount: float = 0.0

    decision: str = "UNDECIDED"

    decision_reasons: list[str] = field(default_factory=list)

    market_regime: str = "unknown"

    maximum_quantity: int = 0

    score_breakdown: dict[str, float] = field(default_factory=dict)

    reasons: list[str] = field(default_factory=list)

    warnings: list[str] = field(default_factory=list)