from fastapi.testclient import TestClient
from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1 import diet
from app.api.v1.deps import get_current_user
from app.core.database import Base, get_db
from app.main import app
from app.models import DietRecord, User, UserCustomFood


@compiles(BigInteger, "sqlite")
def _sqlite_bigint_as_integer(type_, compiler, **kwargs):
    return "INTEGER"


def _payload():
    return {
        "food": {
            "name": "自制鸡胸饭", "category": "主食",
            "calories_per_100g": 150, "carbs_per_100g": 15,
            "protein_per_100g": 12, "fat_per_100g": 4,
            "default_unit": "g",
        },
        "record": {
            "record_date": "2026-07-13", "record_time": "12:00",
            "meal_type": "lunch", "food_source": "custom",
            "unit_type": "g", "amount_g": 200,
        },
    }


def test_custom_food_record_commits_both_rows():
    client, session_factory = _client()
    with client:
        response = client.post("/api/v1/diet/custom-food-record", json=_payload())
    assert response.status_code == 200
    with session_factory() as db:
        assert db.query(UserCustomFood).count() == 1
        assert db.query(DietRecord).count() == 1


def test_custom_food_record_rolls_back_food_when_record_creation_fails(monkeypatch):
    client, session_factory = _client(raise_server_exceptions=False)
    monkeypatch.setattr(diet, "_nutrition_snapshot", lambda *args: (_ for _ in ()).throw(RuntimeError("boom")))
    with client:
        response = client.post("/api/v1/diet/custom-food-record", json=_payload())
    assert response.status_code == 500
    with session_factory() as db:
        assert db.query(UserCustomFood).count() == 0
        assert db.query(DietRecord).count() == 0


def _client(raise_server_exceptions=True):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False)

    def override_db():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: User(id=1, status="active")
    client = TestClient(app, raise_server_exceptions=raise_server_exceptions)
    return client, session_factory
