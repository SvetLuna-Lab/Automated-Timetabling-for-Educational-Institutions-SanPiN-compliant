# src/solvers/ortools_solver.py
from pathlib import Path
from typing import List, Dict, Any

import yaml


def load_data(data_dir: Path) -> Dict[str, Any]:
    """Загрузка всех YAML-данных из папки data/."""
    def load_yaml(name: str):
        with (data_dir / name).open(encoding="utf-8") as f:
            return yaml.safe_load(f)

    subjects = load_yaml("subjects.yaml")["subjects"]
    classes = load_yaml("classes.yaml")["classes"]
    rooms = load_yaml("rooms.yaml")["rooms"]
    teachers = load_yaml("teachers.yaml")["teachers"]
    sanpin = load_yaml("sanpin_limits.yaml")

    return {
        "subjects": subjects,
        "classes": classes,
        "rooms": rooms,
        "teachers": teachers,
        "sanpin": sanpin,
    }


def _build_weekly_plan_for_class(class_obj: Dict[str, Any],
                                 subjects: List[Dict[str, Any]]) -> Dict[str, int]:
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


def _build_subject_difficulty(subjects: List[Dict[str, Any]]) -> Dict[str, int]:
    """Словарь: subject_id -> difficulty_points."""
    return {
        subj["id"]: int(subj.get("difficulty_points", 1))
        for subj in subjects
    }


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
    - мы идём по дням в порядке убывания коэффициента профиля и
      на каждый день пытаемся набрать максимум предметов, не переламывая лимиты.
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

    # Чтобы не зациклиться, просто один проход по дням и слотам
    for day in day_order:
        lessons_planned = 0
        points_today = 0
        last_subject_id = None

        for slot in range(1, slots_per_day + 1):
            if lessons_planned >= max_lessons_per_day:
                break  # достигли лимита по урокам

            # Кандидаты: предметы, у которых остались часы
            # Отсортируем по трудности (от тяжёлых к лёгким), затем по оставшимся часам
            candidates = [
                (subj_id, remaining[subj_id])
                for subj_id in remaining
                if remaining[subj_id] > 0
            ]
            if not candidates:
                break  # всё уже расписали для этого класса

            candidates.sort(
                key=lambda x: (difficulty.get(x[0], 1), x[1]),
                reverse=True,
            )

            chosen_subject_id = None

            # Попробуем выбрать предмет, который влезет по баллам
            for subj_id, _rem in candidates:
                # избегаем ситуации "тот же предмет подряд", если есть альтернатива
                if subj_id == last_subject_id and len(candidates) > 1:
                    continue

                subj_points = difficulty.get(subj_id, 1)
                if points_today + subj_points <= max_points_per_day:
                    chosen_subject_id = subj_id
                    break

            # Если вообще ничего не влезает по баллам — день "закрываем"
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
                    "teacher_id": "",   # распределение учителей позже
                }
            )

    return timetable_rows


def generate_timetable(data_dir: Path) -> List[Dict[str, Any]]:
    """
    Главная функция для cli.py:
    - загружает YAML-данные;
    - для каждого класса генерирует расписание простым жадным алгоритмом;
    - возвращает список строк расписания (class_id, day, slot, subject_id, ...).

    Это учебный прототип:
    - соблюдаются суточные лимиты по баллам и числу уроков;
    - тяжёлые предметы стараемся поставить в более нагруженные дни;
    - кабинеты и учителя пока не распределяются.
    """
    data = load_data(data_dir)

    subjects = data["subjects"]
    classes = data["classes"]
    sanpin = data["sanpin"]

    timetable: List[Dict[str, Any]] = []

    for class_obj in classes:
        class_rows = _greedy_generate_for_class(class_obj, subjects, sanpin)
        timetable.extend(class_rows)

    return timetable
