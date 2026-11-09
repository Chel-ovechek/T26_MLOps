from pathlib import Path

import joblib
import pandas as pd
import pytest

from mlops_team1.train import train_model

FIXTURE = Path(__file__).parents[1] / "tests" / "fixtures" / "flights_sample_v1.csv"


def test_train_creates_versioned_bundle(tmp_path: Path) -> None:
    model_path = tmp_path / "model.joblib"
    score = train_model(FIXTURE, model_path)
    bundle = joblib.load(model_path)
    assert set(bundle) == {
        "model",
        "features",
        "version",
        "split",
        "validation_roc_auc",
        "validation_metrics",
        "parameters",
    }
    assert 0.0 <= score <= 1.0
    assert bundle["features"] == ["DepHour", "IsWeekend"]
    assert bundle["version"] == "0.2.0"
    assert bundle["split"] == {"train_end": 14, "validation_end": 19}
    assert 0.0 <= bundle["validation_roc_auc"] <= 1.0
    assert set(bundle["validation_metrics"]) == {"roc_auc", "precision", "recall", "f1"}
    assert score == bundle["validation_roc_auc"] == bundle["validation_metrics"]["roc_auc"]
    assert bundle["parameters"] == {
        "n_estimators": 80,
        "max_depth": 4,
        "random_state": 42,
    }


@pytest.mark.parametrize("multiple_flights", [False, True], ids=["one-per-day", "four-per-day"])
def test_train_split_has_ordered_disjoint_dates(
    tmp_path: Path, four_flights_per_day_csv: Path, multiple_flights: bool
) -> None:
    data_path = four_flights_per_day_csv if multiple_flights else FIXTURE
    model_path = tmp_path / "model.joblib"
    train_model(data_path, model_path)
    split = joblib.load(model_path)["split"]
    assert split == (
        {"train_end": 16, "validation_end": 20}
        if multiple_flights
        else {"train_end": 14, "validation_end": 19}
    )
    data = pd.read_csv(data_path, parse_dates=["FlightDate"])
    data = data.sort_values("FlightDate", kind="stable").reset_index(drop=True)
    train = data.iloc[: split["train_end"]]
    validation = data.iloc[split["train_end"] : split["validation_end"]]
    test = data.iloc[split["validation_end"] :]
    assert train["FlightDate"].max() < validation["FlightDate"].min()
    assert validation["FlightDate"].max() < test["FlightDate"].min()
    train_dates, validation_dates, test_dates = (
        set(part["FlightDate"]) for part in (train, validation, test)
    )
    assert train_dates.isdisjoint(validation_dates)
    assert train_dates.isdisjoint(test_dates)
    assert validation_dates.isdisjoint(test_dates)


@pytest.mark.parametrize(
    ("case", "message"),
    [
        ("missing_feature", "Отсутствуют обязательные столбцы"),
        ("missing_delay", "пропуски"),
        ("single_class", "нужны примеры обоих классов"),
        ("single_class_validation", "В каждой хронологической части"),
    ],
)
def test_train_rejects_invalid_data(tmp_path: Path, case: str, message: str) -> None:
    data = pd.read_csv(FIXTURE)
    if case == "missing_feature":
        data = data.drop(columns="DepHour")
    elif case == "missing_delay":
        data.loc[3, "ArrDelay"] = float("nan")
    elif case == "single_class":
        data["ArrDelay"] = 5
    elif case == "single_class_validation":
        data.loc[14:18, "ArrDelay"] = 30
    data_path = tmp_path / "invalid.csv"
    data.to_csv(data_path, index=False)
    with pytest.raises(ValueError, match=message):
        train_model(data_path, tmp_path / "model.joblib")
