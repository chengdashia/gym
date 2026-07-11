import pytest
from pydantic import ValidationError

from app.schemas import DietPreferenceIn
from app.services.diet_templates import get_active_templates


def valid_preferences(**overrides):
    values = {
        "meal_count": 3,
        "allergens": [],
        "vegetarian_type": "none",
        "avoid_foods": [],
        "eats_breakfast": True,
        "budget_level": "medium",
        "cooking_setup": "full_kitchen",
        "cuisine_preference": "home_chinese",
        "eating_window_start": None,
        "eating_window_end": None,
    }
    values.update(overrides)
    return values


@pytest.mark.parametrize("meal_count", [1, 7])
def test_meal_count_must_be_between_two_and_six(meal_count):
    with pytest.raises(ValidationError):
        DietPreferenceIn.model_validate(valid_preferences(meal_count=meal_count))


def test_allergens_and_meal_count_are_required():
    for field in ("allergens", "meal_count"):
        payload = valid_preferences()
        payload.pop(field)
        with pytest.raises(ValidationError):
            DietPreferenceIn.model_validate(payload)


def test_allergens_use_supported_codes_and_cannot_repeat():
    with pytest.raises(ValidationError):
        DietPreferenceIn.model_validate(valid_preferences(allergens=["unknown-allergen"]))
    with pytest.raises(ValidationError):
        DietPreferenceIn.model_validate(valid_preferences(allergens=["peanut", "peanut"]))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("vegetarian_type", "sometimes"),
        ("budget_level", "luxury"),
        ("cooking_setup", "restaurant"),
        ("cuisine_preference", "unknown"),
    ],
)
def test_preference_enums_are_validated(field, value):
    with pytest.raises(ValidationError):
        DietPreferenceIn.model_validate(valid_preferences(**{field: value}))


def test_eating_window_requires_both_ends_and_forward_order():
    with pytest.raises(ValidationError):
        DietPreferenceIn.model_validate(valid_preferences(eating_window_start="10:00"))
    with pytest.raises(ValidationError):
        DietPreferenceIn.model_validate(
            valid_preferences(eating_window_start="18:00", eating_window_end="10:00")
        )


def test_preferences_expose_stable_program_snapshot_contract():
    preference = DietPreferenceIn.model_validate(valid_preferences(allergens=["peanut"]))
    snapshot = preference.to_snapshot()
    assert snapshot["schema_version"] == 1
    assert snapshot["hard_constraints"]["allergens"] == ["peanut"]
    assert snapshot["meal_count"] == 3


def test_four_versioned_templates_are_available():
    templates = get_active_templates()
    assert {item["code"] for item in templates} == {
        "balanced_cut",
        "time_restricted_16_8",
        "carb_taper_532",
        "ketogenic",
    }
    assert all(item["version"] >= 1 for item in templates)
    keto = next(item for item in templates if item["code"] == "ketogenic")
    assert keto["rules"]["strict"] is True
    assert keto["rules"]["requires_fiber"] is True
