from types import SimpleNamespace

from app.services.training_summary import build_training_summary


def _set(reps, weight, completed=True, target_reps=10):
    return SimpleNamespace(actual_reps=reps, actual_weight_kg=weight, completed=completed, target_reps=target_reps)


def _session(sets, volume=0):
    exercise = SimpleNamespace(exercise_name_snapshot="卧推", planned_sets=len(sets), sets=sets)
    return SimpleNamespace(
        id=1, session_name="胸部训练", duration_seconds=3600,
        total_volume=volume, exercises=[exercise], ended_at=None,
    )


def test_training_summary_marks_partial_completion_honestly():
    result = build_training_summary(_session([_set(10, 40), _set(None, None, False)]))
    assert result["completed_sets"] == 1
    assert result["planned_sets"] == 2
    assert result["completed_exercises"] == 0
    assert result["exercises"][0]["progression_hint"] is None


def test_training_summary_compares_volume_and_suggests_progression():
    current = _session([_set(10, 40), _set(10, 40)], volume=800)
    previous = _session([_set(10, 35), _set(10, 35)], volume=700)
    result = build_training_summary(current, previous)
    assert result["volume_change"] == 100
    assert result["exercises"][0]["progression_hint"] == "下次可以尝试小幅增加重量"
