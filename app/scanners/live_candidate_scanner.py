from __future__ import annotations

from datetime import date, timedelta

from app.brokers.schwab_market_data import SchwabMarketDataClient
from app.config.strategy_config import PutSpreadConfig
from app.data.schwab_option_chain_adapter import SchwabOptionChainAdapter
from app.evaluation.candidate_pipeline import CandidatePipeline
from app.evaluation.pipeline_diagnostics import PipelineDiagnostics
from app.indicators.market_analysis import MarketAnalysisBuilder
from app.models.market.price_snapshot import PriceSnapshot
from app.models.market.trend_analysis import TrendAnalysis
from app.models.portfolio.portfolio_state import PortfolioState
from app.models.trades.trade_candidate import TradeCandidate


class LiveCandidateScanner:
    """Retrieve live Schwab data and run the candidate pipeline."""

    def __init__(
        self,
        market_data: SchwabMarketDataClient,
        pipeline: CandidatePipeline,
        adapter: SchwabOptionChainAdapter | None = None,
        market_analysis: MarketAnalysisBuilder | None = None,
    ) -> None:
        self._market_data = market_data
        self._pipeline = pipeline
        self._adapter = adapter or SchwabOptionChainAdapter()
        self._market_analysis = market_analysis or MarketAnalysisBuilder()

    def scan(
        self,
        symbol: str,
        price_snapshot: PriceSnapshot,
        trend_analysis: TrendAnalysis,
        config: PutSpreadConfig,
        as_of: date | None = None,
        portfolio_state: PortfolioState | None = None,
    ) -> list[TradeCandidate]:
        candidates, _ = self.scan_with_diagnostics(
            symbol,
            price_snapshot,
            trend_analysis,
            config,
            as_of=as_of,
            portfolio_state=portfolio_state,
        )
        return candidates

    def scan_with_diagnostics(
        self,
        symbol: str,
        price_snapshot: PriceSnapshot,
        trend_analysis: TrendAnalysis,
        config: PutSpreadConfig,
        as_of: date | None = None,
        portfolio_state: PortfolioState | None = None,
        diagnostics: PipelineDiagnostics | None = None,
    ) -> tuple[list[TradeCandidate], PipelineDiagnostics]:
        config.validate()
        normalized_symbol = symbol.strip().upper()
        if price_snapshot.symbol.upper() != normalized_symbol:
            raise ValueError("Price snapshot symbol does not match scan symbol.")

        reference_date = as_of or date.today()
        strategy_type = getattr(self._pipeline, "strategy_type", "BULL_PUT")
        chain_method = (
            self._market_data.get_call_option_chain
            if strategy_type == "BEAR_CALL"
            else self._market_data.get_put_option_chain
        )
        raw = chain_method(
            normalized_symbol,
            from_date=reference_date + timedelta(days=config.minimum_dte),
            to_date=reference_date + timedelta(days=config.maximum_dte),
        )
        chain = self._adapter.to_option_chain(
            raw,
            requested_symbol=normalized_symbol,
        )
        if hasattr(self._pipeline, "run_with_diagnostics"):
            return self._pipeline.run_with_diagnostics(
                chain,
                price_snapshot,
                trend_analysis,
                config,
                portfolio_state=portfolio_state,
                diagnostics=diagnostics,
            )

        if portfolio_state is None:
            candidates = self._pipeline.run(
                chain,
                price_snapshot,
                trend_analysis,
                config,
            )
        else:
            candidates = self._pipeline.run(
                chain,
                price_snapshot,
                trend_analysis,
                config,
                portfolio_state=portfolio_state,
            )
        fallback = diagnostics or PipelineDiagnostics()
        fallback.total_contracts = chain.contract_count()
        fallback.total_puts = len(chain.puts())
        fallback.expiration_count = len(
            {str(contract.expiration_date) for contract in chain.contracts}
        )
        fallback.candidates_built = len(candidates)
        fallback.candidates_evaluated = len(candidates)
        fallback.candidates_ranked = len(candidates)
        return candidates, fallback

    def scan_live(
        self,
        symbol: str,
        config: PutSpreadConfig,
        as_of: date | None = None,
        price_history_years: int = 2,
        portfolio_state: PortfolioState | None = None,
    ) -> list[TradeCandidate]:
        candidates, _ = self.scan_live_with_diagnostics(
            symbol,
            config,
            as_of=as_of,
            price_history_years=price_history_years,
            portfolio_state=portfolio_state,
        )
        return candidates

    def scan_live_with_diagnostics(
        self,
        symbol: str,
        config: PutSpreadConfig,
        as_of: date | None = None,
        price_history_years: int = 2,
        portfolio_state: PortfolioState | None = None,
    ) -> tuple[list[TradeCandidate], PipelineDiagnostics]:
        normalized_symbol = symbol.strip().upper()
        price_history = self._market_data.get_daily_price_history(
            normalized_symbol,
            period_years=price_history_years,
        )
        snapshot, trend = self._market_analysis.build(
            normalized_symbol,
            price_history,
            config,
        )
        diagnostics = PipelineDiagnostics(
            strategy_type=getattr(self._pipeline, "strategy_type", "BULL_PUT")
        )
        candles = price_history.get("candles", [])
        diagnostics.price_history_bars = len(candles) if isinstance(candles, list) else 0

        return self.scan_with_diagnostics(
            symbol=normalized_symbol,
            price_snapshot=snapshot,
            trend_analysis=trend,
            config=config,
            as_of=as_of,
            portfolio_state=portfolio_state,
            diagnostics=diagnostics,
        )
