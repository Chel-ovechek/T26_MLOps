# Таблица рисков контейнера (ЛР6)

Для каждого риска указаны ограничение, которое его снижает, и проверка. Статические проверки читают текст `Dockerfile`, `compose.yaml` и `.dockerignore` (файл `tests/test_container_contract.py`, Docker не нужен). Динамические проверки выполняются командой Docker на собранном образе или запущенном контейнере.

| № | Риск | Ограничение | Проверка |
|---|---|---|---|
| 1 | Процесс в контейнере работает от root, и уязвимость даёт полный доступ внутри контейнера | `USER 10001:10001` в стадии runtime | Статическая: `tests/test_container_contract.py::test_runtime_runs_as_non_root_with_explicit_ids`. Динамическая: `docker image inspect mlops-flight-delay:<тег> --format '{{.Config.User}}'` (ожидается `10001:10001`) |
| 2 | Процесс пишет в файловую систему контейнера и меняет образ во время работы | `read_only: true`, запись только в `tmpfs` на `/tmp` | Статическая: `tests/test_container_contract.py::test_compose_runtime_restrictions`. Динамическая: `docker compose exec <сервис> python -c "open('/app/x', 'w')"` (ожидается ошибка «Read-only file system») |
| 3 | Лишние привилегии Linux у процесса | `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]` | Статическая: `tests/test_container_contract.py::test_compose_runtime_restrictions`. Динамическая: `docker inspect <контейнер> --format '{{json .HostConfig.CapDrop}}'` (ожидается `["ALL"]`) |
| 4 | Образ собирается из непредсказуемой версии (`latest`), и результат меняется без изменений в коде | Явный тег образа и базовый образ `python:3.12-slim`, тега `latest` нет | Статическая: `tests/test_container_contract.py::test_no_latest_tag_anywhere`, `tests/test_container_contract.py::test_dockerfile_has_quality_and_runtime_stages` |
| 5 | Секреты и лишние файлы (`.env`, данные, модели, история Git) попадают в образ | `.dockerignore` исключает `.git`, `.env`, `models`, `reports`, `mlruns`, `mlartifacts`, `docs`; в `environment` нет секретов | Статическая: `tests/test_container_contract.py::test_dockerignore_excludes_sensitive_and_generated_content`, `tests/test_container_contract.py::test_compose_environment_has_no_secrets`. Динамическая: `docker run --rm --entrypoint python mlops-flight-delay:<тег> -c "from pathlib import Path; print([p.name for p in Path('/app').iterdir()])"` (ожидается `['models']`) |
| 6 | Контейнер запущен, но сервис не готов (нет модели), и оркестратор считает его рабочим | `HEALTHCHECK` и healthcheck в Compose обращаются к `/readyz` без `curl` | Статическая: `tests/test_container_contract.py::test_dockerfile_healthcheck_uses_readyz_without_curl`, `tests/test_container_contract.py::test_compose_port_is_configurable_and_healthcheck_uses_readyz`. Динамическая: `docker compose ps` (ожидается `healthy`) |
| 7 | Образ собран без проверки качества: код с ошибками или необученная модель попадает в runtime | Стадия `quality` запускает ruff, pytest, валидацию данных и обучение; runtime копирует модель только из неё | Статическая: `tests/test_container_contract.py::test_quality_gate_runs_ruff_pytest_validation_and_training`, `tests/test_container_contract.py::test_runtime_copies_model_from_quality_stage`. Динамическая: `docker build --tag mlops-flight-delay:<тег> .` (сборка падает, если стадия `quality` не прошла) |
| 8 | Порт 8080 на хосте занят, и контейнер не стартует; порт, зашитый в образ, нельзя поменять без пересборки | Порт хоста задаётся переменной `APP_PORT`, порт контейнера остаётся 8080 | Статическая: `tests/test_container_contract.py::test_compose_port_is_configurable_and_healthcheck_uses_readyz`. Динамическая: `docker compose up --detach` при занятом порту (ожидается ошибка привязки), затем `$env:APP_PORT = "8081"` |
| 9 | Процесс не получает сигнал остановки (shell-форма `CMD`), а Compose печатает предупреждение об устаревшем поле `version` | `CMD` в exec-форме с `mlops_team1.api:app` и портом 8080, в `compose.yaml` нет `version` | Статическая: `tests/test_container_contract.py::test_cmd_uses_exec_form_with_port_8080`, `tests/test_container_contract.py::test_compose_has_no_version_field`. Динамическая: `docker compose down` (контейнер останавливается без ожидания таймаута) |

## Что тесты не доказывают

Статические тесты читают текст файлов, а не образ. Поэтому они не доказывают, что:

- образ действительно собирается: ошибка в команде `RUN` или опечатка в пути не видна в тексте;
- контейнер действительно становится `healthy`: строка с `/readyz` в `HEALTHCHECK` ещё не значит, что сервис отвечает;
- модель в образе загружается и `/readyz` отвечает 200: тест видит строку `COPY --from=quality`, но не содержимое `/app/models`;
- внутри образа нет лишних файлов: `.dockerignore` проверяется по строкам, а не по результату сборки;
- ограничения Compose применяются: `read_only: true` записан в файле, но запись вне `/tmp` блокируется только при запуске контейнера, это видно командой `docker compose exec`;
- пользователь `10001:10001` имеет доступ к нужным файлам.

Эти свойства проверяют динамические команды из таблицы.