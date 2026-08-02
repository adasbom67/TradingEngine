from datetime import date

from app.paper.exporter import PaperTradingExporter
from app.paper.ledger import PaperLedger
from app.paper.service import PaperTradingService


def test_exporter_creates_three_csv_files(tmp_path):
    service = PaperTradingService(PaperLedger(tmp_path / "paper.json"))
    service.initialize(100_000)
    service.open_position(
        "SPY", date(2027, 1, 15), 700, 695, 1.0,
        opened_on=date(2026, 12, 1),
    )
    service.record_observation("SPY", "WATCH", "Test observation")
    service.record_snapshot(snapshot_on=date(2026, 12, 1))

    paths = PaperTradingExporter().export(service.status(), tmp_path / "exports")

    assert len(paths) == 3
    assert all(path.exists() for path in paths)
    assert "position_id" in paths[0].read_text(encoding="utf-8")
