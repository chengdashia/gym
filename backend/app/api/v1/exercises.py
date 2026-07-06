from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.response import ok
from app.models import Exercise, OperationLog, User, UserCustomExercise
from app.schemas import ExerciseCustomIn, ExerciseOut, ExerciseSearchOut


router = APIRouter(prefix="/exercises", tags=["exercises"])


def _to_dict(e, source: str) -> dict:
    return {
        "id": e.id,
        "source": source,
        "name": e.name,
        "body_part": e.body_part,
        "description": e.description,
    }


@router.get("/search")
def search_exercises(
    keyword: Optional[str] = Query(default=None, max_length=64),
    body_part: Optional[str] = Query(default=None, max_length=32),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q_sys = db.query(Exercise).filter(Exercise.is_system == 1, Exercise.status == "active")
    q_custom = db.query(UserCustomExercise).filter(
        UserCustomExercise.user_id == user.id, UserCustomExercise.deleted_at.is_(None)
    )
    if keyword:
        like = f"%{keyword}%"
        q_sys = q_sys.filter(or_(Exercise.name.like(like), Exercise.body_part.like(like)))
        q_custom = q_custom.filter(or_(UserCustomExercise.name.like(like), UserCustomExercise.body_part.like(like)))
    if body_part:
        q_sys = q_sys.filter(Exercise.body_part == body_part)
        q_custom = q_custom.filter(UserCustomExercise.body_part == body_part)

    sys_items = q_sys.order_by(Exercise.id.asc()).all()
    custom_items = q_custom.order_by(UserCustomExercise.id.asc()).all()
    items = [_to_dict(e, "system") for e in sys_items] + [_to_dict(e, "custom") for e in custom_items]
    total = len(items)
    start = (page - 1) * page_size
    items = items[start:start + page_size]
    return ok({"items": items, "total": total})


@router.post("/custom")
def create_custom(
    body: ExerciseCustomIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    e = UserCustomExercise(
        user_id=user.id,
        name=body.name,
        body_part=body.body_part,
        description=body.description,
    )
    db.add(e)
    db.flush()
    db.add(OperationLog(user_id=user.id, action="exercises.custom.create", target_type="exercise", target_id=e.id))
    db.commit()
    db.refresh(e)
    return ok(_to_dict(e, "custom"))