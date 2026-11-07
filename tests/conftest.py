from datetime import date, timedelta
from pathlib import Path

import pytest


@pytest.fixture
def four_flights_per_day_csv(tmp_path: Path) -> Path:
    """24 строки: 6 дней по 4 рейса, в каждой хронологической части оба класса."""
    lines = ["FlightDate,DepHour,IsWeekend,ArrDelay"]
    start = date(2026, 1, 5)
    for day in range(6):
        current = start + timedelta(days=day)
        weekend = int(current.weekday() >= 5)
        for slot, hour in enumerate((6, 10, 14, 18)):
            delay = 30 if (day * 4 + slot) % 2 == 0 else 5
            lines.append(f"{current.isoformat()},{hour},{weekend},{delay}")
    path = tmp_path / "four_per_day.csv"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path
