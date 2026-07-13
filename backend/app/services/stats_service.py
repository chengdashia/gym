from collections import defaultdict
from datetime import date, datetime, time

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models import DietRecord, TrainingSession, WeightRecord
from app.utils.date import range_dates
from app.services.exercise_stats import effective_set_values


def effective_session_volume(session) -> float:
    exercises = getattr(session, "exercises", None) or []
    return sum(effective_set_values(set_row)[2] for exercise in exercises for set_row in (exercise.sets or []))


def add_weight_moving_average(points: list[dict]) -> list[dict]:
    result = []
    for index, point in enumerate(points):
        values = [
            item["weight_kg"] for item in points[max(0, index - 6):index + 1]
            if item["weight_kg"] is not None
        ]
        result.append({
            **point,
            "average_7d": round(sum(values) / len(values), 2) if len(values) >= 3 else None,
        })
    return result


def weight_trend_meta(points: list[dict]) -> dict:
    values = [point["weight_kg"] for point in points if point["weight_kg"] is not None]
    record_days = len(values)
    period_size = len(values) // 2
    previous = values[:period_size]
    current = values[-period_size:] if period_size else []
    return {
        "record_days": record_days,
        "has_trend": record_days >= 3,
        "average_change": round(sum(current) / period_size - sum(previous) / period_size, 2)
        if record_days >= 6 else None,
    }


def diet_series(db: Session, user_id: int, days: int, end: date | None = None,
                calories_goal: float = 0) -> list[dict]:
    end = end or date.today()
    start = end - __import__("datetime").timedelta(days=days - 1)
    start_dt = datetime.combine(start, time(0, 0))
    end_dt = datetime.combine(end, time(23, 59, 59))
    rows = db.query(DietRecord).filter(
        DietRecord.user_id == user_id, DietRecord.deleted_at.is_(None),
        DietRecord.record_date >= start_dt, DietRecord.record_date <= end_dt,
    ).all()

    bucket = {d: {"calories_kcal": 0.0, "carbs_g": 0.0, "protein_g": 0.0, "fat_g": 0.0} for d in range_dates(days, end)}
    for r in rows:
        d = r.record_date.date()
        if d in bucket:
            bucket[d]["calories_kcal"] += float(r.calories_kcal or 0)
            bucket[d]["carbs_g"] += float(r.carbs_g or 0)
            bucket[d]["protein_g"] += float(r.protein_g or 0)
            bucket[d]["fat_g"] += float(r.fat_g or 0)

    out = []
    for d in sorted(bucket.keys()):
        v = bucket[d]
        rate = round(v["calories_kcal"] / calories_goal, 2) if calories_goal > 0 else 0
        out.append({
            "date": d.strftime("%Y-%m-%d"),
            "calories_kcal": round(v["calories_kcal"], 2),
            "carbs_g": round(v["carbs_g"], 2),
            "protein_g": round(v["protein_g"], 2),
            "fat_g": round(v["fat_g"], 2),
            "calories_goal": calories_goal,
            "completion_rate": rate,
        })
    return out


def training_series(db: Session, user_id: int, days: int, end: date | None = None) -> list[dict]:
    end = end or date.today()
    start = end - __import__("datetime").timedelta(days=days - 1)
    start_dt = datetime.combine(start, time(0, 0))
    end_dt = datetime.combine(end, time(23, 59, 59))
    rows = db.query(TrainingSession).filter(
        TrainingSession.user_id == user_id, TrainingSession.deleted_at.is_(None),
        TrainingSession.status == "completed",
        TrainingSession.session_date >= start_dt, TrainingSession.session_date <= end_dt,
    ).all()

    bucket = {d: {"session_count": 0, "duration_seconds": 0, "total_volume": 0.0} for d in range_dates(days, end)}
    for r in rows:
        d = r.session_date.date()
        if d in bucket:
            bucket[d]["session_count"] += 1
            bucket[d]["duration_seconds"] += int(r.duration_seconds or 0)
            recalculated = effective_session_volume(r)
            bucket[d]["total_volume"] += recalculated if recalculated > 0 else float(r.total_volume or 0)

    out = []
    for d in sorted(bucket.keys()):
        v = bucket[d]
        out.append({
            "date": d.strftime("%Y-%m-%d"),
            "session_count": v["session_count"],
            "duration_seconds": v["duration_seconds"],
            "total_volume": round(v["total_volume"], 2),
        })
    return out


def weight_series(db: Session, user_id: int, days: int, end: date | None = None,
                  target_weight: float | None = None) -> list[dict]:
    end = end or date.today()
    start = end - __import__("datetime").timedelta(days=days - 1)
    start_dt = datetime.combine(start, time(0, 0))
    end_dt = datetime.combine(end, time(23, 59, 59))
    rows = db.query(WeightRecord).filter(
        WeightRecord.user_id == user_id, WeightRecord.deleted_at.is_(None),
        WeightRecord.record_date >= start_dt, WeightRecord.record_date <= end_dt,
    ).order_by(WeightRecord.record_date.asc()).all()

    latest_by_day = {}
    for r in rows:
        d = r.record_date.date()
        latest_by_day[d] = float(r.weight_kg)

    out = []
    first = next(iter(latest_by_day.values()), None)
    for d in sorted({d for d in range_dates(days, end)}):
        w = latest_by_day.get(d)
        out.append({
            "date": d.strftime("%Y-%m-%d"),
            "weight_kg": None if w is None else round(w, 2),
            "target_weight_kg": target_weight,
            "diff_kg": None if w is None or target_weight is None else round(w - target_weight, 2),
            "change_from_start": None if w is None or first is None else round(w - first, 2),
        })
    return add_weight_moving_average(out)
