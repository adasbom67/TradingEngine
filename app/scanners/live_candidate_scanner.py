from __future__ import annotations

from datetime import date, timedelta

from app.brokers.schwab_market_data import SchwabMarketDataClient
from app.config.strategy_config import PutSpreadConfig
from app.data.schwab_option_chain_adapter import SchwabOptionChainAdapter
from app.evaluation.candidate_pipeline import CandidatePipeline
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
        config.validate()
        normalized_symbol = symbol.strip().upper()
        if price_snapshot.symbol.upper() != normalized_symbol:
            raise ValueError(
                "Price snapshot symbol does not match scan symbol."
            )

        reference_date = as_of or date.today()
        raw = self._market_data.get_put_option_chain(
            normalized_symbol,
            from_date=reference_date + timedelta(days=config.minimum_dte),
            to_date=reference_date + timedelta(days=config.maximum_dte),
        )
        chain = self._adapter.to_option_chain(
            raw,
            requested_symbol=normalized_symbol,
        )
        if portfolio_state is None:
            return self._pipeline.run(
                chain,
                price_snapshot,
                trend_analysis,
                config,
            )
        return self._pipeline.run(
            chain,
            price_snapshot,
            trend_analysis,
            config,
            portfolio_state=portfolio_state,
        )

    def scan_live(
        self,
        symbol: str,
        config: PutSpreadConfig,
        as_of: date | None = None,
        price_history_years: int = 2,
        portfolio_state: PortfolioState | None = None,
    ) -> list[TradeCandidate]:
        """Build market analysis automatically, then scan live options."""
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
        return self.scan(
            symbol=normalized_symbol,
            price_snapshot=snapshot,
            trend_analysis=trend,
            config=config,
            as_of=as_of,
            portfolio_state=portfolio_state,
        )
