from app.evaluation.default_pipeline import create_default_candidate_pipeline


def test_default_pipeline_is_constructed():
    assert create_default_candidate_pipeline() is not None
