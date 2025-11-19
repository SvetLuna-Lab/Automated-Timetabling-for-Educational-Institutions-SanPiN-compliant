# tests/test_teacher_constraints.py
"""
Тесты ограничений по учителям:

- учитель не может вести два урока одновременно (один и тот же день+слот);
- фактическая недельная нагрузка не превышает max_lessons_per_week;
- фактическая нагрузка по дню не превышает max_lessons_per_day.
"""

from pathlib import Path
from collections import defaultdict

import yaml

from src.solvers.ortools_solver import generate_timetable
from src.io.loader import load_all_data


def test_teacher_not_double_booked_and_respects_limits():
    data_dir = Path("data")

    # Загружаем исходные данные (в том числе teachers.yaml)
    data = load_all_data(data_dir)
    teachers = {t["id"]: t for t in data["teachers"]}

    # Генерируем расписание
    timetable_rows = generate_timetable(data_dir)

    # Структуры для проверки
    # (teacher_id, day, slot) -> сколько раз учитель стоит в этом слоте
    slot_usage = defaultdict(int)

    # Нагрузка: teacher_id -> total_week, day -> per_day
    week_load = defaultdict(int)
    day_load = defaultdict(lambda: defaultdict(int))

    for row in timetable_rows:
        teacher_id = row.get("teacher_id", "").strip()
        day = row.get("day", "").strip()
        slot = int(row.get("slot", 0))

        if not teacher_id:
            # Пустой teacher_id означает дефицит учителей — это не ошибка,
            # но такие слоты пропускаем в проверке ограничений.
            continue

        # Проверяем уникальность слота для учителя
        key = (teacher_id, day, slot)
        slot_usage[key] += 1
        assert (
            slot_usage[key] == 1
        ), f"Учитель {teacher_id} дважды поставлен в {day} слот {slot}"

        # Считаем нагрузку
        week_load[teacher_id] += 1
        day_load[teacher_id][day] += 1

    # Проверяем, что никто не превысил указанные лимиты
    for teacher_id, info in teachers.items():
        max_per_week = int(info.get("max_lessons_per_week", 999))
        max_per_day = int(info.get("max_lessons_per_day", 99))

        total = week_load.get(teacher_id, 0)
        assert (
            total <= max_per_week
        ), f"Учитель {teacher_id} перегружен по неделе: {total} > {max_per_week}"

        for day, count in day_load[teacher_id].items():
            assert (
                count <= max_per_day
            ), f"Учитель {teacher_id} перегружен в день {day}: {count} > {max_per_day}"
