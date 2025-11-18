# src/io/exporter.py
"""
Модуль экспорта расписания для проекта SANPIN-Schedule.

Содержит функции:
- export_timetable_csv(...) — сохранить расписание в CSV
"""

from pathlib import Path
from typing import List, Dict, Any
import csv


# Поля по умолчанию для выгрузки расписания
DEFAULT_FIELDNAMES = [
    "class_id",
    "day",
    "slot",
    "subject_id",
    "room_id",
    "teacher_id",
]


def export_timetable_csv(
    timetable: List[Dict[str, Any]],
    output_path: Path,
    fieldnames: List[str] = None,
    encoding: str = "utf-8",
) -> None:
    """
    Сохраняет расписание в CSV-файл.

    Ожидается, что timetable — это список словарей вида:
    {
        "class_id": ...,
        "day": ...,
        "slot": ...,
        "subject_id": ...,
        "room_id": ...,
        "teacher_id": ...,
    }

    Разделитель — запятая (стандартный CSV), чтобы GitHub и Excel
    корректно распознавали формат.
    """
    if fieldnames is None:
        fieldnames = DEFAULT_FIELDNAMES

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in timetable:
            writer.writerow(row)
