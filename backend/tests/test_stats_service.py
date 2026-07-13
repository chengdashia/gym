from types import SimpleNamespace

from app.services.exercise_stats import aggregate_exercise_sets, effective_set_values
from app.services.stats_service import add_weight_moving_average, effective_session_volume, weight_trend_meta


def exercise(name="卧推"):
    return SimpleNamespace(exercise_name_snapshot=name, body_part_snapshot="胸")


def training_set(**values):
    defaults = dict(actual_weight_kg=None, actual_reps=None, target_weight_kg=None,
                    target_reps=None, completed=1)
    defaults.update(values)
    return SimpleNamespace(**defaults)


def test_exercise_stats_prefers_actual_values_and_computes_volume():
    rows = [(exercise(), training_set(actual_weight_kg=60, actual_reps=8,
             target_weight_kg=50, target_reps=10))]
    item = aggregate_exercise_sets(rows)[0]
    assert item["max_weight_kg"] == 60
    assert item["total_volume"] == 480


def test_exercise_stats_falls_back_to_targets_for_legacy_rows():
    rows = [(exercise(), training_set(actual_weight_kg=0, actual_reps=0,
             target_weight_kg=40, target_reps=12))]
    assert aggregate_exercise_sets(rows)[0]["total_volume"] == 480


def test_exercise_stats_marks_bodyweight_without_fake_weight():
    item = aggregate_exercise_sets([(exercise("俯卧撑"), training_set(actual_reps=12))])[0]
    assert item["has_weight"] is False
    assert item["total_reps"] == 12


def test_effective_values_restore_completed_legacy_set_from_targets():
    row = training_set(target_weight_kg=40, target_reps=10, completed=1)
    assert effective_set_values(row) == (10, 40.0, 400.0)


def test_training_series_volume_can_be_recalculated_from_completed_sets():
    session = SimpleNamespace(exercises=[SimpleNamespace(sets=[
        training_set(target_weight_kg=40, target_reps=10, completed=1),
        training_set(actual_weight_kg=50, actual_reps=8, completed=1),
    ])])
    assert effective_session_volume(session) == 800


def test_weight_average_requires_three_records_and_uses_last_seven_days():
    points = [
        {"date": f"2026-07-{day:02d}", "weight_kg": weight}
        for day, weight in enumerate([70, None, 71, None, 72, 73, 74, 75], start=1)
    ]
    result = add_weight_moving_average(points)
    assert result[2]["average_7d"] is None
    assert result[4]["average_7d"] == 71
    assert result[-1]["average_7d"] == 73


def test_weight_trend_meta_compares_available_moving_averages():
    points = add_weight_moving_average([
        {"date": f"2026-07-{day:02d}", "weight_kg": weight}
        for day, weight in enumerate([70, 70, 70, 69, 69, 69], start=1)
    ])
    assert weight_trend_meta(points) == {
        "record_days": 6,
        "has_trend": True,
        "average_change": -1.0,
    }


def test_weight_trend_meta_reports_insufficient_data():
    assert weight_trend_meta([{"weight_kg": 70, "average_7d": None}]) == {
        "record_days": 1,
        "has_trend": False,
        "average_change": None,
    }
