def progression_proposal(exercise) -> dict | None:
    """Return a conservative double-progression proposal for one completed exercise."""
    sets = sorted(exercise.sets, key=lambda item: getattr(item, "set_index", 0))
    done = [item for item in sets if item.completed]
    if len(done) != exercise.planned_sets or not done:
        return None

    current_reps = max(int(item.target_reps or 0) for item in done)
    achieved_reps = min(int(item.actual_reps if item.actual_reps is not None else item.target_reps or 0) for item in done)
    if current_reps <= 0 or achieved_reps < current_reps:
        return None

    working_weights = [
        float(item.actual_weight_kg if item.actual_weight_kg is not None else item.target_weight_kg or 0)
        for item in done
    ]
    working_weight = min(working_weights)
    if working_weight <= 0:
        if current_reps >= 15:
            return None
        next_reps = current_reps + 1
        return {
            "kind": "reps",
            "target_reps": next_reps,
            "target_weight_kg": None,
            "hint": f"下次每组尝试 {next_reps} 次",
        }

    if current_reps < 12:
        next_reps = current_reps + 1
        return {
            "kind": "reps",
            "target_reps": next_reps,
            "target_weight_kg": working_weight,
            "hint": f"下次保持 {working_weight:g} kg，每组尝试 {next_reps} 次",
        }

    next_weight = round(working_weight + 2.5, 2)
    return {
        "kind": "weight",
        "target_reps": 8,
        "target_weight_kg": next_weight,
        "hint": f"已达到 12 次上限，下次尝试 {next_weight:g} kg × 8 次",
    }


def plan_targets_match_session(plan_exercise, session_exercise) -> bool:
    """Only let a historical session update a plan that still has that session's targets."""
    sets = list(session_exercise.sets)
    if not sets:
        return False
    session_reps = max(int(item.target_reps or 0) for item in sets)
    session_weights = [float(item.target_weight_kg or 0) for item in sets]
    session_weight = min(session_weights) if session_weights else 0.0
    plan_weight = float(plan_exercise.target_weight_kg or 0)
    return (
        int(plan_exercise.target_reps or 0) == session_reps
        and abs(plan_weight - session_weight) < 1e-6
    )


def build_training_summary(session, previous=None) -> dict:
    exercise_rows = []
    completed_sets = 0
    planned_sets = 0
    completed_exercises = 0
    for exercise in session.exercises:
        sets = sorted(exercise.sets, key=lambda item: getattr(item, "set_index", 0))
        done = [item for item in sets if item.completed]
        completed_sets += len(done)
        planned_sets += exercise.planned_sets
        complete = len(done) == exercise.planned_sets
        if complete:
            completed_exercises += 1
        progression = progression_proposal(exercise)
        exercise_rows.append({
            "name": exercise.exercise_name_snapshot,
            "completed_sets": len(done),
            "planned_sets": exercise.planned_sets,
            "sets": [{
                "reps": item.actual_reps,
                "weight_kg": float(item.actual_weight_kg) if item.actual_weight_kg is not None else None,
                "completed": bool(item.completed),
            } for item in sets],
            "progression_hint": progression["hint"] if progression else None,
            "progression": progression,
            "plan_exercise_id": None,
        })
    volume = float(session.total_volume or 0)
    previous_volume = float(previous.total_volume or 0) if previous else None
    return {
        "session_id": session.id,
        "session_name": session.session_name,
        "ended_at": session.ended_at,
        "duration_seconds": session.duration_seconds,
        "completed_exercises": completed_exercises,
        "planned_exercises": len(session.exercises),
        "completed_sets": completed_sets,
        "planned_sets": planned_sets,
        "total_volume": volume,
        "previous_volume": previous_volume,
        "volume_change": round(volume - previous_volume, 2) if previous_volume is not None else None,
        "exercises": exercise_rows,
    }
