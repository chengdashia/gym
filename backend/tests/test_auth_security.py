import time

from app.api.v1 import auth
from app.core import security


def test_verify_password_uses_constant_time_comparison(monkeypatch):
    called = []
    hashed = security.hash_password("correct-password")
    monkeypatch.setattr(
        security.hmac,
        "compare_digest",
        lambda actual, expected: called.append((actual, expected)) or actual == expected,
    )

    assert security.verify_password("correct-password", hashed)
    assert called


def test_captcha_is_removed_after_five_wrong_attempts():
    auth._CAPTCHA_STORE.clear()
    auth._CAPTCHA_STORE["captcha-id"] = {
        "answer": "1234",
        "expires": time.time() + 60,
        "attempts": 0,
    }

    for _ in range(5):
        assert not auth._verify_captcha("captcha-id", "0000")

    assert "captcha-id" not in auth._CAPTCHA_STORE


def test_expired_captchas_are_cleaned_before_new_one_is_added(monkeypatch):
    auth._CAPTCHA_STORE.clear()
    auth._CAPTCHA_STORE["expired"] = {
        "answer": "1234",
        "expires": time.time() - 1,
        "attempts": 0,
    }
    monkeypatch.setattr(auth, "_make_captcha_png", lambda code: "data:image/png;base64,test")

    auth.get_captcha()

    assert "expired" not in auth._CAPTCHA_STORE
    assert len(auth._CAPTCHA_STORE) == 1
