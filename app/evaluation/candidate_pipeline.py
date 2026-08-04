from app.config.strategy_config import PutSpreadConfig
from app.evaluation.candidate_ranker import CandidateRanker
from app.evaluation.evaluation_context import EvaluationContext
from app.evaluation.pipeline_diagnostics import PipelineDiagnostics
from app.evaluation.spread_evaluator import SpreadEvaluator
from app.evaluation.trade_decision import TradeDecisionEngine
from app.models.market.option_chain import OptionChain
from app.models.market.price_snapshot import PriceSnapshot
from app.models.market.trend_analysis import TrendAnalysis
from app.models.portfolio.portfolio_state import PortfolioState
from app.models.trades.trade_candidate import TradeCandidate
from app.risk.portfolio_constraints import PortfolioConstraintService
from app.selection.option_chain_filter import OptionChainFilter
from app.strategies.bull_put_spread_builder import BullPutSpreadBuilder


class CandidatePipeline:
    """Filter, build, evaluate, constrain, and rank spread candidates."""

    def __init__(
        self,
        spread_evaluator: SpreadEvaluator,
        option_filter: OptionChainFilter | None = None,
        spread_builder: BullPutSpreadBuilder | None = None,
        ranker: CandidateRanker | None = None,
        decision_engine: TradeDecisionEngine | None = None,
        portfolio_constraints: PortfolioConstraintService | None = None,
    ) -> None:
        self._spread_evaluator = spread_evaluator
        self._option_filter = option_filter or OptionChainFilter()
        self._spread_builder = spread_builder or BullPutSpreadBuilder()
        self._ranker = ranker or CandidateRanker()
        self._decision_engine = decision_engine or TradeDecisionEngine()
        self._portfolio_constraints = (
            portfolio_constraints or PortfolioConstraintService()
        )

    def run(
        self,
        chain: OptionChain,
        price_snapshot: PriceSnapshot,
        trend_analysis: TrendAnalysis,
        config: PutSpreadConfig,
        portfolio_state: PortfolioState | None = None,
    ) -> list[TradeCandidate]:
        ranked, _ = self.run_with_diagnostics(
            chain,
            price_snapshot,
            trend_analysis,
            config,
            portfolio_state=portfolio_state,
        )
        return ranked

    def run_with_diagnostics(
        self,
        chain: OptionChain,
        price_snapshot: PriceSnapshot,
        trend_analysis: TrendAnalysis,
        config: PutSpreadConfig,
        portfolio_state: PortfolioState | None = None,
        diagnostics: PipelineDiagnostics | None = None,
    ) -> tuple[list[TradeCandidate], PipelineDiagnostics]:
        diagnostics = diagnostics or PipelineDiagnostics()
        eligible_puts, diagnostics = self._option_filter.filter_puts_with_diagnostics(
            chain, config, diagnostics
        )
        candidates, diagnostics = self._spread_builder.build_with_diagnostics(
            eligible_puts, config, diagnostics
        )

        evaluated: list[TradeCandidate] = []
        for candidate in candidates:
            context = EvaluationContext(
                candidate=candidate,
                price_snapshot=price_snapshot,
                trend_analysis=trend_analysis,
                strategy_config=config,
            )
            evaluated_candidate = self._spread_evaluator.evaluate(context)
            diagnostics.candidates_evaluated += 1

            if portfolio_state is not None:
                decision = self._portfolio_constraints.evaluate(
                    evaluated_candidate,
                    portfolio_state,
                    config,
                )
                if not decision.approved:
                    diagnostics.portfolio_rejections += 1
                    continue
                evaluated_candidate.maximum_quantity = decision.maximum_quantity
                evaluated_candidate.reasons.extend(decision.reasons)

            trade_decision = self._decision_engine.evaluate(
                evaluated_candidate,
                config,
            )
            evaluated_candidate.decision = trade_decision.decision.value
            evaluated_candidate.decision_reasons = list(trade_decision.reasons)
            evaluated.append(evaluated_candidate)

        ranked = self._ranker.rank(evaluated)
        diagnostics.candidates_ranked = len(ranked)
        return ranked, diagnostics
