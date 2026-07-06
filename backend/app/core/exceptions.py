from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.response import fail


class BizException(Exception):
    """业务异常：status_code 对应 HTTP，业务 code 对应文档 §3.4 错误码。"""

    def __init__(self, code: int, message: str, status_code: int = 400, data: Any = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.data = data
        super().__init__(message)


async def biz_exception_handler(request: Request, exc: BizException):
    return JSONResponse(status_code=exc.status_code, content=fail(exc.code, exc.message))


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    msg = "; ".join(
        f"{'.'.join(str(p) for p in e['loc'][1:]) or 'body'}: {e['msg']}" for e in errors
    ) or "参数错误"
    return JSONResponse(status_code=422, content=fail(40001, msg))


async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content=fail(50001, f"服务异常: {type(exc).__name__}"))