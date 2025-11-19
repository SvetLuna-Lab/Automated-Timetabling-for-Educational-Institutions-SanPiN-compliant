# api/app.py
"""
Простой API-сервис для генерации школьного расписания.

Идея:
- школа (или админский интерфейс) обращается к HTTP-эндпоинту;
- сервер вызывает существующий планировщик generate_timetable(...);
- отдаёт расписание в виде JSON-списка строк.
"""

from pathlib import Path
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

from src.solvers.ortools_solver import generate_timetable

# Папка с YAML-данными (subjects.yaml, classes.yaml, teachers.yaml, sanpin_limits.yaml)
DATA_DIR = Path("data")

app = FastAPI(
    title="School Timetabling SanPiN API",
    description="Сервис для генерации школьного расписания с учётом СанПиН и нагрузки учителей.",
    version="0.1.0",
)


class TimetableRow(BaseModel):
    """
    Строка расписания для ответа API.

    Содержимое совпадает с тем, что у нас уже есть в generate_timetable(...):
    - class_id   — класс (5A, 7B и т.п.);
    - day        — день недели (monday..friday);
    - slot       — номер урока;
    - subject_id — предмет;
    - room_id    — кабинет (может быть пустой строкой);
    - teacher_id — назначенный учитель (может быть пустой строкой, если не хватает ставок).
    """
    class_id: str
    day: str
    slot: int
    subject_id: str
    room_id: str
    teacher_id: str


@app.get("/health")
def health() -> dict:
    """
    Простейшая проверка «жив ли» сервис.

    Можно дергать из мониторинга или просто из браузера.
    """
    return {"status": "ok"}


@app.get("/generate-timetable", response_model=List[TimetableRow])
def generate_timetable_endpoint() -> List[TimetableRow]:
    """
    Эндпоинт для генерации расписания.

    На первом шаге не принимаем никакого тела запроса:
    - берём все данные из папки data/;
    - вызываем планировщик;
    - возвращаем полный список строк расписания в JSON.

    В будущем сюда можно добавить параметры:
    - фильтрацию по конкретному классу,
    - выбор профиля нагрузки,
    - альтернативные наборы данных и т.п.
    """
    rows = generate_timetable(DATA_DIR)

    result: List[TimetableRow] = []
    for row in rows:
        result.append(
            TimetableRow(
                class_id=str(row.get("class_id", "")),
                day=str(row.get("day", "")),
                slot=int(row.get("slot", 0)),
                subject_id=str(row.get("subject_id", "")),
                room_id=str(row.get("room_id", "")),
                teacher_id=str(row.get("teacher_id", "")),
            )
        )

    return result
