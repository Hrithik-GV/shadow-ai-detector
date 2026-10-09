import logging
from typing import Generator, Optional, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

logger = logging.getLogger(__name__)

_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def get_engine() -> Optional[Engine]:
    """Retrieve or create the SQLAlchemy engine if database URI is configured."""
    global _engine, _session_factory
    uri = settings.sqlalchemy_database_uri
    if not uri:
        return None

    if _engine is None:
        try:
            _engine = create_engine(
                uri,
                pool_pre_ping=True,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_timeout=settings.DB_POOL_TIMEOUT,
            )
            _session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=_engine,
            )
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            return None

    return _engine


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    engine = get_engine()
    if engine is None or _session_factory is None:
        raise RuntimeError("Database connection is not configured or unavailable.")

    db: Session = _session_factory()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> Dict[str, Any]:
    """Perform a real database health check.
    
    Returns:
        dict with status ('up', 'down', or 'not_configured') and details.
    """
    uri = settings.sqlalchemy_database_uri
    if not uri:
        return {
            "status": "not_configured",
            "details": "Database URL is not configured",
        }

    try:
        engine = get_engine()
        if engine is None:
            return {
                "status": "down",
                "details": "Failed to create database engine",
            }
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {
            "status": "up",
            "details": "Database connection verified successfully",
        }
    except Exception as exc:
        logger.warning(f"Database health check failed: {exc}")
        return {
            "status": "down",
            "details": f"Database unreachable: {str(exc)}",
        }
