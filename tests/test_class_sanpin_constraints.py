# tests/test_class_sanpin_constraints.py
"""
Тест соблюдения СанПиН по баллам для классов:

- для каждого класса и дня считаем суммарные difficulty_points;
- сравниваем с max_points_per_day_by_grade для соответствующей ступени (grade);
- если лимит для ступени задан, дневная сумма не должна его превышать.
"""

from pathlib import Path
from collections import defaultdict
from typing import Dict, Any

from src.solvers.ortools_solver import generate_timetable
from src.io.loader import load_all_data


def _build_subject_difficulty(subjects: Dict[str, Any]) -> Dict[str, int]:
    """
    Вспомогательная функция: subject_id -> difficulty_points.
    """
    difficulty = {}
    for subj in subjects:
        subj_id = subj["id"]
        difficulty[subj_id] = int(subj.get("difficulty_points", 1))
    return difficulty


def test_class_daily_points_respect_sanpin_limits():
    data_dir = Path("data")

    # Загружаем все YAML-данные
    data = load_all_data(data_dir)
    subjects = data["subjects"]
    classes = data["classes"]
    sanpin = data["sanpin"]

    # Карты по id
    subject_difficulty = _build_subject_difficulty(subjects)
    class_grades = {cls["id"]: str(cls.get("grade", "")) for cls in classes}
    max_points_by_grade = sanpin.get("max_points_per_day_by_grade", {})

    # Генерируем расписание
    timetable_rows = generate_timetable(data_dir)

    # class_id -> day -> суммарные баллы
    class_day_points = defaultdict(lambda: defaultdict(int))

    for row in timetable_rows:
        class_id = row.get("class_id", "").strip()
        day = row.get("day", "").strip()
        subject_id = row.get("subject_id", "").strip()

        if not class_id or not day or not subject_id:
            continue

        points = subject_difficulty.get(subject_id, 1)
        class_day_points[class_id][day] += points

    # Проверяем по всем классам, для которых есть лимиты
    for class_id, days in class_day_points.items():
        grade = class_grades.get(class_id, "")
        max_points = max_points_by_grade.get(str(grade))

        # Если для этой ступени лимит не задан в sanpin_limits.yaml — пропускаем
        if max_points is None:
            continue

        max_points = int(max_points)

        for day, total_points in days.items():
            assert (
                total_points <= max_points
            ), (
                f"Класс {class_id} перегружен по СанПиН в день {day}: "
                f"{total_points} баллов > {max_points}"
            )
