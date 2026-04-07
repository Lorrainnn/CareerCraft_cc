from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.settings import get_settings


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine, _SessionLocal
    if _engine is not None and _SessionLocal is not None:
        return _engine

    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError(
            "database_url is empty. Set env DATABASE_URL (MySQL) to enable Auth endpoints."
        )

    _engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def get_db() -> Generator[Session, None, None]:
    engine = get_engine()
    _session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = _session_local()
    try:
        yield db
    finally:
        db.close()

