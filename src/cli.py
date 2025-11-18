# src/cli.py
import argparse
from pathlib import Path

from solvers.ortools_solver import generate_timetable
from io.exporter import export_timetable_csv  # новый импорт


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

    export_timetable_csv(timetable, output_path)


if __name__ == "__main__":
    main()

