# tools/generate_timetable_md.py
"""
Генерация Markdown-расписания из timetable.csv.

Использует:
- timetable.csv в корне проекта;
- data/subjects.yaml для названий предметов;
- data/classes.yaml для ступени (класса);
- data/sanpin_limits.yaml для количества уроков в день.

Результат: файл timetable.md в корне проекта
с таблицами для всех классов.
"""

from pathlib import Path
from collections import defaultdict
import argparse
import csv
import yaml


# Порядок и подписи дней недели
DAYS_EN = ["monday", "tuesday", "wednesday", "thursday", "friday"]
DAYS_RU = {
    "monday": "Понедельник",
    "tuesday": "Вторник",
    "wednesday": "Среда",
    "thursday": "Четверг",
    "friday": "Пятница",
}


def load_subject_names(data_dir: Path) -> dict:
    """subject_id -> полное русское название предмета."""
    with (data_dir / "subjects.yaml").open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    mapping = {}
    for subj in data["subjects"]:
        subj_id = subj["id"]
        name = subj.get("name", subj_id)
        mapping[subj_id] = name
    return mapping


def load_classes(data_dir: Path) -> list:
    """Список описаний классов из data/classes.yaml."""
    with (data_dir / "classes.yaml").open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["classes"]


def load_sanpin(data_dir: Path) -> dict:
    """СанПиН-параметры (slots_per_day и др.)."""
    with (data_dir / "sanpin_limits.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_timetable(csv_path: Path) -> list:
    """Читаем timetable.csv (comma-separated)."""
    rows = []
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["slot"] = int(row["slot"])
            rows.append(row)
    return rows


def build_class_day_slot_map(timetable: list) -> dict:
    """
    Структура:
    data[class_id][day][slot] = subject_id
    (если в слоте нет урока, ключа может не быть).
    """
    result = defaultdict(lambda: defaultdict(dict))
    for row in timetable:
        class_id = row["class_id"]
        day = row["day"]
        slot = row["slot"]
        subj_id = row["subject_id"]
        result[class_id][day][slot] = subj_id
    return result


def generate_markdown(
    classes: list,
    class_day_slot: dict,
    subject_names: dict,
    slots_per_day: int,
) -> str:
    """Строим текст Markdown для всех классов."""

    # Класс id -> grade (ступень)
    class_grade = {c["id"]: c.get("grade") for c in classes}

    # Отсортируем классы по ступени, затем по названию
    def class_sort_key(c_id: str):
        grade = class_grade.get(c_id)
        # None ставим в конец
        grade_val = grade if isinstance(grade, int) else 999
        return (grade_val, c_id)

    all_class_ids = sorted(class_day_slot.keys(), key=class_sort_key)

    lines = []
    lines.append("# Автоматически сгенерированное расписание\n")
    lines.append(
        "Этот файл создан автоматически из `timetable.csv` и данных в папке `data/`.\n"
        "Для каждого класса показана неделя с понедельника по пятницу.\n"
    )

    for class_id in all_class_ids:
        grade = class_grade.get(class_id)
        header = (
            f"## Класс {class_id} (ступень {grade})"
            if grade is not None
            else f"## Класс {class_id}"
        )
        lines.append("")
        lines.append(header)
        lines.append("")

        # Заголовок таблицы
        header_cells = ["День"] + [f"Урок {i}" for i in range(1, slots_per_day + 1)]
        header_line = "| " + " | ".join(header_cells) + " |"

        # Разделитель
        sep_cells = ["---"] * (1 + slots_per_day)
        sep_line = "| " + " | ".join(sep_cells) + " |"

        lines.append(header_line)
        lines.append(sep_line)

        # Строки по дням недели (всегда все 5 дней)
        for day_en in DAYS_EN:
            day_ru = DAYS_RU.get(day_en, day_en)
            row_cells = [day_ru]

            day_slots = class_day_slot[class_id].get(day_en, {})

            for slot in range(1, slots_per_day + 1):
                subj_id = day_slots.get(slot)
                if subj_id:
                    name = subject_names.get(subj_id, subj_id)
                else:
                    name = "—"
                row_cells.append(name)

            line = "| " + " | ".join(row_cells) + " |"
            lines.append(line)

    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Генерация timetable.md из timetable.csv"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Корень проекта (где лежат data/ и timetable.csv)",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="timetable.csv",
        help="Путь к входному CSV-файлу (от корня проекта)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="timetable.md",
        help="Путь к выходному Markdown-файлу (от корня проекта)",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    data_dir = project_root / "data"
    csv_path = project_root / args.csv
    output_path = project_root / args.output

    # Загрузка данных
    subject_names = load_subject_names(data_dir)
    classes = load_classes(data_dir)
    sanpin = load_sanpin(data_dir)
    timetable = load_timetable(csv_path)

    slots_per_day = int(sanpin.get("slots_per_day", 6))

    class_day_slot = build_class_day_slot_map(timetable)

    md_text = generate_markdown(classes, class_day_slot, subject_names, slots_per_day)

    output_path.write_text(md_text, encoding="utf-8")
    print(f"Markdown-расписание записано в {output_path}")


if __name__ == "__main__":
    main()
