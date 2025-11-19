# scripts/class_load_report.py
"""
Отчёт по нагрузке классов с точки зрения СанПиН.

Логика:
- читаем:
    * timetable.csv        — итоговое расписание (class_id, day, slot, subject_id, ...)
    * data/subjects.yaml   — предметы и difficulty_points
    * data/classes.yaml    — классы и их grade (ступень)
    * data/sanpin_limits.yaml — max_points_per_day_by_grade
- для каждого класса и дня считаем сумму баллов (difficulty_points);
- сравниваем с лимитами для соответствующей ступени;
- печатаем отчёт: где укладываемся в норму, а где есть превышения.
"""

from pathlib import Path
from collections import defaultdict
from typing import Dict, Any

import csv
import yaml


DAY_ORDER = ["monday", "tuesday", "wednesday", "thursday", "friday"]
DAY_LABELS_RU = {
    "monday": "Пн",
    "tuesday": "Вт",
    "wednesday": "Ср",
    "thursday": "Чт",
    "friday": "Пт",
}


def load_subject_difficulty(subjects_path: Path) -> Dict[str, int]:
    """
    Загружаем difficulty_points из data/subjects.yaml.

    Возвращаем словарь: subject_id -> difficulty_points.
    """
    with subjects_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    subjects = data.get("subjects", [])
    difficulty: Dict[str, int] = {}

    for subj in subjects:
        subj_id = subj["id"]
        difficulty_points = int(subj.get("difficulty_points", 1))
        difficulty[subj_id] = difficulty_points

    return difficulty


def load_class_grades(classes_path: Path) -> Dict[str, str]:
    """
    Загружаем классы и их ступень (grade) из data/classes.yaml.

    Возвращаем словарь: class_id -> grade (в строковом виде, например "5").
    """
    with classes_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    classes = data.get("classes", [])
    by_id: Dict[str, str] = {}

    for cls in classes:
        cid = cls["id"]
        grade = str(cls.get("grade", ""))
        by_id[cid] = grade

    return by_id


def load_sanpin_limits(sanpin_path: Path) -> Dict[str, Any]:
    """
    Загружаем санпин-лимиты из data/sanpin_limits.yaml.

    Ожидается, что там есть max_points_per_day_by_grade: {grade: max_points}.
    """
    with sanpin_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def load_timetable(timetable_path: Path):
    """
    Читаем timetable.csv и возвращаем список строк расписания.
    """
    rows = []
    with timetable_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def main() -> None:
    base_data_dir = Path("data")

    subjects_path = base_data_dir / "subjects.yaml"
    classes_path = base_data_dir / "classes.yaml"
    sanpin_path = base_data_dir / "sanpin_limits.yaml"
    timetable_path = Path("timetable.csv")

    # Загружаем все необходимые справочники
    subject_difficulty = load_subject_difficulty(subjects_path)
    class_grades = load_class_grades(classes_path)
    sanpin = load_sanpin_limits(sanpin_path)
    timetable_rows = load_timetable(timetable_path)

    max_points_by_grade = sanpin.get("max_points_per_day_by_grade", {})

    # Считаем: class_id -> day -> сумма баллов
    class_day_points = defaultdict(lambda: defaultdict(int))

    for row in timetable_rows:
        class_id = row.get("class_id", "").strip()
        day = row.get("day", "").strip()
        subject_id = row.get("subject_id", "").strip()

        if not class_id or not day or not subject_id:
            continue

        points = subject_difficulty.get(subject_id, 1)
        class_day_points[class_id][day] += points

    print("=== Отчёт по нагрузке классов (СанПиН) ===\n")

    # Проходим по классам в алфавитном порядке
    for class_id in sorted(class_day_points.keys()):
        grade = class_grades.get(class_id, "")
        max_points_for_grade = int(max_points_by_grade.get(str(grade), 0))

        print(f"Класс: {class_id} (ступень: {grade})")
        if max_points_for_grade > 0:
            print(f"  Лимит баллов в день по СанПиН: {max_points_for_grade}")
        else:
            print("  ⚠ Лимит баллов в день для этой ступени не задан в sanpin_limits.yaml")

        # Строка вида: Пн: 16 / 20, Вт: 18 / 20, ...
        day_parts = []
        overloaded_days = []

        for day in DAY_ORDER:
            points = class_day_points[class_id].get(day, 0)
            label = DAY_LABELS_RU.get(day, day)

            if max_points_for_grade > 0:
                part = f"{label}: {points} / {max_points_for_grade}"
                if points > max_points_for_grade:
                    overloaded_days.append(label)
            else:
                part = f"{label}: {points}"

            day_parts.append(part)

        print("  По дням: " + ", ".join(day_parts))

        if overloaded_days:
            print(f"  ⚠ Перегруз по дням: {', '.join(overloaded_days)}")

        print()  # пустая строка между классами


if __name__ == "__main__":
    main()
