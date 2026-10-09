import io
import json
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app
from app.models.traffic import TrafficAnalysis, TrafficRecord
from tests.conftest import is_postgres_available


@pytest.fixture(autouse=True)
def require_postgres():
    """Ensure tests in this module run only when PostgreSQL is available."""
    if not is_postgres_available():
        pytest.skip("PostgreSQL is not reachable. Skipping route integration tests.")


@pytest.fixture
def cleanup_analyses():
    """Tracks created analysis IDs and deletes them after tests complete."""
    created_ids = []
    yield created_ids

    # Teardown
    if created_ids:
        from app.db.session import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            with conn.begin():
                for aid in created_ids:
                    conn.execute(
                        select(TrafficAnalysis).where(TrafficAnalysis.id == aid)
                    )
                    from sqlalchemy import text
                    conn.execute(
                        text("DELETE FROM traffic_analyses WHERE id = :id"),
                        {"id": str(aid)},
                    )


def test_analyze_valid_csv_file(client: TestClient, cleanup_analyses):
    """Verify POST /api/traffic/analyze parses and persists a valid CSV capture file."""
    csv_content = (
        "timestamp,src_ip,dest_domain,dest_port,proto,bytes_out,bytes_in\n"
        "2026-10-09T18:00:00Z,192.168.1.50,api.openai.com,443,tcp,1200,45000\n"
        "2026-10-09T18:01:00Z,192.168.1.51,claude.ai,443,tcp,800,12000\n"
    )
    file_bytes = io.BytesIO(csv_content.encode("utf-8"))

    response = client.post(
        "/api/traffic/analyze",
        files={"file": ("firewall_logs.csv", file_bytes, "text/csv")},
    )

    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    analysis_id = uuid.UUID(data["id"])
    cleanup_analyses.append(analysis_id)

    assert data["original_filename"] == "firewall_logs.csv"
    assert data["file_format"] == "csv"
    assert data["status"] == "completed"
    assert data["total_rows_received"] == 2
    assert data["valid_rows"] == 2
    assert data["rejected_rows"] == 0
    assert len(data["rejected_records"]) == 0

    # Verify real metrics summary
    summary = data["summary"]
    assert summary["total_valid_records"] == 2
    assert summary["total_bytes_sent"] == 2000
    assert summary["total_bytes_received"] == 57000
    assert summary["unique_destination_domains"] == 2
    assert summary["unique_source_ips"] == 2
    assert "TCP" in summary["protocols"]


def test_analyze_valid_json_file(client: TestClient, cleanup_analyses):
    """Verify POST /api/traffic/analyze processes a JSON array of traffic objects."""
    records = [
        {"src_ip": "10.0.0.1", "dest_domain": "chatgpt.com", "port": 443, "proto": "TLS"},
        {"src_ip": "10.0.0.2", "destination_ip": "104.18.2.1", "port": 80, "proto": "TCP"},
    ]
    file_bytes = io.BytesIO(json.dumps(records).encode("utf-8"))

    response = client.post(
        "/api/traffic/analyze",
        files={"file": ("proxy_stream.json", file_bytes, "application/json")},
    )

    assert response.status_code == 201
    data = response.json()
    cleanup_analyses.append(uuid.UUID(data["id"]))

    assert data["file_format"] == "json"
    assert data["valid_rows"] == 2
    assert data["status"] == "completed"
    assert data["summary"]["unique_destination_domains"] == 1
    assert data["summary"]["unique_destination_ips"] == 1


def test_analyze_csv_with_mixed_valid_and_invalid_rows(client: TestClient, cleanup_analyses):
    """Verify rejected rows are reported in rejected_records with line numbers and reasons."""
    csv_content = (
        "src_ip,dest_domain,dest_port\n"
        "10.0.0.1,api.openai.com,443\n"     # Row 2: valid
        "999.999.999.999,claude.ai,443\n"    # Row 3: invalid IP
        "10.0.0.3,,8080\n"                   # Row 4: missing destination
    )
    file_bytes = io.BytesIO(csv_content.encode("utf-8"))

    response = client.post(
        "/api/traffic/analyze",
        files={"file": ("mixed_traffic.csv", file_bytes, "text/csv")},
    )

    assert response.status_code == 201
    data = response.json()
    cleanup_analyses.append(uuid.UUID(data["id"]))

    assert data["total_rows_received"] == 3
    assert data["valid_rows"] == 1
    assert data["rejected_rows"] == 2
    assert data["status"] == "completed"

    rejected = data["rejected_records"]
    assert len(rejected) == 2
    assert rejected[0]["row_index"] == 3
    assert any("Invalid IP address" in e["message"] for e in rejected[0]["errors"])
    assert rejected[1]["row_index"] == 4
    assert any("Missing destination" in e["message"] for e in rejected[1]["errors"])


def test_analyze_unsupported_file_extension(client: TestClient):
    """Verify HTTP 400 is returned when an unsupported file type is uploaded."""
    file_bytes = io.BytesIO(b"<xml><traffic></traffic></xml>")
    response = client.post(
        "/api/traffic/analyze",
        files={"file": ("traffic_export.xml", file_bytes, "application/xml")},
    )
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


