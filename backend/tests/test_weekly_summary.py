from app.services.weekly_summary import build_actions


def test_no_data_returns_single_recording_action():
    assert build_actions(diet_days=0, protein_goal_days=0, has_protein_goal=False, training_sessions=0) == [
        "记录更多数据后生成总结，先从今天记录一餐开始"
    ]


def test_actions_are_limited_and_fact_based():
    actions = build_actions(
        diet_days=5,
        protein_goal_days=2,
        has_protein_goal=True,
        training_sessions=1,
    )
    assert len(actions) <= 3
    assert any("蛋白质" in action for action in actions)
    assert any("训练" in action for action in actions)
