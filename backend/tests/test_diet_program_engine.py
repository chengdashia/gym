from datetime import date
from decimal import Decimal

import pytest

from app.services.diet_program_engine import (
    DietSafetyError,
    apply_carb_reduction,
    create_initial_targets,
    estimate_tdee,
    evaluate_532,
)


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
