from app.evaluation.candidate_ranker import CandidateRanker
from app.models.trades.bull_put_spread import BullPutSpread
from app.models.trades.trade_candidate import TradeCandidate
from tests.helpers import create_option


def make_candidate(short_strike: float, credit_bid: float, score: float, warnings=None):
    short_put = create_option(short_strike, bid=credit_bid, ask=credit_bid + 0.05)
    long_put = create_option(short_strike - 5, bid=0.20, ask=0.25)
    return TradeCandidate(
        spread=BullPutSpread(short_put, long_put),
        score=score,
        warnings=warnings or [],
    )


def test_ranks_by_score_then_warning_count():
    lower = make_candidate(500, 1.00, 80)
    more_warnings = make_candidate(505, 1.20, 90, ["a", "b"])
    fewer_warnings = make_candidate(510, 1.10, 90, ["a"])

    ranked = CandidateRanker().rank([lower, more_warnings, fewer_warnings])

    assert ranked == [fewer_warnings, more_warnings, lower]
    assert [candidate.rank for candidate in ranked] == [1, 2, 3]
