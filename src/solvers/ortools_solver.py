# src/solvers/ortools_solver.py
from pathlib import Path
from typing import List, Dict

import yaml

try:
    from ortools.sat.python import cp_model
except ImportError:
    cp_model = None  # Чтобы файл импортировался даже без ortools


def load_data(data_dir: Path) -> Dict:
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


def generate_timetable(data_dir: Path) -> List[Dict]:
    """
    Главная функция: на вход — папка с YAML, на выход — список строк расписания.

    Пока это учебный каркас:
    - загружаем данные;
    - если ortools не установлен, возвращаем пустое расписание;
    - в дальнейшем здесь будет построение модели CP-SAT.
    """
    data = load_data(data_dir)

    if cp_model is None:
        # Заглушка: можно вывести предупреждение или сгенерировать простейшее фиктивное расписание.
        print("WARNING: ortools не установлен. Возвращаю пустое расписание.")
        return []

    model = cp_model.CpModel()

    classes = data["classes"]
    subjects = data["subjects"]
    rooms = data["rooms"]
    sanpin = data["sanpin"]

    # Пример: задаём базовые параметры
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    slots_per_day = sanpin["slots_per_day"]

    # Индексируем сущности для удобства
    class_ids = [c["id"] for c in classes]
    subject_ids = [s["id"] for s in subjects]
    room_ids = [r["id"] for r in rooms]

    # TODO: добавить учителей и связь предметов с учителями

    # ----- Переменные -----
    # x[(class_id, day, slot, subject_id)] = 0/1 — стоит ли предмет в этом слоте
    x = {}
    for c in class_ids:
        for d in days:
            for p in range(1, slots_per_day + 1):
                for s in subject_ids:
                    x[(c, d, p, s)] = model.NewBoolVar(f"x_{c}_{d}_{p}_{s}")

    # Здесь же будут переменные для кабинетов, учителей и т.д.

    # ----- Ограничения (каркас, без реализации) -----

    # 1) В каждом слоте для класса — не более одного предмета
    # for c in class_ids:
    #     for d in days:
    #         for p in range(1, slots_per_day + 1):
    #             model.Add(
    #                 sum(x[(c, d, p, s)] for s in subject_ids) <= 1
    #             )

    # 2) Выполнение недельного плана по предметам
    # (нужно рассчитать, сколько уроков в неделю у класса по каждому предмету
    #  на основе subjects.yaml)

    # 3) Ограничение по баллам в день
    # (сумма x * difficulty_points <= max_points_per_day_by_grade)

    # 4) Ограничения по тяжёлым предметам и положениям уроков

    # 5) Ограничения по кабинетам и учителям — позже

    # ----- Целевая функция -----
    # Для старта можно задать простую цель: минимизировать количество занятых
    # "крайних" уроков тяжёлыми предметами, и/или равномерно распределить нагрузку.

    # objective_terms = []
    # model.Minimize(sum(objective_terms))

    # ----- Решение -----
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    timetable: List[Dict] = []

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for c in class_ids:
            for d in days:
                for p in range(1, slots_per_day + 1):
                    for s in subject_ids:
                        if solver.Value(x[(c, d, p, s)]) == 1:
                            # Пока без кабинета и учителя — только базовая структура
                            timetable.append(
                                {
                                    "class_id": c,
                                    "day": d,
                                    "slot": p,
                                    "subject_id": s,
                                    "room_id": "",      # TODO
                                    "teacher_id": "",   # TODO
                                }
                            )
    else:
        print("Не удалось найти допустимое расписание.")

    return timetable
