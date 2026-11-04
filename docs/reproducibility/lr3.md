# Протокол воспроизводимости ЛР3

## 1. Окружение
- **ОС:** Linux (WSL)
- **Python:** 3.12.15
- **DVC:** 3.67.1

## 2. Таблица версий данных

| Версия | Git commit | DVC hash (md5) | SHA-256 CSV | Период | Строк | Контракт | Результат |
|--------|------------|----------------|-------------|--------|-------|----------|-----------|
| v1     | `a27bc82bb036f1cdb42153757e5abc217ecaa94c` | `b41ffd893842f7038a7004b9eb1e6628` | `d2038bfd4ba28a304e1bed26578c9bfcb556942b51694b8342a75f4f2dbf617e` | 2026-01-05..2026-01-28 | 24 | 2.0.0 | passed |
| v2     | *(ожидается от тимлида)* | *(ожидается)* | *(ожидается)* | 2026-01-05..2026-02-13 | 40 | 2.0.0 | *(ожидается)* |

## 3. Команды восстановления

### PowerShell (Windows)
```powershell
# 1. Распаковать dvc-storage рядом с клоном репозитория
# Пример: C:\Projects\T26_MLOps и C:\Projects\dvc-storage

# 2. Клонировать репозиторий
git clone https://github.com/GundosCore/T26_MLOps.git
cd T26_MLOps

# 3. Установить зависимости
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pip install "dvc>=3,<4"

# 4. Настроить локальный remote (только если dvc-storage НЕ рядом с клоном)
# dvc remote modify --local course-local url C:\путь\к\dvc-storage

# 5. Переключиться на версию v1 и восстановить данные
git switch --detach a27bc82bb036f1cdb42153757e5abc217ecaa94c
dvc pull

# 6. Проверить SHA-256 (должен быть d2038bfd...)
Get-FileHash data\flights_sample.csv -Algorithm SHA256

# 7. Запустить валидатор
python -m mlops_team1.validate_data --data data/flights_sample.csv --contract data/contract.json --report reports/validation/restored-v1.json

# 8. Вернуться в main
git switch main