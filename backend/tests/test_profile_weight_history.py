from sqlalchemy import BigInteger, create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from app.api.v1.users import update_me
from app.core.database import Base
from app.models import User, UserProfile, WeightRecord
from app.schemas import UserMeIn, UserProfileIn


@compiles(BigInteger, "sqlite")
def _sqlite_bigint_as_integer(type_, compiler, **kwargs):
    return "INTEGER"


def test_profile_update_does_not_create_weight_history_record():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False)
    with session_factory() as db:
        user = User(id=1, status="active")
        db.add(user)
        db.add(UserProfile(user_id=1, current_weight_kg=77.5))
        db.commit()

        update_me(
            UserMeIn(nickname="新的昵称", profile=UserProfileIn(current_weight_kg=77.5)),
            user,
            db,
        )

        assert db.query(WeightRecord).count() == 0
