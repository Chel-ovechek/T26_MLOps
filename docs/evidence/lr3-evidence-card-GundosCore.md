# Индивидуальная карточка ЛР3

- **ФИО, группа, команда, GitHub-логин:** Соловцов Станислав Алексеевич, Т.МО41, команда 1, `GundosCore`
- **Роль:** DVC engineer (инициализация DVC, remote, перенос набора под DVC, версии v1 и v2 в DVC и в хранилище), тимлид и владелец хранилища `dvc-storage`. Дополнительно привёл контракт данных к курсовой версии 2.0.0.
- **Issue, pull request, commit:**
  - issue [#36](https://github.com/GundosCore/T26_MLOps/issues/36);
  - PR этапа 1 (DVC, контракт 2.0.0, версия v1), слит коммитом [`c1d5261`](https://github.com/GundosCore/T26_MLOps/commit/c1d526187c1ab0383889a67d828c71fb8b0eca94);
  - PR версии v2 («data: версия данных v2 (синтетическое продолжение)»), слит коммитом [`b3988e4`](https://github.com/GundosCore/T26_MLOps/commit/b3988e453ff6e2f04d81a7658ad5a2cb5a132d1d);
  - командный тег `lr3-v1` на коммите [`b13cb1b`](https://github.com/GundosCore/T26_MLOps/commit/b13cb1bc7c75e37052b6809831b93563c8b6063e);
  - коммиты версий: v1 [`a27bc82`](https://github.com/GundosCore/T26_MLOps/commit/a27bc82bb036f1cdb42153757e5abc217ecaa94c), v2 [`c0224cb`](https://github.com/GundosCore/T26_MLOps/commit/c0224cb1b2537c5f1d0f952957adc20ac153acba).

## Мои изменения (со ссылками на diff)

1. **DVC и remote** — [`f9df3d8`](https://github.com/GundosCore/T26_MLOps/commit/f9df3d84a989e7cd92920e9fcd60599215607200) `chore: initialize DVC with local remote`. Файлы `.dvc/.gitignore`, `.dvc/config`, `.dvcignore`. Remote `course-local` указывает на `../../dvc-storage` (путь считается от `.dvc/config`, то есть папка лежит рядом с клоном, личный путь в конфигурацию не попал). `.dvc/cache` не попадает в Git, служебные файлы DVC версионируются.
2. **Контракт 2.0.0** — [`192c39f`](https://github.com/GundosCore/T26_MLOps/commit/192c39fcae70faecf799ddd2154f39bb367fc238) `chore: align data contract to course version 2.0.0`. В `data/contract.json` добавлены метаданные курсового контракта (`description`, `owner`, `source`), правила команды `sorted` и `rationale` сохранены. Контракт приведён к 2.0.0 до создания v1, чтобы обе версии проходили один контракт. Миграция сделана отдельным коммитом, а не вместе с данными.
3. **Версия v1** — [`a27bc82`](https://github.com/GundosCore/T26_MLOps/commit/a27bc82bb036f1cdb42153757e5abc217ecaa94c) `data: register flight sample v1`. CSV переведён под DVC (`data/flights_sample.csv.dvc`), `.gitignore` теперь игнорирует `data/*.csv` и `data/*.parquet` (со старым `data/*` DVC не видел свой `.dvc`-файл). Копия v1 вынесена в `tests/fixtures/flights_sample_v1.csv`, на неё смотрят тесты и CI (CI не достаёт до локального remote). Добавлен отчёт `docs/reproducibility/validation/lr3-v1.json` (не в `reports/`, потому что `.gitignore` игнорирует любую папку с таким именем).
4. **Версия v2** — [`c0224cb`](https://github.com/GundosCore/T26_MLOps/commit/c0224cb1b2537c5f1d0f952957adc20ac153acba) `data: update flight sample to v2`. Обновлён `.dvc`-файл, добавлен отчёт `lr3-v2.json`. Строки составлены скриптом `src/mlops_team1/generate_v2.py` (seed 2026, 16 дней, по одной строке на день после 2026-01-28), `dvc push` выполнен в то же хранилище. Решение по v2 описано в `docs/reproducibility/v2-decision.md`.

## Review работы другого участника и найденная проблема

**PR [#40](https://github.com/GundosCore/T26_MLOps/pull/40) (Екатерина).** Прочитал diff, подтянул ветку и запустил проверки: `python -m ruff check .` давал 3 ошибки в `tests/test_dvc_refusal.py` (порядок импортов, два вызова `subprocess.run` без `check`), `python -m pytest -q` давал 1 failed. Главная проблема: тест проверял слово `modified` в выводе `dvc status --quiet`, а `--quiet` ничего не печатает (код возврата 1, вывод пустой), поэтому проверка не могла пройти. Исправление: `--quiet` оставлен только для кода возврата, а слово `modified` проверяется отдельным вызовом обычного `dvc status`. Кроме того, `docs/reproducibility/lr3.md` содержал незакрытый блок кода и не содержал разделов, заявленных в описании PR.

## Команда восстановления выбранной версии

```powershell
git switch --detach a27bc82bb036f1cdb42153757e5abc217ecaa94c   # v1; для v2: c0224cb1b2537c5f1d0f952957adc20ac153acba
git rev-parse HEAD
dvc pull
Get-FileHash data\flights_sample.csv -Algorithm SHA256
python -m mlops_team1.validate_data --data data/flights_sample.csv --contract data/contract.json --report reports/validation/restored.json
git switch main
dvc pull
```

Папка `dvc-storage` лежит рядом с клоном. После `git switch main` снова выполняется `dvc pull`: Git переключает `.dvc`-файл, а сам CSV подменяет только DVC.

## Git commit, DVC hash и SHA-256

| Версия | Git commit | DVC hash (md5) | SHA-256 CSV |
| --- | --- | --- | --- |
| v1 | `a27bc82bb036f1cdb42153757e5abc217ecaa94c` | `b41ffd893842f7038a7004b9eb1e6628` | `d2038bfd4ba28a304e1bed26578c9bfcb556942b51694b8342a75f4f2dbf617e` |
| v2 | `c0224cb1b2537c5f1d0f952957adc20ac153acba` | `12e7b5a02885ff28f6560bd895a1330e` | `bf35cf01db04fb31de810dc16009d643e6bf3be22c791faea7c00fdbc25cff08` |

Размер файла: v1 482 байта, v2 780 байт. Git commit идентифицирует состояние проекта, DVC hash — объект данных в хранилище, SHA-256 — байты восстановленного файла. Ни один не заменяет остальные.

## Результат валидатора

Контракт 2.0.0, все 10 проверок `OK`, код возврата 0 для обеих версий.

- v1: 24 строки, период 2026-01-05..2026-01-28, разбиение train/validation/test 14/5/5. Отчёт `docs/reproducibility/validation/lr3-v1.json`.
- v2: 40 строк, период 2026-01-05..2026-02-13, разбиение 24/8/8. Отчёт `docs/reproducibility/validation/lr3-v2.json`.

Границы считаются по числу строк (`int(0.6·n)` и `int(0.8·n)`), поэтому при переходе на v2 test-период сдвигается (бывший test v1 уходит в train). Это осознанное решение, v1 не менялся.

## Отказной сценарий и объяснение

1. **Файл изменён вручную без `dvc add`.** После дописывания строки в `data/flights_sample.csv` команда `dvc status` показывает `changed outs: modified: data\flights_sample.csv`, а `dvc status --quiet` возвращает код 1. Обычный `dvc status` возвращает код 0 даже при изменениях, поэтому в автоматических проверках нужен `--quiet` (автотест `tests/test_dvc_refusal.py`; в CI DVC не установлен, там он пропускается). Объяснение: DVC сравнивает хеш рабочего файла с `md5` из `.dvc`-файла, они расходятся. Вернуть файл: удалить его и выполнить `dvc pull`.
2. **Версия нарушает контракт или порядок дат.** Если поменять местами две строки, валидатор печатает `FAIL sorted` и возвращает код 1 (автотест `tests/test_data_contract.py::test_violation_is_detected`, набор `BAD_CASES`). Объяснение: DVC гарантирует, что файл тот самый, но не что данные корректны; корректность проверяет контракт, поэтому после каждого восстановления валидатор запускается снова.

## Чем Git отличается от DVC cache и remote

Git хранит код, контракт и маленькую «квитанцию» `data/flights_sample.csv.dvc` (хеш и размер), но не сами данные. DVC cache (`.dvc/cache`) — локальная копия объектов данных на машине, в Git она не попадает. Remote (`dvc-storage`, `course-local`) — общее хранилище: `dvc push` кладёт в него объекты, `dvc pull` берёт их на другой машине. Разговорно: Git — записка «чемодан в ячейке №…», cache — тумбочка дома, remote — общий склад; по записке из любого коммита достают именно тот чемодан.

## Использование ИИ

Использовал Claude (Anthropic): план этапов и команд, сборка контракта 2.0.0 из курсового контракта и правил команды, скрипт `generate_v2.py` и тесты к нему (в репозиторий они попали через PR Никиты), проверочные прогоны на копии репозитория, черновики ревью и описаний PR. Команды выполнял и результаты проверял я.
