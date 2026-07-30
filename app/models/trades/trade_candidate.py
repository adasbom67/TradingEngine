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

    reasons: list[str] = field(default_factory=list)

    warnings: list[str] = field(default_factory=list)