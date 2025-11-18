# src/cli.py
import argparse
from pathlib import Path

from solvers.ortools_solver import generate_timetable


def main():
    parser = argparse.ArgumentParser(
        description="SANPIN-Schedule: генерация школьного расписания"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Папка с входными YAML-файлами",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="timetable.csv",
        help="Имя выходного файла с расписанием (CSV)",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_path = Path(args.output)

    timetable = generate_timetable(data_dir)

    # Простейший экспорт в CSV
    # Ожидаем, что timetable — это список словарей:
    # {"class_id": ..., "day": ..., "slot": ..., "subject_id": ..., "room_id": ..., "teacher_id": ...}
    import csv

    fieldnames = ["class_id", "day", "slot", "subject_id", "room_id", "teacher_id"]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for row in timetable:
            writer.writerow(row)


if __name__ == "__main__":
    main()
