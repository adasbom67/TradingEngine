from __future__ import annotations

import json
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class ExecutionMetric:
    operation: str
    started_at: str
    duration_ms: float
    successful: bool
    detail: str | None = None


class MetricsRecorder:
    """Append lightweight execution metrics as JSON lines."""

    def __init__(self, path: str | Path = "logs/metrics.jsonl") -> None:
        self.path = Path(path)

    def record(self, metric: ExecutionMetric) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(metric), sort_keys=True) + "\n")

    @contextmanager
    def measure(self, operation: str) -> Iterator[None]:
        started_at = datetime.now(timezone.utc).isoformat()
        started = time.perf_counter()
        successful = False
        detail = None
        try:
            yield
            successful = True
        except Exception as exc:
            detail = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            self.record(
                ExecutionMetric(
                    operation=operation,
                    started_at=started_at,
                    duration_ms=round((time.perf_counter() - started) * 1000, 3),
                    successful=successful,
                    detail=detail,
                )
            )
