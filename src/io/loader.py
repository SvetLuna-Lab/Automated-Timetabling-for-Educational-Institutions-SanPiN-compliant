# src/io/loader.py
"""
Модуль загрузки входных данных для проекта SANPIN-Schedule.

Содержит функции:
- load_all_data(...)         — загрузка всех YAML из папки data/
- load_subject_difficulty(...) — словарь трудности предметов
- load_sanpin_limits(...)    — параметры лимитов
- load_classes(...)          — список классов
"""

from pathlib import Path
from typing import Dict, Any, List

import yaml


def _load_yaml(path: Path) -> Any:
    """Внутренняя функция: безопасная загрузка YAML."""
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


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
        "subjects": [...],
        "classes": [...],
        "rooms": [...],
        "teachers": [...],
        "sanpin": {...},
    }
    """
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


def load_subject_difficulty(data_dir: Path) -> Dict[str, int]:
    """
    subject_id -> difficulty_points (целое число).

    Берёт значения из data/subjects.yaml.
    """
    subjects = _load_yaml(data_dir / "subjects.yaml")["subjects"]
    difficulty: Dict[str, int] = {}
    for subj in subjects:
        subj_id = subj["id"]
        difficulty[subj_id] = int(subj.get("difficulty_points", 1))
    return difficulty


def load_sanpin_limits(data_dir: Path) -> Dict[str, Any]:
    """Читает data/sanpin_limits.yaml."""
    return _load_yaml(data_dir / "sanpin_limits.yaml")


def load_classes(data_dir: Path) -> List[Dict[str, Any]]:
    """Читает data/classes.yaml и возвращает список описаний классов."""
    return _load_yaml(data_dir / "classes.yaml")["classes"]


def load_subjects(data_dir: Path) -> List[Dict[str, Any]]:
    """Читает data/subjects.yaml и возвращает список описаний предметов."""
    return _load_yaml(data_dir / "subjects.yaml")["subjects"]


def load_rooms(data_dir: Path) -> List[Dict[str, Any]]:
    """Читает data/rooms.yaml и возвращает список кабинетов."""
    return _load_yaml(data_dir / "rooms.yaml")["rooms"]


def load_teachers(data_dir: Path) -> List[Dict[str, Any]]:
    """Читает data/teachers.yaml и возвращает список учителей."""
    return _load_yaml(data_dir / "teachers.yaml")["teachers"]
