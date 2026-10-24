# mlops-team1

Учебный проект команды 1 по курсу MLOps. ЛР1: репозиторий и воспроизводимая среда. ЛР2: контракт данных и проверки качества.

## Требования

- Git
- Python **3.12** (проверьте: `python --version`)

## Установка

Клонируйте репозиторий и перейдите в его папку, затем создайте окружение.

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Linux или macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

После активации в начале строки терминала должно быть `(.venv)`.

## Проверки

```bash
python -m ruff check .
python -m pytest -q
```

Ожидаемый результат: `All checks passed!` и строка `passed` без `failed` и `error`.

## Запуск

```bash
python -c "import mlops_team1; print(mlops_team1.ping())"
```

Ожидаемый вывод: `pong`.

## Данные и контракт (ЛР2)

- `data/contract.json` — машинный контракт данных: поля, типы, диапазоны, версия.
- `data/flights_sample.csv` — учебный образец (24 синтетические строки), нужен для smoke-проверок.
- `docs/data-card.md` — карточка набора данных для человека.

### Проверка данных

```bash
python -m mlops_team1.validate_data --data data/flights_sample.csv --contract data/contract.json --report reports/validation/lr2.json
```

Код завершения 0 означает, что данные соответствуют контракту. Любое нарушение даёт ненулевой код.

### Версии контракта

Версия хранится в поле `contract_version` и меняется осознанно:

- patch: исправление описания без изменения проверки;
- minor: совместимое добавление необязательного поля;
- major: удаление или переименование поля, изменение типа или смысла.

### Отчёты

Отчёты в `reports/` создаются командой выше и в Git не хранятся (каталог указан в `.gitignore`). Отчёт воспроизводится одной командой, а в CI сохраняется как артефакт.

## Структура

- `src/mlops_team1/` — код проекта
- `tests/` — тесты
- `.github/workflows/ci.yml` — автоматические проверки (CI)
- `data/` — контракт и учебный образец; остальное содержимое в Git не добавляется (см. `.gitignore`)
- `reports/` — отчёты проверок (создаются командой, в Git не хранятся)
- `docs/` — документация
