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
        meets_targets = complete and all(
            (item.actual_reps or 0) >= (item.target_reps or 0) for item in done
        )
        exercise_rows.append({
            "name": exercise.exercise_name_snapshot,
            "completed_sets": len(done),
            "planned_sets": exercise.planned_sets,
            "sets": [{
                "reps": item.actual_reps,
                "weight_kg": float(item.actual_weight_kg) if item.actual_weight_kg is not None else None,
                "completed": bool(item.completed),
            } for item in sets],
            "progression_hint": "下次可以尝试小幅增加重量" if meets_targets else None,
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
