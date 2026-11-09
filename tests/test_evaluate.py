import pytest

from mlops_team1.evaluate import classification_metrics


def test_classification_metrics_for_perfect_predictions() -> None:
    metrics = classification_metrics([0, 0, 1, 1], [0.05, 0.2, 0.8, 0.95])
    assert metrics == {
        "roc_auc": 1.0,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0,
    }


@pytest.mark.parametrize(
    ("labels", "scores", "threshold", "message"),
    [
        ([0, 1], [0.2], 0.5, "одинаковую ненулевую длину"),
        ([0, 2], [0.2, 0.8], 0.5, "бинарные метки"),
        ([0, 1], [-0.1, 0.8], 0.5, "от 0 до 1"),
        ([0, 1], [0.2, 0.8], 1.0, "строго между"),
        ([1, 1], [0.6, 0.8], 0.5, "обоих классов"),
        ([0, 1], [0.2, 0.8], 0.0, "строго между"),
        ([0, 1], [float("nan"), 0.8], 0.5, "конечными"),
        ([[0, 1], [1, 0]], [0.2, 0.8], 0.5, "одномерными"),
    ],
)
def test_classification_metrics_rejects_invalid_inputs(
    labels: list[int] | list[list[int]], scores: list[float], threshold: float, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        classification_metrics(labels, scores, threshold=threshold)


def test_classification_metrics_for_imperfect_predictions() -> None:
    metrics = classification_metrics([0, 0, 1, 1], [0.4, 0.6, 0.7, 0.9], threshold=0.5)
    assert metrics == pytest.approx(
        {
            "roc_auc": 1.0,
            "precision": 2 / 3,
            "recall": 1.0,
            "f1": 0.8,
        }
    )
