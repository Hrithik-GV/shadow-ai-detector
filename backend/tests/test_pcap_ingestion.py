import io
import struct
import tempfile
from datetime import datetime, timezone
import pytest
from scapy.layers.dns import DNS, DNSQR, DNSRR
from scapy.layers.inet import IP, TCP, UDP
from scapy.utils import wrpcap

from app.schemas.traffic import NormalizedTrafficRecord
from app.services.ai_detector import default_detector
from app.services.exceptions import (
    EmptyFileError,
    FileParsingError,
    FileTooLargeError,
    UnsupportedFileFormatError,
)
from app.services.ingestion import TrafficIngestionService
from app.services.pcap_service import PcapService, extract_sni_from_bytes
from app.services.risk_engine import EndpointTrafficAggregate, RiskEngine


def build_tls_client_hello(hostname: str) -> bytes:
    """Helper to synthesize valid RFC 6066 TLS ClientHello bytes containing SNI."""
    host_bytes = hostname.encode("ascii")
    sni_entry = b"\x00" + struct.pack(">H", len(host_bytes)) + host_bytes
    sni_list = struct.pack(">H", len(sni_entry)) + sni_entry
    sni_ext = struct.pack(">H", 0) + struct.pack(">H", len(sni_list)) + sni_list
    extensions = struct.pack(">H", len(sni_ext)) + sni_ext

    client_random = b"\x01" * 32
    session_id = b"\x00"  # length 0
    cipher_suites = struct.pack(">H", 2) + b"\xc0\x2f"
    compression_methods = b"\x01\x00"

    body = (
        b"\x03\x03"
        + client_random
        + session_id
        + cipher_suites
        + compression_methods
        + extensions
    )
    handshake = b"\x01" + struct.pack(">I", len(body))[1:] + body
    record = b"\x16\x03\x01" + struct.pack(">H", len(handshake)) + handshake
    return record


def make_pcap_bytes(packets: list) -> bytes:
    """Helper to write Scapy packets into in-memory PCAP bytes."""
    with tempfile.NamedTemporaryFile(suffix=".pcap", delete=True) as tmp:
        wrpcap(tmp.name, packets)
        tmp.seek(0)
        return tmp.read()


class TestPcapSniExtraction:
    """Unit tests for TLS Server Name Indication extraction."""

    def test_extract_valid_sni(self):
        payload = build_tls_client_hello("api.openai.com")
        sni = extract_sni_from_bytes(payload)
        assert sni == "api.openai.com"

    def test_extract_subdomain_sni(self):
        payload = build_tls_client_hello("claude-3-5.anthropic.com")
        sni = extract_sni_from_bytes(payload)
        assert sni == "claude-3-5.anthropic.com"

    def test_extract_sni_from_plain_http(self):
        http_data = b"GET /v1/chat/completions HTTP/1.1\r\nHost: api.openai.com\r\n\r\n"
        assert extract_sni_from_bytes(http_data) is None

    def test_extract_sni_from_truncated_payload(self):
        truncated = b"\x16\x03\x01\x00\x10\x01"
        assert extract_sni_from_bytes(truncated) is None

    def test_extract_sni_from_empty_bytes(self):
        assert extract_sni_from_bytes(b"") is None


