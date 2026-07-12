import io
import base64
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import UploadedFile


ALLOWED_IMAGE_FORMATS = {"jpeg", "png", "webp", "gif"}


def normalize_image(contents: bytes) -> tuple[bytes, str, str]:
    try:
        with Image.open(io.BytesIO(contents)) as source:
            image = ImageOps.exif_transpose(source)
            output = io.BytesIO()
            if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
                image.convert("RGBA").save(output, format="PNG", optimize=True)
                return output.getvalue(), ".png", "image/png"
            image.convert("RGB").save(output, format="JPEG", quality=88, optimize=True)
            return output.getvalue(), ".jpg", "image/jpeg"
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise ValueError("无效的图片内容") from exc


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
    path = local_file_path(file_url)
    if path is None:
        return False

    try:
        path.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def local_file_path(file_url: str) -> Path | None:
    if file_url.startswith(("http://", "https://")):
        file_url = urlparse(file_url).path
    prefixes = (settings.static_url_prefix.rstrip("/"), "/private")
    prefix = next((item for item in prefixes if file_url.startswith(f"{item}/")), None)
    if prefix is None:
        return None
    upload_root = Path(settings.upload_dir).resolve()
    path = (upload_root / file_url[len(prefix):].lstrip("/")).resolve()
    return path if upload_root in path.parents else None


def image_data_url(file_url: str) -> str | None:
    path = local_file_path(file_url)
    if path is None or not path.is_file():
        return None
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def cleanup_expired_uploads(db: Session) -> None:
    expired = db.query(UploadedFile).filter(
        UploadedFile.is_temporary == 1,
        UploadedFile.expired_at.is_not(None),
        UploadedFile.expired_at <= datetime.now(),
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
