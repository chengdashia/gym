import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import auth, ai, diet, diet_programs, exercises, foods, home, stats, training, uploads, users, weight
from app.core.config import settings
from app.core.exceptions import (
    biz_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.response import ok


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return ok({"status": "ok", "app": settings.app_name})

    # Static for uploaded images
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.mount(settings.static_url_prefix, StaticFiles(directory=str(upload_dir)), name="static")

    # Routers
    api_prefix = "/api/v1"
    routers = [auth.router, users.router, home.router, foods.router, diet.router,
               uploads.router, ai.router, exercises.router, training.router,
               weight.router, stats.router, diet_programs.router]
    for r in routers:
        app.include_router(r, prefix=api_prefix)

    app.add_exception_handler(Exception, unhandled_exception_handler)
    from fastapi.exceptions import RequestValidationError
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    from app.core.exceptions import BizException
    app.add_exception_handler(BizException, biz_exception_handler)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
