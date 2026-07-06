import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import BizException
from app.core.response import ok
from app.models import OperationLog, UploadedFile, User


router = APIRouter(prefix="/uploads", tags=["uploads"])

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    usage_type: str = Form(default="food_recognition"),
    temporary: bool = Form(default=True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise BizException(40001, "未上传文件")
    ext = Path(file.filename).suffix.lower() or ".jpg"
    if ext not in ALLOWED_EXT:
        raise BizException(40001, f"不支持的文件类型: {ext}")

    today = datetime.now().strftime("%Y%m%d")
    sub = Path(settings.upload_dir) / today
    sub.mkdir(parents=True, exist_ok=True)
    new_name = f"{uuid.uuid4().hex}{ext}"
    dst = sub / new_name

    contents = await file.read()
    size = len(contents)
    if size > settings.upload_max_size_mb * 1024 * 1024:
        raise BizException(60001, f"文件过大（>{settings.upload_max_size_mb}MB）")

    with open(dst, "wb") as f:
        f.write(contents)

    file_url = f"{settings.static_url_prefix.rstrip('/')}/{today}/{new_name}"
    uf = UploadedFile(
        user_id=user.id,
        file_type="image",
        usage_type=usage_type,
        file_url=file_url,
        storage_provider="local",
        original_name=file.filename,
        file_size=size,
        mime_type=file.content_type,
        is_temporary=1 if temporary else 0,
    )
    db.add(uf)
    db.flush()
    db.add(OperationLog(
        user_id=user.id, action="uploads.image",
        target_type="uploaded_file", target_id=uf.id,
        detail_json={"usage_type": usage_type, "size": size},
    ))
    db.commit()
    db.refresh(uf)

    return ok({"file_id": uf.id, "file_url": uf.file_url, "is_temporary": bool(uf.is_temporary)})