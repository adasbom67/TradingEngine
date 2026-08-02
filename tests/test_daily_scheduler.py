from datetime import datetime
from zoneinfo import ZoneInfo

from app.scheduling.scheduler import DailyScheduler


def test_scheduler_runs_due_jobs_once_per_day(tmp_path):
    scheduler = DailyScheduler(tmp_path / "schedule.json", tmp_path / "state.json")
    scheduler.initialize()
    now = datetime(2026, 8, 3, 16, 0, tzinfo=ZoneInfo("America/New_York"))
    calls = []
    assert scheduler.run_due(lambda job: calls.append(job.name), now) == ["morning-report", "afternoon-report"]
    assert scheduler.run_due(lambda job: calls.append(job.name), now) == []
    assert calls == ["morning-report", "afternoon-report"]


def test_scheduler_skips_weekends(tmp_path):
    scheduler = DailyScheduler(tmp_path / "schedule.json", tmp_path / "state.json")
    scheduler.initialize()
    saturday = datetime(2026, 8, 1, 16, 0, tzinfo=ZoneInfo("America/New_York"))
    assert scheduler.due_jobs(saturday) == []
