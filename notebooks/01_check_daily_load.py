"""
notebooks/01_check_daily_load.py

Проверка суточной нагрузки по баллам для каждого класса
на основе:
- data/subjects.yaml
- data/sanpin_limits.yaml
- timetable.csv (результат работы генератора расписания)

Скрипт печатает отчёт вида:
Класс 5A
  Пн (monday):  2 балла из лимита 20 — OK
  Вт (tuesday): 20 баллов из лимита 20 — OK
  ...
"""

from pathlib import Path
from collections import defaultdict
import csv
import yaml


# Отображение английских названий дней в русские сокращения
DAY_LABELS_RU = {
    "monday": "Пн",
    "tuesday": "Вт",
    "wednesday": "Ср",
    "thursday": "Чт",
    "friday": "Пт",
}


def load_subject_difficulty(data_dir: Path) -> dict:
    """Читаем трудность предметов из data/subjects.yaml: subject_id -> difficulty_points."""
    with (data_dir / "subjects.yaml").open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    difficulty = {}
    for subj in data["subjects"]:
        subj_id = subj["id"]
        difficulty[subj_id] = int(subj.get("difficulty_points", 1))
    return difficulty


def load_sanpin_limits(data_dir: Path) -> dict:
    """Читаем лимиты СанПиН: max_points_per_day_by_grade и т.п."""
    with (data_dir / "sanpin_limits.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_classes(data_dir: Path) -> list:
    """Читаем список классов с их ступенью (grade) из data/classes.yaml."""
    with (data_dir / "classes.yaml").open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["classes"]


def load_timetable(csv_path: Path) -> list:
    """Читаем timetable.csv (разделитель ';')."""
    rows = []
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            # slot можно привести к int, если потребуется
            row["slot"] = int(row["slot"])
            rows.append(row)
    return rows


def compute_daily_loads(
    timetable: list, difficulty: dict
) -> dict:
    """
    Возвращает словарь:
    loads[class_id][day] = суммарное количество баллов за все уроки в этот день.
    """
    loads = defaultdict(lambda: defaultdict(int))

    for row in timetable:
        class_id = row["class_id"]
        day = row["day"]
        subj_id = row["subject_id"]
        points = difficulty.get(subj_id, 1)
        loads[class_id][day] += points

    return loads


def build_grade_map(classes: list) -> dict:
    """
    Возвращает словарь:
    class_id -> grade (строкой).
    """
    result = {}
    for c in classes:
        result[c["id"]] = str(c["grade"])
    return result


def main():
    base_dir = Path(__file__).resolve().parents[1]  # корень проекта (school-timetabling-sanpin/)
    data_dir = base_dir / "data"
    csv_path = base_dir / "timetable.csv"

    # Загрузка данных
    difficulty = load_subject_difficulty(data_dir)
    sanpin = load_sanpin_limits(data_dir)
    classes = load_classes(data_dir)
    timetable = load_timetable(csv_path)

    loads = compute_daily_loads(timetable, difficulty)
    grade_map = build_grade_map(classes)

    max_points_by_grade = sanpin.get("max_points_per_day_by_grade", {})
    days_order = ["monday", "tuesday", "wednesday", "thursday", "friday"]

    # Печать отчёта
    for class_id in sorted(loads.keys()):
        grade_str = grade_map.get(class_id, "?")
        max_points = int(max_points_by_grade.get(grade_str, 0))

        print(f"Класс {class_id} (ступень {grade_str})")
        for day in days_order:
            ru = DAY_LABELS_RU.get(day, day)
            value = loads[class_id].get(day, 0)
            status = "OK"
            if max_points and value > max_points:
                status = "ПРЕВЫШЕНИЕ!"
            print(f"  {ru} ({day}): {value:2d} баллов из лимита {max_points} — {status}")
        print()


if __name__ == "__main__":
    main()
