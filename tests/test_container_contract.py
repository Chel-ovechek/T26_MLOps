"""Статические контрактные тесты контейнера (ЛР6).

Тесты читают текст Dockerfile, compose.yaml и .dockerignore и не запускают Docker.
Они доказывают, что в файлах записано нужное, но не доказывают, что образ
собирается и что контейнер работает.
"""

import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def dockerfile_text() -> str:
    return (ROOT / "Dockerfile").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def compose_text() -> str:
    return (ROOT / "compose.yaml").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def compose_service(compose_text: str) -> dict:
    data = yaml.safe_load(compose_text)
    services = data.get("services")
    assert services, "в compose.yaml нет раздела services"
    return next(iter(services.values()))


@pytest.fixture(scope="module")
def dockerignore_lines() -> set[str]:
    raw = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    lines = (line.strip() for line in raw)
    return {line.strip("/") for line in lines if line and not line.startswith("#")}


def _as_list(value: object) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def test_dockerfile_has_quality_and_runtime_stages(dockerfile_text: str) -> None:
    for stage in ("quality", "runtime"):
        pattern = rf"^FROM python:3\.12-slim AS {stage}\b"
        assert re.search(pattern, dockerfile_text, re.MULTILINE), (
            f"в Dockerfile нет строки 'FROM python:3.12-slim AS {stage}'"
        )


def test_quality_gate_runs_ruff_pytest_validation_and_training(dockerfile_text: str) -> None:
    required = (
        "python -m ruff check",
        "python -m pytest -q",
        "python -m mlops_team1.validate_data",
        "python -m mlops_team1.train",
    )
    missing = [command for command in required if command not in dockerfile_text]
    assert not missing, f"в Dockerfile не найдены команды quality-стадии: {missing}"


def test_runtime_copies_model_from_quality_stage(dockerfile_text: str) -> None:
    lines = [
        line
        for line in dockerfile_text.splitlines()
        if line.lstrip().startswith("COPY --from=quality")
    ]
    assert lines, "в Dockerfile нет строки 'COPY --from=quality'"
    assert any("/app/models/model.joblib" in line for line in lines), (
        f"ни одна строка 'COPY --from=quality' не копирует /app/models/model.joblib: {lines}"
    )


def test_runtime_runs_as_non_root_with_explicit_ids(dockerfile_text: str) -> None:
    match = re.search(r"^USER\s+(\d+):(\d+)\s*$", dockerfile_text, re.MULTILINE)
    assert match, "в Dockerfile нет строки 'USER <uid>:<gid>' с числовыми значениями"
    uid, gid = int(match.group(1)), int(match.group(2))
    assert uid > 0, f"uid должен быть больше 0, найдено {uid}"
    assert gid > 0, f"gid должен быть больше 0, найдено {gid}"


def test_dockerfile_healthcheck_uses_readyz_without_curl(dockerfile_text: str) -> None:
    assert "HEALTHCHECK" in dockerfile_text, "в Dockerfile нет инструкции HEALTHCHECK"
    after_healthcheck = dockerfile_text.split("HEALTHCHECK", 1)[1]
    assert "/readyz" in after_healthcheck, "после HEALTHCHECK не найден путь /readyz"
    assert "curl" not in dockerfile_text, "в Dockerfile найден curl, его нет в slim-образе"


def test_cmd_uses_exec_form_with_port_8080(dockerfile_text: str) -> None:
    match = re.search(r"^CMD\s+(\[.*\])\s*$", dockerfile_text, re.MULTILINE)
    assert match, "в Dockerfile нет CMD в JSON-форме одной строкой"
    args = json.loads(match.group(1))
    assert "mlops_team1.api:app" in args, f"в CMD нет mlops_team1.api:app: {args}"
    assert "8080" in args, f'в CMD нет порта "8080": {args}'
    assert re.search(r"^EXPOSE\s+8080\b", dockerfile_text, re.MULTILINE), (
        "в Dockerfile нет строки 'EXPOSE 8080'"
    )


def test_no_latest_tag_anywhere(dockerfile_text: str, compose_text: str) -> None:
    assert ":latest" not in dockerfile_text, "в Dockerfile найден тег :latest"
    assert ":latest" not in compose_text, "в compose.yaml найден тег :latest"


def test_compose_has_no_version_field(compose_text: str) -> None:
    assert not re.search(r"^version:", compose_text, re.MULTILINE), (
        "в compose.yaml найдено устаревшее поле version:"
    )


def test_compose_runtime_restrictions(compose_service: dict) -> None:
    assert compose_service.get("read_only") is True, (
        f"read_only должен быть true, найдено {compose_service.get('read_only')!r}"
    )
    tmpfs = [str(item) for item in _as_list(compose_service.get("tmpfs"))]
    assert any("/tmp" in item for item in tmpfs), f"в tmpfs нет пути /tmp: {tmpfs}"
    assert compose_service.get("cap_drop") == ["ALL"], (
        f"cap_drop должен быть ['ALL'], найдено {compose_service.get('cap_drop')!r}"
    )
    security_opt = _as_list(compose_service.get("security_opt"))
    assert "no-new-privileges:true" in security_opt, (
        f"в security_opt нет no-new-privileges:true: {security_opt}"
    )


def test_compose_port_is_configurable_and_healthcheck_uses_readyz(compose_service: dict) -> None:
    ports = [str(item) for item in _as_list(compose_service.get("ports"))]
    assert any("${APP_PORT:-8080}" in item for item in ports), (
        f"в ports нет ${{APP_PORT:-8080}}: {ports}"
    )
    healthcheck = compose_service.get("healthcheck") or {}
    assert "/readyz" in str(healthcheck.get("test")), (
        f"в healthcheck.test нет /readyz: {healthcheck.get('test')!r}"
    )


def test_compose_environment_has_no_secrets(compose_service: dict) -> None:
    environment = compose_service.get("environment") or {}
    if isinstance(environment, dict):
        names = [str(name) for name in environment]
    else:
        names = [str(item).split("=", 1)[0] for item in environment]
    forbidden = ("PASSWORD", "SECRET", "TOKEN", "KEY")
    suspicious = [name for name in names if any(word in name.upper() for word in forbidden)]
    assert not suspicious, f"в environment есть похожие на секреты имена: {suspicious}"


def test_dockerignore_excludes_sensitive_and_generated_content(
    dockerignore_lines: set[str],
) -> None:
    must_exclude = (".git", ".env", "models", "reports", "mlruns", "mlartifacts", "docs")
    missing = [name for name in must_exclude if name not in dockerignore_lines]
    assert not missing, f"в .dockerignore не найдены строки: {missing}"
    must_keep = ("src", "tests", "data")
    excluded = [name for name in must_keep if name in dockerignore_lines]
    assert not excluded, f"в .dockerignore исключены нужные для сборки каталоги: {excluded}"
