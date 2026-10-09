from datetime import datetime, timezone
import uuid

import pytest
from app.schemas.traffic import (
    NormalizedTrafficRecord,
    RecordValidationError,
    TrafficAnalysisSummary,
    TrafficRecordInput,
    validate_traffic_batch,
    validate_traffic_record,
)


def test_valid_record_complete():
    """Verify that a full valid record normalizes all fields correctly."""
    raw = {
        "timestamp": "2026-10-09T18:00:00Z",
        "source_ip": "192.168.1.100",
        "destination_ip": "104.18.2.1",
        "destination_domain": "api.openai.com",
        "destination_port": 443,
        "protocol": "tcp",
        "bytes_sent": 1250,
        "bytes_received": 35000,
        "http_method": "post",
        "http_uri": "/v1/chat/completions",
        "http_status_code": 200,
        "user_agent": "Python-SDK/1.0",
        "sni_hostname": "api.openai.com",
    }

    result = validate_traffic_record(raw, row_index=1)
    assert result.is_valid is True
    assert len(result.errors) == 0

    record = result.record
    assert isinstance(record, NormalizedTrafficRecord)
    assert record.timestamp == datetime(2026, 10, 9, 18, 0, 0, tzinfo=timezone.utc)
    assert record.source_ip == "192.168.1.100"
    assert record.destination_ip == "104.18.2.1"
    assert record.destination_domain == "api.openai.com"
    assert record.destination_port == 443
    assert record.protocol == "TCP"
    assert record.bytes_sent == 1250
    assert record.bytes_received == 35000
    assert record.http_method == "POST"
    assert record.http_uri == "/v1/chat/completions"
    assert record.http_status_code == 200
    assert record.sni_hostname == "api.openai.com"


def test_valid_record_missing_optional_fields():
    """Verify record is accepted when optional metadata is missing."""
    # Only destination_domain provided
    res1 = validate_traffic_record({"destination_domain": "claude.ai"})
    assert res1.is_valid is True
    assert res1.record.destination_domain == "claude.ai"
    assert res1.record.source_ip is None
    assert res1.record.bytes_sent is None
    assert res1.record.protocol is None

    # Only destination_ip provided
    res2 = validate_traffic_record({"destination_ip": "142.250.190.46"})
    assert res2.is_valid is True
    assert res2.record.destination_ip == "142.250.190.46"
    assert res2.record.destination_domain is None


def test_empty_string_values_treated_as_none():
    """Verify empty strings and sentinel tokens ('-', 'null', 'N/A') are converted to None."""
    raw = {
        "destination_domain": "chatgpt.com",
        "source_ip": "-",
        "destination_port": "",
        "bytes_sent": "null",
        "protocol": "N/A",
        "user_agent": "   ",
    }
    result = validate_traffic_record(raw)
    assert result.is_valid is True
    record = result.record
    assert record.destination_domain == "chatgpt.com"
    assert record.source_ip is None
    assert record.destination_port is None
    assert record.bytes_sent is None
    assert record.protocol is None
    assert record.user_agent is None


def test_column_aliases_and_case_normalization():
    """Verify common column aliases and casing are mapped to canonical field names."""
    raw = {
        "SRC_IP": "10.0.0.50",
        "DST_IP": "172.67.140.20",
        "HOST": "generativelanguage.googleapis.com",
        "DPORT": "443",
        "PROTO": "tcp",
        "BYTES_OUT": "500",
        "BYTES_IN": "15000",
        "VERB": "POST",
        "AGENT": "CustomClient/2.0",
        "TLS_SNI": "generativelanguage.googleapis.com",
        "TS": "1728498000",
    }

    result = validate_traffic_record(raw)
    assert result.is_valid is True
    rec = result.record

    assert rec.source_ip == "10.0.0.50"
    assert rec.destination_ip == "172.67.140.20"
    assert rec.destination_domain == "generativelanguage.googleapis.com"
    assert rec.destination_port == 443
    assert rec.protocol == "TCP"
    assert rec.bytes_sent == 500
    assert rec.bytes_received == 15000
    assert rec.http_method == "POST"
    assert rec.user_agent == "CustomClient/2.0"
    assert rec.sni_hostname == "generativelanguage.googleapis.com"
    assert rec.timestamp is not None


def test_invalid_ip_addresses():
    """Verify rejection of malformed IPv4 and IPv6 addresses."""
    # Invalid IPv4 octets
    res1 = validate_traffic_record({"destination_ip": "999.999.999.999"})
    assert res1.is_valid is False
    assert any("Invalid IP address" in e.message for e in res1.errors)

    # Incomplete IP
    res2 = validate_traffic_record({"source_ip": "192.168.1", "destination_domain": "example.com"})
    assert res2.is_valid is False
    assert any("source_ip" in str(e.field) for e in res2.errors)

    # Invalid IPv6
    res3 = validate_traffic_record({"destination_ip": "2001:xyz::1"})
    assert res3.is_valid is False
    assert any("Invalid IP address" in e.message for e in res3.errors)


def test_invalid_ports():
    """Verify rejection of out-of-range, negative, and non-integer ports."""
    # Port too large
    res1 = validate_traffic_record({"destination_domain": "example.com", "destination_port": 70000})
    assert res1.is_valid is False
    assert any("outside valid range" in e.message for e in res1.errors)

    # Port zero
    res2 = validate_traffic_record({"destination_domain": "example.com", "destination_port": 0})
    assert res2.is_valid is False
    assert any("outside valid range" in e.message for e in res2.errors)

    # Negative port
    res3 = validate_traffic_record({"destination_domain": "example.com", "destination_port": -443})
    assert res3.is_valid is False
    assert any("outside valid range" in e.message for e in res3.errors)

    # Non-integer port
    res4 = validate_traffic_record({"destination_domain": "example.com", "destination_port": "https"})
    assert res4.is_valid is False
    assert any("valid integer" in e.message for e in res4.errors)


