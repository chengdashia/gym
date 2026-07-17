from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest

from app.api.v1 import auth
from app.core.config import settings
from app.core.exceptions import BizException
from app.models import User
from app.schemas import WechatLoginIn


@pytest.mark.parametrize(
    ("agreement", "nickname", "avatar", "goal", "expected"),
    [
        (False, "昵称", "avatar.png", "fat_loss", "agreement"),
        (True, "", "avatar.png", "fat_loss", "profile"),
        (True, "昵称", "", "fat_loss", "profile"),
        (True, "昵称", "avatar.png", None, "complete"),
        (True, "昵称", "avatar.png", "fat_loss", "complete"),
    ],
)
def test_onboarding_step_is_derived_from_persisted_user_state(
    agreement, nickname, avatar, goal, expected
):
    user = SimpleNamespace(
        agreement_confirmed_at=object() if agreement else None,
        nickname=nickname,
        avatar_url=avatar,
        profile=SimpleNamespace(fitness_goal=goal) if goal else None,
    )

    assert auth._onboarding_step(user) == expected


def test_exchange_wechat_code_returns_openid(monkeypatch):
    response = httpx.Response(
        200,
        json={"openid": "wx-openid-1", "session_key": "session-1"},
        request=httpx.Request("GET", auth.WECHAT_SESSION_URL),
    )
    request = MagicMock(return_value=response)
    monkeypatch.setattr(auth.httpx, "get", request)
    monkeypatch.setattr(settings, "wechat_appid", "test-app-id")
    monkeypatch.setattr(settings, "wechat_secret", "test-secret")

    assert auth._exchange_wechat_code("one-time-code") == {"openid": "wx-openid-1", "session_key": "session-1"}
    request.assert_called_once_with(
        auth.WECHAT_SESSION_URL,
        params={
            "appid": "test-app-id",
            "secret": "test-secret",
            "js_code": "one-time-code",
            "grant_type": "authorization_code",
        },
        timeout=8.0,
    )


def test_exchange_wechat_code_rejects_wechat_error(monkeypatch):
    response = httpx.Response(
        200,
        json={"errcode": 40029, "errmsg": "invalid code"},
        request=httpx.Request("GET", auth.WECHAT_SESSION_URL),
    )
    monkeypatch.setattr(auth.httpx, "get", MagicMock(return_value=response))
    monkeypatch.setattr(settings, "wechat_appid", "test-app-id")
    monkeypatch.setattr(settings, "wechat_secret", "test-secret")

    with pytest.raises(BizException, match="微信登录失败"):
        auth._exchange_wechat_code("expired-code")


def test_wechat_login_reuses_existing_openid_user(monkeypatch):
    user = SimpleNamespace(
        id=7,
        openid="wx-openid-1",
        nickname="Existing",
        avatar_url="",
        agreement_confirmed_at=None,
        is_member=0,
        member_expired_at=None,
        status="active",
        last_login_at=None,
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user
    monkeypatch.setattr(auth, "_exchange_wechat_code", lambda code: {"openid": "wx-openid-1"})
    monkeypatch.setattr(auth, "_issue_token", lambda current_user: "jwt-token")

    result = auth.wechat_login(
        WechatLoginIn(code="one-time-code", nickname="微信昵称", avatar_url="https://avatar.example/avatar.png"),
        db,
    )

    assert result["data"]["access_token"] == "jwt-token"
    assert result["data"]["user"]["id"] == 7
    assert user.nickname == "微信昵称"
    assert user.avatar_url == "https://avatar.example/avatar.png"
    db.add.assert_not_called()
