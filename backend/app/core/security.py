import hmac
from datetime import datetime, timedelta, timezone
from hashlib import pbkdf2_hmac
from secrets import token_hex

import jwt

from app.core.config import settings


def create_access_token(user_id: int, sub: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "uid": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])


def hash_password(password: str) -> str:
    salt = token_hex(16)
    hash_value = pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return f"{salt}${hash_value}"


def verify_password(password: str, hashed: str) -> bool:
    if not hashed or "$" not in hashed:
        return False
    salt, stored_hash = hashed.split("$", 1)
    hash_value = pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return hmac.compare_digest(hash_value, stored_hash)
