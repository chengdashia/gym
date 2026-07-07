from datetime import datetime, time
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.response import ok
from app.models import (
    DietRecord,
    NutritionGoal,
    TrainingPlan,
    TrainingSession,
    User,
    UserProfile,
    WeightRecord,
)
from app.api.v1.training import _session_to_dict, _plan_to_dict
from app.api.v1.stats import _goal_kcal, _target_weight
from app.services.schedule import resolve_today_day


router = APIRouter(prefix="/home", tags=["home"])


@router.get("/summary")
def home_summary(
    date: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    d = datetime.strptime(date, "%Y-%m-%d").date() if date else datetime.now().date()
    start = datetime.combine(d, time(0, 0))
    end = datetime.combine(d, time(23, 59, 59))

    # diet
    goal = _goal_kcal(db, user.id)
    rows = db.query(DietRecord).filter(
        DietRecord.user_id == user.id, DietRecord.deleted_at.is_(None),
        DietRecord.record_date >= start, DietRecord.record_date <= end,
    ).all()
    cal = sum(float(r.calories_kcal or 0) for r in rows)
    c = sum(float(r.carbs_g or 0) for r in rows)
    p = sum(float(r.protein_g or 0) for r in rows)
    f = sum(float(r.fat_g or 0) for r in rows)

    g = db.query(NutritionGoal).filter(NutritionGoal.user_id == user.id).first()
    cal_g = float(g.calories_kcal or 0) if g else 0
    c_g = float(g.carbs_g or 0) if g else 0
    p_g = float(g.protein_g or 0) if g else 0
    f_g = float(g.fat_g or 0) if g else 0

    diet = {
        "calories_kcal": round(cal, 2),
        "calories_goal": cal_g,
        "carbs_g": round(c, 2),
        "carbs_goal": c_g,
        "protein_g": round(p, 2),
        "protein_goal": p_g,
        "fat_g": round(f, 2),
        "fat_goal": f_g,
        "record_count": len(rows),
    }

    # training (today)
    active_plan = db.query(TrainingPlan).filter(
        TrainingPlan.user_id == user.id, TrainingPlan.deleted_at.is_(None),
        TrainingPlan.is_active == 1,
    ).order_by(TrainingPlan.id.desc()).first()

    incomplete = db.query(TrainingSession).filter(
        TrainingSession.user_id == user.id, TrainingSession.deleted_at.is_(None),
        TrainingSession.status.in_(("in_progress", "paused")),
    ).order_by(TrainingSession.started_at.desc()).first()

    if not active_plan:
        training = {
            "status": "no_plan",
            "plan_id": None, "plan_day_id": None, "session_id": None,
            "title": None, "exercise_count": 0, "is_rest_day": False,
        }
    else:
        today_day = resolve_today_day(db, active_plan, d)
        if not today_day:
            training = {
                "status": "rest_day",
                "plan_id": active_plan.id, "plan_day_id": None, "session_id": None,
                "title": None, "exercise_count": 0, "is_rest_day": True,
            }
        else:
            ex_count = len(today_day.exercises)
            incomplete_today = None
            if incomplete and incomplete.plan_id == active_plan.id and incomplete.plan_day_id == today_day.id:
                incomplete_today = incomplete
            status = "completed"
            if incomplete_today:
                status = "in_progress"
            elif incomplete and incomplete.plan_id == active_plan.id and incomplete.plan_day_id != today_day.id:
                status = "in_progress"

            training = {
                "status": status if status != "completed" else "not_started",
                "plan_id": active_plan.id,
                "plan_day_id": today_day.id,
                "session_id": incomplete_today.id if incomplete_today else None,
                "title": today_day.day_name,
                "exercise_count": ex_count,
                "is_rest_day": False,
            }

    # weight
    w = db.query(WeightRecord).filter(
        WeightRecord.user_id == user.id, WeightRecord.deleted_at.is_(None),
    ).order_by(WeightRecord.record_date.desc(), WeightRecord.record_time.desc()).first()
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    target = float(profile.target_weight_kg) if profile and profile.target_weight_kg is not None else None
    if w:
        cw = float(w.weight_kg)
        last_recorded_at = datetime.combine(w.record_date.date(), w.record_time)
    else:
        # 没有体重记录时，回退到个人资料中填写的当前体重
        cw = float(profile.current_weight_kg) if profile and profile.current_weight_kg is not None else None
        last_recorded_at = None
    weight = {
        "current_weight_kg": cw,
        "target_weight_kg": target,
        "diff_kg": round(cw - target, 2) if cw is not None and target is not None else None,
        "last_recorded_at": last_recorded_at,
    }

    return ok({
        "date": d.strftime("%Y-%m-%d"),
        "diet": diet,
        "training": training,
        "weight": weight,
    })