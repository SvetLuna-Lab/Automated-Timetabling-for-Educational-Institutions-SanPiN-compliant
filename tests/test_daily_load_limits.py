# tests/test_daily_load_limits.py
"""
Проверка того, что жадный генератор расписания
соблюдает:
- максимальное число уроков в день;
- максимальную суточную нагрузку в баллах (СанПиН-подобный лимит).
"""

from pathlib import Path
from collections import defaultdict
import csv
import yaml

from src.solvers.ortools_solver import generate_timetable


def load_sanpin(data_dir: Path) -> dict:
    with (data_dir / "sanpin_limits.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_classes(data_dir: Path) -> list:
    with (data_dir / "classes.yaml").open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["classes"]


def load_subject_difficulty(data_dir: Path) -> dict:
    with (data_dir / "subjects.yaml").open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    diff = {}
    for subj in data["subjects"]:
        diff[subj["id"]] = int(subj.get("difficulty_points", 1))
    return diff


def compute_loads_from_timetable(timetable, difficulty):
    """
    Возвращает:
    - daily_points[class_id][day] = сумма баллов;
    - daily_lessons[class_id][day] = число уроков.
    """
    daily_points = defaultdict(lambda: defaultdict(int))
    daily_lessons = defaultdict(lambda: defaultdict(int))

    for row in timetable:
        c = row["class_id"]
        d = row["day"]
        s = row["subject_id"]
        daily_points[c][d] += difficulty.get(s, 1)
        daily_lessons[c][d] += 1

    return daily_points, daily_lessons


def test_daily_limits_not_exceeded():
    """
    Генерируем расписание и проверяем, что:
    - по каждому классу и дню сумма баллов <= max_points_per_day_by_grade;
    - число уроков <= max_lessons_per_day_by_grade.
    """
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"

    sanpin = load_sanpin(data_dir)
    classes = load_classes(data_dir)
    difficulty = load_subject_difficulty(data_dir)

    max_points_by_grade = {
        str(k): int(v)
        for k, v in sanpin.get("max_points_per_day_by_grade", {}).items()
    }
    max_lessons_by_grade = {
        str(k): int(v)
        for k, v in sanpin.get("max_lessons_per_day_by_grade", {}).items()
    }

    # генерируем расписание напрямую, не читая CSV
    timetable = generate_timetable(data_dir)

    daily_points, daily_lessons = compute_loads_from_timetable(
        timetable, difficulty
    )

    class_grade = {c["id"]: str(c["grade"]) for c in classes}

    for class_id, days_points in daily_points.items():
        grade = class_grade.get(class_id)
        # если в sanpin нет ограничений для ступени, тест на этот класс пропускаем
        if grade not in max_points_by_grade or grade not in max_lessons_by_grade:
            continue

        max_points = max_points_by_grade[grade]
        max_lessons = max_lessons_by_grade[grade]

        for day, pts in days_points.items():
            lessons = daily_lessons[class_id][day]
            assert pts <= max_points, (
                f"Класс {class_id}, день {day}: {pts} баллов > лимита {max_points}"
            )
            assert lessons <= max_lessons, (
                f"Класс {class_id}, день {day}: {lessons} уроков > лимита {max_lessons}"
            )
