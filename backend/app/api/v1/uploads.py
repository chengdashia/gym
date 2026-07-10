import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import BizException
from app.core.response import ok
from app.models import OperationLog, UploadedFile, User
from app.services.uploads import (
    cleanup_expired_uploads,
    delete_local_file,
    local_file_path,
    normalize_image,
    validate_image_bytes,
)


router = APIRouter(prefix="/uploads", tags=["uploads"])

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_USAGE = {"food_recognition", "diet_record", "avatar"}


def upload_policy(usage_type: str, temporary: bool) -> tuple[str, bool]:
    if usage_type not in ALLOWED_USAGE:
        raise BizException(40001, "不支持的图片用途")
    if usage_type == "avatar" and temporary:
        raise BizException(40001, "头像必须永久保存")
    return usage_type, temporary


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
    usage_type, temporary = upload_policy(usage_type, temporary)
    ext = Path(file.filename).suffix.lower() or ".jpg"
    if ext not in ALLOWED_EXT:
        raise BizException(40001, f"不支持的文件类型: {ext}")

    today = datetime.now().strftime("%Y%m%d")
    sub = Path(settings.upload_dir) / today
    sub.mkdir(parents=True, exist_ok=True)
    contents = await file.read()
    size = len(contents)
    if size == 0:
        raise BizException(60001, "图片内容为空")
    if size > settings.upload_max_size_mb * 1024 * 1024:
        raise BizException(60001, f"文件过大（>{settings.upload_max_size_mb}MB）")
    try:
        validate_image_bytes(contents, ext)
        contents, ext, mime_type = normalize_image(contents)
        size = len(contents)
    except ValueError as exc:
        raise BizException(60001, str(exc)) from exc

    new_name = f"{uuid.uuid4().hex}{ext}"
    dst = sub / new_name

    cleanup_expired_uploads(db)

    with open(dst, "wb") as f:
        f.write(contents)

    url_prefix = settings.static_url_prefix.rstrip("/") if usage_type == "avatar" else "/private"
    file_url = f"{url_prefix}/{today}/{new_name}"
    uf = UploadedFile(
        user_id=user.id,
        file_type="image",
        usage_type=usage_type,
        file_url=file_url,
        storage_provider="local",
        original_name=file.filename,
        file_size=size,
        mime_type=mime_type,
        is_temporary=1 if temporary else 0,
    )
    uf.expired_at = datetime.now() + timedelta(hours=24) if temporary else None
    try:
        db.add(uf)
        db.flush()
        db.add(OperationLog(
            user_id=user.id, action="uploads.image",
            target_type="uploaded_file", target_id=uf.id,
            detail_json={"usage_type": usage_type, "size": size},
        ))
        db.commit()
        db.refresh(uf)
    except Exception:
        db.rollback()
        delete_local_file(file_url)
        raise

    return ok({"file_id": uf.id, "file_url": uf.file_url, "is_temporary": bool(uf.is_temporary)})


@router.get("/{file_id}/content")
def get_upload_content(
    file_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    upload = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.user_id == user.id,
    ).first()
    if not upload:
        raise BizException(40401, "图片不存在", status_code=404)
    path = local_file_path(upload.file_url)
    if path is None or not path.is_file():
        raise BizException(40401, "图片不存在", status_code=404)
    return FileResponse(path, media_type=upload.mime_type or "application/octet-stream")
