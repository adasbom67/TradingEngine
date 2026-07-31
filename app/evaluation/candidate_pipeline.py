from app.config.strategy_config import PutSpreadConfig
from app.evaluation.candidate_ranker import CandidateRanker
from app.evaluation.evaluation_context import EvaluationContext
from app.evaluation.spread_evaluator import SpreadEvaluator
from app.models.market.option_chain import OptionChain
from app.models.market.price_snapshot import PriceSnapshot
from app.models.market.trend_analysis import TrendAnalysis
from app.models.trades.trade_candidate import TradeCandidate
from app.selection.option_chain_filter import OptionChainFilter
from app.strategies.bull_put_spread_builder import BullPutSpreadBuilder


class CandidatePipeline:
    """Filter, build, evaluate, and rank bull put spread candidates."""

    def __init__(
        self,
        spread_evaluator: SpreadEvaluator,
        option_filter: OptionChainFilter | None = None,
        spread_builder: BullPutSpreadBuilder | None = None,
        ranker: CandidateRanker | None = None,
    ) -> None:
        self._spread_evaluator = spread_evaluator
        self._option_filter = option_filter or OptionChainFilter()
        self._spread_builder = spread_builder or BullPutSpreadBuilder()
        self._ranker = ranker or CandidateRanker()

    def run(
        self,
        chain: OptionChain,
        price_snapshot: PriceSnapshot,
        trend_analysis: TrendAnalysis,
        config: PutSpreadConfig,
    ) -> list[TradeCandidate]:
        eligible_puts = self._option_filter.filter_puts(chain, config)
        candidates = self._spread_builder.build(eligible_puts, config)

        evaluated: list[TradeCandidate] = []
        for candidate in candidates:
            context = EvaluationContext(
                candidate=candidate,
                price_snapshot=price_snapshot,
                trend_analysis=trend_analysis,
                strategy_config=config,
            )
            evaluated.append(self._spread_evaluator.evaluate(context))

        return self._ranker.rank(evaluated)
