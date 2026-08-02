from datetime import date

import pytest

from app.paper.ledger import PaperLedger
from app.paper.service import PaperTradingService
from app.reports.paper_report import PaperReport


def test_paper_position_lifecycle_persists(tmp_path):
    service = PaperTradingService(PaperLedger(tmp_path / "paper.json"))
    service.initialize(50_000)
    position = service.open_position(
        "spy", date(2027, 1, 15), 700, 695, 1.25,
        opened_on=date(2026, 12, 1),
    )
    marked = service.mark_position(position.position_id, 0.60)
    assert marked.unrealized_pnl == 65
    closed = service.close_position(
        position.position_id, 0.55, "profit_target", closed_on=date(2026, 12, 10)
    )
    assert closed.realized_pnl == 70
    account = service.status()
    assert account.realized_pnl == 70
    assert not account.open_positions


def test_paper_rejects_invalid_spread(tmp_path):
    service = PaperTradingService(PaperLedger(tmp_path / "paper.json"))
    with pytest.raises(ValueError, match="Short strike"):
        service.open_position("SPY", date(2027, 1, 15), 695, 700, 1.0)


def test_paper_report_lists_positions(tmp_path):
    service = PaperTradingService(PaperLedger(tmp_path / "paper.json"))
    service.open_position("SPY", date(2027, 1, 15), 700, 695, 1.0)
    text = PaperReport().format_account(service.status())
    assert "Paper Trading Account" in text
    assert "SPY" in text
