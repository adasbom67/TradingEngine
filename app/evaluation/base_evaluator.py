from abc import ABC, abstractmethod

from app.evaluation.evaluation_context import EvaluationContext
from app.evaluation.evaluation_result import EvaluationResult


class BaseEvaluator(ABC):
    """
    Abstract base class for all evaluators.
    """

    @abstractmethod
    def evaluate(
        self,
        context: EvaluationContext,
    ) -> EvaluationResult:
        """
        Evaluate a trade using the supplied evaluation context.
        """
        raise NotImplementedError