# scripts/teacher_load_report.py
"""
Отчёт по нагрузке учителей на основе итогового расписания.

Логика:
- читаем timetable.csv, где уже есть teacher_id;
- считаем:
    * общее число уроков в неделю для каждого учителя;
    * распределение по дням недели;
- сравниваем с лимитами из data/teachers.yaml;
- печатаем краткий текстовый отчёт по каждому учителю.
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


def load_teachers(teachers_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Загружаем информацию об учителях из data/teachers.yaml.

    Возвращаем словарь teacher_id -> данные учителя.
    """
    with teachers_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    teachers_list = data.get("teachers", [])

    teachers_by_id: Dict[str, Dict[str, Any]] = {}
    for t in teachers_list:
        tid = t["id"]
        teachers_by_id[tid] = t

    return teachers_by_id


def load_timetable(timetable_path: Path):
    """
    Читаем timetable.csv и возвращаем строки расписания.
    """
    rows = []
    with timetable_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def main() -> None:
    # Пути к файлам
    teachers_path = Path("data") / "teachers.yaml"
    timetable_path = Path("timetable.csv")

    # Загружаем данные
    teachers = load_teachers(teachers_path)
    timetable_rows = load_timetable(timetable_path)

    # Структуры для подсчёта нагрузки
    # week_load[teacher_id] -> количество уроков в неделю
    week_load = defaultdict(int)

    # day_load[teacher_id][day] -> количество уроков в этот день
    day_load = defaultdict(lambda: defaultdict(int))

    # Проходим по всем урокам и считаем нагрузку
    for row in timetable_rows:
        teacher_id = row.get("teacher_id", "").strip()
        day = row.get("day", "").strip()

        # Пропускаем строки без назначенного учителя
        if not teacher_id:
            continue

        week_load[teacher_id] += 1
        day_load[teacher_id][day] += 1

    # Печатаем отчёт
    print("=== Отчёт по нагрузке учителей ===\n")

    for teacher_id, info in teachers.items():
        name = info.get("name", teacher_id)
        max_per_week = int(info.get("max_lessons_per_week", 0))
        max_per_day = int(info.get("max_lessons_per_day", 0))

        total = week_load.get(teacher_id, 0)

        print(f"Учитель: {name} ({teacher_id})")
        print(f"  Лимит в неделю: {max_per_week} уроков")
        print(f"  Лимит в день:   {max_per_day} уроков")
        print(f"  Фактическая нагрузка в неделю: {total} уроков")

        # Строка с нагрузкой по дням
        day_parts = []
        for day in DAY_ORDER:
            count = day_load[teacher_id].get(day, 0)
            label = DAY_LABELS_RU.get(day, day)
            day_parts.append(f"{label}: {count}")

        print("  По дням: " + ", ".join(day_parts))

        # Простые предупреждения
        if total > max_per_week:
            print("  ⚠ Перегруз по неделе!")

        overloaded_days = [
            day
            for day in DAY_ORDER
            if day_load[teacher_id].get(day, 0) > max_per_day
        ]
        if overloaded_days:
            labels = [DAY_LABELS_RU.get(d, d) for d in overloaded_days]
            print(f"  ⚠ Перегруз по дням: {', '.join(labels)}")

        print()  # пустая строка между учителями


if __name__ == "__main__":
    main()
