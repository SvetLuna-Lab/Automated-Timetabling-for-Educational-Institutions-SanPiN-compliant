# src/models/entities.py
"""
Сущности предметной области для проекта SANPIN-Schedule.

Здесь определены dataclass-описания:
- Subject      — учебный предмет
- SchoolClass  — школьный класс
- Room         — кабинет
- Teacher      — учитель
- TimetableEntry — одна ячейка расписания

А также вспомогательные функции для сборки этих сущностей из словарей,
полученных из YAML (data/*.yaml).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


# ---------- Базовые сущности ----------


@dataclass
class Subject:
    """
    Учебный предмет.

    Пример YAML (subjects.yaml):
      - id: math
        name: "Математика"
        difficulty_points: 4
        weekly_hours_by_grade:
          "5": 5
          "6": 5
    """
    id: str
    name: str
    difficulty_points: int = 1
    weekly_hours_by_grade: Dict[str, int] = field(default_factory=dict)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Subject":
        return Subject(
            id=data["id"],
            name=data.get("name", data["id"]),
            difficulty_points=int(data.get("difficulty_points", 1)),
            weekly_hours_by_grade={
                str(k): int(v)
                for k, v in data.get("weekly_hours_by_grade", {}).items()
            },
        )


@dataclass
class SchoolClass:
    """
    Школьный класс (например, 5А).

    Пример YAML (classes.yaml):
      - id: "5A"
        grade: 5
        size: 25
    """
    id: str
    grade: int
    size: int

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SchoolClass":
        return SchoolClass(
            id=data["id"],
            grade=int(data["grade"]),
            size=int(data["size"]),
        )


@dataclass
class Room:
    """
    Кабинет.

    Пример YAML (rooms.yaml):
      - id: "101"
        name: "Кабинет 101"
        capacity: 28
        type: "общий"
    """
    id: str
    name: str
    capacity: int
    type: str = "общий"

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Room":
        return Room(
            id=data["id"],
            name=data.get("name", data["id"]),
            capacity=int(data.get("capacity", 0)),
            type=data.get("type", "общий"),
        )


@dataclass
class Teacher:
    """
    Учитель.

    Пример YAML (teachers.yaml):
      - id: "t_math_1"
        name: "Иванова И.И."
        subjects: ["math"]
        max_lessons_per_day: 5
        max_lessons_per_week: 25
    """
    id: str
    name: str
    subjects: List[str] = field(default_factory=list)
    max_lessons_per_day: int = 5
    max_lessons_per_week: int = 25

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Teacher":
        return Teacher(
            id=data["id"],
            name=data.get("name", data["id"]),
            subjects=list(data.get("subjects", [])),
            max_lessons_per_day=int(data.get("max_lessons_per_day", 5)),
            max_lessons_per_week=int(data.get("max_lessons_per_week", 25)),
        )


@dataclass
class TimetableEntry:
    """
    Одна ячейка расписания.

    Используется как более строгая альтернатива "сырым" словарям
    с ключами class_id, day, slot, subject_id, room_id, teacher_id.
    """
    class_id: str
    day: str          # "monday"|"tuesday"|...
    slot: int         # номер урока (1..N)
    subject_id: str
    room_id: Optional[str] = ""
    teacher_id: Optional[str] = ""

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "TimetableEntry":
        return TimetableEntry(
            class_id=data["class_id"],
            day=data["day"],
            slot=int(data["slot"]),
            subject_id=data["subject_id"],
            room_id=data.get("room_id", ""),
            teacher_id=data.get("teacher_id", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Удобный экспорт обратно в dict для CSV/JSON."""
        return {
            "class_id": self.class_id,
            "day": self.day,
            "slot": self.slot,
            "subject_id": self.subject_id,
            "room_id": self.room_id or "",
            "teacher_id": self.teacher_id or "",
        }


# ---------- Агрегатор школьных данных ----------


@dataclass
class SchoolData:
    """
    Удобный контейнер для всех сущностей школы.

    Можно использовать в будущем вместо "сырых" словарей из loader:
    - SchoolData.from_raw_yaml(...) соберёт dataclass-объекты
      из словарей, которые возвращает io.loader.load_all_data().
    """
    subjects: List[Subject] = field(default_factory=list)
    classes: List[SchoolClass] = field(default_factory=list)
    rooms: List[Room] = field(default_factory=list)
    teachers: List[Teacher] = field(default_factory=list)
    sanpin: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_raw_yaml(raw: Dict[str, Any]) -> "SchoolData":
        """
        raw ожидается в формате, который сейчас возвращает load_all_data():
        {
            "subjects": [...],
            "classes": [...],
            "rooms": [...],
            "teachers": [...],
            "sanpin": {...},
        }
        """
        return SchoolData(
            subjects=[Subject.from_dict(s) for s in raw.get("subjects", [])],
            classes=[SchoolClass.from_dict(c) for c in raw.get("classes", [])],
            rooms=[Room.from_dict(r) for r in raw.get("rooms", [])],
            teachers=[Teacher.from_dict(t) for t in raw.get("teachers", [])],
            sanpin=raw.get("sanpin", {}),
        )

    # Дополнительно: набор быстрых индексов (по id), если понадобится
    def subjects_by_id(self) -> Dict[str, Subject]:
        return {s.id: s for s in self.subjects}

    def classes_by_id(self) -> Dict[str, SchoolClass]:
        return {c.id: c for c in self.classes}

    def rooms_by_id(self) -> Dict[str, Room]:
        return {r.id: r for r in self.rooms}

    def teachers_by_id(self) -> Dict[str, Teacher]:
        return {t.id: t for t in self.teachers}
