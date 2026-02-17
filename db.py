import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker


def _build_engine():
    default_sqlite_path = Path(__file__).resolve().parent / "data" / "app.db"
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{default_sqlite_path}")
    engine_options = {"pool_pre_ping": True, "future": True}
    if database_url.startswith("sqlite"):
        engine_options["connect_args"] = {"check_same_thread": False}
    return create_engine(database_url, **engine_options)


engine = _build_engine()
SessionLocal = scoped_session(
    sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
)
Base = declarative_base()
Base.query = SessionLocal.query_property()


def init_db():
    from models import blog_models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def close_db_session(exception=None):
    SessionLocal.remove()
