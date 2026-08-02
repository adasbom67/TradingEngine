from datetime import date

from app.paper.ledger import PaperLedger
from app.paper.service import PaperTradingService
from app.reports.paper_report import PaperReport


def test_dashboard_shows_account_metrics(tmp_path):
    service = PaperTradingService(PaperLedger(tmp_path / "paper.json"))
    service.initialize(100_000)
    position = service.open_position(
        "SPY", date(2027, 1, 15), 700, 695, 1.0,
        opened_on=date(2026, 12, 1),
    )
    service.mark_position(position.position_id, 0.5, marked_on=date(2026, 12, 2))
    service.record_snapshot(snapshot_on=date(2026, 12, 2))

    text = PaperReport().format_dashboard(service.status())

    assert "Paper Portfolio Dashboard" in text
    assert "SPY" in text
    assert "Unrealized P/L" in text
