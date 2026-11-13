import hashlib
from pathlib import Path

import pandas as pd

from mlops_team1.model_io import load_bundle
from mlops_team1.validate_data import validate_dataset

REFERENCE_CSV = Path(__file__).parent / "fixtures" / "flights_sample_v1.csv"


def test_valid_frame_passes_contract_after_csv_roundtrip(
    valid_frame: pd.DataFrame, csv_factory, contract_path: Path
) -> None:
    assert len(valid_frame) == 24
    result = validate_dataset(csv_factory(valid_frame), contract_path)
    failed = [check["name"] for check in result["checks"] if not check["passed"]]
    assert result["passed"] is True, f"Корректный набор отклонён проверками: {failed}"


def test_csv_factory_writes_lf_only(valid_frame: pd.DataFrame, csv_factory) -> None:
    raw = csv_factory(valid_frame).read_bytes()
    assert b"\r" not in raw, "csv_factory записал CRLF: контракт и DVC-хеши требуют LF"


def test_changing_valid_frame_does_not_touch_reference_csv(
    valid_frame: pd.DataFrame,
) -> None:
    before = hashlib.sha256(REFERENCE_CSV.read_bytes()).hexdigest()
    valid_frame.loc[0, "DepHour"] = 99
    after = hashlib.sha256(REFERENCE_CSV.read_bytes()).hexdigest()
    assert before == after
    assert pd.read_csv(REFERENCE_CSV).loc[0, "DepHour"] != 99


def test_trained_model_path_gives_loadable_bundle(
    trained_model_path: Path, tmp_path: Path
) -> None:
    bundle = load_bundle(trained_model_path)
    assert bundle["features"] == ["DepHour", "IsWeekend"]
    assert (
        trained_model_path.parent == tmp_path
    ), "Модель должна лежать только в tmp_path"
