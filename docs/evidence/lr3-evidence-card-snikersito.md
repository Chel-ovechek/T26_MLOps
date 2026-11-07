# Evidence card ЛР3: версия данных v2

## 1. Идентификация

- ФИО: Скворцов Никита
- Группа: Т.МО41
- Команда: 1
- GitHub: `snikersito`
- Роль: Data version owner (версия данных v2 и решение по ней)
- Контрольная точка: тег `lr3-v1`, коммит `b13cb1bc7c75e37052b6809831b93563c8b6063e`

## 2. Собственный вклад

PR: [#41](https://github.com/GundosCore/T26_MLOps/pull/41) (мой `main` → ветка `skvortsov`, Approve от Екатерины), затем [#42](https://github.com/GundosCore/T26_MLOps/pull/42) (`skvortsov` → `main`). Связанная задача: #36.

1. **Генератор v2** `src/mlops_team1/generate_v2.py`, коммит [`e0c1c56`](https://github.com/GundosCore/T26_MLOps/commit/e0c1c56). Генератор предложен тимлидом; я проверил его на своём компьютере и исправил ошибку Ruff DTZ007 (строки 48–52, `.replace(tzinfo=datetime.UTC)`), из-за которой `ruff check .` падал локально. Результат генерации от исправления не изменился. Ключевые места: `random.Random(seed)` (строка 28), `lineterminator="\n"` (строка 57).
2. **Тесты генератора** `tests/test_generate_v2.py`, коммит [`c01f340`](https://github.com/GundosCore/T26_MLOps/commit/c01f340): 6 тестов (строки 28–59): одинаковый seed даёт одинаковые байты, другой seed — другие строки, v1 остаётся началом файла, даты и выходные продолжаются верно, только LF, v2 проходит контракт.
3. **Решение по версии** `docs/reproducibility/v2-decision.md` (новый файл), коммит [`dea2883`](https://github.com/GundosCore/T26_MLOps/commit/dea2883): причина (строки 7–9), источник строк (11–22), изменение периода (24–31), влияние на разбиение до/после (33–45), ограничения (47–51), как воспроизвести (53–65).
4. **Проверка воспроизводимости на Windows.** Сгенерировал v2 у себя и получил тот же SHA-256 и размер, что тимлид на Linux. Это подтверждает, что файл не зависит от ОС.

## 3. Проверка коллег

- **PR [#44](https://github.com/GundosCore/T26_MLOps/pull/44) / [#39](https://github.com/GundosCore/T26_MLOps/pull/39), Владимир, README и документация по DVC.** Сверил таблицу версий с репозиторием и сам пересчитал md5 обоих файлов, они совпали с `.dvc`. Сверил числа v2 с `lr3-v2.json` и `v2-decision.md`. Нашёл, что пометки ссылаются на `v2-decision.md` до его появления в `main` (предложил порядок слияния) и что раздел 2 `data-card.md` расходится со строкой про DVC.
- **PR [#45](https://github.com/GundosCore/T26_MLOps/pull/45), Екатерина, протокол `lr3.md` и тест отказа DVC.** Установил DVC и запустил `tests/test_dvc_refusal.py` локально (без DVC он пропускается): 1 passed. Воспроизвёл сценарий 5.2 протокола, перестановка 4-й и 5-й строк даёт `FAIL sorted … line 5`, код 1, как написано. Сверил таблицу версий с `.dvc`-файлами и отчётами.

## 4. Воспроизведение

```powershell
git fetch upstream --tags
git checkout lr3-v1
python -m pip install -e ".[dev]"
python -m mlops_team1.generate_v2 --base tests/fixtures/flights_sample_v1.csv --out $env:TEMP\v2.csv --days 16 --seed 2026
Get-FileHash $env:TEMP\v2.csv -Algorithm SHA256
python -m mlops_team1.validate_data --data $env:TEMP\v2.csv --contract data/contract.json --report $env:TEMP\v2-check.json
git diff --no-index --stat tests/fixtures/flights_sample_v1.csv $env:TEMP\v2.csv
```

Мой результат (Windows, Python 3.12.10):

- SHA-256 v2: `bf35cf01db04fb31de810dc16009d643e6bf3be22c791faea7c00fdbc25cff08`, 780 байт;
- валидатор: 10 проверок OK, код 0, `rows: 40`, контракт 2.0.0;
- `git diff --stat`: `16 insertions(+)`, v1 не изменился;
- `ruff check .` — All checks passed, `pytest -q` — 31 passed.

| Версия | Строк | Период | train / validation / test | Доля `ArrDelay >= 15` |
|---|---|---|---|---|
| v1 | 24 | 2026-01-05 … 01-28 | 14 / 5 / 5 | 0.571 / 0.6 / 0.8 |
| v2 | 40 | 2026-01-05 … 02-13 | 24 / 8 / 8 | 0.625 / 0.875 / 0.75 |

## 5. Отрицательный сценарий

Сгенерировал «v2» с другим seed — так выглядит незаметная подмена данных:

```powershell
python -m mlops_team1.generate_v2 --base tests/fixtures/flights_sample_v1.csv --out $env:TEMP\v2-seed2027.csv --days 16 --seed 2027
Get-FileHash $env:TEMP\v2-seed2027.csv -Algorithm SHA256
python -m mlops_team1.validate_data --data $env:TEMP\v2-seed2027.csv --contract data/contract.json --report $env:TEMP\v2-seed2027.json
```

Результат: SHA-256 `3faa44b9…3976b` (781 байт) вместо `bf35cf01…cff08`; при этом валидатор проходит (код 0), а доля опоздавших в test меняется с 0.75 на 0.875. Вывод: контракт проверяет только форму данных и не замечает подмену. Её ловят SHA-256 и DVC hash. Ту же защиту проверяет тест `test_different_seed_gives_different_rows`.

## 6. Обоснование

- **Почему v2 генерирует скрипт с seed.** Строки, написанные руками, нельзя воспроизвести байт в байт, а скрипт с фиксированным seed даёт одинаковый файл и одинаковый хеш у любого участника и на любой ОС.
- **Почему v1 не меняется.** v1 закреплена в своём коммите (`a27bc82`) и в DVC, к ней всегда можно вернуться. v2 только дописывает строки в конец.
- **Влияние на разбиение.** Границы считаются по числу строк, поэтому весь v1 уходит в train, а новый test состоит только из февральских дней. Метрики на v1 и v2 сравнивать напрямую нельзя: test-периоды разные.
- **Ограничения.** Данные синтетические, признаки и цель независимы по построению. На v2 нельзя делать выводы о качестве модели.

## 7. Использование ИИ

Использовал нейросеть: она вела по шагам (синхронизация, коммиты, PR), подготовила черновик `v2-decision.md` и этой карточки, помогла найти и исправить DTZ007, подготовила тексты ревью. Сам: запускал генератор, валидатор, `ruff` и `pytest` на своём компьютере и проверил, что SHA-256 на Windows совпадает с ожидаемым; читал `generate_v2.py` и могу объяснить, зачем нужны seed, `lineterminator` и почему v1 не меняется.
