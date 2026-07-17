from types import SimpleNamespace
import pytest
from pydantic import ValidationError

from app.api.v1.ai import food_recognition
from app.core.exceptions import BizException
from app.schemas import AIRecognizeIn
from app.schemas import AIRecognizedItem


def test_legacy_mock_recognition_endpoint_is_retired():
    with pytest.raises(BizException) as exc:
        food_recognition(AIRecognizeIn(file_id=9), SimpleNamespace(id=7), SimpleNamespace())

    assert exc.value.status_code == 410


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
