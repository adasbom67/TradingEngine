from app.config.strategy_config import PutSpreadConfig
from app.evaluation.candidate_pipeline import CandidatePipeline
from app.evaluation.spread_evaluator import SpreadEvaluator
from app.evaluation.evaluators.trend_evaluator import TrendEvaluator
from app.models.market.option_chain import OptionChain
from app.models.market.trend_analysis import TrendAnalysis
from tests.helpers import create_option, create_price_snapshot


def test_full_pipeline_filters_builds_evaluates_and_ranks():
    puts = [
        create_option(500, bid=1.50, ask=1.60, delta=-0.20),
        create_option(495, bid=0.70, ask=0.80, delta=-0.18),
        create_option(490, bid=0.25, ask=0.35, delta=-0.16),
        create_option(485, bid=0.10, ask=0.15, delta=-0.10),
    ]
    chain = OptionChain("SPY", 605.0, puts)
    pipeline = CandidatePipeline(SpreadEvaluator([TrendEvaluator()]))

    ranked = pipeline.run(
        chain=chain,
        price_snapshot=create_price_snapshot(),
        trend_analysis=TrendAnalysis(passed=True, score=100),
        config=PutSpreadConfig(minimum_credit=0.50, maximum_risk_per_trade=500),
    )

    assert len(ranked) == 1
    assert ranked[0].spread.short_put.strike == 500
    assert ranked[0].spread.long_put.strike == 495
    assert ranked[0].score == 100
    assert ranked[0].rank == 1
    assert ranked[0].warnings == []


def test_pipeline_assigns_explicit_decision():
    puts = [
        create_option(500, bid=1.50, ask=1.60, delta=-0.20),
        create_option(495, bid=0.70, ask=0.80, delta=-0.18),
    ]
    chain = OptionChain("SPY", 605.0, puts)
    pipeline = CandidatePipeline(SpreadEvaluator([TrendEvaluator()]))

    ranked = pipeline.run(
        chain=chain,
        price_snapshot=create_price_snapshot(),
        trend_analysis=TrendAnalysis(passed=True, score=100),
        config=PutSpreadConfig(minimum_credit=0.50),
    )

    assert ranked[0].decision in {"TRADE", "WATCH", "PASS"}
