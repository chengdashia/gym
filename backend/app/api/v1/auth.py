import base64
import io
import random
import time
from datetime import datetime
from secrets import token_urlsafe

import httpx
from fastapi import APIRouter, Depends
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.core.config import settings
from app.core.exceptions import BizException
from app.core.response import ok
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User, UserProfile
from app.schemas import (
    CaptchaOut,
    PhoneLoginIn,
    RegisterIn,
    UserMeIn,
    UserMeOut,
    UserProfileOut,
    WechatLoginIn,
    WechatLoginOut,
)


router = APIRouter(prefix="/auth", tags=["auth"])

# 内存验证码缓存：{captcha_id: {"answer": str, "expires": timestamp}}
_CAPTCHA_STORE: dict[str, dict] = {}
_CAPTCHA_TTL_SECONDS = 300
_CAPTCHA_MAX_ATTEMPTS = 5
_CAPTCHA_MAX_ITEMS = 1000
WECHAT_SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


def _exchange_wechat_code(code: str) -> dict:
    if not settings.wechat_appid or not settings.wechat_secret:
        raise BizException(40008, "微信登录配置不完整")

    try:
        response = httpx.get(
            WECHAT_SESSION_URL,
            params={
                "appid": settings.wechat_appid,
                "secret": settings.wechat_secret,
                "js_code": code,
                "grant_type": "authorization_code",
            },
            timeout=8.0,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise BizException(40008, "微信登录服务暂时不可用") from exc

    if payload.get("errcode") or not payload.get("openid"):
        raise BizException(40008, "微信登录失败")
    return payload


def _cleanup_captchas(now: float | None = None) -> None:
    current = time.time() if now is None else now
    for captcha_id, item in list(_CAPTCHA_STORE.items()):
        if item["expires"] < current:
            _CAPTCHA_STORE.pop(captcha_id, None)
    while len(_CAPTCHA_STORE) >= _CAPTCHA_MAX_ITEMS:
        _CAPTCHA_STORE.pop(next(iter(_CAPTCHA_STORE)))


def _make_captcha_png(code: str) -> str:
    """生成 120x44 的 PNG 验证码图片，返回 data:image/png;base64 字符串。"""
    w, h = 120, 44
    img = Image.new("RGB", (w, h), "#F0F7F4")
    draw = ImageDraw.Draw(img)

    # 干扰线
    for _ in range(6):
        x1, y1, x2, y2 = random.randint(0, w), random.randint(0, h), random.randint(0, w), random.randint(0, h)
        draw.line([(x1, y1), (x2, y2)], fill="#BFD9CC", width=1)

    # 干扰点
    for _ in range(40):
        x, y = random.randint(0, w), random.randint(0, h)
        draw.point((x, y), fill="#A8CDB8")

    # 字符
    try:
        font = ImageFont.truetype("Arial.ttf", 28)
    except Exception:
        font = ImageFont.load_default()
    for i, ch in enumerate(code):
        x = 16 + i * 24 + random.randint(-4, 4)
        y = 6 + random.randint(-4, 4)
        draw.text((x, y), ch, font=font, fill="#3A6B5A")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def _verify_captcha(captcha_id: str, captcha_code: str) -> bool:
    if not captcha_id or not captcha_code:
        return False
    _cleanup_captchas()
    item = _CAPTCHA_STORE.get(captcha_id)
    if not item:
        return False
    ok = item["answer"].lower() == captcha_code.strip().lower()
    if ok:
        _CAPTCHA_STORE.pop(captcha_id, None)
    else:
        item["attempts"] = item.get("attempts", 0) + 1
        if item["attempts"] >= _CAPTCHA_MAX_ATTEMPTS:
            _CAPTCHA_STORE.pop(captcha_id, None)
    return ok


def _user_summary(user: User, is_new: bool = False) -> dict:
    return {
        "id": user.id,
        "openid": user.openid,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "is_new_user": is_new,
        "agreement_confirmed": user.agreement_confirmed_at is not None,
        "is_member": bool(user.is_member),
        "member_expired_at": user.member_expired_at.isoformat() if user.member_expired_at else None,
    }


def _issue_token(user: User) -> str:
    sub = user.phone or user.openid or str(user.id)
    return create_access_token(user_id=user.id, sub=sub)


@router.get("/captcha")
def get_captcha():
    """获取图形验证码，返回 PNG Base64 图片。"""
    _cleanup_captchas()
    code = "".join(random.choices("0123456789", k=4))
    captcha_id = token_urlsafe(16)
    _CAPTCHA_STORE[captcha_id] = {
        "answer": code,
        "expires": time.time() + _CAPTCHA_TTL_SECONDS,
        "attempts": 0,
    }
    png_data_url = _make_captcha_png(code)
    return ok({"captcha_id": captcha_id, "svg": png_data_url})


@router.post("/phone-login")
def phone_login(body: PhoneLoginIn, db: Session = Depends(get_db)):
    """手机号 + 密码登录。"""
    phone = body.phone.strip()
    user = db.query(User).filter(User.phone == phone).first()
    if not user or not verify_password(body.password, user.password_hash or ""):
        raise BizException(40002, "手机号或密码错误")
    if user.status != "active":
        raise BizException(40003, "账号已被禁用")

    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    token = _issue_token(user)
    return ok({"access_token": token, "token_type": "Bearer", "user": _user_summary(user)})


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    """手机号注册。"""
    phone = body.phone.strip()
    if db.query(User).filter(User.phone == phone).first():
        raise BizException(40004, "该手机号已注册")
    if body.password != body.confirm_password:
        raise BizException(40005, "两次输入的密码不一致")
    if len(body.password) < 6:
        raise BizException(40006, "密码长度不能少于 6 位")
    if not _verify_captcha(body.captcha_id, body.captcha_code):
        raise BizException(40007, "验证码错误或已过期")

    user = User(
        phone=phone,
        password_hash=hash_password(body.password),
        nickname=body.nickname or f"用户{phone[-4:]}",
        avatar_url=body.avatar_url or "",
        status="active",
    )
    db.add(user)
    db.flush()
    db.add(UserProfile(user_id=user.id))
    db.commit()
    db.refresh(user)

    token = _issue_token(user)
    return ok({"access_token": token, "token_type": "Bearer", "user": _user_summary(user, is_new=True)})


@router.post("/wechat-login")
def wechat_login(body: WechatLoginIn, db: Session = Depends(get_db)):
    """使用微信临时 code 登录，并用 openid 绑定本地用户。"""
    code = body.code.strip()
    if not code:
        raise BizException(40001, "code 不能为空")

    if settings.mock_wechat:
        openid = code
    else:
        openid = _exchange_wechat_code(code)["openid"]

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
    else:
        if body.nickname:
            user.nickname = body.nickname
        if body.avatar_url:
            user.avatar_url = body.avatar_url

    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    token = _issue_token(user)
    return ok({"access_token": token, "token_type": "Bearer", "user": _user_summary(user, is_new)})
