# Индивидуальная карточка сдачи ЛР5

## Идентификация

- ФИО: Скворцов Никита
- группа: Т.МО41
- команда и GitHub-логин: команда 1, `snikersito`
- роль в ЛР5 и отличие от роли в ЛР4: Evaluation test engineer (тесты слоя `evaluation`: граница цели и метрики). В ЛР4 я отвечал за загрузку модели из run, тесты `model_io`, соглашение об MLflow и ревью, то есть за инфраструктуру воспроизводимости; в ЛР5 я проверяю, что считаются именно те метки и метрики, которые заявлены.
- issue: [#67](https://github.com/GundosCore/T26_MLOps/issues/67)
- pull request: [#69](https://github.com/GundosCore/T26_MLOps/pull/69) (`test/issue-67-evaluation-target` → `skvortsov`, reviewer Chel-ovechek); моё ревью: [#70](https://github.com/GundosCore/T26_MLOps/pull/70) (Екатерина, тесты данных)
- commit SHA: `33d468b` (`test: граница цели ArrDelay и метрики на пороге (ЛР5)`)

## Личный проверяемый вклад

Связанная задача: #67. Зелёный CI: [run 43574213701](https://github.com/snikersito/T26_MLOps/actions/runs/43574213701) (CI #20, коммит `33d468b`, ветка `test/issue-67-evaluation-target`).

Файл `tests/test_evaluation_target.py` (слой `evaluation`), 4 теста и общая fixture `delays_14_and_15`:

1. `test_arrdelay_15_counts_as_late_in_training`: обучение на данных, где `ArrDelay` чередуется 15 и 14, должно пройти и вернуть ROC AUC от 0 до 1. Тест закрепляет, что значение 15 считается опозданием в `train.py`.
2. `test_arrdelay_15_counts_as_late_in_validator_report`: в отчёте валидатора доля положительного класса по частям `train`, `validation`, `test` равна `[0.5, 0.6, 0.4]`. Закрепляет ту же границу в `validate_data.py`.
3. `test_probability_equal_to_threshold_is_positive`: вероятность ровно 0.5 при пороге 0.5 считается положительным предсказанием (`>=`), precision и recall равны 1.0 (`pytest.approx`).
4. `test_known_metric_values`: на наборе из четырёх примеров ROC AUC 0.75, precision 1.0, recall 0.5, F1 2/3.

Fixture `delays_14_and_15` берёт `valid_frame`, меняет `ArrDelay` на чередование 15 и 14 и записывает CSV через `csv_factory`. Значения 14 и 15 нужны оба: при одном значении получится один класс, и тест не отличил бы `>=` от `>`.

Критерий приёмки: `ruff check .` чистый; `pytest -q` на моей ветке: 81 passed (было 77), слой `evaluation`: 14 тестов (было 10); дефект на границе цели ловится тестом из пункта 1 (см. ниже).

## Review работы другого участника

- PR [#70](https://github.com/GundosCore/T26_MLOps/pull/70) (Екатерина, `tests/test_data_negative.py`): прочитал diff и сверил значения с `data/contract.json`: `DepHour` от 0 до 23, `ArrDelay` от −180 до 1440, `IsWeekend` равен 0 или 1. В файле 7 отрицательных случаев (за пределами контракта, дробное и пустое значение, несуществующая дата) и 5 граничных, которые должны приниматься (`DepHour` 0 и 23, `IsWeekend` 1, `ArrDelay` −180 и 1440). Блокирующих замечаний не нашёл, ревью завершил как Approve.

## Контролируемый риск

Граница цели `ArrDelay >= 15` записана в нескольких местах кода: литерал в `src/mlops_team1/train.py` (строка 34), `LATE_MINUTES` в `validate_data.py` и `TARGET_THRESHOLD_MINUTES` в `train_mlflow.py`. Если изменить одно место (например, `> 15`), обучение и отчёт валидатора начнут считать разные метки, а метрики и отчёт станут несопоставимы. Мои тесты 1 и 2 закрывают первые два места. Известное ограничение: третье место (`train_mlflow.py`) моими тестами не покрыто.

## Defect injection

- дефект: в `src/mlops_team1/train.py`, строка 34, `>= 15` заменено на `> 15`
- ожидаемый падающий тест (назван заранее): `tests/test_evaluation_target.py::test_arrdelay_15_counts_as_late_in_training`
- фактический результат на момент запуска: тот же тест упал, итог одного теста `1 failed in 1.68s`; весь набор `1 failed, 80 passed, 7 warnings in 21.11s`
- что показал первый полезный фрагмент traceback: строка `y = (data["ArrDelay"] > 15).astype(int)` в `src\mlops_team1\train.py`, затем `ValueError: Для обучения нужны примеры обоих классов` (`src\mlops_team1\train.py:36`) и `FAILED tests/test_evaluation_target.py::test_arrdelay_15_counts_as_late_in_training - ValueError: Для обучения нужны примеры обоих классов`
- причина: при `> 15` значение 15 перестаёт быть опозданием, и у данных из значений 14 и 15 все метки равны 0, поэтому обучение отказывает. Тест отчёта валидатора остаётся зелёным: ошибка в `train.py`, а не в валидаторе.
- до моего теста этот дефект не ловил ни один тест: остальные 77 тестов оставались зелёными.
- откат: `git restore src/mlops_team1/train.py`; `git status --short` показывает только мой новый файл, тест снова проходит (`4 passed`). Дефект не попал ни в коммит, ни в PR.

## Воспроизведение

Из корня репозитория, в активированном `.venv`:

- `python -m pytest -q "tests/test_evaluation_target.py::test_arrdelay_15_counts_as_late_in_training"`: 1 passed;
- `python -m pytest -q tests/test_evaluation_target.py`: 4 passed;
- `python -m pytest -q -m evaluation`: 14 passed;
- `python -m pytest -q`: 81 passed (с DVC).

## Инженерное решение и риск

Граница проверена через два независимых пути (обучение и отчёт валидатора) на данных, где значения 14 и 15 стоят рядом. Альтернатива: вынести порог в одну общую константу и импортировать её во все три места; тогда тест на границу был бы нужен реже, но это правка `src/`, которая вне моей роли, поэтому я записал её как рекомендацию тимлиду. Остаточный риск: `TARGET_THRESHOLD_MINUTES` в `train_mlflow.py` тестом не закрыт.

Соседний слой не заменяет мой тест: тест валидатора не заметит неверный порог в обучении, и наоборот. Поэтому для каждого места нужна своя проверка.

## Использование ИИ

- использованный инструмент: Claude (Anthropic) в чате проекта. ИИ подготовил черновик `tests/test_evaluation_target.py`, исправил в нём структуру отчёта валидатора (`["split"]["parts"]` оказалась словарём, а не списком), составил тексты описания PR #69, ревью PR #70 и эту карточку.
- что проверено самостоятельно: запустил на своём компьютере (Windows) все четыре команды воспроизведения и получил цифры выше; сам выполнил defect injection (замена `>= 15` на `> 15`, падение названного теста, `git restore`, повторный зелёный прогон); прочитал `tests/test_evaluation_target.py` и `train.py` и могу объяснить, зачем в данных оба значения 14 и 15, почему порог вероятности проверяется через `>=`, зачем нужен `pytest.approx` и почему соседние слои не заменяют этот тест.
- какими командами или источниками выполнена проверка: `ruff check .`, `pytest -q`, `pytest -q -m evaluation`, `pytest -q` по node ID теста, `git restore`, `git status --short`, страница CI [run 43574213701](https://github.com/snikersito/T26_MLOps/actions/runs/43574213701), страницы PR #69 и #70.