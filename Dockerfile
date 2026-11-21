FROM python:3.12-slim AS quality

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

COPY pyproject.toml ./
RUN python -c "import tomllib; from pathlib import Path; p = tomllib.loads(Path('pyproject.toml').read_text()); deps = p['project']['dependencies'] + p['project']['optional-dependencies']['dev'] + p['project']['optional-dependencies']['tracking']; Path('/tmp/requirements.txt').write_text('\n'.join(deps))" \
    && python -m pip install --no-cache-dir -r /tmp/requirements.txt

COPY src ./src
COPY tests ./tests
COPY data/contract.json ./data/contract.json
COPY data/flights_sample.csv.dvc ./data/flights_sample.csv.dvc
COPY README.md ./

RUN python -m pip install --no-cache-dir --no-deps -e . \
    && python -m ruff check src tests \
    && python -m pytest -q \
        --ignore=tests/test_container_contract.py \
        --ignore=tests/test_container_smoke.py \
        --ignore=tests/test_api_contract_smoke.py \
        --ignore=tests/test_openapi_snapshot.py \
    && python -m mlops_team1.validate_data \
        --data tests/fixtures/flights_sample_v1.csv \
        --contract data/contract.json \
        --report /tmp/validation.json \
    && python -m mlops_team1.train \
        --data tests/fixtures/flights_sample_v1.csv \
        --model /artifacts/model.joblib \
    && python -m pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_PATH=/app/models/model.joblib \
    PATH=/opt/venv/bin:$PATH

RUN addgroup --system --gid 10001 app \
    && adduser --system --uid 10001 --ingroup app --home /nonexistent --no-create-home app \
    && python -m venv /opt/venv

WORKDIR /app

COPY --from=quality /wheels /wheels
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels mlops-team1 \
    && rm -rf /wheels

COPY --from=quality --chown=10001:10001 /artifacts/model.joblib /app/models/model.joblib

USER 10001:10001

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/readyz', timeout=2)"]

CMD ["uvicorn", "mlops_team1.api:app", "--host", "0.0.0.0", "--port", "8080"]

