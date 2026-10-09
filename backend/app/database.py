from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

engine = None
SessionLocal = None


class Base(DeclarativeBase):
    pass


def _sqlite_file(url: str) -> Path | None:
    if not url.startswith("sqlite:///") or url in {"sqlite://", "sqlite:///:memory:"}:
        return None
    raw = url.removeprefix("sqlite:///")
    if raw.startswith(":memory:"):
        return None
    return Path(raw)


def init_db(url: str) -> None:
    global engine, SessionLocal
    file_path = _sqlite_file(url)
    if file_path is not None:
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            url = "sqlite:////tmp/senda-demo.db"

    kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs = {"connect_args": {"check_same_thread": False}}

    engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    SessionLocal = sessionmaker(bind=engine, autoflush=True, autocommit=False)


def get_engine():
    if engine is None:
        raise RuntimeError("La base de datos no está inicializada")
    return engine


def get_session():
    if SessionLocal is None:
        raise RuntimeError("La base de datos no está inicializada")
    return SessionLocal()


def get_db():
    db = get_session()
    try:
        yield db
    finally:
        db.close()
