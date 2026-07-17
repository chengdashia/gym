from datetime import date
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
from app.models import DietPreference, DietProgramStage, DietProgramTemplate, NutritionGoal, User, UserDietProgram, UserProfile
from app.services.diet_program_engine import (
    DietSafetyError,
    TargetLossRateError,
    apply_carb_reduction,
    create_initial_targets,
    estimate_tdee,
    evaluate_532,
    validate_target_loss_rate,
)


# MySQL uses BIGINT AUTO_INCREMENT for production IDs. SQLite only auto-assigns
# the exact INTEGER PRIMARY KEY spelling, so make the request-level test schema
# behave like the production schema without changing application models.
@compiles(BigInteger, "sqlite")
def _sqlite_bigint_as_integer(type_, compiler, **kwargs):
    return "INTEGER"


def test_estimate_tdee_uses_mifflin_st_jeor_and_fixed_activity_multiplier():
    result = estimate_tdee(
        {"gender": "male", "age": 30, "height_cm": 175, "current_weight_kg": 70},
        "moderate",
    )

    # (10 * 70 + 6.25 * 175 - 5 * 30 + 5) * 1.55
    assert result == Decimal("2555.56")


@pytest.mark.parametrize("field", ["gender", "age", "height_cm", "current_weight_kg"])
def test_estimate_tdee_requires_complete_profile(field):
    profile = {"gender": "female", "age": 30, "height_cm": 165, "current_weight_kg": 60}
    profile.pop(field)

    result = estimate_tdee(profile, "light")

    assert result["status"] == "needs_profile"
    assert result["missing_fields"] == [field]


def test_532_macros_use_442_or_532_energy_conversion():
    result = create_initial_targets(2000, ratio="532")

    assert result == {
        "calories_kcal": Decimal("2000.00"),
        "carbs_g": Decimal("250.00"),
        "protein_g": Decimal("150.00"),
        "fat_g": Decimal("44.44"),
    }
    assert create_initial_targets(2000, ratio="442") == {
        "calories_kcal": Decimal("2000.00"),
        "carbs_g": Decimal("200.00"),
        "protein_g": Decimal("200.00"),
        "fat_g": Decimal("44.44"),
    }


def test_low_calorie_plan_is_rejected():
    with pytest.raises(DietSafetyError):
        create_initial_targets(1100, ratio="532")


def test_other_program_templates_have_explicit_safe_initial_targets():
    from app.services.diet_program_engine import create_program_initial_targets

    balanced = create_program_initial_targets("balanced_cut", 1800)
    fasting = create_program_initial_targets("time_restricted_16_8", 1800)
    keto = create_program_initial_targets("ketogenic", 1800)

    assert balanced == fasting
    assert balanced["calories_kcal"] == Decimal("1800.00")
    assert keto["carbs_g"] == Decimal("30")
    assert keto["protein_g"] == Decimal("135.00")
    assert keto["fat_g"] == Decimal("126.67")


def test_532_adjustment_only_reduces_carbs_and_respects_floor():
    stage = create_initial_targets(2000, ratio="532")
    next_stage = apply_carb_reduction(stage, grams=20)

    assert next_stage["protein_g"] == stage["protein_g"]
    assert next_stage["fat_g"] == stage["fat_g"]
    assert next_stage["carbs_g"] == Decimal("230.00")
    assert next_stage["calories_kcal"] == Decimal("1920.00")
    with pytest.raises(DietSafetyError):
        apply_carb_reduction({**stage, "carbs_g": Decimal("110")}, grams=15)
    with pytest.raises(DietSafetyError):
        apply_carb_reduction({**stage, "calories_kcal": Decimal("1250")}, grams=15)


def test_532_needs_two_complete_windows_and_observation_period():
    result = evaluate_532(
        previous_weights=[70, 70, 70, 70, 70],
        current_weights=[70, 70, 70, 70, 70],
        adherence_rate=0.9,
        target_loss_rate=Decimal("0.005"),
        stage=create_initial_targets(2000, ratio="532"),
        observation_days=9,
    )

    assert result.status == "needs_observation"


