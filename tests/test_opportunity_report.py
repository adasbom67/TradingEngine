from app.models.trades.bull_put_spread import BullPutSpread
from app.models.trades.trade_candidate import TradeCandidate
from app.reports.opportunity_report import OpportunityReport
from tests.helpers import create_option, create_price_snapshot


def create_candidate(decision="TRADE"):
    return TradeCandidate(
        spread=BullPutSpread(
            short_put=create_option(500, bid=1.50, ask=1.60),
            long_put=create_option(495, bid=0.70, ask=0.80),
        ),
        score=88.5,
        rank=1,
        probability_of_profit=0.80,
        return_on_risk=0.16,
        managed_expected_value=12.50,
        unmanaged_expected_value=-30.0,
        profit_target_amount=35.0,
        stop_loss_amount=140.0,
        decision=decision,
        decision_reasons=["All configured requirements passed."],
        reasons=["Strong trend."],
    )


def test_report_formats_trade_metrics_and_decision():
    report = OpportunityReport().format_candidate(
        create_candidate(),
        create_price_snapshot(),
    )

    assert "SPY Bull Put Credit Spread" in report
    assert "Decision: TRADE" in report
    assert "Sell 500 Put / Buy 495 Put" in report
    assert "Estimated probability of profit: 80.0%" in report
    assert "Managed expected value: $12.50" in report
    assert "Overall score: 88.5/100" in report
    assert "not guarantees" in report


def test_watchlist_summary_uses_best_candidate():
    summary = OpportunityReport().format_summary({
        "SPY": [create_candidate("TRADE")],
        "QQQ": [],
    })
    assert "SPY    TRADE" in summary
    assert "QQQ    PASS" in summary


def test_empty_ranked_report_is_clear():
    assert OpportunityReport().format_ranked([]) == (
        "No qualifying bull put spread candidates found."
    )
