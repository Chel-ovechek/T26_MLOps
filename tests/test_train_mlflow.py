import re
from collections.abc import Iterator
from pathlib import Path

import pytest

mlflow = pytest.importorskip("mlflow")

from mlops_team1.train_mlflow import run_experiment

ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "flights_sample_v1.csv"
CONTRACT = ROOT / "data" / "contract.json"
REQUIRED_TAGS = {
    "git.commit",
    "git.dirty",
    "data.dvc_hash",
    "data.sha256",
    "data.contract_version",
    "split.policy",
    "team.code",
    "validation.status",
}


@pytest.fixture
def tracking(tmp_path: Path) -> Iterator[str]:
    """Отдельная sqlite-база и каталог артефактов во временной папке, сервер не нужен."""
    previous = mlflow.get_tracking_uri()
    mlflow.set_tracking_uri(f"sqlite:///{(tmp_path / 'mlflow.db').as_posix()}")
    name = "lr4-smoke"
    mlflow.create_experiment(name, artifact_location=(tmp_path / "artifacts").as_uri())
    yield name
    mlflow.set_tracking_uri(previous)


def test_run_experiment_logs_tags_params_metrics_and_artifacts(tracking: str) -> None:
    run_id = run_experiment(
        FIXTURE, CONTRACT, tracking, 10, 3, 42, team_code="team-1", hypothesis="Проверка"
    )
    client = mlflow.MlflowClient()
    run = client.get_run(run_id)

    assert REQUIRED_TAGS <= set(run.data.tags)
    assert run.data.tags["data.dvc_hash"] == "not-tracked"
    assert run.data.tags["data.contract_version"] == "2.0.0"
    assert run.data.tags["team.code"] == "team-1"
    assert run.data.tags["validation.status"] == "candidate"
    assert re.fullmatch(r"[0-9a-f]{64}", run.data.tags["data.sha256"])

    assert run.data.params["max_depth"] == "3"
    assert run.data.params["split_validation_rows"] == "5"
    assert {"validation_roc_auc", "validation_precision", "validation_recall"} <= set(
        run.data.metrics
    )
    assert 0.0 <= run.data.metrics["validation_positive_rate"] <= 1.0
    assert {i.dataset.name for i in run.inputs.dataset_inputs} == {
        "flight-delay-train",
        "flight-delay-validation",
    }

    paths = {a.path for a in client.list_artifacts(run_id, "reports")}
    assert paths == {
        "reports/split_manifest.json",
        "reports/metrics.json",
        "reports/validation_report.json",
        "reports/run_summary.md",
    }
    assert [a.path for a in client.list_artifacts(run_id, "model")] == ["model/model.joblib"]
    assert [a.path for a in client.list_artifacts(run_id, "environment")] == [
        "environment/requirements.txt"
    ]


def test_run_experiment_refuses_data_that_fails_contract(tracking: str, tmp_path: Path) -> None:
    lines = FIXTURE.read_text(encoding="utf-8").splitlines()
    broken = tmp_path / "broken.csv"
    broken.write_text("\n".join([*lines, lines[-1]]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="контракт"):
        run_experiment(broken, CONTRACT, tracking, 10, 3, 42)


def test_run_experiment_logs_boundaries_shifted_to_end_of_day(
    tracking: str, four_flights_per_day_csv: Path
) -> None:
    run_id = run_experiment(four_flights_per_day_csv, CONTRACT, tracking, 5, 2, 42)
    params = mlflow.MlflowClient().get_run(run_id).data.params
    assert (params["split_train_rows"], params["split_validation_rows"]) == ("16", "4")
    assert params["split_test_rows"] == "4"
