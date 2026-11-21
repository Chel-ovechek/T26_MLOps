"""Проверки логики scripts/container_smoke.py без сети и Docker."""

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "container_smoke.py"
spec = importlib.util.spec_from_file_location("container_smoke", SCRIPT)
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)

GOOD = {
    "delay_probability": 0.7,
    "delayed": True,
    "threshold": 0.5,
    "model_version": "0.2.0",
    "request_id": "abc",
}


def fake_requests(prediction: dict):
    def fake(url: str, payload: dict | None = None) -> dict:
        return {"status": "ready"} if url.endswith("/readyz") else prediction

    return fake


def test_run_smoke_returns_report(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(smoke, "request_json", fake_requests(GOOD))
    report = smoke.run_smoke("http://x/", timeout=1)
    assert report["ready"] is True
    assert report["response"] == GOOD
    assert report["base_url"] == "http://x"


@pytest.mark.parametrize("probability", [1.5, -0.1, None, "0.5", True])
def test_run_smoke_rejects_bad_probability(
    monkeypatch: pytest.MonkeyPatch, probability: object
) -> None:
    monkeypatch.setattr(
        smoke, "request_json", fake_requests({**GOOD, "delay_probability": probability})
    )
    with pytest.raises(RuntimeError, match="delay_probability"):
        smoke.run_smoke("http://x", timeout=1)


@pytest.mark.parametrize("missing", ["model_version", "request_id"])
def test_run_smoke_requires_version_and_request_id(
    monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    monkeypatch.setattr(smoke, "request_json", fake_requests({**GOOD, missing: ""}))
    with pytest.raises(RuntimeError, match="model_version или request_id"):
        smoke.run_smoke("http://x", timeout=1)


def test_wait_until_ready_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    def refused(url: str, payload: dict | None = None) -> dict:
        raise ConnectionRefusedError("connection refused")

    monkeypatch.setattr(smoke, "request_json", refused)
    with pytest.raises(TimeoutError, match="не стал ready"):
        smoke.wait_until_ready("http://x", timeout=0.2)


def test_main_returns_1_and_writes_no_report_on_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    output = tmp_path / "smoke.json"
    monkeypatch.setattr(smoke, "request_json", fake_requests({**GOOD, "request_id": ""}))
    monkeypatch.setattr("sys.argv", ["container_smoke.py", "--output", str(output)])
    assert smoke.main() == 1
    assert not output.exists()
    assert "SMOKE FAILED" in capsys.readouterr().err
