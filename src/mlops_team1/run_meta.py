"""Метаданные для связи MLflow run с Git, DVC и окружением.

Модуль не импортирует mlflow, поэтому его функции проверяются обычными тестами.
"""

from __future__ import annotations

import platform
import re
import subprocess
from collections.abc import Mapping
from importlib import metadata
from pathlib import Path

TRACKED_PACKAGES = ("numpy", "pandas", "scikit-learn", "joblib", "mlflow")
_MD5_LINE = re.compile(r"^\s*(?:-\s*)?md5:\s*([0-9a-f]{32})\s*$")


def _git(args: list[str]) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], text=True, encoding="utf-8", stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def git_commit() -> str:
    """Полный SHA текущего коммита или unknown, если Git недоступен."""
    return _git(["rev-parse", "HEAD"]) or "unknown"


def git_dirty() -> str:
    """true, если в рабочем дереве есть изменения; false; unknown, если Git недоступен."""
    status = _git(["status", "--porcelain"])
    if status is None:
        return "unknown"
    return "true" if status else "false"


def read_dvc_md5(data_path: Path) -> str:
    """md5 версии данных из файла .dvc рядом с набором.

    Понимает формат DVC 3 (строка `- md5: ...` внутри outs) и плоскую строку `md5: ...`.
    Возвращает not-tracked, если .dvc нет, и unknown, если md5 в нём не найден.
    """
    metafile = data_path.with_suffix(data_path.suffix + ".dvc")
    if not metafile.exists():
        return "not-tracked"
    for line in metafile.read_text(encoding="utf-8").splitlines():
        match = _MD5_LINE.match(line)
        if match:
            return match.group(1)
    return "unknown"


def environment_lines(packages: tuple[str, ...] = TRACKED_PACKAGES) -> list[str]:
    """Версии Python и ключевых библиотек в формате requirements.txt."""
    lines = [f"python=={platform.python_version()}"]
    for name in packages:
        try:
            lines.append(f"{name}=={metadata.version(name)}")
        except metadata.PackageNotFoundError:
            lines.append(f"{name}==not-installed")
    return lines


def build_run_summary(
    *,
    run_name: str,
    hypothesis: str,
    parameters: Mapping[str, object],
    metrics: Mapping[str, float],
    split: Mapping[str, object],
    tags: Mapping[str, str],
) -> str:
    """Краткий run_summary.md: гипотеза, конфигурация, validation-метрики, версии, вывод."""
    parameter_lines = [f"- {key}: {value}" for key, value in parameters.items()]
    metric_lines = [f"| {key} | {value:.4f} |" for key, value in metrics.items()]
    split_lines = [f"- {key}: {value}" for key, value in split.items()]
    tag_lines = [f"- {key}: {value}" for key, value in tags.items()]
    sections = [
        f"# Run {run_name}",
        f"## Гипотеза\n{hypothesis}",
        "## Конфигурация\n" + "\n".join(parameter_lines),
        "## Validation-метрики\n| Метрика | Значение |\n|---|---:|\n" + "\n".join(metric_lines),
        "## Границы частей\n" + "\n".join(split_lines),
        "## Версии\n" + "\n".join(tag_lines),
        (
            "## Вывод\n"
            "Метрики посчитаны только на validation-периоде, test в выборе не участвовал. "
            "Решение по запуску (candidate или rejected) фиксируется в "
            "reports/experiments/lr4-comparison.md после сравнения двух конфигураций."
        ),
    ]
    return "\n\n".join(sections) + "\n"
