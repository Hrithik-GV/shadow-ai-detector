from datetime import datetime, timezone
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.traffic import AnalysisStatus, TrafficAnalysis, TrafficRecord
from app.services.traffic_summary_service import TrafficSummaryService
from tests.conftest import is_postgres_available


@pytest.fixture(autouse=True)
def require_postgres():
    """Ensure tests in this module run only when PostgreSQL is available."""
    if not is_postgres_available():
        pytest.skip("PostgreSQL is not reachable. Skipping summary service tests.")


def test_summary_empty_dataset(db_session: Session):
    """Verify calculating summary statistics for an analysis with 0 records."""
    analysis = TrafficAnalysis(
        original_filename="empty_run.csv",
        file_format="csv",
        status=AnalysisStatus.FAILED,
        total_rows_received=5,
        valid_rows=0,
        rejected_rows=5,
    )
    db_session.add(analysis)
    db_session.flush()

    summary = TrafficSummaryService.calculate_analysis_summary(db_session, analysis)

    assert summary.total_records_received == 5
    assert summary.valid_records == 0
    assert summary.total_valid_records == 0
    assert summary.rejected_records == 5
    assert summary.unique_source_ips == 0
    assert summary.unique_destination_ips == 0
    assert summary.unique_destination_domains == 0
    assert summary.total_bytes_sent == 0
    assert summary.total_bytes_received == 0
    assert summary.bytes_sent_reported_count == 0
    assert summary.bytes_received_reported_count == 0
    assert summary.missing_bytes_sent_count == 0
    assert summary.missing_bytes_received_count == 0
    assert summary.protocols == []
    assert summary.protocol_distribution == {}
    assert summary.missing_protocol_count == 0
    assert summary.earliest_timestamp is None
    assert summary.latest_timestamp is None
    assert summary.records_with_timestamp == 0
    assert summary.missing_timestamp_count == 0


def test_summary_missing_optional_fields(db_session: Session):
    """Verify missing optional fields are treated as unknown, not zero, and missing counts tracked."""
    analysis = TrafficAnalysis(
        original_filename="partial_logs.json",
        file_format="json",
        status=AnalysisStatus.COMPLETED,
        total_rows_received=3,
        valid_rows=3,
        rejected_rows=0,
    )
    db_session.add(analysis)
    db_session.flush()

    # Record 1: All optional fields missing
    rec1 = TrafficRecord(
        analysis_id=analysis.id,
        destination_domain="example.com",
    )
    # Record 2: Timestamp present, protocol present, bytes missing, IP missing
    rec2 = TrafficRecord(
        analysis_id=analysis.id,
        timestamp=datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc),
        destination_domain="api.openai.com",
        protocol="TLS",
    )
    # Record 3: Bytes present, source IP present, timestamp missing
    rec3 = TrafficRecord(
        analysis_id=analysis.id,
        source_ip="192.168.1.50",
        destination_ip="104.18.2.1",
        protocol="tcp",
        bytes_sent=500,
        bytes_received=1500,
    )
    db_session.add_all([rec1, rec2, rec3])
    db_session.flush()

    summary = TrafficSummaryService.calculate_analysis_summary(db_session, analysis)

    assert summary.total_records_received == 3
    assert summary.valid_records == 3
    assert summary.rejected_records == 0

    # IP and domain counts exclude nulls
    assert summary.unique_source_ips == 1  # only rec3 has source_ip
    assert summary.unique_destination_ips == 1  # only rec3 has destination_ip
    assert summary.unique_destination_domains == 2  # rec1 and rec2

    # Bytes: only rec3 provided bytes
    assert summary.total_bytes_sent == 500
    assert summary.total_bytes_received == 1500
    assert summary.bytes_sent_reported_count == 1
    assert summary.bytes_received_reported_count == 1
    assert summary.missing_bytes_sent_count == 2
    assert summary.missing_bytes_received_count == 2

    # Protocol: rec2 ('TLS') and rec3 ('tcp' -> 'TCP')
    assert summary.protocol_distribution == {"TLS": 1, "TCP": 1}
    assert summary.protocols == ["TCP", "TLS"]
    assert summary.missing_protocol_count == 1  # rec1 had None

    # Timestamps: only rec2 provided a timestamp
    assert summary.earliest_timestamp == datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
    assert summary.latest_timestamp == datetime(2026, 10, 9, 12, 0, tzinfo=timezone.utc)
    assert summary.records_with_timestamp == 1
    assert summary.missing_timestamp_count == 2


