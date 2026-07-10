from types import SimpleNamespace

from app.services.diet_shortcuts import recent_unique_records


def test_recent_foods_are_unique_and_newest_first():
    rows = [
        SimpleNamespace(food_source="system", food_id=1, custom_food_id=None, food_name_snapshot="鸡蛋"),
        SimpleNamespace(food_source="system", food_id=1, custom_food_id=None, food_name_snapshot="鸡蛋"),
        SimpleNamespace(food_source="system", food_id=2, custom_food_id=None, food_name_snapshot="米饭"),
    ]

    result = recent_unique_records(rows, limit=10)

    assert [row.food_name_snapshot for row in result] == ["鸡蛋", "米饭"]
