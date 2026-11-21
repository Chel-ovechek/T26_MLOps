# Индивидуальная карточка сдачи ЛР5

## Идентификация

- ФИО: Соловцов Станислав Алексеевич
- группа: Т.МО41
- команда и GitHub-логин: команда 1, GundosCore
- роль в ЛР5 и отличие от роли в ЛР4: Integration engineer и Quality reviewer (общие fixtures и слои тестов, сквозной smoke test `validate -> train -> load -> predict`, проверка слоёв, исправление `load_bundle`, таблица рисков, отчёты, приёмка и тег). В ЛР4 была роль Experiment owner и Model engineer (код обучения и MLflow-запуска, соглашение о тегах, сервер и два run), в ЛР3 DVC engineer.
- issue: [#67](https://github.com/GundosCore/T26_MLOps/issues/67). Критерии приёмки общего issue: `ruff` без замечаний, `pytest` зелёный, у каждого участника личный тест и defect injection, PR прошли review, тег `lr5-v1` после приёмки с чистого клона. Мой личный критерий: smoke test проходит на `main` и при удалении поля `version` из bundle падает на шаге load, а итоговый набор даёт `115 passed` с DVC.
- pull request: [#68](https://github.com/GundosCore/T26_MLOps/pull/68) (этап 0: общие fixtures и слои тестов, слит merge-коммитом `9ea3748`), [#75](https://github.com/GundosCore/T26_MLOps/pull/75) (smoke test, `test_layers.py`, исправление `load_bundle`, таблица рисков, отчёты, README; слит merge-коммитом `c5156f8`), review в [#71](https://github.com/GundosCore/T26_MLOps/pull/71)
- commit SHA или tag: тег `lr5-v1` (аннотированный) на `c5156f8a154c3b63c1f9f80257ea7008c4317198`

## Личный тестовый артефакт

- test node ID: основной `tests/test_pipeline_smoke.py::test_validate_train_load_predict_chain`. Остальные мои тесты: `tests/test_pipeline_smoke.py::test_cli_reports_same_version_and_probability_as_bundle`, `tests/test_layers.py::test_every_test_has_exactly_one_layer`, `tests/test_model_io.py::test_load_bundle_rejects_corrupted_file` и `tests/test_model_io.py::test_main_returns_2_without_traceback_for_corrupted_file` (по три случая: `garbage-bytes`, `empty-file`, `truncated-file`), `tests/test_fixtures.py` (4 теста).
- fixture или вход: `valid_frame`, `csv_factory`, `contract_path` из `tests/conftest.py` (эталон `tests/fixtures/flights_sample_v1.csv`, 24 строки); данные записываются в `tmp_path`, обучение идёт во временный файл `artifacts/model.joblib`; вход предсказания `DepHour` = 10, `IsWeekend` = 0.
- контролируемый риск: сквозная связка рвётся, хотя отдельные компоненты исправны (в bundle не записано поле `version`: обучение проходит, загрузка отказывает). Дополнительно: повреждённый файл модели давал сырые `KeyError` и `EOFError` и трассировку в командной строке (теперь контролируемый `ValueError`, код 2); файл тестов без слоя; CRLF в CSV из `csv_factory`.
- ожидаемый успешный результат: все четыре слоя smoke проходят (validate: `passed` равно `True`; train: файл модели создан, ROC AUC в диапазоне 0..1; load: версия формата `0.2.0`; predict: форма `(1, 2)`, вероятности в диапазоне `[0, 1]`); полный набор `115 passed` с DVC.
- ссылка на diff: [#68](https://github.com/GundosCore/T26_MLOps/pull/68/files), [#75](https://github.com/GundosCore/T26_MLOps/pull/75/files)

## Defect injection

- временно внесённый дефект: из bundle убрано поле версии (в `src/mlops_team1/train.py` удалена строка `"version": "0.2.0",` в словаре, который сохраняется через `joblib.dump`).
- ожидаемый failing test: `tests/test_pipeline_smoke.py::test_validate_train_load_predict_chain` (назван до запуска; отказ ожидался на шаге load).
- команда запуска: `python -m pytest -q "tests/test_pipeline_smoke.py::test_validate_train_load_predict_chain"`, затем весь набор `python -m pytest -q`.
- первый полезный фрагмент traceback (строки с временными путями и содержимым таблицы данных опущены):

```
    # Слой load: файл читается и содержит версию формата.
>       bundle = load_bundle(model_path)

tests\test_pipeline_smoke.py:30:
...
E           ValueError: В файле модели (словарь) нет ключей: version

src\mlops_team1\model_io.py:44: ValueError
FAILED tests/test_pipeline_smoke.py::test_validate_train_load_predict_chain - ValueError: В файле модели (словарь) нет ключей: version
1 failed in 1.80s
```

- фактическая причина: обучение отработало и файл создан, но `load_bundle` не нашёл обязательный ключ `version`, поэтому падение на шаге load, а не validate, train или predict. Весь набор с тем же дефектом на тот момент: `7 failed, 79 passed` (упали `test_fixtures.py::test_trained_model_path_gives_loadable_bundle`, три теста в `test_model_io.py`, два теста в `test_pipeline_smoke.py` и `test_train_model.py::test_train_creates_versioned_bundle`). Фрагмент полностью сохранён в `reports/tests/lr5-fail-fragment.txt`. После слияния тестов остальных участников тот же дефект роняет 10 тестов.
- подтверждение восстановления корректного кода: дефект снят командой `git restore src/mlops_team1/train.py` и не входит ни в один коммит; приёмка с чистого клона на теге `lr5-v1` дала `115 passed`.

## Review

- ссылка на review другого участника: [PR #71](https://github.com/GundosCore/T26_MLOps/pull/71) (Владимир, `tests/test_model_bundle.py`)
- проверенный риск или найденная проблема: в тексте review указано, что запуск и внесение дефектов выполнил ИИ-помощник в песочнице (Linux, Python 3.12), Windows и CI в ней не проверялись. Результат: на чистом дереве ветки `ruff` чистый, набор зелёный; на копии внесены дефекты: перестановка `FEATURES` роняет его личный тест `test_bundle_features_keep_exact_order` (всего 3 failed), удаление `version` роняет `test_bundle_has_required_keys`, если не передавать `random_state` в модель, падает тест детерминированности. Найдено: нет теста, что seed попадает в параметры MLflow run (пункт раздела 12 задания); после review Владимир добавил его коммитом `581d267` (`test_seed_is_reflected_in_run_params`).

## Воспроизведение

- команда запуска одного теста: `python -m pytest -q "tests/test_pipeline_smoke.py::test_validate_train_load_predict_chain"`
- команда полного набора: `python -m pytest -q` (с DVC), слой одной командой `python -m pytest -q -m pipeline`
- путь к JUnit XML: `reports/tests/lr5-pass.xml` (получен командой `python -m pytest -q --junitxml=reports/tests/lr5-pass.xml`)
- итог pass/fail: pass, 115 тестов, 0 упавших, 0 пропущенных (DVC установлен); без DVC `114 passed` и `1 skipped`

## Объяснение

- почему выбранный слой теста необходим: интеграционный smoke ловит расхождение между компонентами, которое тесты каждого компонента по отдельности пропускают: каждая часть исправна, а связка рвётся (потеряно поле версии: train отработал, load отказал). Тест называет слой отказа (validate, train, load или predict), и по первому же сообщению видно, куда идти.
- какой соседний тест его не заменяет: `tests/test_train_model.py::test_train_creates_versioned_bundle` проверяет состав bundle сразу после обучения, но не читает файл через `load_bundle` и не строит предсказание; `tests/test_model_io.py::test_load_bundle_returns_all_required_keys` проверяет загрузку файла из fixture, но не связывает её с валидацией и обучением на данных, прошедших контракт.
- где тест может дать ложную уверенность: эталон маленький (24 строки), smoke идёт на v1, а не на рабочем наборе v2 под DVC; качество модели не оценивается; HTTP API в проекте пока нет (слой `api` закрыт тестами интерфейса `model_io`); версия формата сверяется с константой `0.2.0`, при смене формата её надо менять в тесте; порог цели записан в трёх местах и покрыт двумя тестами; в CI DVC не ставится, поэтому там один тест пропускается.

## Использование ИИ

- использованный инструмент или «не использовался»: Claude (Anthropic) в чате проекта. ИИ помог разобрать задание, распределить роли, подготовил общие fixtures и разметку слоёв, smoke test, `test_layers.py`, исправление `load_bundle` и тесты к нему, таблицу рисков и разделы README, пакеты для участников, тексты ревью и инструкции по приёмке и тегу; проверил файлы участников на пробной реализации в песочнице.
- какие фрагменты проверены самостоятельно: запустил `ruff` и `pytest` на своей машине (Windows 11, PowerShell, с DVC); сам внёс дефект, получил падение названного теста и вернул код; снял отчёт `reports/tests/lr5-pass.xml`; сделал приёмку с чистого клона (`dvc pull`, размер данных 780 байт, SHA-256 `bf35cf01db04fb31de810dc16009d643e6bf3be22c791faea7c00fdbc25cff08`, валидатор с кодом 0, `git ls-files data tests/fixtures`); поставил тег `lr5-v1`; слил PR и закрыл issue.
- какими командами или источниками выполнена проверка: `python -m ruff check .`, `python -m pytest -q`, `python -m pytest -q --junitxml=reports/tests/lr5-pass.xml`, `git restore src/mlops_team1/train.py`, `dvc pull`, `Get-FileHash data\flights_sample.csv -Algorithm SHA256`, `python -m mlops_team1.validate_data ...`, `git ls-remote --tags origin`, страницы PR #68, #71 и #75.
