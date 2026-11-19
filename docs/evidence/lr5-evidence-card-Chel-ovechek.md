# Индивидуальная карточка сдачи ЛР5

## Студент

- ФИО: Владимир Псюрников
- Группа: Т.МО41
- Команда и GitHub-логин: команда 1, Chel-ovechek

## Роль

Model test engineer: тесты артефакта модели (bundle) и детерминированности обучения. В ЛР4 был Reproducibility reviewer (независимо воспроизводил run тимлида), в ЛР3 Documentation reviewer. Другие роли ЛР5 в команде: Станислав (интеграция и качество), Екатерина (тесты данных), Никита (тесты оценки). Я проверяю PR Никиты, меня проверяет Станислав.

## Задача

Командная issue [#67](https://github.com/GundosCore/T26_MLOps/issues/67) «[ЛР5] Тестирование данных, модели и pipeline». Личной issue нет, в PR использовано `Refs #67`. Критерии приёмки issue: ruff чистый, pytest зелёный, у каждого участника есть личный тест и defect injection, PR прошли review, тег `lr5-v1` после приёмки с чистого клона. Тег `lr5-v1` создан тимлидом и опубликован в репозитории команды, указывает на коммит `c5156f8a154c3b63c1f9f80257ea7008c4317198` (`test: сквозной smoke test, таблица рисков и отчёты (ЛР5)`), проверено командой `git ls-remote --tags upstream`.

## Личный артефакт

- Pull request: [#71](https://github.com/GundosCore/T26_MLOps/pull/71), ветка `test/issue-67-model-bundle` → `psyurnikov`, один файл `tests/test_model_bundle.py` (+176). Слит тимлидом. Коммиты: `b8b816f` (12 тестов), `581d267` (тест seed в параметрах run по замечанию Станислава). Итого 13 тестов, слой `model` (маркер ставится по имени файла в `tests/conftest.py`). Код в `src` не менялся.
- Ключевые node ID:
  - `tests/test_model_bundle.py::test_bundle_features_keep_exact_order`
  - `tests/test_model_bundle.py::test_bundle_has_required_keys`
  - `tests/test_model_bundle.py::test_predict_proba_shape_and_range_for_one_row`
  - `tests/test_model_bundle.py::test_training_is_deterministic_for_same_seed`
  - `tests/test_model_bundle.py::test_seed_is_saved_in_bundle`
  - `tests/test_model_bundle.py::test_seed_is_reflected_in_run_params`
- Fixtures из `tests/conftest.py`: `valid_frame`, `csv_factory`, `trained_model_path`, `contract_path`.
- CI на последнем коммите `581d267`: [запуск #28, Success](https://github.com/Chel-ovechek/T26_MLOps/actions/runs/43600890563).
- Review Станислава на #71: [ссылка](https://github.com/GundosCore/T26_MLOps/pull/71#pullrequestreview-5905487450). Его замечание 1 (нет теста «seed отражён в run metadata», §12 задания) устранено вторым коммитом `581d267`. Строка длиннее 100 символов разбита. Остальные замечания (имена тестов отличаются от пакета, частичный дубль с `test_train_creates_versioned_bundle`) не блокирующие, таблицу рисков он пересобирает сам.
- Review другого участника: [PR #69 Никиты](https://github.com/GundosCore/T26_MLOps/pull/69#pullrequestreview-5904211826), `tests/test_evaluation_target.py`, Approve. Проверил локально на коде PR: ruff чистый, `pytest -q` 80 passed, 1 skipped, `-m evaluation` 14 passed, diff с базой PR один коммит и один файл. Пересчитал вручную доли классов 0.5/0.6/0.4 и метрики (ROC AUC 0.75, precision 1.0, recall 0.5, f1 2/3), CI открыл сам. Три незначительных замечания (проверка `0 <= roc_auc <= 1` почти тавтологична, мутация описана только для `train.py`, вкладка Checks в PR пуста, CI запущен в форке автора). Мутацию Никиты сам не воспроизводил.

## Контролируемый риск

Порядок признаков в bundle (`features`) расходится с ожидаемым `["DepHour", "IsWeekend"]`. Клиент собирает DataFrame по этому списку, перестановка меняет смысл столбцов, а ошибки при предсказании не будет. Остальные тесты файла проверяют форму и диапазон `predict_proba` (1, 2), порядок классов `[0, 1]`, ключи bundle, версию, параметры, границы split (совпадают с `split_cuts`), validation-метрики, детерминированность при одном seed и сохранение seed в bundle и в параметрах MLflow run.

## Defect injection

- Внесённый дефект: в `src/mlops_team1/train.py` `FEATURES = ["DepHour", "IsWeekend"]` заменён на `FEATURES = ["IsWeekend", "DepHour"]`.
- Ожидаемый failing test: `test_bundle_features_keep_exact_order`.
- Фактический failing test: он же, `1 failed`. Весь файл при дефекте: `1 failed, 11 passed` (на тот момент 12 тестов). Остальные тесты не упали, потому что модель обучается и предсказывает согласованно с любым порядком. Ошибка проявилась бы только у клиента, который собирает DataFrame по другому списку.
- Откат: `git restore src\mlops_team1\train.py`, `git status` показал только новый тест, файл снова зелёный. Дефект в PR не попал.
- Ограничение: дефект проверялся на файле из 12 тестов, тест seed в параметрах run (13-й) на этом дефекте отдельно не прогонялся.

## Диагностика

```
FAILED tests/test_model_bundle.py::test_bundle_features_keep_exact_order
E   AssertionError: Порядок признаков в bundle: ['IsWeekend', 'DepHour'], ожидалось ['DepHour', 'IsWeekend']. Клиент строит DataFrame по этому списку, перестановка меняет смысл столбцов
E   At index 0 diff: 'IsWeekend' != 'DepHour'
```

Причина: `train_model` кладёт в bundle переменную `FEATURES`, а тест сравнивает её с эталонным порядком. Сообщение assert содержит фактическое и ожидаемое значение.

## Воспроизведение

Из корня клона, в активированном `.venv`:

- Один тест: `python -m pytest -q "tests/test_model_bundle.py::test_bundle_features_keep_exact_order"`
- Файл: `python -m pytest -q tests/test_model_bundle.py` (13 passed на коммите `581d267`)
- Слой: `python -m pytest -q -m model` (20 passed, 70 deselected на коммите `581d267`)
- Весь набор: `python -m pytest -q` (89 passed, 1 skipped на коммите `581d267`)
- Линтер: `python -m ruff check .` (чисто)

Числа относятся к состоянию ветки PR до слияния. На коммите тега `lr5-v1` в набор добавлены тесты других участников, поэтому общее число отличается. Предупреждения pytest (`SADeprecationWarning`, `UserWarning` про dataset source и integer schema) приходят из MLflow и SQLAlchemy, на результат не влияют.

## Найденное вне PR

Повреждённый файл модели: `joblib.load` на содержимом `b"not a model"` даёт `KeyError: 110`. `load_bundle` не превращает его в `ValueError`, а `model_io.main` ловит только `ValueError` и `OSError`, поэтому CLI даёт трассировку вместо кода 2 (проверено). Риск «модельный файл повреждён → контролируемая ошибка» из таблицы рисков на момент проверки не закрыт. Теста на это не добавлял: тест на `KeyError` закрепил бы случайное поведение pickle, а `skip`/`xfail` скрыли бы проблему. По договорённости со Станиславом описано в PR #71 без отдельной issue.

## Использование ИИ

- Инструмент: Claude (Anthropic), в чате.
- Что делал ИИ: черновики кода `tests/test_model_bundle.py`, разбор кода и тестов Никиты для ревью, команды проверки, тексты PR, ревью и этой карточки.
- Что проверено самостоятельно: все команды выполнены мной на своей машине (ruff, pytest по файлу, по слою и полным набором, defect injection и откат, проверка `joblib.load` на мусорном файле); результаты взяты из моего вывода. Запуски CI в Actions форка открыты и проверены мной (статус Success). Ревью PR #69 сделано по diff и локальному запуску на коде PR. Решение не использовать `KeyError` в тесте принято мной после воспроизведения ошибки.
- Источники: задание ЛР5, пакет задач Станислава, `src/mlops_team1/train.py`, `model_io.py`, `train_mlflow.py`, `tests/conftest.py`.
