import socket
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import BigInteger, create_engine, event
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


def _resolve_db_url() -> str:
    """Keep local debug usable when its optional remote MySQL is offline."""
    url = settings.db_url
    parsed = urlparse(url)
    if not settings.debug or not parsed.scheme.startswith("mysql") or not parsed.hostname:
        return url
    try:
        socket.getaddrinfo(parsed.hostname, parsed.port or 3306)
        return url
    except OSError:
        local_dir = Path(__file__).resolve().parents[2] / ".local"
        local_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{local_dir / 'fitness_diet.db'}"


db_url = _resolve_db_url()
using_local_sqlite = db_url.startswith("sqlite")


@compiles(BigInteger, "sqlite")
def _compile_big_integer_as_integer(_type, _compiler, **_kw):
    # SQLite only auto-increments a primary key declared exactly as INTEGER.
    return "INTEGER"


class Base(DeclarativeBase):
    pass


engine_options = {"connect_args": {"check_same_thread": False}} if using_local_sqlite else {
    "pool_pre_ping": True, "pool_recycle": 3600, "pool_size": 5, "max_overflow": 10,
}
engine = create_engine(db_url, **engine_options)

if using_local_sqlite:
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
