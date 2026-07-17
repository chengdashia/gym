from app.services.weekly_summary import behavior_streak, build_actions, nutrition_target_days


def test_no_data_returns_three_concrete_starting_actions():
    actions = build_actions(diet_days=0, protein_goal_days=0, has_protein_goal=False, training_sessions=0)

    assert len(actions) == 3
    assert any("一餐" in action for action in actions)
    assert any("训练" in action for action in actions)
    assert any("体重" in action for action in actions)


def test_actions_are_limited_and_fact_based():
    actions = build_actions(
        diet_days=5,
        protein_goal_days=2,
        has_protein_goal=True,
        training_sessions=1,
    )
    assert len(actions) == 3
    assert any("蛋白质" in action for action in actions)
    assert any("训练" in action for action in actions)


def test_behavior_streak_counts_any_effective_behavior_once_per_day():
    diet = [{"date": "2026-07-11", "calories_kcal": 0}, {"date": "2026-07-12", "calories_kcal": 1200}, {"date": "2026-07-13", "calories_kcal": 0}]
    training = [{"date": "2026-07-11", "session_count": 0}, {"date": "2026-07-12", "session_count": 1}, {"date": "2026-07-13", "session_count": 1}]
    weights = [{"date": "2026-07-11", "weight_kg": None}, {"date": "2026-07-12", "weight_kg": 70}, {"date": "2026-07-13", "weight_kg": None}]

    assert behavior_streak(diet, training, weights) == 2


def test_nutrition_target_days_uses_inclusive_85_to_115_percent_range():
    rows = [{"calories_kcal": value} for value in (849, 850, 1000, 1150, 1151)]
    assert nutrition_target_days(rows, 1000) == 3
    assert nutrition_target_days(rows, 0) == 0
