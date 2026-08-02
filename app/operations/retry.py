from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    attempts: int = 3
    initial_delay_seconds: float = 0.5
    backoff_multiplier: float = 2.0
    maximum_delay_seconds: float = 5.0

    def validate(self) -> None:
        if self.attempts <= 0:
            raise ValueError("attempts must be greater than zero.")
        if self.initial_delay_seconds < 0:
            raise ValueError("initial_delay_seconds cannot be negative.")
        if self.backoff_multiplier < 1:
            raise ValueError("backoff_multiplier must be at least 1.")
        if self.maximum_delay_seconds < 0:
            raise ValueError("maximum_delay_seconds cannot be negative.")


def retry_call(
    operation: Callable[[], T],
    policy: RetryPolicy,
    *,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
    sleep: Callable[[float], None] = time.sleep,
    on_retry: Callable[[int, BaseException, float], None] | None = None,
) -> T:
    """Execute an operation with bounded exponential backoff."""
    policy.validate()
    delay = min(policy.initial_delay_seconds, policy.maximum_delay_seconds)
    for attempt in range(1, policy.attempts + 1):
        try:
            return operation()
        except retry_on as exc:
            if attempt >= policy.attempts:
                raise
            if on_retry is not None:
                on_retry(attempt, exc, delay)
            sleep(delay)
            delay = min(delay * policy.backoff_multiplier, policy.maximum_delay_seconds)
    raise RuntimeError("Retry loop ended unexpectedly.")
