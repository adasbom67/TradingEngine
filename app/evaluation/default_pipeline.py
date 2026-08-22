from app.evaluation.candidate_pipeline import CandidatePipeline
from app.evaluation.evaluators.market_regime_evaluator import MarketRegimeEvaluator
from app.evaluation.evaluators.opportunity_evaluator import OpportunityEvaluator
from app.evaluation.evaluators.trend_evaluator import TrendEvaluator
from app.evaluation.spread_evaluator import SpreadEvaluator


def create_default_candidate_pipeline(strategy_type: str = "BULL_PUT") -> CandidatePipeline:
    """Create the production candidate pipeline with all standard evaluators."""
    return CandidatePipeline(
        SpreadEvaluator([
            TrendEvaluator(),
            MarketRegimeEvaluator(),
            OpportunityEvaluator(),
        ]),
        strategy_type=strategy_type,
    )
