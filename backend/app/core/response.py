from datetime import datetime, timezone


def ok(data=None, message: str = "success"):
    return {"code": 0, "message": message, "data": data}


def fail(code: int, message: str):
    return {"code": code, "message": message, "data": None}


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)