def test_summary_repeated_ips_and_domains(db_session: Session):
    """Verify unique counts deduplicate repeated IPs/domains and exclude NULLs."""
    analysis = TrafficAnalysis(
        original_filename="repeated_traffic.csv",
        file_format="csv",
        status=AnalysisStatus.COMPLETED,
        total_rows_received=5,
        valid_rows=5,
        rejected_rows=0,
    )
    db_session.add(analysis)
    db_session.flush()

    # 4 records with the exact same source IP and destination domain, 1 with null
    records = [
        TrafficRecord(analysis_id=analysis.id, source_ip="10.0.0.1", destination_domain="claude.ai"),
        TrafficRecord(analysis_id=analysis.id, source_ip="10.0.0.1", destination_domain="claude.ai"),
        TrafficRecord(analysis_id=analysis.id, source_ip="10.0.0.1", destination_domain="claude.ai"),
        TrafficRecord(analysis_id=analysis.id, source_ip="10.0.0.2", destination_domain="claude.ai"),
        TrafficRecord(analysis_id=analysis.id, source_ip=None, destination_domain=None, destination_ip="1.1.1.1"),
    ]
    db_session.add_all(records)
    db_session.flush()

    summary = TrafficSummaryService.calculate_analysis_summary(db_session, analysis)

    assert summary.valid_records == 5
    assert summary.unique_source_ips == 2  # 10.0.0.1 and 10.0.0.2, null excluded
    assert summary.unique_destination_domains == 1  # claude.ai, null excluded
    assert summary.unique_destination_ips == 1  # 1.1.1.1, null excluded


def test_summary_byte_totals_calculation(db_session: Session):
    """Verify byte sums correctly handle missing values without treating them as zero."""
    analysis = TrafficAnalysis(
        original_filename="bandwidth_logs.csv",
        file_format="csv",
        status=AnalysisStatus.COMPLETED,
        total_rows_received=4,
        valid_rows=4,
        rejected_rows=0,
    )
    db_session.add(analysis)
    db_session.flush()

    records = [
        TrafficRecord(analysis_id=analysis.id, destination_domain="a.com", bytes_sent=1500, bytes_received=None),
        TrafficRecord(analysis_id=analysis.id, destination_domain="b.com", bytes_sent=None, bytes_received=8000),
        TrafficRecord(analysis_id=analysis.id, destination_domain="c.com", bytes_sent=500, bytes_received=2000),
        TrafficRecord(analysis_id=analysis.id, destination_domain="d.com", bytes_sent=None, bytes_received=None),
    ]
    db_session.add_all(records)
    db_session.flush()

    summary = TrafficSummaryService.calculate_analysis_summary(db_session, analysis)

    assert summary.total_bytes_sent == 2000  # 1500 + 500
    assert summary.total_bytes_received == 10000  # 8000 + 2000
    assert summary.bytes_sent_reported_count == 2
    assert summary.bytes_received_reported_count == 2
    assert summary.missing_bytes_sent_count == 2
    assert summary.missing_bytes_received_count == 2


def test_summary_timestamp_ranges(db_session: Session):
    """Verify earliest and latest timestamp computation over available timestamps."""
    analysis = TrafficAnalysis(
        original_filename="timed_capture.json",
        file_format="json",
        status=AnalysisStatus.COMPLETED,
        total_rows_received=4,
        valid_rows=4,
        rejected_rows=0,
    )
    db_session.add(analysis)
    db_session.flush()

    t_earliest = datetime(2026, 10, 9, 8, 15, tzinfo=timezone.utc)
    t_mid = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)
    t_latest = datetime(2026, 10, 9, 12, 30, tzinfo=timezone.utc)

    records = [
        TrafficRecord(analysis_id=analysis.id, destination_domain="a.com", timestamp=t_mid),
        TrafficRecord(analysis_id=analysis.id, destination_domain="b.com", timestamp=None),
        TrafficRecord(analysis_id=analysis.id, destination_domain="c.com", timestamp=t_latest),
        TrafficRecord(analysis_id=analysis.id, destination_domain="d.com", timestamp=t_earliest),
    ]
    db_session.add_all(records)
    db_session.flush()

    summary = TrafficSummaryService.calculate_analysis_summary(db_session, analysis)

    assert summary.earliest_timestamp == t_earliest
    assert summary.latest_timestamp == t_latest
    assert summary.records_with_timestamp == 3
    assert summary.missing_timestamp_count == 1


def test_summary_protocol_distributions(db_session: Session):
    """Verify protocol frequencies normalize casing and separate missing counts."""
    analysis = TrafficAnalysis(
        original_filename="proto_capture.csv",
        file_format="csv",
        status=AnalysisStatus.COMPLETED,
        total_rows_received=5,
        valid_rows=5,
        rejected_rows=0,
    )
    db_session.add(analysis)
    db_session.flush()

    records = [
        TrafficRecord(analysis_id=analysis.id, destination_domain="a.com", protocol="tcp"),
        TrafficRecord(analysis_id=analysis.id, destination_domain="b.com", protocol="TCP"),
        TrafficRecord(analysis_id=analysis.id, destination_domain="c.com", protocol="udp"),
        TrafficRecord(analysis_id=analysis.id, destination_domain="d.com", protocol=None),
        TrafficRecord(analysis_id=analysis.id, destination_domain="e.com", protocol="TLS"),
    ]
    db_session.add_all(records)
    db_session.flush()

    summary = TrafficSummaryService.calculate_analysis_summary(db_session, analysis)

    assert summary.protocol_distribution == {"TCP": 2, "UDP": 1, "TLS": 1}
    assert summary.protocols == ["TCP", "TLS", "UDP"]
    assert summary.missing_protocol_count == 1


