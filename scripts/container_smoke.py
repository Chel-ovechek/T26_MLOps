"""Smoke test контейнера ЛР6: ждёт /readyz, делает /predict, пишет компактный отчёт."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REQUEST = {"dep_hour": 9, "is_weekend": 0}


def request_json(url: str, payload: dict[str, int] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET" if data is None else "POST",
    )
    with urllib.request.urlopen(request, timeout=3) as response:
        if response.status != 200:
            raise RuntimeError(f"Неожиданный HTTP status: {response.status}")
        return json.loads(response.read().decode("utf-8"))


def wait_until_ready(base_url: str, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while True:
        try:
            if request_json(f"{base_url}/readyz").get("status") == "ready":
                return
        except (OSError, ValueError, urllib.error.URLError) as error:
            last_error = error
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Сервис не стал ready за {timeout:.1f} с: {last_error}")
        time.sleep(0.5)


def run_smoke(base_url: str, timeout: float) -> dict[str, Any]:
    base_url = base_url.rstrip("/")
    wait_until_ready(base_url, timeout)
    prediction = request_json(f"{base_url}/predict", REQUEST)
    probability = prediction.get("delay_probability")
    if (
        isinstance(probability, bool)
        or not isinstance(probability, (int, float))
        or not 0.0 <= probability <= 1.0
    ):
        raise RuntimeError("delay_probability отсутствует или находится вне [0, 1]")
    if not prediction.get("model_version") or not prediction.get("request_id"):
        raise RuntimeError("Ответ не содержит model_version или request_id")
    return {"base_url": base_url, "ready": True, "request": REQUEST, "response": prediction}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run_smoke(args.base_url, args.timeout)
    except (TimeoutError, RuntimeError, OSError, ValueError) as error:
        print(f"SMOKE FAILED: {error}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
