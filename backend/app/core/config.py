from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Fitness Diet API"
    debug: bool = True

    db_url: str = (
        "mysql+pymysql://root_fitlog:44EnrkDixGUKhP5I@mysql6.sqlpub.com:3311/fitlog?charset=utf8mb4"
    )

    jwt_secret: str = "fitness-diet-miniapp-dev-secret-change-me"
    jwt_alg: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 30

    cors_origins: list[str] = ["*"]

    upload_dir: str = "uploads"
    static_url_prefix: str = "/static"

    mock_wechat: bool = True
    wechat_appid: str = ""
    wechat_secret: str = ""

    upload_max_size_mb: int = 10


settings = Settings()