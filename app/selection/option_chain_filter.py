from app.config.strategy_config import PutSpreadConfig
from app.evaluation.pipeline_diagnostics import PipelineDiagnostics
from app.models.market.option_chain import OptionChain
from app.models.market.option_contract import OptionContract

DELTA_BUCKETS = (
    (0.05, "<0.05"), (0.10, "0.05-0.10"), (0.15, "0.10-0.15"),
    (0.20, "0.15-0.20"), (0.25, "0.20-0.25"), (0.30, "0.25-0.30"),
    (0.40, "0.30-0.40"), (float("inf"), ">=0.40"),
)

def delta_bucket(delta: float | None) -> str:
    if delta is None:
        return "missing"
    value = abs(delta)
    for upper, label in DELTA_BUCKETS:
        if value < upper:
            return label
    return ">=0.40"

class OptionChainFilter:
    """Select liquid put contracts that satisfy strategy constraints."""

    def filter_puts(self, chain: OptionChain, config: PutSpreadConfig) -> list[OptionContract]:
        eligible, _ = self.filter_puts_with_diagnostics(chain, config)
        return eligible

    def filter_puts_with_diagnostics(self, chain: OptionChain, config: PutSpreadConfig,
                                     diagnostics: PipelineDiagnostics | None = None):
        config.validate()
        diagnostics = diagnostics or PipelineDiagnostics()
        puts = chain.puts()
        diagnostics.total_contracts = chain.contract_count()
        diagnostics.total_puts = len(puts)
        diagnostics.expiration_count = len({str(c.expiration_date) for c in chain.contracts})
        diagnostics.filter_input_puts = len(puts)

        eligible = []
        for contract in puts:
            diagnostics.increment_delta_bucket(delta_bucket(contract.delta))
            reason = self._rejection_reason(contract, config)
            if reason is None:
                eligible.append(contract)
            else:
                diagnostics.increment_filter_rejection(reason)

        diagnostics.eligible_puts = len(eligible)
        eligible.sort(key=lambda c: (str(c.expiration_date), -c.strike, c.symbol))
        return eligible, diagnostics

    @staticmethod
    def _rejection_reason(contract: OptionContract, config: PutSpreadConfig) -> str | None:
        if not config.minimum_dte <= contract.days_to_expiration <= config.maximum_dte:
            return "dte_out_of_range"
        if contract.delta is None:
            return "missing_delta"
        absolute_delta = abs(contract.delta)
        if absolute_delta < config.minimum_delta:
            return "delta_below_minimum"
        if absolute_delta > config.maximum_delta:
            return "delta_above_maximum"
        if contract.bid < config.minimum_bid:
            return "bid_below_minimum"
        if contract.open_interest < config.minimum_open_interest:
            return "open_interest_below_minimum"
        if contract.volume < config.minimum_volume:
            return "volume_below_minimum"
        if contract.ask < contract.bid:
            return "invalid_bid_ask"
        if contract.ask - contract.bid > config.maximum_bid_ask_spread:
            return "bid_ask_spread_too_wide"
        return None

    @classmethod
    def _is_eligible(cls, contract: OptionContract, config: PutSpreadConfig) -> bool:
        return cls._rejection_reason(contract, config) is None
