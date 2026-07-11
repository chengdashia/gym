from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import BizException
from app.core.response import ok
from app.models import Food, OperationLog, User, UserCustomFood
from app.schemas import FoodCustomIn, FoodOut, FoodSearchOut


router = APIRouter(prefix="/foods", tags=["foods"])


def _food_to_dict(f, source: str) -> dict:
    return {
        "id": f.id,
        "source": source,
        "name": f.name,
        "category": f.category,
        "calories_per_100g": f.calories_per_100g,
        "carbs_per_100g": f.carbs_per_100g,
        "protein_per_100g": f.protein_per_100g,
        "fat_per_100g": f.fat_per_100g,
        "fiber_per_100g": f.fiber_per_100g,
        "default_unit": f.default_unit,
        "serving_weight_g": f.serving_weight_g,
    }


@router.get("/search")
def search_foods(
    keyword: Optional[str] = Query(default=None, max_length=64),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q_sys = db.query(Food).filter(Food.status == "active", Food.is_system == 1)
    q_custom = db.query(UserCustomFood).filter(
        UserCustomFood.user_id == user.id, UserCustomFood.deleted_at.is_(None)
    )
    if keyword:
        like = f"%{keyword}%"
        q_sys = q_sys.filter(or_(Food.name.like(like), Food.category.like(like)))
        q_custom = q_custom.filter(or_(UserCustomFood.name.like(like), UserCustomFood.category.like(like)))

    sys_items = q_sys.order_by(Food.id.asc()).all()
    custom_items = q_custom.order_by(UserCustomFood.id.asc()).all()

    items = [_food_to_dict(f, "system") for f in sys_items] + [
        _food_to_dict(f, "custom") for f in custom_items
    ]
    total = len(items)
    start = (page - 1) * page_size
    items = items[start:start + page_size]
    return ok({"items": items, "total": total})


@router.get("/{food_id}")
def get_food(
    food_id: int,
    source: str = Query(default="system", pattern="^(system|custom)$"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if source == "custom":
        f = db.query(UserCustomFood).filter(
            UserCustomFood.id == food_id, UserCustomFood.user_id == user.id,
            UserCustomFood.deleted_at.is_(None),
        ).first()
    else:
        f = db.query(Food).filter(Food.id == food_id, Food.is_system == 1, Food.status == "active").first()
    if not f:
        raise BizException(40401, "食物不存在")
    return ok(_food_to_dict(f, source))


@router.post("/custom")
def create_custom_food(
    body: FoodCustomIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    f = UserCustomFood(
        user_id=user.id,
        name=body.name,
        category=body.category,
        calories_per_100g=body.calories_per_100g,
        carbs_per_100g=body.carbs_per_100g,
        protein_per_100g=body.protein_per_100g,
        fat_per_100g=body.fat_per_100g,
        default_unit=body.default_unit,
        serving_weight_g=body.serving_weight_g,
    )
    db.add(f)
    db.flush()
    db.add(OperationLog(user_id=user.id, action="foods.custom.create", target_type="food", target_id=f.id))
    db.commit()
    db.refresh(f)
    return ok(_food_to_dict(f, "custom"))
