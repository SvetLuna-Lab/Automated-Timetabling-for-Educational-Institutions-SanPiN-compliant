# src/io/exporter.py
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
import csv


# Порядок дней недели для сортировки и вывода
DAY_ORDER = ["monday", "tuesday", "wednesday", "thursday", "friday"]

# Человекочитаемые названия дней (для Markdown)
DAY_LABELS_RU = {
    "monday": "Понедельник",
    "tuesday": "Вторник",
    "wednesday": "Среда",
    "thursday": "Четверг",
    "friday": "Пятница",
}


def export_timetable(
    timetable: List[Dict[str, Any]],
    csv_path: Path,
    md_path: Path,
) -> None:
    """
    Экспорт расписания в два формата:
    - CSV-файл (timetable.csv) для машинной обработки;
    - Markdown-файл (timetable.md) для человека.

    Ожидается, что каждая строка расписания имеет ключи:
    - class_id
    - day
    - slot
    - subject_id
    - room_id
    - teacher_id
    """

    # Создаём родительские папки для файлов (если их ещё нет)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    # --- 1. Экспорт в CSV ---

    # Явно задаём порядок колонок в CSV
    fieldnames = ["class_id", "day", "slot", "subject_id", "room_id", "teacher_id"]

    with csv_path.open("w", newline="", encoding="utf-8") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
        writer.writeheader()
        # Пишем строки как есть (без группировки)
        for row in timetable:
            writer.writerow(
                {
                    "class_id": row.get("class_id", ""),
                    "day": row.get("day", ""),
                    "slot": row.get("slot", ""),
                    "subject_id": row.get("subject_id", ""),
                    "room_id": row.get("room_id", ""),
                    "teacher_id": row.get("teacher_id", ""),
                }
            )

    # --- 2. Подготовка структуры для Markdown ---

    # Группируем: class_id -> day -> список строк
    grouped: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for row in timetable:
        class_id = str(row.get("class_id", ""))
        day = str(row.get("day", ""))
        grouped[class_id][day].append(row)

    # Для аккуратного вывода сортируем по slot внутри каждого дня
    for class_id, days in grouped.items():
        for day, rows in days.items():
            rows.sort(key=lambda r: int(r.get("slot", 0)))

    # --- 3. Экспорт в Markdown ---

    with md_path.open("w", encoding="utf-8") as f_md:
        # Заголовок уровня документа
        f_md.write("# Расписание по классам\n\n")

        # Проходим по классам в алфавитном порядке
        for class_id in sorted(grouped.keys()):
            f_md.write(f"## Класс {class_id}\n\n")

            # Проходим по дням в заданном порядке DAY_ORDER
            for day in DAY_ORDER:
                if day not in grouped[class_id]:
                    continue  # в этот день нет уроков

                day_label = DAY_LABELS_RU.get(day, day)
                f_md.write(f"### {day_label}\n\n")

                # Таблица с уроками за этот день
                f_md.write("| Урок | Предмет      | Кабинет | Учитель ID |\n")
                f_md.write("|------|--------------|---------|------------|\n")

                for row in grouped[class_id][day]:
                    slot = row.get("slot", "")
                    subject_id = row.get("subject_id", "")
                    room_id = row.get("room_id", "")
                    teacher_id = row.get("teacher_id", "")

                    f_md.write(
                        f"| {slot} | {subject_id} | {room_id} | {teacher_id} |\n"
                    )

                f_md.write("\n")  # пустая строка после таблицы для читаемости
