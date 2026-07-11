from decimal import Decimal
from types import SimpleNamespace

from app.api.v1.foods import _food_to_dict
from app.core.database import Base
from app.models import Food, UserCustomFood


def test_diet_program_tables_exist_in_metadata():
    expected = {
        "diet_preferences",
        "diet_program_templates",
        "user_diet_programs",
        "diet_program_stages",
        "meal_plan_days",
        "meal_plan_meals",
        "meal_plan_items",
    }

    assert expected <= set(Base.metadata.tables)


def test_foods_include_nullable_fiber():
    assert "fiber_per_100g" in Food.__table__.columns
    assert Food.__table__.columns["fiber_per_100g"].nullable is True
    assert "fiber_per_100g" in UserCustomFood.__table__.columns
    assert UserCustomFood.__table__.columns["fiber_per_100g"].nullable is True


def test_user_owned_program_resources_are_indexable():
    assert "user_id" in Base.metadata.tables["diet_preferences"].columns
    assert "user_id" in Base.metadata.tables["user_diet_programs"].columns
    assert any(
        tuple(column.name for column in index.columns) == ("user_id",)
        for index in Base.metadata.tables["user_diet_programs"].indexes
    )


def test_program_status_dates_stage_number_and_targets_are_queryable_columns():
    programs = Base.metadata.tables["user_diet_programs"].columns
    assert {"status", "start_date", "end_date"} <= set(programs.keys())

    stages = Base.metadata.tables["diet_program_stages"].columns
    assert {
        "stage_number",
        "status",
        "start_date",
        "end_date",
        "calories_kcal",
        "carbs_g",
        "protein_g",
        "fat_g",
    } <= set(stages.keys())


def test_food_api_output_includes_nullable_fiber():
    food = SimpleNamespace(
        id=1,
        name="燕麦",
        category="主食",
        calories_per_100g=Decimal("389"),
        carbs_per_100g=Decimal("66.3"),
        protein_per_100g=Decimal("13"),
        fat_per_100g=Decimal("6.5"),
        fiber_per_100g=Decimal("10.1"),
        default_unit="g",
        serving_weight_g=None,
    )

    assert _food_to_dict(food, "system")["fiber_per_100g"] == Decimal("10.1")
