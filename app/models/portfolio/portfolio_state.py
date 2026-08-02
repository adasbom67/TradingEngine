from dataclasses import dataclass


@dataclass(frozen=True)
class PortfolioState:
    """Minimum portfolio information required for pre-trade constraints."""

    account_value: float
    available_buying_power: float
    open_positions: int = 0
    committed_risk: float = 0.0
    daily_realized_loss: float = 0.0
