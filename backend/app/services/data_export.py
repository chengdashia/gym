import codecs
import csv
import io
import json
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import DietRecord, NutritionGoal, TrainingSession, UserProfile, WeightRecord


FIELDS = ("record_type", "recorded_at", "name", "details")


def _json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    raise TypeError(f"Unsupported value: {type(value)!r}")


def records_to_csv(records: list[dict]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS)
    writer.writeheader()
    for record in records:
        row = {key: record.get(key, "") for key in FIELDS}
        row["details"] = json.dumps(row["details"], ensure_ascii=False, default=_json_default)
        writer.writerow(row)
    return codecs.BOM_UTF8 + output.getvalue().encode("utf-8")


def build_user_export(db: Session, user_id: int) -> bytes:
    records: list[dict] = []
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile:
        records.append({
            "record_type": "身体资料",
            "recorded_at": profile.updated_at,
            "name": "基础资料",
            "details": {
                "gender": profile.gender,
                "age": profile.age,
                "height_cm": profile.height_cm,
                "current_weight_kg": profile.current_weight_kg,
                "target_weight_kg": profile.target_weight_kg,
                "fitness_goal": profile.fitness_goal,
                "training_frequency": profile.training_frequency,
            },
        })
    goal = db.query(NutritionGoal).filter(NutritionGoal.user_id == user_id).first()
    if goal:
        records.append({
            "record_type": "营养目标",
            "recorded_at": goal.updated_at,
            "name": "每日目标",
            "details": {
                "calories_kcal": goal.calories_kcal,
                "carbs_g": goal.carbs_g,
                "protein_g": goal.protein_g,
                "fat_g": goal.fat_g,
            },
        })
    for row in db.query(DietRecord).filter(
        DietRecord.user_id == user_id, DietRecord.deleted_at.is_(None)
    ).all():
        records.append({
            "record_type": "饮食",
            "recorded_at": f"{row.record_date.date()} {row.record_time}",
            "name": row.food_name_snapshot,
            "details": {
                "meal_type": row.meal_type,
                "unit_type": row.unit_type,
                "amount_g": row.amount_g,
                "serving_count": row.serving_count,
                "calories_kcal": row.calories_kcal,
                "carbs_g": row.carbs_g,
                "protein_g": row.protein_g,
                "fat_g": row.fat_g,
            },
        })
    for session in db.query(TrainingSession).filter(
        TrainingSession.user_id == user_id, TrainingSession.deleted_at.is_(None)
    ).all():
        records.append({
            "record_type": "训练",
            "recorded_at": session.started_at,
            "name": session.session_name,
            "details": {
                "status": session.status,
                "duration_seconds": session.duration_seconds,
                "total_volume": session.total_volume,
                "exercises": [
                    {
                        "name": exercise.exercise_name_snapshot,
                        "sets": [
                            {
                                "set_index": item.set_index,
                                "actual_reps": item.actual_reps,
                                "actual_weight_kg": item.actual_weight_kg,
                                "completed": bool(item.completed),
                            }
                            for item in exercise.sets
                        ],
                    }
                    for exercise in session.exercises
                ],
            },
        })
    for row in db.query(WeightRecord).filter(
        WeightRecord.user_id == user_id, WeightRecord.deleted_at.is_(None)
    ).all():
        records.append({
            "record_type": "体重",
            "recorded_at": f"{row.record_date.date()} {row.record_time}",
            "name": "体重记录",
            "details": {"weight_kg": row.weight_kg, "note": row.note},
        })
    return records_to_csv(records)
