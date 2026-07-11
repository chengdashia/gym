from datetime import date, time
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.deps import get_current_user
from app.core.database import Base, get_db
from app.main import app
from app.services.meal_planner import MealPlanConflict, generate_seven_day_plan, replace_item, validate_meal_plan
from app.models import DietProgramStage, DietProgramTemplate, Food, User, UserDietProgram


@compiles(BigInteger, "sqlite")
def _sqlite_bigint_as_integer(type_, compiler, **kwargs):
    return "INTEGER"


@pytest.fixture
def program_http_client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False)
    def override_db():
        db = session_factory()
        try: yield db
        finally: db.close()
    def override_user(): return User(id=1, status="active")
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    with TestClient(app) as client: yield client, session_factory, {"value": 1}
    app.dependency_overrides.clear(); Base.metadata.drop_all(engine); engine.dispose()


TARGETS = {
    "calories_kcal": Decimal("1800"), "carbs_g": Decimal("200"),
    "protein_g": Decimal("135"), "fat_g": Decimal("60"),
}


def preferences(**updates):
    value = {
        "meal_count": 3,
        "hard_constraints": {"allergens": [], "vegetarian_type": "none", "avoid_foods": []},
        "preferences": {"budget_level": "medium", "cooking_setup": "full_kitchen", "cuisine_preference": "home_chinese"},
    }
    value.update(updates)
    return value


def test_allergens_never_appear_in_plan():
    plan = generate_seven_day_plan(TARGETS, preferences(hard_constraints={
        "allergens": ["dairy"], "vegetarian_type": "none", "avoid_foods": [],
    }))
    assert all("dairy" not in item["allergens"] for day in plan["days"] for meal in day["meals"] for item in meal["items"])


def test_16_8_meals_stay_inside_window():
    plan = generate_seven_day_plan(TARGETS, preferences(
        preferences={"eating_window_start": "10:00:00", "eating_window_end": "18:00:00"},
    ), code="time_restricted_16_8")
    assert all(time(10) <= meal["planned_time"] <= time(18) for day in plan["days"] for meal in day["meals"])


def test_keto_rejects_unknown_fiber_and_uses_net_carbs():
    with pytest.raises(MealPlanConflict) as exc:
        generate_seven_day_plan(TARGETS, preferences(), code="ketogenic", foods=[{
            "name": "未知纤维食物", "calories_per_100g": 100, "carbs_per_100g": 10,
            "protein_per_100g": 10, "fat_per_100g": 5, "fiber_per_100g": None,
            "role": "protein", "allergens": [], "vegetarian": True,
        }])
    assert "fiber_per_100g" in exc.value.fields


def test_plan_is_seven_days_and_daily_calories_are_within_five_percent():
    plan = generate_seven_day_plan(TARGETS, preferences())
    assert len(plan["days"]) == 7
    for day in plan["days"]:
        assert abs(day["totals"]["calories_kcal"] - TARGETS["calories_kcal"]) <= TARGETS["calories_kcal"] * Decimal("0.05")
        validate_meal_plan(day, TARGETS)


def test_conflicting_hard_constraints_return_structured_recovery():
    with pytest.raises(MealPlanConflict) as exc:
        generate_seven_day_plan(TARGETS, preferences(hard_constraints={
            "allergens": ["dairy", "egg", "soy", "fish", "shellfish"],
            "vegetarian_type": "vegan", "avoid_foods": ["鸡", "豆", "油"],
        }))
    assert exc.value.fields
    assert exc.value.suggestions


def test_keto_plan_uses_net_carbs_and_known_fiber_candidates():
    targets = {"calories_kcal": Decimal("1800"), "carbs_g": Decimal("30"), "protein_g": Decimal("135"), "fat_g": Decimal("126.67")}
    plan = generate_seven_day_plan(targets, preferences(), code="ketogenic")
    day = plan["days"][0]
    assert day["totals"]["net_carbs_g"] <= Decimal("30")
    assert all(item["nutrition"]["fiber_g"] >= 0 for meal in day["meals"] for item in meal["items"])


def test_soft_preferences_filter_budget_and_cooking_then_sort_cuisine():
    plan = generate_seven_day_plan(TARGETS, preferences(preferences={
        "budget_level": "low", "cooking_setup": "none", "cuisine_preference": "takeout",
    }))
    foods = [item["food"] for meal in plan["days"][0]["meals"] for item in meal["items"]]
    assert all(food["budget"] == "low" and food["cooking"] == "none" for food in foods)
    assert all("takeout" in food["cuisines"] for food in foods)


