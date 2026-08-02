from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, time as clock_time
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class ScheduledJob:
    name: str
    at: str
    weekdays_only: bool = True


DEFAULT_JOBS = [
    ScheduledJob("morning-report", "09:45"),
    ScheduledJob("afternoon-report", "15:45"),
]


class DailyScheduler:
    """Persistent, idempotent scheduler for local daily workflows."""

    def __init__(
        self,
        config_path: str | Path = "config/schedule.json",
        state_path: str | Path = "data/scheduler_state.json",
        timezone_name: str = "America/New_York",
    ) -> None:
        self.config_path = Path(config_path)
        self.state_path = Path(state_path)
        self.timezone = ZoneInfo(timezone_name)

    def initialize(self, overwrite: bool = False) -> list[ScheduledJob]:
        if self.config_path.exists() and not overwrite:
            return self.load_jobs()
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timezone": str(self.timezone),
            "jobs": [job.__dict__ for job in DEFAULT_JOBS],
        }
        self.config_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return list(DEFAULT_JOBS)

    def load_jobs(self) -> list[ScheduledJob]:
        if not self.config_path.exists():
            return self.initialize()
        data = json.loads(self.config_path.read_text(encoding="utf-8"))
        if data.get("timezone"):
            self.timezone = ZoneInfo(data["timezone"])
        jobs = [ScheduledJob(**item) for item in data.get("jobs", [])]
        if not jobs:
            raise ValueError("Schedule must contain at least one job.")
        for job in jobs:
            self._parse_time(job.at)
        return jobs

    def due_jobs(self, now: datetime | None = None) -> list[ScheduledJob]:
        current = (now or datetime.now(self.timezone)).astimezone(self.timezone)
        state = self._load_state()
        due: list[ScheduledJob] = []
        for job in self.load_jobs():
            if job.weekdays_only and current.weekday() >= 5:
                continue
            scheduled = datetime.combine(current.date(), self._parse_time(job.at), self.timezone)
            key = f"{current.date().isoformat()}:{job.name}"
            if current >= scheduled and key not in state.get("completed", []):
                due.append(job)
        return due

    def run_due(self, runner: Callable[[ScheduledJob], None], now: datetime | None = None) -> list[str]:
        current = (now or datetime.now(self.timezone)).astimezone(self.timezone)
        state = self._load_state()
        completed = set(state.get("completed", []))
        executed: list[str] = []
        for job in self.due_jobs(current):
            runner(job)
            key = f"{current.date().isoformat()}:{job.name}"
            completed.add(key)
            executed.append(job.name)
        self._save_state({"completed": sorted(completed)[-100:]})
        return executed

    def loop(self, runner: Callable[[ScheduledJob], None], poll_seconds: int = 60) -> None:
        if poll_seconds < 5:
            raise ValueError("Poll interval must be at least 5 seconds.")
        while True:
            self.run_due(runner)
            time.sleep(poll_seconds)

    def _load_state(self) -> dict:
        if not self.state_path.exists():
            return {"completed": []}
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def _save_state(self, state: dict) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.state_path)

    @staticmethod
    def _parse_time(value: str) -> clock_time:
        try:
            hour, minute = (int(part) for part in value.split(":"))
            return clock_time(hour, minute)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid schedule time: {value!r}") from exc
