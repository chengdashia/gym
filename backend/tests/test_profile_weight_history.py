from datetime import datetime, time

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


def test_profile_updates_keep_one_weight_history_record_per_day():
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
        update_me(
            UserMeIn(profile=UserProfileIn(current_weight_kg=76.5)),
            user,
            db,
        )

        records = db.query(WeightRecord).all()
        assert len(records) == 1
        assert float(records[0].weight_kg) == 76.5
        assert records[0].note == "基础资料同步"


def test_profile_update_merges_existing_duplicate_profile_weight_records():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False)
    now = datetime.now()
    with session_factory() as db:
        user = User(id=1, status="active")
        db.add(user)
        db.add(UserProfile(user_id=1, current_weight_kg=77.5))
        db.add_all([
            WeightRecord(user_id=1, record_date=datetime.combine(now.date(), time.min), record_time=time(8), weight_kg=77.5, note="基础资料同步"),
            WeightRecord(user_id=1, record_date=datetime.combine(now.date(), time.min), record_time=time(9), weight_kg=77.5, note="基础资料同步"),
        ])
        db.commit()

        update_me(UserMeIn(profile=UserProfileIn(current_weight_kg=76.5)), user, db)

        active_records = db.query(WeightRecord).filter(WeightRecord.deleted_at.is_(None)).all()
        assert len(active_records) == 1
        assert float(active_records[0].weight_kg) == 76.5
