import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_engine, check_db_connection
from app.main import app


def is_postgres_available() -> bool:
    """Check if a real PostgreSQL instance is reachable."""
    result = check_db_connection()
    return result.get("status") == "up"


@pytest.fixture(scope="module")
def client():
    """Test client fixture for making requests to FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db_session():
    """Isolated database session fixture using a rolled-back transaction.
    
    Guarantees no state is persisted across tests, preventing test pollution
    without substituting SQLite.
    """
    if not is_postgres_available():
        pytest.skip("PostgreSQL database is not reachable. Skipping database integration test.")

    engine = get_engine()
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    # Ensure tables exist for testing
    Base.metadata.create_all(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
