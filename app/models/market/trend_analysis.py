from dataclasses import dataclass, field


@dataclass
class TrendAnalysis:
    """
    Result of evaluating whether an underlying
    meets a strategy's trend requirements.
    """

    passed: bool
    score: int = 0
    reasons: list[str] = field(default_factory=list)