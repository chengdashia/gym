import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import BizException
from app.core.response import ok
from app.models import Food, User
from app.schemas import AIRecognizeIn


router = APIRouter(prefix="/ai", tags=["ai"])

FOOD_LABELS_FILE = Path(__file__).resolve().parents[2] / "data" / "food_model_labels.json"


@router.get("/food-recognition/model-manifest")
def food_model_manifest(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.id not in settings.experimental_user_ids:
        raise BizException(40301, "该实验功能尚未向当前账号开放", 403)
    if not settings.food_model_url or not settings.food_model_version:
        raise BizException(50301, "本地识别模型尚未发布", 503)

    labels = json.loads(FOOD_LABELS_FILE.read_text(encoding="utf-8"))
    foods_by_name = {
        row.name: row.id
        for row in db.query(Food).filter(Food.is_system == 1, Food.status == "active").all()
    }
    return ok({
        "version": settings.food_model_version,
        "model_url": settings.food_model_url,
        "input_size": 320,
        "input_name": "images",
        "output_names": {
            "scores": "scores",
            "labels": "labels",
            "area_ratios": "area_ratios",
        },
        "score_threshold": 0.35,
        "labels": [
            {**label, "food_id": foods_by_name.get(label["name"])}
            for label in labels
        ],
    })


@router.post("/food-recognition")
def food_recognition(
    body: AIRecognizeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    raise BizException(41001, "旧版云端模拟识别已停用，请升级到本地识别版本", 410)
