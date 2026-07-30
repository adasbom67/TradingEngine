from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List

from app.models.market.option_contract import OptionContract


@dataclass
class OptionChain:
    """
    Represents a normalized option chain for a single underlying.
    """

    underlying_symbol: str
    underlying_price: float
    contracts: List[OptionContract] = field(default_factory=list)

    def puts(self) -> List[OptionContract]:
        """Return all put contracts."""
        return [
            contract
            for contract in self.contracts
            if contract.option_type == "PUT"
        ]

    def calls(self) -> List[OptionContract]:
        """Return all call contracts."""
        return [
            contract
            for contract in self.contracts
            if contract.option_type == "CALL"
        ]

    def expirations(self) -> List[date]:
        """Return all unique expiration dates."""
        return sorted(
            {contract.expiration_date for contract in self.contracts}
        )

    def contract_count(self) -> int:
        """Return the total number of contracts."""
        return len(self.contracts)