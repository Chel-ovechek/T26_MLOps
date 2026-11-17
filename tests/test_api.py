from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mlops_team1.api import create_app
from mlops_team1.model_io import load_bundle, predict_proba_row

VALID_PAYLOAD = {"dep_hour": 10, "is_weekend": 0}


def test_healthz_ok_even_without_model(tmp_path: Path) -> None:
    with TestClient(create_app(tmp_path / "missing.joblib")) as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_ready_with_model(trained_model_path: Path) -> None:
    with TestClient(create_app(trained_model_path)) as client:
        response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readyz_503_without_model(tmp_path: Path) -> None:
    with TestClient(create_app(tmp_path / "missing.joblib")) as client:
        response = client.get("/readyz")
    assert response.status_code == 503
    assert response.json()["error_code"] == "not_ready"


def test_readyz_503_with_corrupt_model(tmp_path: Path) -> None:
    corrupt = tmp_path / "corrupt.joblib"
    corrupt.write_bytes(b"not a model")
    with TestClient(create_app(corrupt)) as client:
        assert client.get("/healthz").status_code == 200
        assert client.get("/readyz").status_code == 503


def test_predict_contract(trained_model_path: Path) -> None:
    with TestClient(create_app(trained_model_path)) as client:
        response = client.post(
            "/predict", json=VALID_PAYLOAD, headers={"X-Request-ID": "lr6-contract-test"}
        )
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {
        "delay_probability",
        "delayed",
        "threshold",
        "model_version",
        "request_id",
    }
    assert 0.0 <= body["delay_probability"] <= 1.0
    assert body["threshold"] == 0.5
    assert body["delayed"] is (body["delay_probability"] >= body["threshold"])
    assert body["model_version"] == "0.2.0"
    assert body["request_id"] == "lr6-contract-test"
    assert response.headers["X-Request-ID"] == "lr6-contract-test"


def test_predict_matches_model_io(trained_model_path: Path) -> None:
    expected = predict_proba_row(load_bundle(trained_model_path), 10, 0)
    with TestClient(create_app(trained_model_path)) as client:
        response = client.post("/predict", json=VALID_PAYLOAD)
    assert response.status_code == 200, response.text
    assert response.json()["delay_probability"] == pytest.approx(expected)


def test_predict_generates_request_id(trained_model_path: Path) -> None:
    with TestClient(create_app(trained_model_path)) as client:
        response = client.post("/predict", json=VALID_PAYLOAD)
    assert response.status_code == 200, response.text
    request_id = response.json()["request_id"]
    assert request_id
    assert request_id == response.headers["X-Request-ID"]


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"dep_hour": 24, "is_weekend": 0}, id="hour-24"),
        pytest.param({"dep_hour": -1, "is_weekend": 0}, id="hour-minus-1"),
        pytest.param({"dep_hour": 10, "is_weekend": 2}, id="weekend-2"),
        pytest.param({"dep_hour": 10}, id="missing-field"),
        pytest.param({"dep_hour": "10", "is_weekend": 0}, id="hour-as-string"),
        pytest.param({"dep_hour": 10, "is_weekend": 0, "arr_delay": 42}, id="extra-field"),
    ],
)
def test_predict_rejects_invalid_payload(trained_model_path: Path, payload: dict) -> None:
    with TestClient(create_app(trained_model_path)) as client:
        response = client.post("/predict", json=payload)
    assert response.status_code == 422, response.text
    body = response.json()
    assert body["error_code"] == "validation_error"
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert body["details"]


def test_predict_503_without_model(tmp_path: Path) -> None:
    with TestClient(create_app(tmp_path / "missing.joblib")) as client:
        response = client.post("/predict", json=VALID_PAYLOAD)
    assert response.status_code == 503, response.text
    assert response.json()["error_code"] == "not_ready"


def test_model_path_is_read_from_environment(
    trained_model_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MODEL_PATH", str(trained_model_path))
    with TestClient(create_app()) as client:
        response = client.get("/readyz")
    assert response.status_code == 200, response.text


def test_openapi_describes_predict(trained_model_path: Path) -> None:
    with TestClient(create_app(trained_model_path)) as client:
        schema = client.get("/openapi.json").json()
    request_schema = schema["components"]["schemas"]["PredictionRequest"]
    assert request_schema["additionalProperties"] is False
    assert set(request_schema["required"]) == {"dep_hour", "is_weekend"}
    for path in ("/healthz", "/readyz", "/predict"):
        assert path in schema["paths"]
