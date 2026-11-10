# Сравнение двух MLflow run (ЛР4)

Эксперимент: `mlops-tmo41-team1-flight-delay`. Коммит, на котором сделаны run: `048a7a4ab0a63de24ed7a0a40ee272f522347612`. Тест-период не использовался: конфигурации сравниваются только по validation.

## Таблица

| Run ID                             | Конфигурация               | Версия данных                                         | Validation ROC AUC | Precision | Recall   | F1  | Решение   |
| ---------------------------------- | -------------------------- | ----------------------------------------------------- | ------------------ | --------- | -------- | --- | --------- |
| `948852493dc44fecac6c486b74d204b1` | RF, глубина 3, 80 деревьев | v2 (DVC 12e7b5a0…, SHA-256 bf35cf01…, контракт 2.0.0) | 0.571429           | 1.0       | 0.428571 | 0.6 | rejected  |
| `0f3f587b777f44238bc0a5f9244eaf7e` | RF, глубина 6, 80 деревьев | v2 (DVC 12e7b5a0…, SHA-256 bf35cf01…, контракт 2.0.0) | 0.714286           | 1.0       | 0.428571 | 0.6 | candidate |

Run ID и метрики взяты из run тимлида. Доля опоздавших в validation (positive_rate) у обоих 0.875.

## Гипотезы

- Глубина 3: «Неглубокие деревья (глубина 3) достаточно описывают данные».
- Глубина 6: «Увеличение глубины до 6 улучшает validation ROC AUC».

## Наблюдение

ROC AUC выше у глубины 6 (0.714286 против 0.571429). Precision, recall, F1 и positive_rate у двух конфигураций совпадают. При доле опоздавших 0.875 (7 из 8 строк validation), recall 0.428571 (3 из 7) и precision 1.0 это значит, что при пороге 0.5 обе модели находят по 3 опоздавших, дают 0 ложных срабатываний и пропускают по 4. Классы на пороге у них одинаковые по итогам, а различается только упорядочивание вероятностей, которое и измеряет ROC AUC. Поэтому метрики порога совпали, а ROC AUC разошёлся.

## Ограничение выборки

В validation 8 строк: 7 опоздавших и 1 нет. Поэтому ROC AUC принимает значения только с шагом 1/7. Разница 0.571429 → 0.714286 равна ровно одному шагу, то есть одной паре «опоздавший — не опоздавший», которую модель с глубиной 6 ранжирует верно, а с глубиной 3 нет. Это не доказывает, что глубина 6 лучше. Test-период не использовался.

## Решение

Правило: выбираем по validation ROC AUC, при равенстве более простую модель (меньшая глубина). ROC AUC не равен, поэтому по правилу выбирается глубина 6 (candidate), глубина 3 отклоняется (rejected). Выбор предварительный, из-за размера validation его нужно перепроверить на бо́льших данных. Теги `validation.status` выставляет тимлид.

## Воспроизведение

Независимое воспроизведение на том же коммите и данных, свой MLflow-сервер (sqlite, вне репозитория).

Мои run: глубина 3 — `578fa5295c1342ffabc32372d237c773`, глубина 6 — `52fa14defdce47a6ada976768eda516c`.

Команды (PowerShell, корень клона, `<SHA>` = `048a7a4ab0a63de24ed7a0a40ee272f522347612`):

```powershell
git fetch upstream
git switch --detach <SHA>
git status --short
dvc pull
(Get-Item data\flights_sample.csv).Length
Get-FileHash data\flights_sample.csv -Algorithm SHA256
python -m mlops_team1.validate_data --data data/flights_sample.csv --contract data/contract.json --report reports/validation/lr4-restored.json
python -m pip install -e ".[dev,tracking]"
mlflow server --host 127.0.0.1 --port 5000 --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlartifacts
$env:MLFLOW_TRACKING_URI="http://127.0.0.1:5000"
python -m mlops_team1.train_mlflow --data data/flights_sample.csv --contract data/contract.json --n-estimators 80 --max-depth 3 --experiment mlops-tmo41-team1-flight-delay --hypothesis "Неглубокие деревья (глубина 3) достаточно описывают данные"
python -m mlops_team1.train_mlflow --data data/flights_sample.csv --contract data/contract.json --n-estimators 80 --max-depth 6 --experiment mlops-tmo41-team1-flight-delay --hypothesis "Увеличение глубины до 6 улучшает validation ROC AUC"
```

Результат восстановления данных: `git status --short` пустой, размер 780 байт, SHA-256 `BF35CF01DB04FB31DE810DC16009D643E6BF3BE22C791FAEA7C00FDBC25CFF08`, валидатор вывел 10 строк OK, код выхода 0.

Результат сравнения: все метрики моих run совпали с метриками тимлида до 6-го знака (глубина 3: ROC AUC 0.571429; глубина 6: ROC AUC 0.714286; precision 1.0, recall 0.428571, F1 0.6, positive_rate 0.875). Теги `git.commit` (равен `<SHA>`), `data.dvc_hash` (12e7b5a02885ff28f6560bd895a1330e), `data.sha256` (bf35cf01…cff08), `data.contract_version` (2.0.0), `team.code` (team-1) совпали с ожидаемыми, `git.dirty` = false. Расхождений нет, сравнение `environment/requirements.txt` не потребовалось. Поиск по `tags.data.dvc_hash = "12e7b5a02885ff28f6560bd895a1330e"` вернул оба run.
