# Соглашение об экспериментах MLflow (ЛР4)

Документ описывает, что записывает каждый запуск обучения. Источник правды — код: `src/mlops_team1/train_mlflow.py` и `src/mlops_team1/run_meta.py`. Если код и документ расходятся, прав код, а документ нужно исправить.

## Experiment и run

- **Experiment:** `mlops-tmo41-team1-flight-delay`. Слаг группы `tmo41` — предположение тимлида.
- **Run:** `rf-depth-<глубина>`, например `rf-depth-4`. Один run — одно обучение с одной конфигурацией.

## Теги

Каждый run получает 8 тегов.

| Тег | Смысл | Откуда значение |
|---|---|---|
| `git.commit` | Полный SHA коммита, на котором запущено обучение | `git_commit()` в `run_meta.py`: `git rev-parse HEAD`, без Git — `unknown` |
| `git.dirty` | Были ли незакоммиченные изменения | `git_dirty()`: `git status --porcelain`; `true`, `false` или `unknown` |
| `data.dvc_hash` | md5 версии данных в DVC | `read_dvc_md5()`: строка `md5` из `.dvc`-файла рядом с набором; без `.dvc` — `not-tracked`, без md5 — `unknown` |
| `data.sha256` | SHA-256 байтов файла данных | `hashlib.sha256` в `train_mlflow.py` |
| `data.contract_version` | Версия контракта, по которому проверен набор | поле `contract_version` отчёта `validate_dataset` |
| `split.policy` | Правило разбиения | константа `SPLIT_POLICY = "chronological-60-20-20"` |
| `team.code` | Команда | аргумент `--team-code`, по умолчанию `team-1` |
| `validation.status` | Статус run | константа `candidate`; итоговое решение фиксируется при сравнении конфигураций |

## Параметры, метрики, inputs и артефакты

- **Параметры:** `algorithm`, `n_estimators`, `max_depth`, `random_state`, `target_threshold_minutes` (15), `probability_threshold` (0.5), `split_policy` и границы частей `split_rows`, `split_train_rows`, `split_validation_rows`, `split_test_rows`, `split_train_end`, `split_validation_end`, `split_test_end`.
- **Метрики** (только validation): `validation_roc_auc`, `validation_precision`, `validation_recall`, `validation_f1`, `validation_positive_rate`.
- **Inputs:** `flight-delay-train` (context `training`) и `flight-delay-validation` (context `validation`).
- **Артефакты:** `model/model.joblib`, `reports/split_manifest.json`, `reports/metrics.json`, `reports/validation_report.json`, `reports/run_summary.md`, `environment/requirements.txt`.

Перед обучением набор проверяется контрактом (`validate_dataset`). Если проверка не прошла, run не создаётся.

## Как запустить

Установка: `python -m pip install -e ".[dev,tracking]"`.

Сервер запускается из отдельной папки **вне репозитория**, чтобы `mlflow.db` и `mlartifacts/` не попали в Git:

```powershell
mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlartifacts
```

Обучение (из корня репозитория, в другом окне терминала; данные — после `dvc pull`):

```powershell
$env:MLFLOW_TRACKING_URI="http://127.0.0.1:5000"
python -m mlops_team1.train_mlflow --data data/flights_sample.csv --contract data/contract.json --experiment mlops-tmo41-team1-flight-delay --max-depth 4
```

Команда печатает `MLflow run_id: <ID>`.

## Как загрузить модель

```powershell
python -m mlops_team1.model_io --run-id <ID>
python -m mlops_team1.model_io --path <путь к model.joblib> --dep-hour 10 --is-weekend 0
```

Модуль скачивает `model/model.joblib` из artifact указанного run (адрес сервера — из `MLFLOW_TRACKING_URI`), проверяет обязательные ключи файла и печатает `bundle_version=<версия>` и `probability=<вероятность опоздания>`. Неполный файл, неверный ввод (`--dep-hour` вне 0–23, `--is-weekend` не 0 или 1) или несуществующий run дают код 2.

Модель берётся из artifact конкретного run, а не из локальной папки: так известно, на каком коммите, данных и параметрах она получена.

## Что не коммитить

`mlflow.db`, `mlartifacts/`, `mlruns/`, файлы моделей (`*.joblib`, `*.pkl`), данные, `.venv`, `.env`. В Git из `reports/` попадает только `reports/experiments/`.

## Test закрыт

Модель и конфигурация выбираются только по validation. Test-период в выборе не участвует и используется один раз для итоговой оценки. В validation версии v2 всего 8 строк (7 опоздавших, 1 нет), поэтому ROC AUC меняется шагами по 1/7: разница метрик между конфигурациями почти ничего не доказывает.
