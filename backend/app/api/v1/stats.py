from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import BizException
from app.core.response import ok
from app.models import NutritionGoal, TrainingSession, TrainingSessionExercise, TrainingSessionSet, User, UserProfile
from app.schemas import DietStatOut, TrainingStatOut, WeightStatOut
from app.services.stats_service import diet_series, training_series, weight_series


router = APIRouter(prefix="/stats", tags=["stats"])

VALID_RANGES = {7, 30, 90}


def _normalize_range(value: int) -> int:
    if value not in VALID_RANGES:
        raise BizException(40001, "range 仅支持 7/30/90")
    return value


def _goal_kcal(db: Session, user_id: int) -> float:
    g = db.query(NutritionGoal).filter(NutritionGoal.user_id == user_id).first()
    return float(g.calories_kcal or 0) if g else 0


def _target_weight(db: Session, user_id: int) -> float | None:
    p = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if p and p.target_weight_kg is not None:
        return float(p.target_weight_kg)
    return None


@router.get("/diet")
def diet_stats(
    range: int = Query(7),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    days = _normalize_range(range)
    items = diet_series(db, user.id, days, calories_goal=_goal_kcal(db, user.id))
    return ok({"range": days, "items": items})


@router.get("/training")
def training_stats(
    range: int = Query(7),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    days = _normalize_range(range)
    items = training_series(db, user.id, days)
    return ok({"range": days, "items": items})


@router.get("/weight")
def weight_stats(
    range: int = Query(30),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    days = _normalize_range(range)
    items = weight_series(db, user.id, days, target_weight=_target_weight(db, user.id))
    return ok({"range": days, "items": items})


@router.get("/exercises")
def exercise_stats(
    range: int = Query(30),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    days = _normalize_range(range)
    from datetime import date, datetime, time, timedelta
    start = datetime.combine(date.today() - timedelta(days=days - 1), time.min)
    rows = db.query(TrainingSessionExercise, TrainingSessionSet).join(
        TrainingSessionSet, TrainingSessionSet.session_exercise_id == TrainingSessionExercise.id
    ).join(TrainingSession, TrainingSession.id == TrainingSessionExercise.session_id).filter(
        TrainingSession.user_id == user.id,
        TrainingSession.status == "completed",
        TrainingSession.deleted_at.is_(None),
        TrainingSession.session_date >= start,
        TrainingSessionSet.completed == 1,
    ).all()
    grouped: dict[str, dict] = {}
    for exercise, set_row in rows:
        item = grouped.setdefault(exercise.exercise_name_snapshot, {
            "exercise_name": exercise.exercise_name_snapshot,
            "body_part": exercise.body_part_snapshot,
            "completed_sets": 0, "total_reps": 0, "max_weight_kg": 0.0, "total_volume": 0.0,
        })
        item["completed_sets"] += 1
        item["total_reps"] += int(set_row.actual_reps or 0)
        item["max_weight_kg"] = max(item["max_weight_kg"], float(set_row.actual_weight_kg or 0))
        item["total_volume"] += float(set_row.volume or 0)
    items = sorted(grouped.values(), key=lambda item: item["total_volume"], reverse=True)
    for item in items:
        item["total_volume"] = round(item["total_volume"], 2)
    return ok({"range": days, "items": items})
