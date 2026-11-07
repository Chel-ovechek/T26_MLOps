from pathlib import Path

import pytest

from mlops_team1.validate_data import validate_dataset

ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "flights_sample_v1.csv"
CONTRACT = ROOT / "data" / "contract.json"


def test_validate_dataset_returns_report_for_valid_data() -> None:
    report = validate_dataset(FIXTURE, CONTRACT)
    assert report["passed"] is True
    assert report["rows"] == 24
    assert report["contract_version"] == "2.0.0"
    assert len(report["sha256"]) == 64
    assert report["split"] is not None


def test_validate_dataset_reports_failure_for_duplicate_row(tmp_path: Path) -> None:
    lines = FIXTURE.read_text(encoding="utf-8").splitlines()
    broken = tmp_path / "broken.csv"
    broken.write_text("\n".join([*lines, lines[-1]]) + "\n", encoding="utf-8")
    report = validate_dataset(broken, CONTRACT)
    assert report["passed"] is False
    assert report["split"] is None


def test_validate_dataset_raises_for_missing_file(tmp_path: Path) -> None:
    with pytest.raises(OSError):
        validate_dataset(tmp_path / "missing.csv", CONTRACT)
