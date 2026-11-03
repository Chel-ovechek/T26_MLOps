import os
import sys
import subprocess
import shutil
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    not shutil.which("dvc"),
    reason="DVC is not installed, skipping DVC refusal test"
)

def test_dvc_status_detects_modification(tmp_path: Path):
    """
    Сценарий: файл изменён вручную без dvc add.
    Ожидание: dvc status --quiet возвращает код 1 и содержит 'modified'.
    """
    env = os.environ.copy()
    env["DVC_NO_ANALYTICS"] = "1"
    
    subprocess.run(
        [sys.executable, "-m", "dvc", "init", "--no-scm"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
        check=True
    )
    
    fixture_path = Path(__file__).parent / "fixtures" / "flights_sample_v1.csv"
    target_csv = tmp_path / "flights_sample.csv"
    shutil.copy(fixture_path, target_csv)
    
    subprocess.run(
        [sys.executable, "-m", "dvc", "add", str(target_csv)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env,
        check=True
    )
    
    result_clean = subprocess.run(
        [sys.executable, "-m", "dvc", "status", "--quiet"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env
    )
    assert result_clean.returncode == 0, f"Expected clean status (0), got {result_clean.returncode}"
    
    with open(target_csv, "a") as f:
        f.write("2026-01-29,9,0,10\n")
    
    result_modified = subprocess.run(
        [sys.executable, "-m", "dvc", "status", "--quiet"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=env
    )
    
    assert result_modified.returncode == 1, f"Expected modified status (1), got {result_modified.returncode}"
    assert "modified" in result_modified.stdout.lower() or "modified" in result_modified.stderr.lower(), \
        "Expected 'modified' in dvc status output"