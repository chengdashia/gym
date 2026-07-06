from datetime import datetime, time
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import BizException
from app.core.response import ok
from app.models import OperationLog, User, WeightRecord
from app.schemas import WeightListOut, WeightRecordIn, WeightRecordOut, WeightRecordUpdateIn
from app.utils.date import range_dates


router = APIRouter(prefix="/weight", tags=["weight"])


def _to_dict(r: WeightRecord) -> dict:
    return {
        "id": r.id,
        "record_date": r.record_date.date(),
        "record_time": r.record_time,
        "weight_kg": r.weight_kg,
        "note": r.note,
    }


@router.get("/records")
def list_records(
    range: Optional[int] = Query(default=None),
    start_date: Optional[str] = Query(default=None),
    end_date: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(WeightRecord).filter(
        WeightRecord.user_id == user.id, WeightRecord.deleted_at.is_(None),
    )
    if range and not start_date and not end_date:
        end = datetime.now()
        start = datetime.combine(end.date() - __import__("datetime").timedelta(days=range - 1), time(0, 0))
        q = q.filter(WeightRecord.record_date >= start, WeightRecord.record_date <= end)
    if start_date:
        s = datetime.strptime(start_date, "%Y-%m-%d")
        q = q.filter(WeightRecord.record_date >= s)
    if end_date:
        e = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        q = q.filter(WeightRecord.record_date <= e)
    q = q.order_by(WeightRecord.record_date.desc(), WeightRecord.record_time.desc())
    return ok({"items": [_to_dict(r) for r in q.all()]})


@router.post("/records")
def create_record(body: WeightRecordIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = WeightRecord(
        user_id=user.id,
        record_date=datetime.combine(body.record_date, time(0, 0)),
        record_time=body.record_time,
        weight_kg=body.weight_kg,
        note=body.note,
    )
    db.add(r)
    db.flush()
    db.add(OperationLog(user_id=user.id, action="weight.create", target_type="weight", target_id=r.id))
    db.commit()
    db.refresh(r)
    return ok(_to_dict(r))


@router.put("/records/{record_id}")
def update_record(
    record_id: int, body: WeightRecordUpdateIn,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    r = db.query(WeightRecord).filter(
        WeightRecord.id == record_id, WeightRecord.user_id == user.id, WeightRecord.deleted_at.is_(None),
    ).first()
    if not r:
        raise BizException(40401, "体重记录不存在")
    if body.record_date is not None:
        r.record_date = datetime.combine(body.record_date, time(0, 0))
    if body.record_time is not None:
        r.record_time = body.record_time
    if body.weight_kg is not None:
        r.weight_kg = body.weight_kg
    if body.note is not None:
        r.note = body.note
    db.add(OperationLog(user_id=user.id, action="weight.update", target_type="weight", target_id=r.id))
    db.commit()
    db.refresh(r)
    return ok(_to_dict(r))


@router.delete("/records/{record_id}")
def delete_record(record_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.query(WeightRecord).filter(
        WeightRecord.id == record_id, WeightRecord.user_id == user.id, WeightRecord.deleted_at.is_(None),
    ).first()
    if not r:
        raise BizException(40401, "体重记录不存在")
    r.deleted_at = datetime.utcnow()
    db.add(OperationLog(user_id=user.id, action="weight.delete", target_type="weight", target_id=r.id))
    db.commit()
    return ok({"deleted": record_id})