# tests/test_api_smoke.py
"""
Простейшие smoke-тесты для API:

- /health отвечает 200 и {"status": "ok"};
- /generate-timetable отвечает 200 и возвращает список строк расписания
  с ожидаемой структурой.
"""

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_health_ok():
    """Проверяем, что сервис «жив» и возвращает статус ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"


def test_generate_timetable_structure():
    """
    Проверяем базовую работоспособность эндпоинта генерации расписания:

    - код ответа 200;
    - тело ответа — список;
    - у первой строки есть ключи class_id, day, slot, subject_id, room_id, teacher_id.
    """
    resp = client.get("/generate-timetable")
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data, list), "Ожидался список строк расписания"

    if not data:
        # Если данных нет (например, пустые YAML), это не ошибка API,
        # но дальше структуру проверить не получится.
        return

    row = data[0]
    for key in ["class_id", "day", "slot", "subject_id", "room_id", "teacher_id"]:
        assert key in row, f"В строке расписания нет ключа {key}"
