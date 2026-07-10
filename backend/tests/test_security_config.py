import pytest
from pathlib import Path

from app.core.config import Settings


def test_env_file_is_anchored_to_backend_directory():
    env_file = Path(Settings.model_config["env_file"])

    assert env_file.is_absolute()
    assert env_file == Path(__file__).resolve().parents[1] / ".env"


def test_production_rejects_missing_secrets():
    settings = Settings(debug=False, db_url="", jwt_secret="", _env_file=None)

    with pytest.raises(ValueError, match="DB_URL"):
        settings.validate_for_runtime()


def test_debug_mode_allows_local_defaults():
    settings = Settings(debug=True, db_url="sqlite:///./fitness.db", jwt_secret="dev-only", _env_file=None)

    settings.validate_for_runtime()
