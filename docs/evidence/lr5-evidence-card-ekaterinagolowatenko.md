# ЛР5. Индивидуальная карточка Екатерины Головатенко

## Студент, роль и задача

- ФИО: Головатенко Екатерина Васильевна.
- Группа: Т.МО41; команда №1 (`team-1`).
- GitHub: `ekaterinagolowatenko`.
- Роль в ЛР5: **Data test engineer** — проверки данных и контракта.
  В ЛР4 роль **Evaluation engineer** охватывала метрики и обучение;
  здесь личный вклад относится к слою `data` и границам входных значений.
- Задача: [issue #67](https://github.com/GundosCore/T26_MLOps/issues/67).

Карточка подготовлена по [разделу 16 исходного задания](https://github.com/Irina-64/T26_MLOps/blob/270431d9c7f806a8804fa5402aaf20029228a19b/Лабораторные%20работы/ЛР5/ЛР5%20Тестирование%20данных%20модели%20и%20pipeline.md#16-индивидуальная-сдача-участника-команды).

**Личный критерий приёмки:** семь параметризованных нарушений контракта
отклоняются с ожидаемым именем проверки; пять допустимых значений принимаются.
Используются общие fixtures, эталонный CSV не изменяется. При временном
разрешении `DepHour=24` заранее названный тест падает, после восстановления
контракта проходит. Личный PR должен пройти review другого участника;
pytest должен быть зелёным, Ruff — без замечаний.

Командные критерии issue #67: слои data/evaluation/model/api/pipeline,
общие fixtures, минимум три негативных сценария, интеграционный smoke,
JUnit XML, отрицательный фрагмент, таблица рисков и тег `lr5-v1`.
Их выполнение не приписывается целиком личному вкладу.

## Артефакты и версии

- [PR #70 и diff](https://github.com/GundosCore/T26_MLOps/pull/70/files):
  один новый файл `tests/test_data_negative.py`, 66 строк; слит 14.11.2026
  в `golovatenko`.
- Личный коммит: [`abb652bc1a8876098f3bbaf0eb7991236c377d70`](https://github.com/ekaterinagolowatenko/T26_MLOps/commit/abb652bc1a8876098f3bbaf0eb7991236c377d70).
- Merge PR #70: [`36cdc1201c9b7f31afededd276b1d58acd86fa4f`](https://github.com/GundosCore/T26_MLOps/commit/36cdc1201c9b7f31afededd276b1d58acd86fa4f).
- Командный [тег `lr5-v1`](https://github.com/GundosCore/T26_MLOps/tree/lr5-v1)
  разрешается в commit `c5156f8a154c3b63c1f9f80257ea7008c4317198`.
  Объект аннотированного тега: `a6c50bc9c855d60369127c9f60335781f59c4cc2`.
- [Личные тесты в принятой командной версии](https://github.com/GundosCore/T26_MLOps/blob/c5156f8a154c3b63c1f9f80257ea7008c4317198/tests/test_data_negative.py).
- [Общие fixtures](https://github.com/GundosCore/T26_MLOps/blob/c5156f8a154c3b63c1f9f80257ea7008c4317198/tests/conftest.py):
  `valid_frame` читает новую копию Git-эталона v1 (24 строки), `csv_factory`
  пишет CSV с LF в `tmp_path`, `contract_path` указывает на `data/contract.json`.
  Эти fixtures — командная инфраструктура, не личная разработка PR #70.

## Личный тест, риск и ожидаемые сигналы

Основной node ID:
`tests/test_data_negative.py::test_value_outside_contract_is_rejected[dephour-24-above-max]`.

| Негативный case | Вход | Ожидаемая проверка с `passed=False` |
|---|---|---|
| `dephour-24-above-max` | `DepHour=24` | `ranges` |
| `dephour-minus1-below-min` | `DepHour=-1` | `ranges` |
| `dephour-fractional` | `DepHour=10.5` | `types` |
| `isweekend-2` | `IsWeekend=2` | `allowed_values` |
| `arrdelay-1441-above-max` | `ArrDelay=1441` | `ranges` |
| `date-feb-30` | `FlightDate="2026-02-30"` | `types` |
| `dephour-empty` | `DepHour=""` | `no_missing_values` |

Во всех семи случаях дополнительно проверяется `result["passed"] is False`.
Пять позитивных cases функции `test_boundary_value_is_accepted` принимают
`DepHour=0/23`, `IsWeekend=1`, `ArrDelay=-180/1440`.

Контролируемый риск: ослабление контракта пропускает несуществующий час 24.
Пара «23 принимается, 24 отклоняется» фиксирует точную границу. Проверка
`DepHour=25` этого дефекта не заменяет: 25 остаётся за максимумом 24.
Модельные тесты не устанавливают допустимый диапазон входного часа.

Минимальное изменение входа — одна ячейка строки 0 в копии корректной
таблицы. `astype(object)` позволяет записать значение другого типа;
исходный CSV остаётся неизменным. Assert выводит столбец, значение и
список упавших проверок. Ограничение: проверяется наличие нужной проверки
среди отказавших, но не единственность отказа. Конечные cases также не
доказывают корректность валидатора на всех возможных входах.

## Defect injection и диагностика

Временный дефект: в `data/contract.json`, `columns.DepHour.maximum`,
значение 23 заменено на 24. Ожидаемый и фактический failing test совпадают
с основным node ID выше.

Историческое [review Никиты Скворцова (`snikersito`), APPROVED](https://github.com/GundosCore/T26_MLOps/pull/70#pullrequestreview-5905424020)
подтверждает `1 failed, 11 passed` для файла с дефектом и `12 passed`
после восстановления. Оригинальный личный терминальный лог в доступных
материалах не найден; ниже приведён **новый запуск Codex 16.11.2026**
на командном commit `c5156f8a154c3b63c1f9f80257ea7008c4317198`,
а не реконструкция исторического traceback:

```text
>       assert result["passed"] is False, f"Invalid value was accepted: {diagnostic}"
E       AssertionError: Invalid value was accepted: DepHour=24; failed checks: []
E       assert True is False
tests\test_data_negative.py:38: AssertionError
FAILED tests/test_data_negative.py::test_value_outside_contract_is_rejected[dephour-24-above-max]
1 failed in 0.26s
```

Причина: ослабленный контракт считает 24 допустимым, валидатор возвращает
`passed=True`, список отказов пуст; тест обнаруживает нарушение ожидаемой
границы. После эксперимента исходные байты контракта восстановлены в
`finally`; `git diff --exit-code -- data/contract.json` завершился успешно,
повторный запуск файла дал `12 passed in 0.13s`. Дефект в карточку как
изменение контракта и в принимаемый код не входит.

Командный [отрицательный отчёт](https://github.com/GundosCore/T26_MLOps/blob/c5156f8a154c3b63c1f9f80257ea7008c4317198/reports/tests/lr5-fail-fragment.txt)
посвящён другому дефекту — отсутствию `version` в bundle. Это не личный
traceback проверки `DepHour`.

## Воспроизведение и результаты

Команды из корня нужной версии проекта, Python 3.12 с зависимостями
`.[dev,tracking]`:

```powershell
python -m pytest -q "tests/test_data_negative.py::test_value_outside_contract_is_rejected[dephour-24-above-max]"
python -m pytest -q tests/test_data_negative.py
python -m pytest -q -m data
python -m pytest -q
python -m ruff check .
```

Для defect injection временно изменить только максимум `DepHour`, выполнить
команду одного теста, затем восстановить `data/contract.json` и повторить
проверку. В чистой отдельной рабочей копии восстановление можно выполнить
командой `git restore -- data/contract.json`.

| Источник и версия | Результат |
|---|---|
| Описание PR #70, исторические локальные проверки | файл: `12 passed`; слой data: `44 passed`; полный набор: `88 passed, 1 skipped` (нет DVC); Ruff без замечаний |
| Review PR #70 | файл: `12 passed`; data: `44 passed`; Ruff чистый; с дефектом: `1 failed, 11 passed`; после восстановления: `12 passed` |
| Командный JUnit XML в `lr5-v1` | `tests=115`, `failures=0`, `errors=0`, `skipped=0`; timestamp `2026-11-15T12:01:40.392788+03:00` |
| Codex, 16.11.2026, командный commit `c5156f8…` | файл до дефекта: `12 passed`; один тест с дефектом: `1 failed`; после восстановления файл: `12 passed` |

Число 88 относится к этапу PR #70, а не к финальному командному набору.
Точный SHA исторического локального прогона отдельно в описании не указан.
При подготовке карточки полный набор и Ruff повторно не запускались;
новые результаты выше получены агентом, а не объявлены самостоятельными
запусками студентки. Для изоляции агент использовал Python из существующей
`.venv`, `PYTHONPATH=<worktree>/src` и дополнительные аргументы pytest
`-p no:cacheprovider --basetemp=../.lr5-pytest-tmp`.

Командные подтверждения:
[JUnit XML `reports/tests/lr5-pass.xml`](https://github.com/GundosCore/T26_MLOps/blob/c5156f8a154c3b63c1f9f80257ea7008c4317198/reports/tests/lr5-pass.xml),
[таблица рисков](https://github.com/GundosCore/T26_MLOps/blob/c5156f8a154c3b63c1f9f80257ea7008c4317198/docs/testing/lr5-risk-table.md),
[итог issue #67](https://github.com/GundosCore/T26_MLOps/issues/67#issuecomment-6892481149).
Отметка CI в описании PR #70 содержит оговорку об ожидании результата;
сама по себе она не является ссылкой на успешный Actions run.

## Использование ИИ

Использовались ChatGPT и Codex (OpenAI): обсуждение ЛР5, помощь в подготовке
тестовой части и карточки, сопоставление требований с кодом и источниками.
При подготовке этой карточки Codex прочитал раздел 16, issue, PR и review,
сверил SHA и командные отчёты, выполнил описанный повторный эксперимент.

Подтверждённые проверки перечислены с указанием исполнителя и источника:
исторические результаты — описание PR #70, независимые проверки — review
Никиты, новые запуски — Codex. Доступные материалы не позволяют отделить
команды, лично введённые студенткой, от выполненных с помощью агента;
поэтому утверждение «все проверки выполнены самостоятельно» не делается.
Самостоятельная демонстрация студенткой на защите и объяснение assertion,
fixture и риска не заменяются результатом агента и здесь не заявлены
как уже состоявшиеся.
