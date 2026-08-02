from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config.runtime_config import LoggingSettings


class JsonLineFormatter(logging.Formatter):
    """Format each log record as one machine-readable JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key in ("event", "symbol", "position_id", "job_name", "decision", "correlation_id", "duration_ms"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload, sort_keys=True)


def configure_logging(settings: LoggingSettings) -> Path:
    settings.validate()
    directory = Path(settings.directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / settings.filename

    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.level.upper()))
    root.handlers.clear()

    file_handler = RotatingFileHandler(
        path,
        maxBytes=settings.max_bytes,
        backupCount=settings.backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(JsonLineFormatter())
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    root.addHandler(console_handler)
    return path
