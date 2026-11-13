from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).parents[1]
SAMPLE_V1 = REPO_ROOT / "tests" / "fixtures" / "flights_sample_v1.csv"
CONTRACT_PATH = REPO_ROOT / "data" / "contract.json"

# Слой пирамиды тестов (ЛР5) по имени файла. Файлы, которых ещё нет, внесены заранее:
# так каждый участник добавляет только свой файл тестов и не правит conftest.py.
LAYER_BY_FILE = {
    "test_data_contract": "data",
    "test_validate_dataset": "data",
    "test_split_cuts": "data",
    "test_generate_v2": "data",
    "test_data_negative": "data",
    "test_evaluate": "evaluation",
    "test_evaluation_target": "evaluation",
    "test_train_model": "model",
    "test_model_bundle": "model",
    "test_model_io": "api",
    "test_train_mlflow": "pipeline",
    "test_run_meta": "pipeline",
    "test_dvc_refusal": "pipeline",
    "test_pipeline_smoke": "pipeline",
    "test_smoke": "project",
    "test_quality": "project",
    "test_fixtures": "project",
    "test_layers": "project",
}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        layer = LAYER_BY_FILE.get(item.path.stem)
        if layer is not None:
            item.add_marker(getattr(pytest.mark, layer))


@pytest.fixture
def four_flights_per_day_csv(tmp_path: Path) -> Path:
    """24 строки: 6 дней по 4 рейса, в каждой хронологической части оба класса."""
    lines = ["FlightDate,DepHour,IsWeekend,ArrDelay"]
    start = date(2026, 1, 5)
    for day in range(6):
        current = start + timedelta(days=day)
        weekend = int(current.weekday() >= 5)
        for slot, hour in enumerate((6, 10, 14, 18)):
            delay = 30 if (day * 4 + slot) % 2 == 0 else 5
            lines.append(f"{current.isoformat()},{hour},{weekend},{delay}")
    path = tmp_path / "four_per_day.csv"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


@pytest.fixture
def valid_frame() -> pd.DataFrame:
    """Новая копия корректного набора v1 (24 строки) для каждого теста."""
    return pd.read_csv(SAMPLE_V1)


@pytest.fixture
def csv_factory(tmp_path: Path):
    """Записывает DataFrame в CSV внутри tmp_path (всегда с LF, как требует контракт)."""

    def write(frame: pd.DataFrame, name: str = "input.csv") -> Path:
        path = tmp_path / name
        frame.to_csv(path, index=False, lineterminator="\n")
        return path

    return write


@pytest.fixture
def contract_path() -> Path:
    return CONTRACT_PATH


@pytest.fixture
def trained_model_path(tmp_path: Path) -> Path:
    """Файл модели, обученной на v1 во временной папке (обучение занимает доли секунды)."""
    from mlops_team1.train import train_model

    path = tmp_path / "model.joblib"
    train_model(SAMPLE_V1, path)
    return path