def test_dashboard_stats_endpoint_with_analysis_id(client: TestClient, db_session: Session):
    """Verify GET /api/dashboard/stats?analysis_id=... scopes statistics to the selected analysis."""
    from app.db.session import get_db
    from app.main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        analysis = TrafficAnalysis(
            original_filename="dashboard_test.csv",
            file_format="csv",
            status=AnalysisStatus.COMPLETED,
            total_rows_received=1,
            valid_rows=1,
            rejected_rows=0,
        )
        db_session.add(analysis)
        db_session.flush()

        record = TrafficRecord(
            analysis_id=analysis.id,
            source_ip="192.168.1.10",
            destination_domain="platform.openai.com",
            bytes_sent=1000,
            bytes_received=5000,
            protocol="HTTPS",
        )
        db_session.add(record)
        db_session.flush()

        response = client.get(f"/api/dashboard/stats?analysis_id={analysis.id}")
        assert response.status_code == 200
        data = response.json()

        assert data["scope"] == "selected_analysis"
        assert data["analysis_id"] == str(analysis.id)
        assert data["analyses_count"] == 1
        assert data["valid_records"] == 1
        assert data["unique_source_ips"] == 1
        assert data["unique_destination_domains"] == 1
        assert data["total_bytes_sent"] == 1000
        assert data["total_bytes_received"] == 5000
        assert data["protocol_distribution"] == {"HTTPS": 1}
        assert "record_type_note" in data
        assert "byte_calculation_note" in data

    finally:
        app.dependency_overrides.pop(get_db, None)


def test_dashboard_stats_endpoint_all_analyses(client: TestClient):
    """Verify GET /api/dashboard/stats returns global aggregate statistics."""
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["scope"] == "all_analyses"
    assert data["analysis_id"] is None
    assert isinstance(data["analyses_count"], int)
    assert isinstance(data["valid_records"], int)
    assert isinstance(data["total_bytes_sent"], int)
    assert isinstance(data["total_bytes_received"], int)
    assert isinstance(data["unique_source_ips"], int)
    assert isinstance(data["unique_destination_domains"], int)
    assert isinstance(data["protocol_distribution"], dict)
    assert "Counts represent ingested log records" in data["record_type_note"]


def test_dashboard_stats_unknown_analysis_id_returns_404(client: TestClient):
    """Verify GET /api/dashboard/stats with unknown UUID returns 404."""
    unknown_id = uuid.uuid4()
    response = client.get(f"/api/dashboard/stats?analysis_id={unknown_id}")
    assert response.status_code == 404
    assert f"Analysis with ID '{unknown_id}' was not found" in response.json()["detail"]


def test_get_analysis_summary_endpoint(client: TestClient, db_session: Session):
    """Verify GET /api/traffic/{analysis_id}/summary returns detailed statistics."""
    from app.db.session import get_db
    from app.main import app

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        analysis = TrafficAnalysis(
            original_filename="summary_endpoint_test.json",
            file_format="json",
            status=AnalysisStatus.COMPLETED,
            total_rows_received=1,
            valid_rows=1,
            rejected_rows=0,
        )
        db_session.add(analysis)
        db_session.flush()

        record = TrafficRecord(
            analysis_id=analysis.id,
            source_ip="172.16.0.5",
            destination_domain="anthropic.com",
            protocol="TLS",
            bytes_sent=750,
            bytes_received=4500,
        )
        db_session.add(record)
        db_session.flush()

        response = client.get(f"/api/traffic/{analysis.id}/summary")
        assert response.status_code == 200
        data = response.json()

        assert data["valid_records"] == 1
        assert data["total_valid_records"] == 1
        assert data["unique_source_ips"] == 1
        assert data["unique_destination_domains"] == 1
        assert data["total_bytes_sent"] == 750
        assert data["total_bytes_received"] == 4500
        assert data["protocol_distribution"] == {"TLS": 1}
        assert data["protocols"] == ["TLS"]

        # Also test 404
        unknown_id = uuid.uuid4()
        res_404 = client.get(f"/api/traffic/{unknown_id}/summary")
        assert res_404.status_code == 404

    finally:
        app.dependency_overrides.pop(get_db, None)

