from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvaluationResult:
    """
    Represents the result produced by a single evaluator.
    """

    score: float = 0.0
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)