class TestPcapIngestionService:
    """Integration tests for PCAP/PCAPNG ingestion pipeline."""

    def test_empty_pcap_file_rejected(self):
        service = TrafficIngestionService()
        with pytest.raises(EmptyFileError):
            service.ingest(b"", "empty.pcap")

    def test_malformed_magic_bytes_rejected(self):
        service = TrafficIngestionService()
        garbage = b"This is not a PCAP file at all, just plain text."
        with pytest.raises(FileParsingError):
            service.ingest(garbage, "corrupt.pcap")

    def test_unsupported_file_extension(self):
        service = TrafficIngestionService()
        with pytest.raises(UnsupportedFileFormatError):
            service.ingest(b"dummy", "sample.pcapng123")

    def test_pcap_dns_query_and_response_correlation(self):
        """DNS query + response maps server IP to domain, creating normalized flow."""
        client_ip = "192.168.1.100"
        dns_server = "8.8.8.8"
        openai_ip = "104.18.7.192"

        # 1. DNS Query
        dns_query = (
            IP(src=client_ip, dst=dns_server)
            / UDP(sport=53000, dport=53)
            / DNS(rd=1, qd=DNSQR(qname="api.openai.com"))
        )
        # 2. DNS Response
        dns_resp = (
            IP(src=dns_server, dst=client_ip)
            / UDP(sport=53, dport=53000)
            / DNS(
                qr=1,
                aa=1,
                qd=DNSQR(qname="api.openai.com"),
                an=DNSRR(rrname="api.openai.com", type="A", rdata=openai_ip),
            )
        )
        # 3. Subsequent TCP connection to openai_ip
        tcp_syn = (
            IP(src=client_ip, dst=openai_ip)
            / TCP(sport=49152, dport=443, flags="S")
        )

        pcap_data = make_pcap_bytes([dns_query, dns_resp, tcp_syn])
        service = TrafficIngestionService()
        res = service.ingest(pcap_data, "traffic_dns_openai.pcap")

        assert res.is_successful
        assert res.valid_count >= 1

        # Check correlated record
        openai_records = [
            r for r in res.valid_records if r.destination_domain == "api.openai.com"
        ]
        assert len(openai_records) >= 1
        record = openai_records[0]
        assert record.destination_ip in (openai_ip, dns_server)
        assert record.extra_metadata["evidence_source"] in ("dns_correlation", "dns_query")
        assert "byte_measurement" in record.extra_metadata

    def test_pcap_tls_sni_extraction_and_flow_aggregation(self):
        """TLS ClientHello extracts SNI without payload decryption and aggregates bytes."""
        client_ip = "10.0.0.15"
        server_ip = "160.153.63.10"
        sni_host = "api.anthropic.com"

        tls_payload = build_tls_client_hello(sni_host)

        # Client -> Server ClientHello
        client_pkt = (
            IP(src=client_ip, dst=server_ip)
            / TCP(sport=51234, dport=443, flags="PA")
            / tls_payload
        )
        # Server -> Client ACK
        server_pkt = (
            IP(src=server_ip, dst=client_ip)
            / TCP(sport=443, dport=51234, flags="A")
        )

        pcap_data = make_pcap_bytes([client_pkt, server_pkt])
        service = TrafficIngestionService()
        res = service.ingest(pcap_data, "anthropic_tls.pcap")

        assert res.is_successful
        record = res.valid_records[0]
        assert record.destination_domain == sni_host
        assert record.sni_hostname == sni_host
        assert record.source_ip == client_ip
        assert record.destination_ip == server_ip
        assert record.destination_port == 443
        assert record.protocol == "TLS"
        assert record.bytes_sent > 0
        assert record.bytes_received > 0
        assert record.extra_metadata["evidence_source"] == "tls_sni"

    def test_plain_ip_traffic_does_not_infer_hostname(self):
        """Plain IP traffic without SNI or DNS records must keep destination_domain as None."""
        client_ip = "192.168.1.5"
        server_ip = "198.51.100.20"

        plain_pkt = (
            IP(src=client_ip, dst=server_ip)
            / TCP(sport=41000, dport=8080, flags="P")
            / b"Random non-TLS binary data"
        )

        pcap_data = make_pcap_bytes([plain_pkt])
        service = TrafficIngestionService()
        res = service.ingest(pcap_data, "unassociated_ip.pcap")

        assert res.is_successful
        assert res.valid_count == 1
        record = res.valid_records[0]
        assert record.destination_domain is None
        assert record.sni_hostname is None
        assert record.destination_ip == server_ip
        assert record.extra_metadata["evidence_source"] == "ip_only"

        # Verify detector does not treat plain IP as AI
        detection = default_detector.classify_target(
            domain=record.destination_domain,
            sni_hostname=record.sni_hostname,
            destination_ip=record.destination_ip,
        )
        assert not detection.is_ai

    def test_truncated_pcap_graceful_handling(self):
        """Truncated PCAP header or frame must be caught gracefully without crashing."""
        valid_pkt = (
            IP(src="1.1.1.1", dst="2.2.2.2")
            / TCP(sport=1234, dport=80)
        )
        full_data = make_pcap_bytes([valid_pkt])

        # Truncate halfway through packet record
        truncated_data = full_data[: len(full_data) - 10]

        service = TrafficIngestionService()
        # Should either process the partial frames or record rejection
        try:
            res = service.ingest(truncated_data, "truncated.pcap")
            # If parsed, it must record valid count or rejection
            assert res.valid_count >= 0
        except FileParsingError:
            # FileParsingError on corrupt global header is also valid
            pass

    def test_ai_provider_detection_and_risk_evidence_provenance(self):
        """Detected AI endpoint preserves evidence provenance and byte definitions."""
        client_ip = "172.16.0.40"
        server_ip = "104.18.7.192"
        sni_host = "api.openai.com"

        tls_payload = build_tls_client_hello(sni_host)
        pkt = (
            IP(src=client_ip, dst=server_ip)
            / TCP(sport=55000, dport=443, flags="PA")
            / tls_payload
        )

        pcap_data = make_pcap_bytes([pkt])
        service = TrafficIngestionService()
        res = service.ingest(pcap_data, "openai_flow.pcap")

        assert res.is_successful
        rec = res.valid_records[0]

        # Detector classification
        det = default_detector.classify_target(
            domain=rec.destination_domain,
            sni_hostname=rec.sni_hostname,
            destination_ip=rec.destination_ip,
        )
        assert det.is_ai
        assert det.provider == "OpenAI"

        # Risk engine assessment
        agg = EndpointTrafficAggregate(
            target=rec.destination_domain,
            provider=det.provider,
            category=det.category,
            total_calls=1,
            bytes_sent=rec.bytes_sent or 0,
            bytes_received=rec.bytes_received or 0,
            source_ips=[rec.source_ip] if rec.source_ip else [],
            evidence_sources=[rec.extra_metadata["evidence_source"]],
        )

        engine = RiskEngine()
        inv_item, risk_finding = engine.evaluate_endpoint(agg)

        # Check evidence contains provenance and byte measurement note
        assert any("TLS Server Name Indication" in e for e in inv_item.evidence)
        assert any("Measurement Basis: Wire bytes" in e for e in inv_item.evidence)
        assert not any("token" in e.lower() and "count" in e.lower() and "actual" in e.lower() for e in inv_item.evidence)

    def test_api_upload_pcap_file_end_to_end(self):
        """Test full HTTP POST upload to /api/traffic/analyze with PCAP payload."""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        client_ip = "192.168.1.99"
        server_ip = "104.18.7.192"
        sni_host = "api.openai.com"

        tls_payload = build_tls_client_hello(sni_host)
        pkt = (
            IP(src=client_ip, dst=server_ip)
            / TCP(sport=58100, dport=443, flags="PA")
            / tls_payload
        )
        pcap_data = make_pcap_bytes([pkt])

        response = client.post(
            "/api/traffic/analyze",
            files={"file": ("live_capture.pcap", io.BytesIO(pcap_data), "application/vnd.tcpdump.pcap")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["file_format"] == "pcap"
        assert data["valid_rows"] >= 1
        assert data["status"] in ("completed", "processing")
        assert "summary" in data
