from decimal import Decimal
from datetime import date, datetime, time
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import BizException
from app.core.response import ok
from app.models import DietRecord, Food, OperationLog, User, UserCustomFood
from app.schemas import CustomFoodRecordIn, DietDayOut, DietRecordIn, DietRecordOut, DietRecordUpdateIn, DietSummary
from app.services.nutrition import calc_nutrition_per_100g, calc_nutrition_per_serving, sum_nutrition
from app.services.diet_shortcuts import recent_unique_records
from app.services.validation import merge_and_validate_diet_quantity
from app.services.uploads import delete_local_file, finalize_upload
from app.utils.date import day_bounds


router = APIRouter(prefix="/diet", tags=["diet"])


MEAL_TYPES = ("breakfast", "lunch", "dinner", "snack")


class CopyMealIn(BaseModel):
    source_date: date
    source_meal_type: str
    target_date: date
    target_meal_type: str
    record_time: time


def _ensure_food(db: Session, user_id: int, source: str, food_id: Optional[int], custom_food_id: Optional[int]):
    if source == "custom":
        if not custom_food_id:
            raise BizException(40001, "custom_food_id 必填")
        f = db.query(UserCustomFood).filter(
            UserCustomFood.id == custom_food_id,
            UserCustomFood.user_id == user_id,
            UserCustomFood.deleted_at.is_(None),
        ).first()
    else:
        if not food_id:
            raise BizException(40001, "food_id 必填")
        f = db.query(Food).filter(Food.id == food_id, Food.is_system == 1, Food.status == "active").first()
    if not f:
        raise BizException(40401, "食物不存在")
    return f


def _nutrition_snapshot(food, food_source: str, unit_type: str, amount_g, serving_count):
    per_100g = {
        "calories_per_100g": Decimal(food.calories_per_100g or 0),
        "carbs_per_100g": Decimal(food.carbs_per_100g or 0),
        "protein_per_100g": Decimal(food.protein_per_100g or 0),
        "fat_per_100g": Decimal(food.fat_per_100g or 0),
    }
    if unit_type == "serving":
        if not food.serving_weight_g:
            raise BizException(40001, "该食物未配置单份重量，请改用克数")
        return calc_nutrition_per_serving(per_100g, food.serving_weight_g, Decimal(serving_count or 0))
    return calc_nutrition_per_100g(per_100g, Decimal(amount_g or 0))


def _record_to_dict(r: DietRecord) -> dict:
    return {
        "id": r.id,
        "record_date": r.record_date.date(),
        "record_time": r.record_time,
        "meal_type": r.meal_type,
        "food_source": r.food_source,
        "food_id": r.food_id,
        "custom_food_id": r.custom_food_id,
        "food_name_snapshot": r.food_name_snapshot,
        "unit_type": r.unit_type,
        "amount_g": r.amount_g,
        "serving_count": r.serving_count,
        "image_url": r.image_url,
        "calories_kcal": r.calories_kcal,
        "carbs_g": r.carbs_g,
        "protein_g": r.protein_g,
        "fat_g": r.fat_g,
        "note": r.note,
    }


