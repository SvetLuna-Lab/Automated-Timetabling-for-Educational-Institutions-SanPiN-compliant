# scripts/export_timetable.py
"""
Небольшой служебный скрипт для генерации и экспорта расписания.

Логика:
- вызываем generate_timetable(...) из solvers;
- получаем список строк расписания (class_id, day, slot, subject_id, room_id, teacher_id);
- сохраняем результат в два файла:
  * timetable.csv  — машинно-читаемый CSV;
  * timetable.md   — человекочитаемая Markdown-таблица по классам и дням.
"""

from pathlib import Path

from src.solvers.ortools_solver import generate_timetable
from src.io.exporter import export_timetable


def main() -> None:
    # Папка с входными YAML-файлами (subjects.yaml, classes.yaml, rooms.yaml, teachers.yaml, sanpin_limits.yaml)
    data_dir = Path("data")

    # Пути для выходных файлов
    output_csv = Path("timetable.csv")
    output_md = Path("timetable.md")

    # Генерация расписания (по классам + назначение учителей)
    timetable_rows = generate_timetable(data_dir)

    # Экспорт в CSV и Markdown
    export_timetable(timetable_rows, output_csv, output_md)

    print(f"[OK] Расписание сохранено в {output_csv}")
    print(f"[OK] Расписание в Markdown сохранено в {output_md}")


if __name__ == "__main__":
    main()
