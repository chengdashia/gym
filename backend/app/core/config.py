from pathlib import Path

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

    upload_dir: str = "uploads"
    static_url_prefix: str = "/static"

    mock_wechat: bool = True
    wechat_appid: str = ""
    wechat_secret: str = ""

    upload_max_size_mb: int = 10

    def validate_for_runtime(self) -> None:
        if not self.debug and (not self.db_url or len(self.jwt_secret) < 32):
            raise ValueError("生产环境必须配置 DB_URL 和至少 32 位 JWT_SECRET")


settings = Settings()
settings.validate_for_runtime()