@router.get("/recent-foods")
def recent_foods(
    limit: int = Query(10, ge=1, le=20),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.query(DietRecord).filter(
        DietRecord.user_id == user.id,
        DietRecord.deleted_at.is_(None),
    ).order_by(DietRecord.created_at.desc(), DietRecord.id.desc()).limit(100).all()
    items = []
    for row in recent_unique_records(rows, limit):
        try:
            food = _ensure_food(db, user.id, row.food_source, row.food_id, row.custom_food_id)
        except BizException:
            continue
        items.append({
            "id": food.id,
            "source": row.food_source,
            "name": food.name,
            "category": food.category,
            "calories_per_100g": food.calories_per_100g,
            "carbs_per_100g": food.carbs_per_100g,
            "protein_per_100g": food.protein_per_100g,
            "fat_per_100g": food.fat_per_100g,
            "default_unit": row.unit_type,
            "serving_weight_g": food.serving_weight_g,
            "recent_amount": row.serving_count if row.unit_type == "serving" else row.amount_g,
        })
    return ok({"items": items})


@router.post("/copy-meal")
def copy_meal(
    body: CopyMealIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.source_meal_type not in MEAL_TYPES or body.target_meal_type not in MEAL_TYPES:
        raise BizException(40001, "餐次不正确")
    start, end = day_bounds(body.source_date)
    source_rows = db.query(DietRecord).filter(
        DietRecord.user_id == user.id,
        DietRecord.deleted_at.is_(None),
        DietRecord.record_date >= start,
        DietRecord.record_date < end,
        DietRecord.meal_type == body.source_meal_type,
    ).all()
    if not source_rows:
        raise BizException(40401, "没有可复制的餐次记录")
    copied = []
    for source in source_rows:
        row = DietRecord(
            user_id=user.id,
            record_date=datetime.combine(body.target_date, time.min),
            record_time=body.record_time,
            meal_type=body.target_meal_type,
            food_source=source.food_source,
            food_id=source.food_id,
            custom_food_id=source.custom_food_id,
            food_name_snapshot=source.food_name_snapshot,
            unit_type=source.unit_type,
            amount_g=source.amount_g,
            serving_count=source.serving_count,
            image_url=None,
            save_image=0,
            calories_kcal=source.calories_kcal,
            carbs_g=source.carbs_g,
            protein_g=source.protein_g,
            fat_g=source.fat_g,
            note=source.note,
        )
        db.add(row)
        copied.append(row)
    db.add(OperationLog(user_id=user.id, action="diet.copy_meal"))
    db.commit()
    return ok({"count": len(copied)})


@router.get("/records")
def list_records(
    date: str = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from datetime import datetime
    d = datetime.strptime(date, "%Y-%m-%d").date()
    start, end = day_bounds(d)
    rows = db.query(DietRecord).filter(
        DietRecord.user_id == user.id,
        DietRecord.deleted_at.is_(None),
        DietRecord.record_date >= start,
        DietRecord.record_date < end,
    ).order_by(DietRecord.record_time.asc()).all()

    meals = {m: [] for m in MEAL_TYPES}
    summary_rows = []
    for r in rows:
        d = _record_to_dict(r)
        meals[r.meal_type if r.meal_type in MEAL_TYPES else "snack"].append(d)
        summary_rows.append(d)

    s = sum_nutrition(summary_rows)
    return ok({
        "date": date,
        "summary": {
            "calories_kcal": s["calories_kcal"],
            "carbs_g": s["carbs_g"],
            "protein_g": s["protein_g"],
            "fat_g": s["fat_g"],
        },
        "meals": meals,
    })


@router.get("/records/{record_id}")
def get_record(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(DietRecord).filter(
        DietRecord.id == record_id, DietRecord.user_id == user.id, DietRecord.deleted_at.is_(None)
    ).first()
    if not r:
        raise BizException(40401, "饮食记录不存在")
    return ok(_record_to_dict(r))


@router.post("/records")
def create_record(
    body: DietRecordIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    f = _ensure_food(db, user.id, body.food_source, body.food_id, body.custom_food_id)
    nutrition = _nutrition_snapshot(f, body.food_source, body.unit_type, body.amount_g, body.serving_count)
    delete_url = None
    image_url = None
    if body.image_file_id is not None:
        try:
            image_url, delete_url = finalize_upload(
                db, user.id, body.image_file_id, keep=body.save_image
            )
        except ValueError as exc:
            raise BizException(40401, str(exc)) from exc
    elif body.save_image or body.image_url:
        raise BizException(40001, "image_file_id 必填")

    r = DietRecord(
        user_id=user.id,
        record_date=body.record_date,
        record_time=body.record_time,
        meal_type=body.meal_type,
        food_source=body.food_source,
        food_id=body.food_id if body.food_source == "system" else None,
        custom_food_id=body.custom_food_id if body.food_source == "custom" else None,
        food_name_snapshot=f.name,
        unit_type=body.unit_type,
        amount_g=nutrition.get("amount_g") if body.unit_type == "serving" else body.amount_g,
        serving_count=body.serving_count if body.unit_type == "serving" else None,
        image_url=image_url,
        save_image=1 if body.save_image else 0,
        calories_kcal=nutrition["calories_kcal"],
        carbs_g=nutrition["carbs_g"],
        protein_g=nutrition["protein_g"],
        fat_g=nutrition["fat_g"],
        note=body.note,
    )
    db.add(r)
    db.flush()
    db.add(OperationLog(user_id=user.id, action="diet.create", target_type="diet_record", target_id=r.id))
    db.commit()
    if delete_url:
        delete_local_file(delete_url)
    db.refresh(r)
    return ok(_record_to_dict(r))


@router.post("/custom-food-record")
def create_custom_food_record(
    body: CustomFoodRecordIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    food = UserCustomFood(
        user_id=user.id,
        name=body.food.name,
        category=body.food.category,
        calories_per_100g=body.food.calories_per_100g,
        carbs_per_100g=body.food.carbs_per_100g,
        protein_per_100g=body.food.protein_per_100g,
        fat_per_100g=body.food.fat_per_100g,
        default_unit=body.food.default_unit,
        serving_weight_g=body.food.serving_weight_g,
    )
    db.add(food)
    db.flush()

    record_in = body.record
    nutrition = _nutrition_snapshot(
        food, "custom", record_in.unit_type, record_in.amount_g, record_in.serving_count
    )
    record = DietRecord(
        user_id=user.id,
        record_date=datetime.combine(record_in.record_date, time.min),
        record_time=record_in.record_time,
        meal_type=record_in.meal_type,
        food_source="custom",
        custom_food_id=food.id,
        food_name_snapshot=food.name,
        unit_type=record_in.unit_type,
        amount_g=nutrition.get("amount_g") if record_in.unit_type == "serving" else record_in.amount_g,
        serving_count=record_in.serving_count if record_in.unit_type == "serving" else None,
        calories_kcal=nutrition["calories_kcal"],
        carbs_g=nutrition["carbs_g"],
        protein_g=nutrition["protein_g"],
        fat_g=nutrition["fat_g"],
        note=record_in.note,
    )
    db.add(record)
    db.flush()
    db.add_all([
        OperationLog(user_id=user.id, action="foods.custom.create", target_type="food", target_id=food.id),
        OperationLog(user_id=user.id, action="diet.create", target_type="diet_record", target_id=record.id),
    ])
    db.commit()
    db.refresh(record)
    return ok({"food": {"id": food.id, "name": food.name, "source": "custom"}, "record": _record_to_dict(record)})


@router.put("/records/{record_id}")
def update_record(
    record_id: int,
    body: DietRecordUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(DietRecord).filter(
        DietRecord.id == record_id, DietRecord.user_id == user.id, DietRecord.deleted_at.is_(None)
    ).first()
    if not r:
        raise BizException(40401, "饮食记录不存在")

    # if any nutrient-related field changes, re-calc against original food
    need_recalc = any([
        body.unit_type is not None, body.amount_g is not None, body.serving_count is not None,
    ])
    if need_recalc:
        # fetch the food used
        f = _ensure_food(db, user.id, r.food_source, r.food_id, r.custom_food_id)
        unit_type, amount_g, serving_count = merge_and_validate_diet_quantity(
            body,
            r.unit_type,
            r.amount_g,
            r.serving_count,
        )
        n = _nutrition_snapshot(f, r.food_source, unit_type, amount_g, serving_count)
        r.calories_kcal = n["calories_kcal"]
        r.carbs_g = n["carbs_g"]
        r.protein_g = n["protein_g"]
        r.fat_g = n["fat_g"]
        if unit_type == "serving":
            r.amount_g = n.get("amount_g")
            r.serving_count = serving_count
        else:
            r.amount_g = amount_g
            r.serving_count = None
        r.unit_type = unit_type

    if body.record_date is not None:
        import datetime as _dt
        r.record_date = _dt.datetime.combine(body.record_date, _dt.time(0, 0))
    if body.record_time is not None:
        r.record_time = body.record_time
    if body.meal_type is not None:
        r.meal_type = body.meal_type
    if body.image_url is not None:
        r.image_url = body.image_url
    if body.save_image is not None:
        r.save_image = 1 if body.save_image else 0
    if body.note is not None:
        r.note = body.note

    db.add(OperationLog(user_id=user.id, action="diet.update", target_type="diet_record", target_id=r.id))
    db.commit()
    db.refresh(r)
    return ok(_record_to_dict(r))


@router.delete("/records/{record_id}")
def delete_record(
    record_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(DietRecord).filter(
        DietRecord.id == record_id, DietRecord.user_id == user.id, DietRecord.deleted_at.is_(None)
    ).first()
    if not r:
        raise BizException(40401, "饮食记录不存在")
    from datetime import datetime
    r.deleted_at = datetime.utcnow()
    db.add(OperationLog(user_id=user.id, action="diet.delete", target_type="diet_record", target_id=r.id))
    db.commit()
    return ok({"deleted": record_id})
