from pathlib import Path
from app.api.recommendation_history import RecommendationHistoryStore

def test_scan_history_round_trip(tmp_path: Path):
    store=RecommendationHistoryStore(tmp_path/"history.json",maximum_entries=2)
    first=store.save({"constraints":{"minimum_score":80}},{"scanned_at":"2026-08-03T10:00:00+00:00","symbols":["SPY"],"summary":{"candidate_count":1},"candidates":[{"symbol":"SPY"}]})
    assert store.get(first["id"])["candidates"][0]["symbol"]=="SPY"
    assert store.list_entries()[0]["summary"]["candidate_count"]==1

def test_history_limit_is_enforced(tmp_path: Path):
    store=RecommendationHistoryStore(tmp_path/"history.json",maximum_entries=2)
    for index in range(3): store.save({"constraints":{}},{"scanned_at":f"2026-08-03T10:0{index}:00+00:00","symbols":["SPY"],"summary":{}})
    assert len(store.list_entries(limit=10))==2
