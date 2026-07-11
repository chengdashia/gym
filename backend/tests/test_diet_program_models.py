from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.v1.foods import _food_to_dict
from app.core.database import Base
from app.models import (
    DietProgramStage,
    Food,
    MealPlanDay,
    MealPlanItem,
    MealPlanMeal,
    UserCustomFood,
)


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


def test_stage_owns_meal_plan_days_with_delete_orphan_cascade():
    cascade = DietProgramStage.meal_plan_days.property.cascade

    assert "delete" in cascade
    assert "delete-orphan" in cascade


def test_deleting_stage_deletes_complete_meal_plan_subtree():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    stage = DietProgramStage(
        id=1,
        program_id=10,
        stage_number=1,
        calories_kcal=Decimal("1800"),
        carbs_g=Decimal("200"),
        protein_g=Decimal("135"),
        fat_g=Decimal("51"),
    )
    day = MealPlanDay(
        id=2,
        program_id=10,
        plan_date=date(2026, 7, 11),
        target_snapshot_json={},
    )
    meal = MealPlanMeal(id=3, meal_type="lunch", target_snapshot_json={})
    item = MealPlanItem(
        id=4,
        food_source="system",
        food_snapshot_json={"name": "米饭"},
        amount_g=Decimal("150"),
        nutrition_snapshot_json={},
    )
    meal.items.append(item)
    day.meals.append(meal)
    stage.meal_plan_days.append(day)

    with Session(engine) as session:
        session.add(stage)
        session.commit()
        session.delete(stage)
        session.commit()

        assert session.get(DietProgramStage, 1) is None
        assert session.get(MealPlanDay, 2) is None
        assert session.get(MealPlanMeal, 3) is None
        assert session.get(MealPlanItem, 4) is None
