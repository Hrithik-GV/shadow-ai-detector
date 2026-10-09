import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.traffic import TrafficAnalysis, TrafficRecord, AnalysisStatus


def test_create_and_retrieve_traffic_analysis(db_session: Session):
    """Verify persisting and querying a TrafficAnalysis entity in PostgreSQL."""
    analysis = TrafficAnalysis(
        original_filename="proxy_logs_oct2026.csv",
        file_format="csv",
        status=AnalysisStatus.PROCESSING,
        total_rows_received=5000,
        valid_rows=4950,
        rejected_rows=50,
    )
    db_session.add(analysis)
    db_session.flush()

    assert analysis.id is not None
    assert isinstance(analysis.id, uuid.UUID)

    # Query back
    stmt = select(TrafficAnalysis).where(TrafficAnalysis.id == analysis.id)
    retrieved = db_session.scalar(stmt)

    assert retrieved is not None
    assert retrieved.original_filename == "proxy_logs_oct2026.csv"
    assert retrieved.status == AnalysisStatus.PROCESSING
    assert retrieved.total_rows_received == 5000
    assert retrieved.valid_rows == 4950
    assert retrieved.rejected_rows == 50


def test_create_traffic_records_relationship(db_session: Session):
    """Verify one-to-many relationship and back-population between analysis and records."""
    analysis = TrafficAnalysis(
        original_filename="tls_stream.pcap",
        file_format="pcap",
        status=AnalysisStatus.COMPLETED,
        total_rows_received=2,
        valid_rows=2,
    )
    db_session.add(analysis)
    db_session.flush()

    record1 = TrafficRecord(
        analysis_id=analysis.id,
        timestamp=datetime.now(timezone.utc),
        source_ip="10.0.0.15",
        destination_ip="172.67.140.20",
        destination_domain="api.openai.com",
        destination_port=443,
        protocol="TLS",
        bytes_sent=1200,
        bytes_received=4500,
        sni_hostname="api.openai.com",
    )
    record2 = TrafficRecord(
        analysis_id=analysis.id,
        timestamp=datetime.now(timezone.utc),
        source_ip="10.0.0.15",
        destination_ip="142.250.72.206",
        destination_domain="generativelanguage.googleapis.com",
        destination_port=443,
        protocol="TLS",
        bytes_sent=800,
        bytes_received=15000,
        sni_hostname="generativelanguage.googleapis.com",
    )

    db_session.add_all([record1, record2])
    db_session.flush()

    # Refresh analysis to verify relation
    db_session.refresh(analysis)
    assert len(analysis.records) == 2
    domains = {r.destination_domain for r in analysis.records}
    assert "api.openai.com" in domains
    assert "generativelanguage.googleapis.com" in domains

    # Verify back-populates link
    assert record1.analysis.original_filename == "tls_stream.pcap"


def test_cascade_delete_traffic_records(db_session: Session):
    """Verify deleting a TrafficAnalysis cascades and deletes all child TrafficRecords."""
    analysis = TrafficAnalysis(
        original_filename="to_delete.json",
        file_format="json",
    )
    db_session.add(analysis)
    db_session.flush()

    record = TrafficRecord(
        analysis_id=analysis.id,
        destination_domain="claude.ai",
        protocol="HTTPS",
    )
    db_session.add(record)
    db_session.flush()

    record_id = record.id

    # Delete parent analysis
    db_session.delete(analysis)
    db_session.flush()

    # Child record should be removed
    stmt = select(TrafficRecord).where(TrafficRecord.id == record_id)
    orphan = db_session.scalar(stmt)
    assert orphan is None


def test_nullable_fields_handling(db_session: Session):
    """Verify real-world sparse traffic logs can be stored with missing optional fields."""
    analysis = TrafficAnalysis(
        original_filename="sparse_log.csv",
        file_format="csv",
    )
    db_session.add(analysis)
    db_session.flush()

    # Omit IP, domain, protocol, HTTP details
    sparse_record = TrafficRecord(
        analysis_id=analysis.id,
        destination_port=8080,
    )
    db_session.add(sparse_record)
    db_session.flush()

    assert sparse_record.id is not None
    assert sparse_record.source_ip is None
    assert sparse_record.destination_domain is None
    assert sparse_record.bytes_sent is None
    assert sparse_record.user_agent is None
    assert sparse_record.sni_hostname is None


def test_query_filtering_by_domain_and_status(db_session: Session):
    """Verify indexed queries by destination domain and analysis status."""
    analysis = TrafficAnalysis(
        original_filename="filtered_batch.pcap",
        file_format="pcap",
        status=AnalysisStatus.COMPLETED,
    )
    db_session.add(analysis)
    db_session.flush()

    record = TrafficRecord(
        analysis_id=analysis.id,
        destination_domain="chatgpt.com",
        sni_hostname="chatgpt.com",
        protocol="TLS",
    )
    db_session.add(record)
    db_session.flush()

    stmt = (
        select(TrafficRecord)
        .join(TrafficAnalysis)
        .where(
            TrafficAnalysis.status == AnalysisStatus.COMPLETED,
            TrafficRecord.destination_domain == "chatgpt.com",
        )
    )
    matches = db_session.scalars(stmt).all()
    assert len(matches) >= 1
    assert matches[0].destination_domain == "chatgpt.com"
