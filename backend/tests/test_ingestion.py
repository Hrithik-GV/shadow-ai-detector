import io
import json
import pytest

from app.schemas.traffic import TrafficAnalysisSummary
from app.services.exceptions import (
    EmptyFileError,
    FileParsingError,
    FileTooLargeError,
    RowLimitExceededError,
    UnsupportedFileFormatError,
)
from app.services.ingestion import (
    IngestionResult,
    TrafficIngestionService,
    ingest_traffic_file,
)


def test_ingest_valid_csv():
    """Verify standard CSV with headers is ingested and normalized properly."""
    csv_content = (
        "timestamp,src_ip,destination_domain,dest_port,protocol,bytes_out,bytes_in\n"
        "2026-10-09T18:00:00Z,192.168.1.10,api.openai.com,443,tcp,1000,25000\n"
        "2026-10-09T18:05:00Z,192.168.1.11,claude.ai,443,tcp,850,14000\n"
    )

    result = ingest_traffic_file(csv_content, "proxy_traffic.csv")
    assert isinstance(result, IngestionResult)
    assert result.file_format == "csv"
    assert result.total_rows == 2
    assert result.valid_count == 2
    assert result.rejected_count == 0
    assert result.is_successful is True

    record = result.valid_records[0]
    assert record.destination_domain == "api.openai.com"
    assert record.source_ip == "192.168.1.10"
    assert record.destination_port == 443
    assert record.protocol == "TCP"
    assert record.bytes_sent == 1000
    assert record.bytes_received == 25000


def test_ingest_csv_mixed_valid_and_invalid_records():
    """Verify mixed valid and invalid CSV rows are partitioned with accurate line numbers."""
    csv_content = (
        "src_ip,dest_domain,dest_port,bytes_out\n"
        "10.0.0.1,api.openai.com,443,500\n"        # Row 2 (valid)
        "999.999.999.999,claude.ai,443,200\n"       # Row 3 (invalid IP)
        "10.0.0.3,,8080,100\n"                     # Row 4 (missing destination)
        "10.0.0.4,chatgpt.com,-80,150\n"           # Row 5 (negative port)
        "10.0.0.5,gemini.google.com,443,300\n"     # Row 6 (valid)
    )

    result = ingest_traffic_file(csv_content, "mixed_audit.csv")
    assert result.total_rows == 5
    assert result.valid_count == 2
    assert result.rejected_count == 3

    assert result.valid_records[0].destination_domain == "api.openai.com"
    assert result.valid_records[1].destination_domain == "gemini.google.com"

    # Line numbers start at 2 because header is line 1
    rejected_lines = [r.row_index for r in result.rejected_records]
    assert rejected_lines == [3, 4, 5]

    # Verify meaningful error messages
    error_row3 = result.rejected_records[0]
    assert any("Invalid IP address" in e.message for e in error_row3.errors)

    error_row4 = result.rejected_records[1]
    assert any("Missing destination" in e.message for e in error_row4.errors)

    error_row5 = result.rejected_records[2]
    assert any("outside valid range" in e.message for e in error_row5.errors)


def test_ingest_csv_with_duplicate_headers():
    """Verify CSV with duplicate header names is handled without crash."""
    csv_content = (
        "src_ip,dest_domain,dest_port,dest_port\n"
        "192.168.1.1,api.openai.com,443,8443\n"
    )
    result = ingest_traffic_file(csv_content, "dup_headers.csv")
    assert result.total_rows == 1
    assert result.valid_count == 1
    assert result.valid_records[0].destination_port == 443


def test_ingest_csv_with_utf8_bom():
    """Verify CSV with UTF-8-SIG byte order mark decodes cleanly."""
    bom_csv = "\ufeffsrc_ip,dest_domain,port\n192.168.1.5,claude.ai,443\n".encode("utf-8")
    result = ingest_traffic_file(bom_csv, "excel_export.csv")
    assert result.total_rows == 1
    assert result.valid_count == 1
    assert result.valid_records[0].destination_domain == "claude.ai"


def test_ingest_valid_json_array():
    """Verify JSON file containing an array of objects."""
    data = [
        {"src_ip": "10.0.0.1", "dest_domain": "api.openai.com", "port": 443},
        {"src_ip": "10.0.0.2", "destination_ip": "104.18.2.1", "proto": "TLS"},
    ]
    json_bytes = json.dumps(data).encode("utf-8")

    result = ingest_traffic_file(json_bytes, "traffic.json")
    assert result.file_format == "json"
    assert result.total_rows == 2
    assert result.valid_count == 2
    assert result.rejected_count == 0
    assert result.valid_records[0].destination_domain == "api.openai.com"
    assert result.valid_records[1].destination_ip == "104.18.2.1"