def test_replacement_recalculates_food_snapshot_and_nutrition():
    original = {"role": "carb", "name": "米饭", "amount_g": Decimal("100"), "allergens": [], "food": {
        "name": "米饭", "role": "carb", "calories_per_100g": 116, "carbs_per_100g": 25.6, "protein_per_100g": 2.6, "fat_per_100g": .3, "fiber_per_100g": 0, "allergens": [],
    }, "nutrition": {"calories_kcal": Decimal("116"), "carbs_g": Decimal("25.6"), "protein_g": Decimal("2.6"), "fat_g": Decimal(".3")}}
    oat = {"name": "燕麦", "role": "carb", "calories_per_100g": 389, "carbs_per_100g": 66.3, "protein_per_100g": 13, "fat_per_100g": 6.5, "fiber_per_100g": 10.1, "allergens": [], "vegetarian": True, "vegan": True}
    replaced = replace_item(original, oat, preferences())
    assert replaced["food"]["name"] == "燕麦"
    assert replaced["nutrition"]["calories_kcal"] == Decimal("389.00")
    assert replaced["nutrition"]["fiber_g"] == Decimal("10.10")


def test_validate_plan_rejects_locked_protein_or_fat_macro_change():
    day = {"totals": {"calories_kcal": Decimal("1800"), "carbs_g": Decimal("180"), "protein_g": Decimal("110"), "fat_g": Decimal("60")}}
    with pytest.raises(MealPlanConflict) as exc:
        validate_meal_plan(day, {"calories_kcal": Decimal("1800"), "carbs_g": Decimal("180"), "protein_g": Decimal("135"), "fat_g": Decimal("60")}, code="carb_taper_532")
    assert "protein_g" in exc.value.fields


def test_soft_preference_conflict_is_structured_when_role_has_no_candidate():
    with pytest.raises(MealPlanConflict) as exc:
        generate_seven_day_plan(TARGETS, preferences(preferences={
            "budget_level": "low", "cooking_setup": "none", "cuisine_preference": "home_chinese",
        }))
    assert "cooking_setup" in exc.value.fields


def test_validate_plan_allows_carb_change_while_532_protein_and_fat_are_locked():
    day = {"totals": {"calories_kcal": Decimal("1760"), "carbs_g": Decimal("170"), "protein_g": Decimal("135"), "fat_g": Decimal("60")}}
    validate_meal_plan(day, {"calories_kcal": Decimal("1800"), "carbs_g": Decimal("180"), "protein_g": Decimal("135"), "fat_g": Decimal("60")}, code="carb_taper_532")


def _seed_active_program(session_factory):
    with session_factory() as db:
        db.add_all([
            Food(name="米饭", category="主食", calories_per_100g=116, carbs_per_100g=25.6, protein_per_100g=2.6, fat_per_100g=.3, fiber_per_100g=0),
            Food(name="鸡胸肉", category="肉蛋奶", calories_per_100g=165, carbs_per_100g=0, protein_per_100g=31, fat_per_100g=3.6, fiber_per_100g=0),
            Food(name="西兰花", category="蔬菜", calories_per_100g=34, carbs_per_100g=6.6, protein_per_100g=2.8, fat_per_100g=.4, fiber_per_100g=2.6),
            Food(name="橄榄油", category="其他", calories_per_100g=884, carbs_per_100g=0, protein_per_100g=0, fat_per_100g=100, fiber_per_100g=0),
        ])
        template = DietProgramTemplate(code="balanced_cut", name="均衡减脂", version=1, rules_json={}, status="active")
        db.add(template); db.flush()
        program = UserDietProgram(user_id=1, template_id=template.id, template_version=1, status="active", eligibility_snapshot_json={}, preference_snapshot_json=preferences())
        db.add(program); db.flush()
        db.add(DietProgramStage(program_id=program.id, stage_number=1, status="active", calories_kcal=1800, carbs_g=180, protein_g=135, fat_g=60))
        db.commit()
        return program.id


def test_meal_plan_api_generates_then_records_once_without_counting_before_confirmation(program_http_client):
    client, session_factory, _ = program_http_client
    with session_factory() as db:
        db.add(User(id=1, status="active", phone="13800000001")); db.commit()
    program_id = _seed_active_program(session_factory)

    generated = client.get(f"/api/v1/diet-programs/{program_id}/meal-plan")
    assert generated.status_code == 200
    meal = generated.json()["data"]["days"][0]["meals"][0]
    assert meal["recorded"] is False

    recorded = client.post(f"/api/v1/meal-plan/meals/{meal['id']}/record")
    assert recorded.status_code == 200
    assert recorded.json()["data"]["created_count"] > 0
    repeated = client.post(f"/api/v1/meal-plan/meals/{meal['id']}/record")
    assert repeated.status_code == 409
