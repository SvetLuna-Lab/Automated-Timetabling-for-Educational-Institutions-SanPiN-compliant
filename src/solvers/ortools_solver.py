# src/solvers/ortools_solver.py
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

from ..io.loader import load_all_data


def _build_weekly_plan_for_class(
    class_obj: Dict[str, Any],
    subjects: List[Dict[str, Any]],
) -> Dict[str, int]:
    """
    Строим недельный план для конкретного класса:
    subject_id -> кол-во уроков в неделю.

    Используем поле weekly_hours_by_grade в subjects.yaml.
    """
    grade_str = str(class_obj["grade"])
    weekly_plan: Dict[str, int] = {}

    for subj in subjects:
        subj_id = subj["id"]
        weekly_by_grade = subj.get("weekly_hours_by_grade", {})
        if grade_str in weekly_by_grade:
            weekly_plan[subj_id] = weekly_by_grade[grade_str]

    return weekly_plan


def _build_subject_difficulty(
    subjects: List[Dict[str, Any]]
) -> Dict[str, int]:
    """Словарь: subject_id -> difficulty_points."""
    return {
        subj["id"]: int(subj.get("difficulty_points", 1))
        for subj in subjects
    }


def _build_teacher_state(teachers: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Подготовка структуры состояния для каждого учителя.

    На выходе:
    teacher_id -> {
        "subjects": set([...]),
        "max_per_week": int,
        "max_per_day": int,
        "week_load": int,
        "day_load": {day: int, ...}
    }
    """
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]

    state: Dict[str, Dict[str, Any]] = {}

    for t in teachers:
        tid = t["id"]
        subjects = set(t.get("subjects", []))
        max_per_week = int(t.get("max_lessons_per_week", 999))
        max_per_day = int(t.get("max_lessons_per_day", 8))

        state[tid] = {
            "subjects": subjects,
            "max_per_week": max_per_week,
            "max_per_day": max_per_day,
            "week_load": 0,
            "day_load": {d: 0 for d in days},
        }

    return state


def _assign_teachers_greedy(
    timetable_rows: List[Dict[str, Any]],
    teachers: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Жадное распределение уроков по учителям.

    На входе:
    - список строк расписания по классам (class_id, day, slot, subject_id, room_id, teacher_id="");
    - список учителей с предметами и лимитами.

    Логика:
    - для каждого урока ищем учителей, которые:
        * ведут этот предмет (subject_id ∈ subjects),
        * не заняты в этот день/урок,
        * не превысили max_lessons_per_day и max_lessons_per_week;
    - из подходящих выбираем того, у кого наименьшая текущая недельная нагрузка
      (чтобы нагрузка по людям была более ровной);
    - если никого не нашли — оставляем teacher_id = "" (показывает дефицит ставок).
    """
    # Состояние по учителям
    teacher_state = _build_teacher_state(teachers)

    # Занятость: (teacher_id, day, slot) -> bool
    busy: Dict[tuple, bool] = defaultdict(bool)

    # Для стабильности отсортируем уроки:
    # сначала по дню, потом по номеру слота, потом по предмету и классу.
    def sort_key(row: Dict[str, Any]):
        return (row["day"], row["slot"], row["subject_id"], row["class_id"])

    sorted_rows = sorted(timetable_rows, key=sort_key)

    for row in sorted_rows:
        day = row["day"]
        slot = row["slot"]
        subject_id = row["subject_id"]

        candidates = []
        for t in teachers:
            tid = t["id"]
            st = teacher_state[tid]

            # учитель не ведёт этот предмет
            if subject_id not in st["subjects"]:
                continue

            # занят в этом слоте
            if busy[(tid, day, slot)]:
                continue

            # превышен недельный или дневной лимит
            if st["week_load"] >= st["max_per_week"]:
                continue
            if st["day_load"][day] >= st["max_per_day"]:
                continue

            candidates.append(tid)

        if not candidates:
            # никого не удалось поставить — фиксируем пустой teacher_id
            row["teacher_id"] = ""
            continue

        # выбираем учителя с минимальной недельной нагрузкой
        best_tid = min(candidates, key=lambda tid: teacher_state[tid]["week_load"])

        row["teacher_id"] = best_tid
        teacher_state[best_tid]["week_load"] += 1
        teacher_state[best_tid]["day_load"][day] += 1
        busy[(best_tid, day, slot)] = True

    return timetable_rows


def _greedy_generate_for_class(
    class_obj: Dict[str, Any],
    subjects: List[Dict[str, Any]],
    sanpin: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Простейший жадный генератор расписания для одного класса.

    Идея:
    - есть недельный план (сколько уроков каждого предмета нужно);
    - есть лимит уроков и лимит баллов в день;
    - есть профиль "нагруженности" дней (target_load_profile);
    - идём по дням в порядке убывания коэффициента профиля и
      на каждый день набираем максимум предметов, не переламывая лимиты.
    """

    # Базовые параметры
    grade_str = str(class_obj["grade"])
    max_lessons_by_grade = sanpin["max_lessons_per_day_by_grade"]
    max_points_by_grade = sanpin["max_points_per_day_by_grade"]
    slots_per_day = int(sanpin["slots_per_day"])

    max_lessons_per_day = int(max_lessons_by_grade.get(grade_str, slots_per_day))
    max_points_per_day = int(max_points_by_grade.get(grade_str, 20))

    target_profile = sanpin.get("target_load_profile", {})
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]

    # Упорядочим дни недели по убыванию желательной нагрузки (двугорбый профиль)
    def profile_value(day: str) -> float:
        return float(target_profile.get(day, 1.0))

    day_order = sorted(days, key=profile_value, reverse=True)

    # Недельный план и трудности
    weekly_plan = _build_weekly_plan_for_class(class_obj, subjects)
    difficulty = _build_subject_difficulty(subjects)

    # Сколько уроков осталось поставить по каждому предмету
    remaining = dict(weekly_plan)

    timetable_rows: List[Dict[str, Any]] = []

    # Один проход по дням и слотам
    for day in day_order:
        lessons_planned = 0
        points_today = 0
        last_subject_id = None

        for slot in range(1, slots_per_day + 1):
            if lessons_planned >= max_lessons_per_day:
                # достигли лимита по урокам на день
                break

            # Кандидаты: предметы, у которых остались часы
            candidates = [
                (subj_id, remaining[subj_id])
                for subj_id in remaining
                if remaining[subj_id] > 0
            ]
            if not candidates:
                # всё уже расписали для этого класса
                break

            # От тяжёлых к лёгким, затем по оставшимся часам
            candidates.sort(
                key=lambda x: (difficulty.get(x[0], 1), x[1]),
                reverse=True,
            )

            chosen_subject_id = None

            # Выбираем предмет, который влезет по баллам
            for subj_id, _rem in candidates:
                # избегаем "тот же предмет подряд", если есть альтернатива
                if subj_id == last_subject_id and len(candidates) > 1:
                    continue

                subj_points = difficulty.get(subj_id, 1)
                if points_today + subj_points <= max_points_per_day:
                    chosen_subject_id = subj_id
                    break

            # Если ничего не влезает по баллам — день "закрываем"
            if chosen_subject_id is None:
                break

            # Фиксируем выбор
            remaining[chosen_subject_id] -= 1
            lessons_planned += 1
            points_today += difficulty.get(chosen_subject_id, 1)
            last_subject_id = chosen_subject_id

            timetable_rows.append(
                {
                    "class_id": class_obj["id"],
                    "day": day,
                    "slot": slot,
                    "subject_id": chosen_subject_id,
                    "room_id": "",      # распределение кабинетов позже
                    "teacher_id": "",   # будет заполнен на втором шаге
                }
            )

    return timetable_rows


def generate_timetable(data_dir: Path) -> List[Dict[str, Any]]:
    """
    Главная функция для cli.py:
    - загружает YAML-данные через io.loader.load_all_data;
    - для каждого класса генерирует расписание жадным алгоритмом по СанПиН;
    - затем жадно распределяет уроки по учителям;
    - возвращает список строк расписания (class_id, day, slot, subject_id, room_id, teacher_id, ...).

    Это учебный прототип:
    - соблюдаются суточные лимиты по баллам и числу уроков для класса;
    - тяжёлые предметы стараемся ставить в более нагруженные дни;
    - кабинеты пока не распределяются;
    - учителя назначаются с учётом их недельной и дневной нагрузки.
    """
    data = load_all_data(data_dir)

    subjects = data["subjects"]
    classes = data["classes"]
    teachers = data["teachers"]
    sanpin = data["sanpin"]

    timetable: List[Dict[str, Any]] = []

    for class_obj in classes:
        class_rows = _greedy_generate_for_class(class_obj, subjects, sanpin)
        timetable.extend(class_rows)

    # Второй шаг: распределение уроков по учителям
    timetable_with_teachers = _assign_teachers_greedy(timetable, teachers)

    return timetable_with_teachers