def test_ingest_valid_json_wrapped_structures():
    """Verify JSON with wrapper objects ('records', 'traffic', 'data')."""
    wrapped_records = {"records": [{"dest_domain": "chatgpt.com", "port": 443}]}
    res1 = ingest_traffic_file(json.dumps(wrapped_records), "wrapped.json")
    assert res1.total_rows == 1
    assert res1.valid_count == 1
    assert res1.valid_records[0].destination_domain == "chatgpt.com"

    wrapped_traffic = {"traffic": [{"destination_ip": "8.8.8.8", "proto": "UDP"}]}
    res2 = ingest_traffic_file(json.dumps(wrapped_traffic), "wrapped2.json")
    assert res2.valid_count == 1
    assert res2.valid_records[0].destination_ip == "8.8.8.8"


def test_ingest_json_lines_and_ndjson():
    """Verify JSON Lines (.jsonl / .ndjson) format."""
    ndjson_content = (
        '{"src_ip": "10.0.0.1", "dest_domain": "api.openai.com", "port": 443}\n'
        '{"src_ip": "10.0.0.2", "destination_domain": "claude.ai", "bytes_out": -5}\n'
        '{"src_ip": "10.0.0.3", "dest_domain": "perplxity.ai", "port": 443}\n'
    )

    result = ingest_traffic_file(ndjson_content, "stream.jsonl")
    assert result.file_format == "jsonl"
    assert result.total_rows == 3
    assert result.valid_count == 2
    assert result.rejected_count == 1
    assert result.rejected_records[0].row_index == 2


def test_ingest_json_fallback_for_ndjson_in_json_extension():
    """Verify line-delimited JSON saved with .json extension falls back gracefully."""
    ndjson = (
        '{"src_ip": "1.1.1.1", "dest_domain": "google.com"}\n'
        '{"src_ip": "2.2.2.2", "dest_domain": "openai.com"}\n'
    )
    result = ingest_traffic_file(ndjson, "ndjson_with_json_ext.json")
    assert result.valid_count == 2


def test_ingest_empty_file_handling():
    """Verify rejection of empty files and whitespace-only files."""
    with pytest.raises(EmptyFileError, match="empty"):
        ingest_traffic_file(b"", "empty.csv")

    with pytest.raises(EmptyFileError, match="empty"):
        ingest_traffic_file("   \n\t  ", "blank.json")


def test_ingest_csv_header_only():
    """Verify CSV with only headers produces 0 total rows without crashing."""
    csv_header_only = "src_ip,dest_domain,dest_port\n"
    result = ingest_traffic_file(csv_header_only, "header_only.csv")
    assert result.total_rows == 0
    assert result.valid_count == 0
    assert result.rejected_count == 0


def test_ingest_malformed_syntax():
    """Verify syntax errors in JSON and CSV raise FileParsingError."""
    # Corrupt JSON syntax
    with pytest.raises(FileParsingError, match="Malformed JSON"):
        ingest_traffic_file("{invalid json content, missing quotes", "corrupt.json")

    # Corrupt CSV
    corrupt_csv = 'col1,col2\n"unclosed quote,123\n'
    with pytest.raises(FileParsingError, match="Malformed CSV"):
        ingest_traffic_file(corrupt_csv, "corrupt.csv")


def test_ingest_unsupported_extensions():
    """Verify rejection of unsupported file extensions and missing extensions."""
    with pytest.raises(UnsupportedFileFormatError, match="Unsupported file extension"):
        ingest_traffic_file(b"some content", "traffic.xml")

    with pytest.raises(UnsupportedFileFormatError, match="missing an extension"):
        ingest_traffic_file(b"some content", "traffic_log_no_ext")


def test_max_upload_size_limit_enforcement():
    """Verify file exceeding max_upload_size is rejected."""
    service = TrafficIngestionService(max_upload_size=100)  # 100 bytes limit
    large_content = b"a" * 105

    with pytest.raises(FileTooLargeError, match="exceeds the maximum allowed size"):
        service.ingest(large_content, "large_file.csv")


def test_max_row_limit_enforcement():
    """Verify file exceeding max_rows limit is rejected."""
    service = TrafficIngestionService(max_rows=2)
    csv_3_rows = (
        "dest_domain\n"
        "domain1.com\n"
        "domain2.com\n"
        "domain3.com\n"
    )

    with pytest.raises(RowLimitExceededError, match="exceeds configured limit"):
        service.ingest(csv_3_rows, "too_many_rows.csv")


def test_ingest_file_stream_input():
    """Verify stream input (io.StringIO or io.BytesIO) works identically."""
    stream = io.StringIO("destination_domain,dest_port\napi.openai.com,443\n")
    result = ingest_traffic_file(stream, "from_stream.csv")
    assert result.valid_count == 1
    assert result.valid_records[0].destination_domain == "api.openai.com"


def test_ingestion_summary_generation():
    """Verify IngestionResult converts cleanly to TrafficAnalysisSummary."""
    csv_data = "dest_domain\nopenai.com\n\n"
    result = ingest_traffic_file("dest_domain\nopenai.com\n", "summary_test.csv")
    summary = result.to_summary()

    assert isinstance(summary, TrafficAnalysisSummary)
    assert summary.original_filename == "summary_test.csv"
    assert summary.file_format == "csv"
    assert summary.status == "completed"
    assert summary.total_rows_received == 1
    assert summary.valid_rows == 1
    assert summary.rejected_rows == 0
