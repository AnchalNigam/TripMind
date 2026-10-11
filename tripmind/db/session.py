"""Database session management with SQLAlchemy."""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from tripmind.config import settings

logger = logging.getLogger("tripmind.db")

Base = declarative_base()

try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args={"connect_timeout": 3},
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.warning(f"Could not initialize PostgreSQL engine: {e}")
    engine = None
    SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    """Dependency / context manager yielding a database session."""
    if SessionLocal is None:
        raise RuntimeError("Database engine is not initialized.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
