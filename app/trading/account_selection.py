from __future__ import annotations

import os
import json
from dataclasses import dataclass
from typing import Iterable

from app.trading.models import BrokerAccount


ACCOUNT_HASH_ENVIRONMENT_VARIABLE = "SCHWAB_LIVE_ACCOUNT_HASH"


def mask_sensitive(value: str, *, visible_prefix: int = 4, visible_suffix: int = 4) -> str:
    normalized = value.strip()
    if not normalized:
        return "(not set)"
    if len(normalized) <= visible_prefix + visible_suffix:
        return "*" * len(normalized)
    return (
        normalized[:visible_prefix]
        + "..."
        + normalized[-visible_suffix:]
    )


@dataclass(frozen=True)
class AccountSelection:
    account: BrokerAccount
    source: str


class AccountSelectionRequired(RuntimeError):
    """Raised when a linked Schwab account cannot be selected safely."""

    def __init__(self, message: str, accounts: Iterable[BrokerAccount] = ()) -> None:
        super().__init__(message)
        self.accounts = tuple(accounts)

    def user_message(self) -> str:
        lines = [str(self), ""]
        if self.accounts:
            lines.extend(["Available Schwab accounts:", ""])
            for account in self.accounts:
                lines.append(
                    f"- Account {account.masked_id}  "
                    f"(hash fingerprint {mask_sensitive(account.account_hash)})"
                )
            lines.append("")
        lines.extend([
            "Set SCHWAB_LIVE_ACCOUNT_HASH in your local .env file to the full hash",
            "for the account you want TradingEngine to use.",
            "",
            "Example:",
            "SCHWAB_LIVE_ACCOUNT_HASH=<full Schwab account hash>",
            "",
            "Do not commit the account hash to config/runtime.json or Git.",
        ])
        return "\n".join(lines)


def configured_account_hash() -> tuple[str, str]:
    """Resolve the live Schwab account from local environment configuration.

    Account identifiers are machine-specific and must not be stored in tracked
    runtime configuration. SCHWAB_LIVE_ACCOUNT_HASH is the only supported
    selector when more than one Schwab account is linked.
    """
    environment_value = os.getenv(ACCOUNT_HASH_ENVIRONMENT_VARIABLE, "").strip()
    if environment_value:
        return environment_value, "environment"
    try:
        from app.web.settings import LocalSettingsStore
        local_value = LocalSettingsStore().load().schwab_live_account_hash.strip()
    except (OSError, ValueError, json.JSONDecodeError):
        local_value = ""
    if local_value:
        return local_value, "local_settings"
    return "", "unconfigured"


def select_account(
    accounts: Iterable[BrokerAccount],
) -> AccountSelection:
    linked = tuple(accounts)
    if not linked:
        raise AccountSelectionRequired("No Schwab accounts were returned by the broker.")

    configured_hash, source = configured_account_hash()
    if configured_hash:
        for account in linked:
            if account.account_hash == configured_hash:
                return AccountSelection(account=account, source=source)
        raise AccountSelectionRequired(
            "The configured Schwab account hash did not match a linked account.",
            linked,
        )

    if len(linked) == 1:
        return AccountSelection(account=linked[0], source="single_linked_account")

    raise AccountSelectionRequired(
        "Multiple Schwab accounts are linked, so TradingEngine will not guess.",
        linked,
    )
