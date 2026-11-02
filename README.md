# mlops-team1

Учебный проект команды 1 по курсу MLOps. ЛР1: репозиторий и воспроизводимая среда. ЛР2: контракт данных и проверки качества. ЛР3: версионирование данных (DVC).

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
- `data/flights_sample.csv` — учебный образец (24 синтетические строки) под управлением DVC: в Git лежит `data/flights_sample.csv.dvc`, сам файл достаётся командой `dvc pull`. Копия версии v1 для тестов и CI: `tests/fixtures/flights_sample_v1.csv`.
- `docs/data-card.md` — карточка набора данных для человека.

Получение данных: `python -m pip install "dvc>=3,<4"`, затем `dvc pull`. Каталог `dvc-storage` должен лежать рядом с папкой репозитория; иначе задайте путь командой `dvc remote modify --local course-local <путь>`.

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

Версия 2.0.0: контракт приведён к курсовой версии. Добавлены метаданные description, owner и source; правила команды sorted и rationale сохранены.

### Отчёты

Отчёты в `reports/` создаются командой выше и в Git не хранятся (каталог указан в `.gitignore`). Отчёт воспроизводится одной командой, а в CI сохраняется как артефакт.

## Отклонения от задания (ЛР3)

- **Имя пакета.** В методичке команды запускаются через `mlops_flight_delay`, в проекте пакет называется `mlops_team1`.
- **Копия v1 для тестов.** CSV версии v1 лежит в Git как `tests/fixtures/flights_sample_v1.csv`. Тесты и шаг валидатора в CI используют её, потому что CI не имеет доступа к локальному remote.
- **Отчёт v1.** Лежит в `docs/reproducibility/validation/lr3-v1.json`, а не в `reports/`, потому что `.gitignore` игнорирует каталог `reports/`.
- **`.gitignore`.** Вместо `data/*` с исключениями игнорируются `data/*.csv` и `data/*.parquet`, иначе Git не видит `.dvc`-файл набора.
- **Окончания строк.** CSV хранится с LF (`.gitattributes`). При переносе на Windows файл был с CRLF, его исправили до `dvc add`, чтобы хэш не зависел от ОС.
- **Remote.** В общей конфигурации указан относительный путь `../dvc-storage` без секретов. Если каталог лежит в другом месте, путь задаётся командой `dvc remote modify --local course-local <путь>` (хранится в `.dvc/config.local`, в Git не попадает).
- **Имя отчёта в CI.** Шаг CI пишет отчёт в `reports/validation/lr2.json`, имя сохранено со времён ЛР2.

## Структура

- `src/mlops_team1/` — код проекта
- `tests/` — тесты
- `.github/workflows/ci.yml` — автоматические проверки (CI)
- `data/` — контракт и `.dvc`-метаданные набора; сами CSV в Git не добавляются, их версионирует DVC (см. `.gitignore`)
- `reports/` — отчёты проверок (создаются командой, в Git не хранятся)
- `docs/` — документация
