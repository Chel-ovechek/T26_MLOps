from datetime import date, timedelta
from pathlib import Path

import joblib

from mlops_team1.train import train_model
from mlops_team1.validate_data import split_cuts, validate_dataset

ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "data" / "contract.json"


def test_split_cuts_for_one_row_per_day_follows_plain_fractions() -> None:
    days = [date(2026, 1, 5) + timedelta(days=i) for i in range(24)]
    assert split_cuts(days) == (14, 19)


def test_split_cuts_moves_boundary_to_end_of_day() -> None:
    days = [date(2026, 1, 5) + timedelta(days=i // 4) for i in range(24)]
    assert split_cuts(days) == (16, 20)


def test_validator_and_training_use_the_same_boundaries(
    four_flights_per_day_csv: Path, tmp_path: Path
) -> None:
    data = four_flights_per_day_csv
    report = validate_dataset(data, CONTRACT)
    assert report["passed"] is True
    parts = report["split"]["parts"]
    assert [parts[name]["rows"] for name in ("train", "validation", "test")] == [16, 4, 4]

    model = tmp_path / "model.joblib"
    train_model(data, model, n_estimators=5, max_depth=2)
    assert joblib.load(model)["split"] == {"train_end": 16, "validation_end": 20}
