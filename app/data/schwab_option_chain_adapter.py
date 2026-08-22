from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Iterable

from app.models.market.option_chain import OptionChain
from app.models.market.option_contract import OptionContract


class SchwabOptionChainFormatError(ValueError):
    pass


class SchwabOptionChainAdapter:
    def to_option_chain(self, payload: dict[str, Any], requested_symbol: str | None = None) -> OptionChain:
        symbol = self._underlying_symbol(payload, requested_symbol)
        underlying_price = self._underlying_price(payload)
        contracts = self._read_map(payload.get("putExpDateMap"), "PUT")
        contracts.extend(self._read_map(payload.get("callExpDateMap"), "CALL"))
        return OptionChain(symbol, underlying_price, contracts)

    def _read_map(self, expiration_map: Any, option_type: str) -> list[OptionContract]:
        if expiration_map is None:
            return []
        if not isinstance(expiration_map, dict):
            raise SchwabOptionChainFormatError(f"{option_type} expiration map must be an object.")
        normalized=[]
        for expiration_key, strike_map in expiration_map.items():
            if not isinstance(strike_map, dict):
                continue
            fallback_expiration=self._date_from_expiration_key(str(expiration_key))
            for strike_key, raw_contracts in strike_map.items():
                for raw in self._as_contract_list(raw_contracts):
                    normalized.append(self._to_contract(raw, option_type, strike_key, fallback_expiration))
        return normalized

    def _to_contract(self, raw, option_type, fallback_strike, fallback_expiration):
        expiration=self._contract_expiration(raw.get("expirationDate"), fallback_expiration)
        dte=self._optional_int(raw.get("daysToExpiration"))
        if dte is None:
            dte=max((expiration-date.today()).days,0)
        return OptionContract(
            symbol=str(raw.get("symbol") or "").strip(),
            expiration_date=expiration,
            strike=self._float(raw.get("strikePrice", fallback_strike), "strike"),
            option_type=str(raw.get("putCall") or option_type).upper(),
            bid=self._float(raw.get("bid",0.0),"bid"),
            ask=self._float(raw.get("ask",0.0),"ask"),
            last=self._float(raw.get("last",0.0),"last"),
            delta=self._optional_float(raw.get("delta")),
            volume=self._optional_int(raw.get("totalVolume")) or 0,
            open_interest=self._optional_int(raw.get("openInterest")) or 0,
            days_to_expiration=dte,
            implied_volatility=self._optional_float(raw.get("volatility")),
            quote_time=self._optional_datetime(raw.get("quoteTimeInLong")),
        )

    @staticmethod
    def _underlying_symbol(payload, requested_symbol):
        underlying=payload.get("underlying")
        candidate=underlying.get("symbol") if isinstance(underlying,dict) else None
        candidate=candidate or payload.get("symbol") or requested_symbol
        if not candidate:
            raise SchwabOptionChainFormatError("Unable to determine underlying symbol.")
        return str(candidate).strip().upper()

    @staticmethod
    def _underlying_price(payload):
        value=payload.get("underlyingPrice")
        if value is None and isinstance(payload.get("underlying"),dict):
            u=payload["underlying"]
            value=u.get("mark") or u.get("last") or u.get("close")
        if value is None:
            raise SchwabOptionChainFormatError("Unable to determine underlying price.")
        return SchwabOptionChainAdapter._float(value,"underlying price")

    @staticmethod
    def _as_contract_list(value) -> Iterable[dict[str, Any]]:
        if isinstance(value,dict): return [value]
        if isinstance(value,list): return [x for x in value if isinstance(x,dict)]
        return []

    @staticmethod
    def _date_from_expiration_key(value):
        try: return date.fromisoformat(value[:10])
        except ValueError as exc: raise SchwabOptionChainFormatError(f"Invalid Schwab expiration key: {value!r}") from exc

    @staticmethod
    def _contract_expiration(value, fallback):
        if value in (None,""): return fallback
        if isinstance(value,(int,float)):
            ts=float(value)
            if ts>10_000_000_000: ts/=1000
            return datetime.fromtimestamp(ts,tz=timezone.utc).date()
        try: return date.fromisoformat(str(value)[:10])
        except ValueError: return fallback

    @staticmethod
    def _float(value, field_name):
        try: return float(value)
        except (TypeError,ValueError) as exc: raise SchwabOptionChainFormatError(f"Invalid {field_name}: {value!r}") from exc

    @staticmethod
    def _optional_float(value):
        if value in (None,""): return None
        try: return float(value)
        except (TypeError,ValueError): return None

    @staticmethod
    def _optional_int(value):
        if value in (None,""): return None
        try: return int(value)
        except (TypeError,ValueError): return None

    @staticmethod
    def _optional_datetime(value):
        if value in (None, ""): return None
        try:
            timestamp=float(value)
            if timestamp>10_000_000_000: timestamp/=1000
            return datetime.fromtimestamp(timestamp,tz=timezone.utc)
        except (TypeError,ValueError,OverflowError,OSError): return None
