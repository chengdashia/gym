import io
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import UploadedFile


ALLOWED_IMAGE_FORMATS = {"jpeg", "png", "webp", "gif"}


def validate_image_bytes(contents: bytes, extension: str) -> str:
    if not contents:
        raise ValueError("图片内容为空")
    try:
        with Image.open(io.BytesIO(contents)) as image:
            image.verify()
            image_format = (image.format or "").lower()
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise ValueError("无效的图片内容") from exc
    if image_format not in ALLOWED_IMAGE_FORMATS:
        raise ValueError("不支持的图片内容")
    return image_format


def delete_local_file(file_url: str) -> bool:
    prefix = settings.static_url_prefix.rstrip("/")
    if not file_url.startswith(f"{prefix}/"):
        return False

    upload_root = Path(settings.upload_dir).resolve()
    path = (upload_root / file_url[len(prefix):].lstrip("/")).resolve()
    if upload_root not in path.parents:
        return False

    try:
        path.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def cleanup_expired_uploads(db: Session) -> None:
    expired = db.query(UploadedFile).filter(
        UploadedFile.is_temporary == 1,
        UploadedFile.expired_at.is_not(None),
        UploadedFile.expired_at <= datetime.utcnow(),
    ).all()
    if not expired:
        return

    file_urls = [upload.file_url for upload in expired]
    for upload in expired:
        db.delete(upload)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    for file_url in file_urls:
        delete_local_file(file_url)


def finalize_upload(
    db: Session,
    user_id: int,
    file_id: int,
    keep: bool,
) -> Tuple[Optional[str], Optional[str]]:
    upload = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.user_id == user_id,
    ).first()
    if not upload or upload.user_id != user_id:
        raise ValueError("图片不存在")

    if keep:
        upload.is_temporary = 0
        upload.usage_type = "diet_record"
        upload.expired_at = None
        return upload.file_url, None

    db.delete(upload)
    return None, upload.file_url
