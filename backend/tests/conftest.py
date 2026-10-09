import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    """Test client fixture for making requests to FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client
