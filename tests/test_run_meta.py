import re
from pathlib import Path

from mlops_team1.run_meta import (
    build_run_summary,
    environment_lines,
    git_commit,
    git_dirty,
    read_dvc_md5,
)

ROOT = Path(__file__).parents[1]
MD5 = "12e7b5a02885ff28f6560bd895a1330e"


def test_read_dvc_md5_supports_dvc3_format(tmp_path: Path) -> None:
    data = tmp_path / "data.csv"
    (tmp_path / "data.csv.dvc").write_text(
        f"outs:\n- md5: {MD5}\n  size: 780\n  hash: md5\n  path: data.csv\n", encoding="utf-8"
    )
    assert read_dvc_md5(data) == MD5


def test_read_dvc_md5_supports_flat_format(tmp_path: Path) -> None:
    data = tmp_path / "data.csv"
    (tmp_path / "data.csv.dvc").write_text(f"md5: {MD5}\n", encoding="utf-8")
    assert read_dvc_md5(data) == MD5


def test_read_dvc_md5_without_metafile_is_not_tracked(tmp_path: Path) -> None:
    assert read_dvc_md5(tmp_path / "data.csv") == "not-tracked"


def test_read_dvc_md5_without_hash_is_unknown(tmp_path: Path) -> None:
    data = tmp_path / "data.csv"
    (tmp_path / "data.csv.dvc").write_text("outs:\n- path: data.csv\n", encoding="utf-8")
    assert read_dvc_md5(data) == "unknown"


def test_repository_dvc_file_gives_real_hash() -> None:
    value = read_dvc_md5(ROOT / "data" / "flights_sample.csv")
    assert re.fullmatch(r"[0-9a-f]{32}", value)


def test_git_helpers_return_expected_shapes() -> None:
    assert re.fullmatch(r"[0-9a-f]{40}|unknown", git_commit())
    assert git_dirty() in {"true", "false", "unknown"}


def test_environment_lines_list_python_and_libraries() -> None:
    lines = environment_lines()
    assert lines[0].startswith("python==")
    assert any(line.startswith("pandas==") for line in lines)
    assert environment_lines(("no-such-package-xyz",))[1] == "no-such-package-xyz==not-installed"


def test_run_summary_contains_hypothesis_metrics_and_validation_only_note() -> None:
    text = build_run_summary(
        run_name="rf-depth-3",
        hypothesis="Глубина 3 достаточна",
        parameters={"max_depth": 3},
        metrics={"validation_roc_auc": 0.5},
        split={"train_rows": 14},
        tags={"git.commit": "abc"},
    )
    assert text.startswith("# Run rf-depth-3")
    assert "Глубина 3 достаточна" in text
    assert "| validation_roc_auc | 0.5000 |" in text
    assert "test в выборе не участвовал" in text
