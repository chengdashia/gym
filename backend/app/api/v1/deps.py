from typing import Optional

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import BizException
from app.core.security import decode_access_token
from app.models import User


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization:
        raise BizException(40101, "未登录或 token 失效", status_code=401)
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise BizException(40101, "未登录或 token 失效", status_code=401)
    token = parts[1]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise BizException(40101, "未登录或 token 失效", status_code=401)
    user_id = payload.get("uid")
    if not user_id:
        raise BizException(40101, "未登录或 token 失效", status_code=401)
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.status != "active":
        raise BizException(40101, "未登录或 token 失效", status_code=401)
    return user