def test_negative_byte_counts():
    """Verify rejection of negative byte counters."""
    res1 = validate_traffic_record({"destination_domain": "example.com", "bytes_sent": -1})
    assert res1.is_valid is False
    assert any("cannot be negative" in e.message for e in res1.errors)

    res2 = validate_traffic_record({"destination_domain": "example.com", "bytes_received": -500})
    assert res2.is_valid is False
    assert any("cannot be negative" in e.message for e in res2.errors)


def test_timestamp_validation_and_formats():
    """Verify support for ISO 8601, epoch seconds/ms, and rejection of malformed strings."""
    # ISO 8601 with timezone offset
    res_iso = validate_traffic_record({
        "destination_domain": "example.com",
        "timestamp": "2026-10-09T14:30:00+02:00",
    })
    assert res_iso.is_valid is True
    assert res_iso.record.timestamp == datetime(2026, 10, 9, 12, 30, 0, tzinfo=timezone.utc)

    # Epoch milliseconds
    res_epoch_ms = validate_traffic_record({
        "destination_domain": "example.com",
        "timestamp": 1728498000123,
    })
    assert res_epoch_ms.is_valid is True
    assert res_epoch_ms.record.timestamp.microsecond == 123000

    # Malformed timestamp string
    res_bad = validate_traffic_record({
        "destination_domain": "example.com",
        "timestamp": "invalid_date_time_string",
    })
    assert res_bad.is_valid is False
    assert any("Invalid timestamp format" in e.message for e in res_bad.errors)


def test_missing_required_destination():
    """Verify rejection when neither destination_domain nor destination_ip is present."""
    raw = {
        "timestamp": "2026-10-09T18:00:00Z",
        "source_ip": "192.168.1.100",
        "destination_port": 443,
        "protocol": "TCP",
    }
    result = validate_traffic_record(raw)
    assert result.is_valid is False
    assert any("Missing destination" in e.message for e in result.errors)


def test_invalid_domain_format():
    """Verify rejection of domains containing URLs, paths, or illegal characters."""
    # Full URL passed as domain
    res1 = validate_traffic_record({"destination_domain": "https://api.openai.com/v1"})
    assert res1.is_valid is False
    assert any("URL scheme or path" in e.message for e in res1.errors)

    # Domain with illegal whitespace
    res2 = validate_traffic_record({"destination_domain": "api .openai.com"})
    assert res2.is_valid is False
    assert any("Invalid domain format" in e.message for e in res2.errors)


def test_sensitive_fields_redacted_in_validation_error():
    """Verify sensitive fields (passwords, tokens, cookies) are redacted in error reports."""
    raw = {
        "destination_domain": "example.com",
        "destination_port": 99999,  # Triggers validation failure
        "Authorization": "Bearer super-secret-key-123",
        "cookie": "session_token=xyz987",
        "api_key": "sk-secret-ai-token",
    }
    result = validate_traffic_record(raw, row_index=42)
    assert result.is_valid is False

    err_report = RecordValidationError(
        row_index=result.row_index,
        errors=result.errors,
        raw_record=result.errors and {
            k: ("[REDACTED]" if any(s in k.lower() for s in ["auth", "cookie", "key"]) else v)
            for k, v in raw.items()
        },
    )

    assert err_report.raw_record["Authorization"] == "[REDACTED]"
    assert err_report.raw_record["cookie"] == "[REDACTED]"
    assert err_report.raw_record["api_key"] == "[REDACTED]"
    assert err_report.raw_record["destination_domain"] == "example.com"


def test_validate_traffic_batch():
    """Verify validate_traffic_batch partitions valid and invalid records accurately."""
    batch = [
        {"destination_domain": "api.openai.com", "port": 443},  # Valid (row 1)
        {"destination_ip": "invalid_ip"},                       # Invalid (row 2)
        {"dest_domain": "claude.ai", "bytes_out": -10},          # Invalid (row 3)
        {"dest_ip": "104.18.2.1", "proto": "TLS"},               # Valid (row 4)
    ]

    valid, errors = validate_traffic_batch(batch)
    assert len(valid) == 2
    assert len(errors) == 2

    assert valid[0].destination_domain == "api.openai.com"
    assert valid[0].destination_port == 443
    assert valid[1].destination_ip == "104.18.2.1"
    assert valid[1].protocol == "TLS"

    assert errors[0].row_index == 2
    assert errors[1].row_index == 3


def test_to_db_dict_compatibility():
    """Verify NormalizedTrafficRecord translates to SQLAlchemy TrafficRecord model kwargs."""
    analysis_id = uuid.uuid4()
    norm = NormalizedTrafficRecord(
        timestamp=datetime.now(timezone.utc),
        source_ip="10.0.0.1",
        destination_domain="chatgpt.com",
        destination_port=443,
        protocol="TCP",
        bytes_sent=100,
        bytes_received=2000,
    )

    db_kwargs = norm.to_db_dict(analysis_id=analysis_id)
    assert db_kwargs["analysis_id"] == analysis_id
    assert db_kwargs["destination_domain"] == "chatgpt.com"
    assert db_kwargs["destination_port"] == 443
    assert db_kwargs["bytes_sent"] == 100
    assert "extra_metadata" not in db_kwargs
