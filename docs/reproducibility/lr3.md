# Протокол воспроизводимости ЛР3

## 1. Окружение
- **ОС:** Linux (WSL)
- **Python:** 3.12.x
- **DVC:** 3.x.x (установлен через `pip install "dvc>=3,<4"`)

## 2. Таблица версий данных

| Версия | Git commit | DVC hash (md5) | SHA-256 CSV | Период | Строк | Контракт | Результат |
|--------|------------|----------------|-------------|--------|-------|----------|-----------|
| v1     | `a27bc82bb036f1cdb42153757e5abc217ecaa94c` | `b41ffd893842f7038a7004b9eb1e6628` | `d2038bfd4ba28a304e1bed26578c9bfcb556942b51694b8342a75f4f2dbf617e` | 2026-01-05..2026-01-28 | 24 | 2.0.0 | passed |
| v2     | *(ожидается от тимлида)* | *(ожидается)* | *(ожидается)* | 2026-01-05..2026-02-13 | 40 | 2.0.0 | *(ожидается)* |

## 3. Команды восстановления (PowerShell / Bash)
```bash
# 1. Клонировать репозиторий
git clone https://github.com/GundosCore/T26_MLOps.git
cd T26_MLOps

# 2. Установить зависимости
python3 -m venv .venv
source .venv/bin/activate  # Для Windows: .venv\Scripts\Activate.ps1
python3 -m pip install -e ".[dev]"
python3 -m pip install "dvc>=3,<4"

# 3. Настроить локальный remote (только локально!)
dvc remote modify --local course-local url /путь/к/папке/dvc-storage

# 4. Переключиться на версию и восстановить данные
git switch --detach <commit_hash>
dvc pull

# 5. Проверить контракт
python3 -m mlops_team1.validate_data --data data/flights_sample.csv --contract data/contract.json --report docs/reproducibility/validation/restored.json