def test_analyze_empty_file(client: TestClient):
    """Verify HTTP 400 is returned for empty files."""
    file_bytes = io.BytesIO(b"")
    response = client.post(
        "/api/traffic/analyze",
        files={"file": ("empty.csv", file_bytes, "text/csv")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_analyze_malformed_csv_syntax(client: TestClient):
    """Verify HTTP 400 is returned when CSV content has broken syntax."""
    file_bytes = io.BytesIO(b'col1,col2\n"unclosed quote,123\n')
    response = client.post(
        "/api/traffic/analyze",
        files={"file": ("broken.csv", file_bytes, "text/csv")},
    )
    assert response.status_code == 400
    assert "Malformed CSV" in response.json()["detail"]


def test_get_analysis_by_id(client: TestClient, cleanup_analyses):
    """Verify GET /api/traffic/{analysis_id} returns details and computed metrics."""
    # Create analysis via POST first
    csv_content = "dest_domain,dest_port\ngenerativelanguage.googleapis.com,443\n"
    res_post = client.post(
        "/api/traffic/analyze",
        files={"file": ("gemini.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    analysis_id = res_post.json()["id"]
    cleanup_analyses.append(uuid.UUID(analysis_id))

    # Retrieve via GET
    res_get = client.get(f"/api/traffic/{analysis_id}")
    assert res_get.status_code == 200
    data = res_get.json()

    assert data["id"] == analysis_id
    assert data["original_filename"] == "gemini.csv"
    assert data["status"] == "completed"
    assert data["summary"]["unique_destination_domains"] == 1


def test_get_analysis_by_unknown_id_returns_404(client: TestClient):
    """Verify GET /api/traffic/{analysis_id} returns 404 for unknown IDs."""
    unknown_id = uuid.uuid4()
    response = client.get(f"/api/traffic/{unknown_id}")
    assert response.status_code == 404
    assert "was not found" in response.json()["detail"]


def test_get_analysis_records_pagination(client: TestClient, cleanup_analyses):
    """Verify GET /api/traffic/{analysis_id}/records supports pagination and total count."""
    csv_content = (
        "dest_domain,dest_port\n"
        "domain1.com,80\n"
        "domain2.com,80\n"
        "domain3.com,80\n"
    )
    res_post = client.post(
        "/api/traffic/analyze",
        files={"file": ("batch.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    analysis_id = res_post.json()["id"]
    cleanup_analyses.append(uuid.UUID(analysis_id))

    # Fetch page 1 (limit=2, offset=0)
    res_p1 = client.get(f"/api/traffic/{analysis_id}/records?limit=2&offset=0")
    assert res_p1.status_code == 200
    p1 = res_p1.json()
    assert p1["total_records"] == 3
    assert len(p1["records"]) == 2
    assert p1["limit"] == 2
    assert p1["offset"] == 0

    # Fetch page 2 (limit=2, offset=2)
    res_p2 = client.get(f"/api/traffic/{analysis_id}/records?limit=2&offset=2")
    assert res_p2.status_code == 200
    p2 = res_p2.json()
    assert p2["total_records"] == 3
    assert len(p2["records"]) == 1


def test_get_analysis_records_unknown_id_returns_404(client: TestClient):
    """Verify GET /api/traffic/{analysis_id}/records returns 404 for missing analysis."""
    unknown_id = uuid.uuid4()
    response = client.get(f"/api/traffic/{unknown_id}/records")
    assert response.status_code == 404


def test_list_analyses_history_and_pagination(client: TestClient, cleanup_analyses):
    """Verify GET /api/traffic returns saved analysis history with pagination."""
    # Create 2 analyses
    for name in ["history1.csv", "history2.csv"]:
        res = client.post(
            "/api/traffic/analyze",
            files={"file": (name, io.BytesIO(b"dest_domain\nexample.com\n"), "text/csv")},
        )
        cleanup_analyses.append(uuid.UUID(res.json()["id"]))

    response = client.get("/api/traffic?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()

    assert "total_analyses" in data
    assert data["total_analyses"] >= 2
    assert len(data["analyses"]) >= 2
    assert "original_filename" in data["analyses"][0]


def test_database_error_handling_in_analyze(client: TestClient):
    """Verify HTTP 500 is returned cleanly if database persistence raises an error."""
    from unittest.mock import patch

    with patch(
        "app.api.v1.endpoints.traffic.process_and_persist_traffic_file",
        side_effect=RuntimeError("Simulated database failure"),
    ):
        csv_content = b"dest_domain\nopenai.com\n"
        response = client.post(
            "/api/traffic/analyze",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")},
        )
        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]


def test_versioned_v1_traffic_routes(client: TestClient, cleanup_analyses):
    """Verify /api/v1/traffic/... routes mirror the /api/traffic/... endpoints."""
    csv_content = b"dest_domain\nv1_test.com\n"
    res = client.post(
        "/api/v1/traffic/analyze",
        files={"file": ("v1.csv", io.BytesIO(csv_content), "text/csv")},
    )
    assert res.status_code == 201
    analysis_id = res.json()["id"]
    cleanup_analyses.append(uuid.UUID(analysis_id))

    res_get = client.get(f"/api/v1/traffic/{analysis_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == analysis_id
