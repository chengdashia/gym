from types import SimpleNamespace

from app.services.training_summary import build_training_summary


def _set(reps, weight, completed=True, target_reps=10):
    return SimpleNamespace(
        actual_reps=reps, actual_weight_kg=weight, completed=completed,
        target_reps=target_reps, target_weight_kg=weight, set_index=1,
    )


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


def test_training_summary_compares_volume_and_suggests_rep_progression():
    current = _session([_set(10, 40), _set(10, 40)], volume=800)
    previous = _session([_set(10, 35), _set(10, 35)], volume=700)
    result = build_training_summary(current, previous)
    assert result["volume_change"] == 100
    assert result["exercises"][0]["progression"] == {
        "kind": "reps", "target_reps": 11, "target_weight_kg": 40.0,
        "hint": "下次保持 40 kg，每组尝试 11 次",
    }


def test_training_summary_increases_weight_after_rep_ceiling():
    result = build_training_summary(_session([
        _set(12, 40, target_reps=12),
        _set(12, 40, target_reps=12),
    ]))

    assert result["exercises"][0]["progression"] == {
        "kind": "weight", "target_reps": 8, "target_weight_kg": 42.5,
        "hint": "已达到 12 次上限，下次尝试 42.5 kg × 8 次",
    }
