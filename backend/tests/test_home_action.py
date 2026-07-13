import pytest

from app.services.home_action import choose_primary_action


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ({"needs_profile": True}, "complete_profile"),
        ({"has_goal": False}, "set_nutrition_goal"),
        ({"meal_recorded": False}, "record_meal"),
        ({"training_status": "in_progress"}, "resume_training"),
        ({"training_status": "not_started"}, "start_training"),
        ({"weight_recorded_today": False}, "record_weight"),
        ({}, "day_complete"),
    ],
)
def test_primary_action_priority(state, expected):
    defaults = {
        "needs_profile": False, "has_goal": True, "meal_recorded": True,
        "training_status": "completed", "weight_recorded_today": True,
    }
    assert choose_primary_action(**{**defaults, **state})["type"] == expected


def test_higher_priority_wins_when_multiple_actions_are_available():
    action = choose_primary_action(
        needs_profile=False, has_goal=False, meal_recorded=False,
        training_status="in_progress", weight_recorded_today=False,
    )
    assert action["type"] == "set_nutrition_goal"
