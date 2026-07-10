from sqlalchemy.orm import Session

from app.models import TrainingSession, TrainingSessionExercise


def completed_set_values(exercise: TrainingSessionExercise) -> dict:
    return {
        item.set_index: (item.actual_reps, item.actual_weight_kg)
        for item in exercise.sets
        if item.completed and (item.actual_reps is not None or item.actual_weight_kg is not None)
    }


def last_completed_sets(db: Session, user_id: int, exercise_name: str) -> dict:
    exercise = db.query(TrainingSessionExercise).join(
        TrainingSession, TrainingSession.id == TrainingSessionExercise.session_id
    ).filter(
        TrainingSession.user_id == user_id,
        TrainingSession.status == "completed",
        TrainingSession.deleted_at.is_(None),
        TrainingSessionExercise.exercise_name_snapshot == exercise_name,
    ).order_by(TrainingSession.ended_at.desc(), TrainingSession.id.desc()).first()
    return completed_set_values(exercise) if exercise else {}
