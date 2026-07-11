from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from pydantic import ValidationError

from app.api.v1.ai import food_recognition
from app.schemas import AIRecognizeIn
from app.schemas import AIRecognizedItem


def test_mock_recognition_returns_editable_items():
    uploaded = SimpleNamespace(id=9, user_id=7, file_url="/uploads/meal.jpg")
    foods = [SimpleNamespace(id=1, name="米饭"), SimpleNamespace(id=2, name="鸡蛋")]
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = uploaded
    db.query.return_value.filter.return_value.limit.return_value.all.return_value = foods
    db.refresh.side_effect = lambda log: setattr(log, "id", 42)

    payload = food_recognition(AIRecognizeIn(file_id=9), SimpleNamespace(id=7), db)["data"]

    items = payload["recognized_items"]
    assert items
    assert 1 <= len(items) <= 3
    assert set(items[0]) >= {"food_id", "source", "name", "confidence", "estimated_amount_g"}
    assert payload["provider"] == "mock"
    assert payload["candidates"]
    assert all(item["estimated_amount_g"] > 0 for item in items)
    log = db.add.call_args.args[0]
    assert log.candidates_json["recognized_items"] == items


def test_recognized_item_accepts_custom_food_id_without_system_id():
    item = AIRecognizedItem(
        food_id=None, custom_food_id=8, source="custom", name="自制便当",
        confidence=0.8, estimated_amount_g=120,
    )
    assert item.food_id is None
    assert item.custom_food_id == 8


def test_recognized_item_requires_the_id_for_its_source():
    with pytest.raises(ValidationError):
        AIRecognizedItem(
            food_id=None, custom_food_id=None, source="custom", name="无效",
            confidence=0.8, estimated_amount_g=120,
        )
