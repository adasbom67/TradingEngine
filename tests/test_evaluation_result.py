from app.evaluation.evaluation_result import EvaluationResult


def test_default_values():
    result = EvaluationResult()

    assert result.score == 0.0
    assert result.reasons == []
    assert result.warnings == []


def test_custom_values():
    result = EvaluationResult(
        score=20,
        reasons=["Excellent credit"],
        warnings=["Low volume"],
    )

    assert result.score == 20
    assert result.reasons == ["Excellent credit"]
    assert result.warnings == ["Low volume"]