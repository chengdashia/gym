import pytest

from app.core.config import Settings


def test_production_rejects_missing_secrets():
    settings = Settings(debug=False, db_url="", jwt_secret="", _env_file=None)

    with pytest.raises(ValueError, match="DB_URL"):
        settings.validate_for_runtime()


def test_debug_mode_allows_local_defaults():
    settings = Settings(debug=True, db_url="sqlite:///./fitness.db", jwt_secret="dev-only", _env_file=None)

    settings.validate_for_runtime()
