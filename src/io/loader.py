# src/io/loader.py
"""
Модуль загрузки входных данных для проекта SANPIN-Schedule.

Содержит функции:

- load_all_data(data_dir)  -> dict
    Загружает "сырые" словари из YAML (subjects, classes, rooms, teachers, sanpin).
    Формат совместим с текущим решателем generate_timetable.

- load_school_data(data_dir) -> SchoolData
    Обёртка над load_all_data: собирает dataclass-объекты (Subject, SchoolClass, Room, Teacher)
    в контейнер SchoolData.

- load_subject_difficulty(data_dir) -> dict[str, int]
- load_sanpin_limits(data_dir)     -> dict
- load_classes(data_dir)           -> list[dict]
- load_subjects(data_dir)          -> list[dict]
- load_rooms(data_dir)             -> list[dict]
- load_teachers(data_dir)          -> list[dict]
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

import yaml

from ..models.entities import SchoolData


def _load_yaml(path: Path) -> Any:
    """Внутренняя функция: безопасная загрузка YAML."""
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Сырые словари (для обратной совместимости с существующим кодом)
# ---------------------------------------------------------------------------


def load_all_data(data_dir: Path) -> Dict[str, Any]:
    """
    Загружает все основные YAML-файлы из папки data/.

    Ожидаются файлы:
    - subjects.yaml
    - classes.yaml
    - rooms.yaml
    - teachers.yaml
    - sanpin_limits.yaml

    Возвращает словарь:
    {
        "subjects": [...],   # список dict'ов
        "classes": [...],
        "rooms": [...],
        "teachers": [...],
        "sanpin": {...},
    }

    Этот формат совместим с текущей реализацией generate_timetable
    в src/solvers/ortools_solver.py.
    """
    data_dir = Path(data_dir)

    subjects = _load_yaml(data_dir / "subjects.yaml")["subjects"]
    classes = _load_yaml(data_dir / "classes.yaml")["classes"]
    rooms = _load_yaml(data_dir / "rooms.yaml")["rooms"]
    teachers = _load_yaml(data_dir / "teachers.yaml")["teachers"]
    sanpin = _load_yaml(data_dir / "sanpin_limits.yaml")

    return {
        "subjects": subjects,
        "classes": classes,
        "rooms": rooms,
        "teachers": teachers,
        "sanpin": sanpin,
    }


# ---------------------------------------------------------------------------
# Dataclass-обёртка (новый "инженерный" уровень)
# ---------------------------------------------------------------------------


def load_school_data(data_dir: Path) -> SchoolData:
    """
    Загружает все данные школы и возвращает объект SchoolData
    с dataclass-сущностями (Subject, SchoolClass, Room, Teacher).

    Внутри использует load_all_data(...), так что структура YAML
    остаётся общей для "сырых" словарей и dataclass-слоя.
    """
    raw = load_all_data(data_dir)
    return SchoolData.from_raw_yaml(raw)


# ---------------------------------------------------------------------------
# Удобные частичные загрузчики
# ---------------------------------------------------------------------------


def load_subject_difficulty(data_dir: Path) -> Dict[str, int]:
    """
    subject_id -> difficulty_points (целое число).

    Берёт значения из data/subjects.yaml.
    Удобно для проверки суточной нагрузки по баллам.
    """
    data_dir = Path(data_dir)
    subjects = _load_yaml(data_dir / "subjects.yaml")["subjects"]

    difficulty: Dict[str, int] = {}
    for subj in subjects:
        subj_id = subj["id"]
        difficulty[subj_id] = int(subj.get("difficulty_points", 1))
    return difficulty


def load_sanpin_limits(data_dir: Path) -> Dict[str, Any]:
    """Читает data/sanpin_limits.yaml и возвращает словарь с лимитами."""
    data_dir = Path(data_dir)
    return _load_yaml(data_dir / "sanpin_limits.yaml")


def load_classes(data_dir: Path) -> List[Dict[str, Any]]:
    """Читает data/classes.yaml и возвращает список описаний классов (dict)."""
    data_dir = Path(data_dir)
    return _load_yaml(data_dir / "classes.yaml")["classes"]


def load_subjects(data_dir: Path) -> List[Dict[str, Any]]:
    """Читает data/subjects.yaml и возвращает список описаний предметов (dict)."""
    data_dir = Path(data_dir)
    return _load_yaml(data_dir / "subjects.yaml")["subjects"]


def load_rooms(data_dir: Path) -> List[Dict[str, Any]]:
    """Читает data/rooms.yaml и возвращает список кабинетов (dict)."""
    data_dir = Path(data_dir)
    return _load_yaml(data_dir / "rooms.yaml")["rooms"]


def load_teachers(data_dir: Path) -> List[Dict[str, Any]]:
    """Читает data/teachers.yaml и возвращает список учителей (dict)."""
    data_dir = Path(data_dir)
    return _load_yaml(data_dir / "teachers.yaml")["teachers"]
