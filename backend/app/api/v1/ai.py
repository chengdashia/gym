import random
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import BizException
from app.core.response import ok
from app.models import Food, FoodRecognitionLog, UploadedFile, User
from app.schemas import AIRecognizeIn, AICandidate, AIRecognizedItem


router = APIRouter(prefix="/ai", tags=["ai"])

MOCK_CANDIDATES = [
    {"food_id": 1, "name": "米饭", "confidence": 0.92, "source": "system"},
    {"food_id": 2, "name": "鸡蛋", "confidence": 0.81, "source": "system"},
    {"food_id": 3, "name": "鸡胸肉", "confidence": 0.76, "source": "system"},
]


@router.post("/food-recognition")
def food_recognition(
    body: AIRecognizeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uf = db.query(UploadedFile).filter(UploadedFile.id == body.file_id, UploadedFile.user_id == user.id).first()
    if not uf:
        raise BizException(40401, "图片不存在")

    sys_foods = db.query(Food).filter(Food.is_system == 1, Food.status == "active").limit(20).all()
    if sys_foods:
        pool = [(f.id, f.name, "system") for f in sys_foods]
        chosen = random.sample(pool, k=min(3, len(pool)))
        candidates_payload = []
        for i, (fid, name, source) in enumerate(chosen):
            candidates_payload.append({
                "food_id": fid, "source": source, "name": name,
                "confidence": round(0.95 - i * 0.08, 2),
            })
    else:
        candidates_payload = list(MOCK_CANDIDATES)

    recognized_items_payload = [
        {**candidate, "estimated_amount_g": 100}
        for candidate in candidates_payload[:3]
    ]
    candidates = [AICandidate(**c) for c in candidates_payload]
    recognized_items = [AIRecognizedItem(**item) for item in recognized_items_payload]
    recognized_items_json = [item.model_dump(mode="json") for item in recognized_items]

    log = FoodRecognitionLog(
        user_id=user.id,
        image_url=uf.file_url,
        recognition_status="success",
        candidates_json={
            "recognized_items": recognized_items_json,
            "candidates": candidates_payload,
        },
        provider="mock",
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return ok({
        "recognition_id": log.id,
        "provider": "mock",
        "recognized_items": recognized_items_json,
        "candidates": [c.model_dump() for c in candidates],
    })
