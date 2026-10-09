import uuid
from datetime import datetime, timezone
from app.models.traffic import TrafficAnalysis, TrafficRecord, AnalysisStatus


def test_traffic_analysis_instantiation():
    """Verify TrafficAnalysis default fields and types."""
    analysis = TrafficAnalysis(
        original_filename="capture_sample.pcap",
        file_format="pcap",
    )

    assert analysis.original_filename == "capture_sample.pcap"
    assert analysis.file_format == "pcap"
    assert analysis.status == AnalysisStatus.PENDING
    assert analysis.total_rows_received == 0
    assert analysis.valid_rows == 0
    assert analysis.rejected_rows == 0
    assert analysis.error_details is None
    assert "TrafficAnalysis" in repr(analysis)


def test_traffic_record_instantiation():
    """Verify TrafficRecord instantiation and field defaults."""
    analysis_id = uuid.uuid4()
    record = TrafficRecord(
        analysis_id=analysis_id,
        source_ip="192.168.1.10",
        destination_ip="142.250.190.46",
        destination_domain="google.com",
        destination_port=443,
        protocol="TLS",
        bytes_sent=1500,
        bytes_received=45000,
        http_method="GET",
        http_uri="/search",
        http_status_code=200,
        user_agent="Mozilla/5.0",
        sni_hostname="google.com",
    )

    assert record.analysis_id == analysis_id
    assert record.destination_domain == "google.com"
    assert record.protocol == "TLS"
    assert record.bytes_sent == 1500
    assert record.bytes_received == 45000
    assert record.sni_hostname == "google.com"
    assert "TrafficRecord" in repr(record)


def test_analysis_status_enum_values():
    """Verify all valid status values are defined."""
    assert AnalysisStatus.PENDING.value == "pending"
    assert AnalysisStatus.PROCESSING.value == "processing"
    assert AnalysisStatus.COMPLETED.value == "completed"
    assert AnalysisStatus.FAILED.value == "failed"
