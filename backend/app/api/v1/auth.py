from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import BizException
from app.core.response import ok
from app.core.security import create_access_token
from app.models import User, UserProfile
from app.schemas import UserMeIn, UserMeOut, UserProfileOut, WechatLoginIn, WechatLoginOut


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/wechat-login")
def wechat_login(body: WechatLoginIn, db: Session = Depends(get_db)):
    """开发期 mock：直接用 code 作为 openid upsert。"""
    openid = body.code.strip()
    if not openid:
        raise BizException(40001, "code 不能为空")

    user = db.query(User).filter(User.openid == openid).first()
    is_new = False
    if not user:
        user = User(
            openid=openid,
            nickname=body.nickname or "微信用户",
            avatar_url=body.avatar_url or "",
            status="active",
        )
        db.add(user)
        db.flush()
        db.add(UserProfile(user_id=user.id))
        is_new = True

    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    token = create_access_token(openid=user.openid, user_id=user.id)
    summary = {
        "id": user.id,
        "openid": user.openid if not is_new else None,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "is_new_user": is_new,
        "agreement_confirmed": user.agreement_confirmed_at is not None,
        "is_member": bool(user.is_member),
        "member_expired_at": user.member_expired_at.isoformat() if user.member_expired_at else None,
    }
    return ok({"access_token": token, "token_type": "Bearer", "user": summary})