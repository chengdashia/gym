from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Fitness Diet API"
    debug: bool = True

    db_url: str = "mysql+pymysql://root@127.0.0.1:3306/fitness_diet?charset=utf8mb4"

    jwt_secret: str = "dev-only-change-before-production"
    jwt_alg: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 30

    cors_origins: list[str] = ["*"]

    # Must not depend on the directory from which uvicorn happens to start.
    # Otherwise an uploaded avatar can be written to one uploads/ directory
    # while StaticFiles serves another after a restart.
    upload_dir: str = str(Path(__file__).resolve().parents[1] / "uploads")
    static_url_prefix: str = "/static"

    mock_wechat: bool = False
    wechat_appid: str = ""
    wechat_secret: str = ""

    upload_max_size_mb: int = 10

    # Controlled-beta account allowlist. Keep empty in public environments.
    experimental_user_ids: list[int] = Field(default_factory=list)
    food_model_url: str = ""
    food_model_version: str = ""

    def validate_for_runtime(self) -> None:
        if self.debug:
            return
        if not self.db_url:
            raise ValueError("生产环境必须配置 DB_URL")
        if len(self.jwt_secret) < 32 or self.jwt_secret == "dev-only-change-before-production":
            raise ValueError("生产环境必须配置非默认且至少 32 位的 JWT_SECRET")
        if self.mock_wechat:
            raise ValueError("生产环境禁止启用 MOCK_WECHAT")


settings = Settings()
settings.validate_for_runtime()
