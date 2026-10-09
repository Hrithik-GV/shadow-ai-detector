import io
import json
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.conftest import is_postgres_available


@pytest.fixture(autouse=True)
def require_postgres():
    """Ensure end-to-end flow tests run only when PostgreSQL is available."""
    if not is_postgres_available():
        pytest.skip("PostgreSQL is not reachable. Skipping end-to-end integration tests.")


@pytest.fixture
def managed_analyses():
    """Tracks analysis IDs created during end-to-end flows and cleans them up after testing."""
    ids = []
    yield ids

    if ids:
        from app.db.session import get_engine
        engine = get_engine()
        with engine.connect() as conn:
            with conn.begin():
                for aid in ids:
                    conn.execute(
                        text("DELETE FROM traffic_analyses WHERE id = :id"),
                        {"id": str(aid)},
                    )


def test_complete_csv_analysis_lifecycle(client: TestClient, managed_analyses):
    """End-to-end flow:
    1. Upload CSV capture with multiple traffic flows.
    2. Persist records and verify ingestion response.
    3. Retrieve analysis details via GET /api/traffic/{analysis_id}.
    4. Retrieve detailed summary via GET /api/traffic/{analysis_id}/summary.
    5. Query paginated flow records via GET /api/traffic/{analysis_id}/records.
    6. Verify dashboard stats scoping via GET /api/dashboard/stats?analysis_id={id}.
    """
    csv_payload = (
        "timestamp,source_ip,destination_domain,destination_port,protocol,bytes_sent,bytes_received\n"
        "2026-10-09T14:00:00Z,10.0.0.1,api.openai.com,443,tcp,1500,45000\n"
        "2026-10-09T14:05:00Z,10.0.0.2,claude.ai,443,tcp,800,22000\n"
        "2026-10-09T14:10:00Z,10.0.0.1,generativelanguage.googleapis.com,443,tls,2100,60000\n"
    )

    # Step 1: Upload and Analyze
    res_upload = client.post(
        "/api/traffic/analyze",
        files={"file": ("corp_egress.csv", io.BytesIO(csv_payload.encode("utf-8")), "text/csv")},
    )
    assert res_upload.status_code == 201
    upload_data = res_upload.json()

    analysis_id = uuid.UUID(upload_data["id"])
    managed_analyses.append(analysis_id)

    assert upload_data["status"] == "completed"
    assert upload_data["total_rows_received"] == 3
    assert upload_data["valid_rows"] == 3
    assert upload_data["rejected_rows"] == 0
    assert len(upload_data["rejected_records"]) == 0

    # Step 2: Retrieve Analysis Details
    res_get = client.get(f"/api/traffic/{analysis_id}")
    assert res_get.status_code == 200
    detail_data = res_get.json()
    assert detail_data["id"] == str(analysis_id)
    assert detail_data["original_filename"] == "corp_egress.csv"
    assert detail_data["valid_rows"] == 3

    # Step 3: Retrieve Summary Statistics
    res_summary = client.get(f"/api/traffic/{analysis_id}/summary")
    assert res_summary.status_code == 200
    summary_data = res_summary.json()
    assert summary_data["valid_records"] == 3
    assert summary_data["unique_source_ips"] == 2  # 10.0.0.1 and 10.0.0.2
    assert summary_data["unique_destination_domains"] == 3
    assert summary_data["total_bytes_sent"] == 4400  # 1500 + 800 + 2100
    assert summary_data["total_bytes_received"] == 127000  # 45000 + 22000 + 60000
    assert summary_data["protocol_distribution"] == {"TCP": 2, "TLS": 1}
    assert summary_data["protocols"] == ["TCP", "TLS"]
    
    # Timezone-independent timestamp comparison
    from datetime import datetime, timezone
    earliest_dt = datetime.fromisoformat(summary_data["earliest_timestamp"])
    assert earliest_dt == datetime(2026, 10, 9, 14, 0, tzinfo=timezone.utc)
    latest_dt = datetime.fromisoformat(summary_data["latest_timestamp"])
    assert latest_dt == datetime(2026, 10, 9, 14, 10, tzinfo=timezone.utc)

    # Step 4: Paginated Records Retrieval (Page 1: limit 2, offset 0)
    res_page1 = client.get(f"/api/traffic/{analysis_id}/records?limit=2&offset=0")
    assert res_page1.status_code == 200
    page1_data = res_page1.json()
    assert page1_data["total_records"] == 3
    assert len(page1_data["records"]) == 2
    assert page1_data["records"][0]["destination_domain"] == "api.openai.com"
    assert page1_data["records"][1]["destination_domain"] == "claude.ai"

    # Step 5: Paginated Records Retrieval (Page 2: limit 2, offset 2)
    res_page2 = client.get(f"/api/traffic/{analysis_id}/records?limit=2&offset=2")
    assert res_page2.status_code == 200
    page2_data = res_page2.json()
    assert page2_data["total_records"] == 3
    assert len(page2_data["records"]) == 1
    assert page2_data["records"][0]["destination_domain"] == "generativelanguage.googleapis.com"

    # Step 6: Scoped Dashboard Overview Stats
    res_dash = client.get(f"/api/dashboard/stats?analysis_id={analysis_id}")
    assert res_dash.status_code == 200
    dash_data = res_dash.json()
    assert dash_data["scope"] == "selected_analysis"
    assert dash_data["analysis_id"] == str(analysis_id)
    assert dash_data["total_bytes_sent"] == 4400
    assert dash_data["unique_source_ips"] == 2


def test_complete_json_analysis_lifecycle(client: TestClient, managed_analyses):
    """End-to-end flow with JSON array payload and mixed field population."""
    records = [
        {
            "src_ip": "172.16.10.5",
            "destination_domain": "api.anthropic.com",
            "dest_port": 443,
            "proto": "TLS",
            "bytes_sent": 950,
            "bytes_received": 18000,
            "timestamp": "2026-10-09T15:30:00Z",
        },
        {
            "src_ip": "172.16.10.6",
            "destination_ip": "142.250.190.46",
            "dest_port": 80,
            "proto": "TCP",
            "bytes_sent": 300,
            "bytes_received": 1200,
            "timestamp": "2026-10-09T15:35:00Z",
        },
    ]
    file_bytes = io.BytesIO(json.dumps(records).encode("utf-8"))

    res_upload = client.post(
        "/api/traffic/analyze",
        files={"file": ("api_feed.json", file_bytes, "application/json")},
    )
    assert res_upload.status_code == 201
    upload_data = res_upload.json()

    analysis_id = uuid.UUID(upload_data["id"])
    managed_analyses.append(analysis_id)

    assert upload_data["status"] == "completed"
    assert upload_data["valid_rows"] == 2

    # Verify summary
    res_summary = client.get(f"/api/traffic/{analysis_id}/summary")
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert summary["valid_records"] == 2
    assert summary["unique_source_ips"] == 2
    assert summary["unique_destination_domains"] == 1
    assert summary["unique_destination_ips"] == 1
    assert summary["total_bytes_sent"] == 1250
    assert summary["total_bytes_received"] == 19200
    assert summary["protocol_distribution"] == {"TLS": 1, "TCP": 1}

    # Verify records listing
    res_records = client.get(f"/api/traffic/{analysis_id}/records?limit=10&offset=0")
    assert res_records.status_code == 200
    assert res_records.json()["total_records"] == 2