@pytest.mark.parametrize(
    ("previous", "current", "adherence", "expected"),
    [
        ([70] * 4, [70] * 5, 0.9, "needs_data"),
        ([70] * 5, [70] * 5, 0.79, "improve_adherence"),
        ([70] * 5, [69.5] * 5, 0.9, "continue"),
        ([70] * 5, [70] * 5, 0.9, "suggest_carb_reduction"),
    ],
)
def test_532_evaluation_state_machine(previous, current, adherence, expected):
    result = evaluate_532(
        previous_weights=previous,
        current_weights=current,
        adherence_rate=adherence,
        target_loss_rate=Decimal("0.005"),
        stage=create_initial_targets(2000, ratio="532"),
        observation_days=14,
    )

    assert result.status == expected
    assert (result.pending_adjustment is not None) == (expected == "suggest_carb_reduction")


def test_532_stops_at_goal_or_carb_floor_without_pending_change():
    stage = create_initial_targets(2000, ratio="532")
    at_goal = evaluate_532(
        previous_weights=[70] * 5, current_weights=[69.5] * 5, adherence_rate=1,
        target_loss_rate=Decimal("0.005"), stage=stage, observation_days=14,
        target_weight_kg=Decimal("69.5"),
    )
    at_floor = evaluate_532(
        previous_weights=[70] * 5, current_weights=[70] * 5, adherence_rate=1,
        target_loss_rate=Decimal("0.005"), stage={**stage, "carbs_g": Decimal("100")},
        observation_days=14,
    )

    assert at_goal.status == "stop"
    assert at_floor.status == "stop"
    assert at_goal.pending_adjustment is None
    assert at_floor.pending_adjustment is None


def test_suggested_adjustment_is_pending_and_requires_confirmation():
    stage = create_initial_targets(2000, ratio="532")
    result = evaluate_532(
        previous_weights=[70] * 5, current_weights=[70] * 5, adherence_rate=1,
        target_loss_rate=Decimal("0.005"), stage=stage, observation_days=14, reduction_g=25,
    )

    assert result.pending_adjustment["current_carbs_g"] == Decimal("250.00")
    assert result.pending_adjustment["new_carbs_g"] == Decimal("225.00")
    assert stage["carbs_g"] == Decimal("250.00")


@pytest.mark.parametrize(
    ("weight_kg", "rate", "should_raise"),
    [
        (Decimal("90"), Decimal("0.01"), False),
        (Decimal("100"), Decimal("0.01"), True),
        (Decimal("250"), Decimal("0.005"), True),
    ],
)
def test_target_loss_rate_respects_absolute_weekly_ceiling(weight_kg, rate, should_raise):
    if should_raise:
        with pytest.raises(TargetLossRateError) as exc:
            validate_target_loss_rate(rate, weight_kg)
        assert exc.value.weekly_loss_kg > Decimal("0.90")
    else:
        assert validate_target_loss_rate(rate, weight_kg) == Decimal("0.90")


@pytest.fixture
def program_http_client(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "experimental_user_ids", [1, 2])
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    current_user_id = {"value": 1}

    def override_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    def override_user():
        return User(id=current_user_id["value"], status="active")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    with TestClient(app) as client:
        yield client, session_factory, current_user_id
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def _seed_program_user(
    session_factory, user_id: int, *, gender: str | None = "female", weight_kg: Decimal = Decimal("60"),
):
    with session_factory() as db:
        db.add(User(id=user_id, status="active", phone=f"1380000{user_id:04d}"))
        db.add(DietPreference(
            user_id=user_id, meal_count=3, allergens_json=[], preference_rules_json={
                "vegetarian_type": "none", "avoid_foods": [], "eats_breakfast": True,
                "budget_level": "medium", "cooking_setup": "full_kitchen",
                "cuisine_preference": "home_chinese", "eating_window_start": None,
                "eating_window_end": None,
            },
        ))
        if gender is not None:
            db.add(UserProfile(
                user_id=user_id, gender=gender, age=30, height_cm=Decimal("165"),
                current_weight_kg=weight_kg, target_weight_kg=Decimal("55"),
            ))
        db.commit()


def _create_payload(**overrides):
    body = {
        "template_code": "carb_taper_532", "activity_level": "light", "calories_kcal": 1800,
        "macro_ratio": "532",
        "eligibility": {
            "under_18": False, "pregnant_or_breastfeeding": False, "diabetes": False,
            "serious_liver_kidney_gallbladder": False, "eating_disorder_history": False,
        },
    }
    body.update(overrides)
    return body


@pytest.mark.parametrize("template_code", ["balanced_cut", "time_restricted_16_8", "ketogenic"])
def test_http_creation_supports_all_confirmed_program_templates(program_http_client, template_code):
    client, session_factory, _ = program_http_client
    _seed_program_user(session_factory, 1)

    created = client.post("/api/v1/diet-programs", json=_create_payload(template_code=template_code))
    assert created.status_code == 200
    assert created.json()["data"]["stage"]["calories_kcal"] == 1800

    with session_factory() as db:
        db.query(UserProfile).filter(UserProfile.user_id == 1).delete()
        db.commit()
    missing = client.post("/api/v1/diet-programs", json=_create_payload())
    assert missing.status_code == 400
    assert missing.json()["data"] == {
        "status": "needs_profile",
        "missing_fields": ["gender", "age", "height_cm", "current_weight_kg"],
    }


def test_http_creation_returns_4xx_for_other_gender_profile(program_http_client):
    client, session_factory, _ = program_http_client
    _seed_program_user(session_factory, 1, gender="other")

    response = client.post("/api/v1/diet-programs", json=_create_payload())

    assert response.status_code == 400
    assert response.json()["data"]["status"] == "unsupported_profile"
    assert response.json()["data"]["unsupported_fields"] == ["gender"]


def test_http_creation_rejects_target_speed_above_absolute_weekly_cap(program_http_client):
    client, session_factory, _ = program_http_client
    _seed_program_user(session_factory, 1, weight_kg=Decimal("100"))

    response = client.post("/api/v1/diet-programs", json=_create_payload(target_loss_rate="0.01"))

    assert response.status_code == 400
    assert response.json()["code"] == 40042
    assert response.json()["data"]["status"] == "target_loss_rate_exceeds_cap"
    assert response.json()["data"]["weekly_loss_kg"] == 1


def test_http_confirm_is_idempotent_and_programs_are_user_isolated(program_http_client):
    client, session_factory, user_id = program_http_client
    _seed_program_user(session_factory, 1)
    _seed_program_user(session_factory, 2)
    create = client.post("/api/v1/diet-programs", json=_create_payload())
    assert create.status_code == 200
    program_id = create.json()["data"]["id"]

    user_id["value"] = 2
    forbidden = client.post(f"/api/v1/diet-programs/{program_id}/confirm")
    assert forbidden.status_code == 404

    user_id["value"] = 1
    assert client.post(f"/api/v1/diet-programs/{program_id}/confirm").status_code == 200
    repeated = client.post(f"/api/v1/diet-programs/{program_id}/confirm")
    assert repeated.status_code == 200
    assert repeated.json()["data"]["status"] == "active"
    with session_factory() as db:
        assert db.query(NutritionGoal).filter(NutritionGoal.user_id == 1).count() == 1


def test_http_evaluate_rejects_non_532_program(program_http_client):
    client, session_factory, _ = program_http_client
    _seed_program_user(session_factory, 1)
    with session_factory() as db:
        template = DietProgramTemplate(
            code="balanced_cut", name="均衡减脂", version=1, rules_json={}, status="active",
        )
        db.add(template)
        db.flush()
        program = UserDietProgram(
            user_id=1, template_id=template.id, template_version=1, status="active",
            eligibility_snapshot_json={}, preference_snapshot_json={},
        )
        db.add(program)
        db.flush()
        db.add(DietProgramStage(
            program_id=program.id, stage_number=1, status="active", start_date=date.today(),
            calories_kcal=Decimal("1800"), carbs_g=Decimal("225"), protein_g=Decimal("135"), fat_g=Decimal("40"),
        ))
        db.commit()
        program_id = program.id

    response = client.post(f"/api/v1/diet-programs/{program_id}/evaluate", json={})

    assert response.status_code == 400
    assert response.json()["code"] == 40041
