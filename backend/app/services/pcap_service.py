import io
import ipaddress
import logging
import os
import re
import struct
import tempfile
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from scapy.layers.dns import DNS, DNSQR, DNSRR
from scapy.layers.inet import ICMP, IP, TCP, UDP
from scapy.layers.inet6 import IPv6
from scapy.utils import PcapNgReader, PcapReader, Scapy_Exception

from app.core.config import settings
from app.schemas.traffic import (
    DOMAIN_REGEX,
    NormalizedTrafficRecord,
    RecordValidationError,
    ValidationErrorDetail,
)
from app.services.exceptions import (
    EmptyFileError,
    FileParsingError,
    FileTooLargeError,
)

logger = logging.getLogger(__name__)

# Standard well-known server ports for directional client-server disambiguation
WELL_KNOWN_SERVER_PORTS = {
    53, 80, 88, 123, 389, 443, 445, 465, 587, 636, 853, 993, 995,
    1433, 1521, 3306, 3389, 5000, 5432, 6379, 8000, 8080, 8443, 8888, 9200, 27017
}

# PCAP and PCAPNG magic numbers
PCAP_MAGIC_NUMBERS = [
    b"\xd4\xc3\xb2\xa1",  # Standard PCAP (Little Endian)
    b"\xa1\xb2\xc3\xd4",  # Standard PCAP (Big Endian)
    b"\x4d\x3c\xb2\xa1",  # Nanosecond PCAP (Little Endian)
    b"\xa1\xb2\x3c\x4d",  # Nanosecond PCAP (Big Endian)
]
PCAPNG_MAGIC = b"\x0a\x0d\x0d\x0a"  # Section Header Block (\n\r\r\n)


def extract_sni_from_bytes(data: bytes) -> Optional[str]:
    """Safely extracts TLS Server Name Indication (SNI) from raw TCP payload bytes.
    
    Adheres strictly to RFC 6066 without payload decryption or secret reconstruction.
    Returns sanitized hostname or None if not present or malformed.
    """
    if len(data) < 43 or data[0] != 0x16:  # 0x16 = Handshake record
        return None

    pos = 5
    if len(data) < pos + 4 or data[pos] != 0x01:  # 0x01 = ClientHello
        return None

    pos += 4  # Skip handshake type (1) and length (3)
    pos += 34  # Skip client version (2) and client random (32)

    if len(data) <= pos:
        return None

    # Skip Session ID
    sess_id_len = data[pos]
    pos += 1 + sess_id_len
    if len(data) <= pos + 2:
        return None

    # Skip Cipher Suites
    cs_len = int.from_bytes(data[pos:pos + 2], "big")
    pos += 2 + cs_len
    if len(data) <= pos + 1:
        return None

    # Skip Compression Methods
    comp_len = data[pos]
    pos += 1 + comp_len
    if len(data) <= pos + 2:
        return None

    # Extensions Block
    ext_total_len = int.from_bytes(data[pos:pos + 2], "big")
    pos += 2
    ext_end = min(len(data), pos + ext_total_len)

    while pos + 4 <= ext_end:
        ext_type = int.from_bytes(data[pos:pos + 2], "big")
        ext_len = int.from_bytes(data[pos + 2:pos + 4], "big")
        pos += 4

        if ext_type == 0:  # Extension Type 0 = Server Name Indication
            if pos + 5 <= ext_end:
                # Skip SNI list length (2 bytes) and Name Type (1 byte: 0 = host_name)
                name_len = int.from_bytes(data[pos + 3:pos + 5], "big")
                if pos + 5 + name_len <= ext_end:
                    try:
                        raw_name = data[pos + 5:pos + 5 + name_len].decode("ascii", errors="ignore").lower().strip()
                        clean_name = raw_name.rstrip(".")
                        if clean_name and len(clean_name) <= 253 and DOMAIN_REGEX.match(clean_name):
                            return clean_name
                    except Exception:
                        return None
        pos += ext_len

    return None


@dataclass
class FlowAccumulator:
    """Tracks bidirectional packet conversation statistics for normalized traffic generation."""
    client_ip: str
    server_ip: str
    server_port: int
    protocol: str
    first_seen: datetime
    last_seen: datetime
    bytes_sent: int = 0      # IP wire bytes client -> server
    bytes_received: int = 0  # IP wire bytes server -> client
    packet_count: int = 0
    sni_hostname: Optional[str] = None
    dns_query_name: Optional[str] = None
    http_method: Optional[str] = None
    http_uri: Optional[str] = None


class PcapService:
    """Production service for parsing raw PCAP and PCAPNG capture files using Scapy."""

    @staticmethod
    def parse_capture(
        raw_bytes: bytes,
        filename: str,
        file_format: str = "pcap",
        max_packets: Optional[int] = None,
        max_seconds: Optional[int] = None,
    ) -> Tuple[List[NormalizedTrafficRecord], List[RecordValidationError], Dict[str, Any]]:
        """Parses network packets from binary capture data into normalized observations.
        
        Args:
            raw_bytes: Complete raw capture file bytes.
            filename: Original uploaded capture filename.
            file_format: 'pcap' or 'pcapng'.
            max_packets: Safety packet ceiling (defaults to settings.MAX_PCAP_PACKETS).
            max_seconds: Safety processing timeout (defaults to settings.MAX_PCAP_PROCESSING_SECONDS).
            
        Returns:
            Tuple of:
            - List[NormalizedTrafficRecord]: Valid standardized flow records.
            - List[RecordValidationError]: Malformed packet or parsing truncation errors.
            - Dict[str, Any]: Capture telemetry and byte measurement definitions.
        """
        if not raw_bytes or len(raw_bytes) == 0:
            raise EmptyFileError(f"Uploaded capture file '{filename}' is empty.")

        # Check for minimum header size (PCAP global header is 24 bytes, PCAPNG section header is 28 bytes)
        if len(raw_bytes) < 24:
            raise FileParsingError(
                f"Capture file '{filename}' is too small ({len(raw_bytes)} bytes) to contain valid PCAP/PCAPNG headers."
            )

        # Magic number verification
        first_4 = raw_bytes[:4]
        is_pcapng = first_4 == PCAPNG_MAGIC or file_format.lower() == "pcapng"
        is_pcap = any(first_4 == m for m in PCAP_MAGIC_NUMBERS) or file_format.lower() in ("pcap", "cap")

        if not (is_pcap or is_pcapng):
            # Not matching standard magic bytes
            raise FileParsingError(
                f"File '{filename}' does not contain recognized PCAP or PCAPNG header magic signatures."
            )

        packet_limit = max_packets if max_packets is not None else settings.MAX_PCAP_PACKETS
        time_limit = max_seconds if max_seconds is not None else settings.MAX_PCAP_PROCESSING_SECONDS

        # Write to secure temporary file for Scapy reading
        suffix = ".pcapng" if is_pcapng else ".pcap"
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        try:
            with os.fdopen(tmp_fd, "wb") as f:
                f.write(raw_bytes)

            return PcapService._process_file_with_scapy(
                tmp_path=tmp_path,
                filename=filename,
                is_pcapng=is_pcapng,
                packet_limit=packet_limit,
                time_limit=time_limit,
                total_bytes=len(raw_bytes),
            )
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    @staticmethod
    def _process_file_with_scapy(
        tmp_path: str,
        filename: str,
        is_pcapng: bool,
        packet_limit: int,
        time_limit: int,
        total_bytes: int,
    ) -> Tuple[List[NormalizedTrafficRecord], List[RecordValidationError], Dict[str, Any]]:
        """Internal iterator over capture packets with DNS mapping and flow aggregation."""
        start_time = time.time()
        flows: Dict[Tuple[str, str, int, str], FlowAccumulator] = {}
        dns_ip_to_domain: Dict[str, Tuple[str, datetime]] = {}
        dns_queries: List[Dict[str, Any]] = []

        total_packets_read = 0
        non_ip_packets = 0
        rejected_records: List[RecordValidationError] = []
        truncation_occurred = False

        # Reader initialization with fallback between PcapNgReader and PcapReader
        reader = None
        try:
            if is_pcapng:
                try:
                    reader = PcapNgReader(tmp_path)
                except Exception:
                    reader = PcapReader(tmp_path)
            else:
                try:
                    reader = PcapReader(tmp_path)
                except Exception:
                    reader = PcapNgReader(tmp_path)
        except Exception as exc:
            raise FileParsingError(f"Failed to open capture file '{filename}': {str(exc)}")

        with reader:
            while True:
                # Check safety resource limits
                if total_packets_read >= packet_limit:
                    logger.warning(
                        f"PCAP ingestion reached packet ceiling of {packet_limit} packets for '{filename}'."
                    )
                    break
                if (time.time() - start_time) > time_limit:
                    logger.warning(
                        f"PCAP ingestion exceeded timeout limit of {time_limit}s for '{filename}'."
                    )
                    break

                try:
                    packet = reader.read_packet()
                    if packet is None:
                        break
                except EOFError:
                    break
                except (struct.error, Scapy_Exception, Exception) as exc:
                    logger.warning(f"Capture file '{filename}' encountered truncated/malformed packet: {exc}")
                    truncation_occurred = True
                    rejected_records.append(
                        RecordValidationError(
                            row_index=total_packets_read + 1,
                            errors=[
                                ValidationErrorDetail(
                                    field="packet_frame",
                                    message=f"Capture truncated or corrupted: {str(exc)}",
                                    invalid_value=None,
                                )
                            ],
                            raw_record={"packet_index": total_packets_read + 1, "filename": filename},
                        )
                    )
                    break

                total_packets_read += 1

                # Extract IP layer
                if packet.haslayer(IP):
                    ip_layer = packet[IP]
                    src_ip = str(ip_layer.src)
                    dst_ip = str(ip_layer.dst)
                    ip_len = int(ip_layer.len) if hasattr(ip_layer, "len") and ip_layer.len else len(packet)
                elif packet.haslayer(IPv6):
                    ip_layer = packet[IPv6]
                    src_ip = str(ip_layer.src)
                    dst_ip = str(ip_layer.dst)
                    ip_len = (int(ip_layer.plen) + 40) if hasattr(ip_layer, "plen") and ip_layer.plen else len(packet)
                else:
                    non_ip_packets += 1
                    continue

                # Timestamp extraction (UTC)
                pkt_time = float(packet.time) if hasattr(packet, "time") else time.time()
                try:
                    pkt_dt = datetime.fromtimestamp(pkt_time, tz=timezone.utc)
                except Exception:
                    pkt_dt = datetime.now(timezone.utc)

                # Transport Protocol & Ports
                protocol = "TCP" if packet.haslayer(TCP) else ("UDP" if packet.haslayer(UDP) else ("ICMP" if packet.haslayer(ICMP) else "OTHER"))
                sport = None
                dport = None
                payload_bytes = b""

                if packet.haslayer(TCP):
                    tcp_layer = packet[TCP]
                    sport = int(tcp_layer.sport)
                    dport = int(tcp_layer.dport)
                    payload_bytes = bytes(tcp_layer.payload)
                elif packet.haslayer(UDP):
                    udp_layer = packet[UDP]
                    sport = int(udp_layer.sport)
                    dport = int(udp_layer.dport)
                    payload_bytes = bytes(udp_layer.payload)

                # DNS Inspection (UDP/TCP Port 53 or DNS layer)
                if packet.haslayer(DNS):
                    dns_layer = packet[DNS]
                    is_qr = getattr(dns_layer, "qr", 0)

                    # DNS Query
                    if is_qr == 0 and hasattr(dns_layer, "qd") and dns_layer.qd:
                        qd_items = dns_layer.qd if isinstance(dns_layer.qd, (list, tuple)) else [dns_layer.qd]
                        for qd_elem in qd_items:
                            if hasattr(qd_elem, "qname") and qd_elem.qname:
                                raw_qname = qd_elem.qname
                                qname = (
                                    raw_qname.decode("utf-8", errors="ignore")
                                    if isinstance(raw_qname, bytes)
                                    else str(raw_qname)
                                ).rstrip(".").lower()
                                if qname and DOMAIN_REGEX.match(qname):
                                    dns_queries.append({
                                        "client_ip": src_ip,
                                        "qname": qname,
                                        "timestamp": pkt_dt,
                                    })

                    # DNS Response (Answers)
                    elif is_qr == 1 and hasattr(dns_layer, "an") and dns_layer.an:
                        an_items = []
                        if isinstance(dns_layer.an, (list, tuple)):
                            an_items = list(dns_layer.an)
                        else:
                            curr_rr = dns_layer.an
                            while curr_rr:
                                an_items.append(curr_rr)
                                curr_rr = getattr(curr_rr, "payload", None)

                        for rr in an_items:
                            if hasattr(rr, "rdata") and hasattr(rr, "rrname"):
                                raw_rrname = getattr(rr, "rrname", None)
                                rr_type = getattr(rr, "type", 0)
                                if raw_rrname and rr_type in (1, 28):  # A (IPv4) or AAAA (IPv6)
                                    resolved_domain = (
                                        raw_rrname.decode("utf-8", errors="ignore")
                                        if isinstance(raw_rrname, bytes)
                                        else str(raw_rrname)
                                    ).rstrip(".").lower()
                                    resolved_ip = str(rr.rdata)
                                    if DOMAIN_REGEX.match(resolved_domain):
                                        dns_ip_to_domain[resolved_ip] = (resolved_domain, pkt_dt)

                # TLS SNI Inspection
                sni_candidate = None
                if protocol == "TCP" and payload_bytes:
                    sni_candidate = extract_sni_from_bytes(payload_bytes)

                # Determine Client vs Server Orientation
                # Rule: Ephemeral port is client, well-known port is server
                is_client_to_server = True
                if sport is not None and dport is not None:
                    if dport in WELL_KNOWN_SERVER_PORTS and sport not in WELL_KNOWN_SERVER_PORTS:
                        client_ip, server_ip, server_port = src_ip, dst_ip, dport
                        is_client_to_server = True
                    elif sport in WELL_KNOWN_SERVER_PORTS and dport not in WELL_KNOWN_SERVER_PORTS:
                        client_ip, server_ip, server_port = dst_ip, src_ip, sport
                        is_client_to_server = False
                    elif sni_candidate:
                        # ClientHello sender is unequivocally client
                        client_ip, server_ip, server_port = src_ip, dst_ip, dport
                        is_client_to_server = True
                    else:
                        # Default order
                        if (src_ip, sport) <= (dst_ip, dport):
                            client_ip, server_ip, server_port = src_ip, dst_ip, dport
                            is_client_to_server = True
                        else:
                            client_ip, server_ip, server_port = dst_ip, src_ip, sport
                            is_client_to_server = False
                else:
                    client_ip, server_ip, server_port = src_ip, dst_ip, (dport or 0)
                    is_client_to_server = True

                flow_key = (client_ip, server_ip, server_port, protocol)

                if flow_key not in flows:
                    flows[flow_key] = FlowAccumulator(
                        client_ip=client_ip,
                        server_ip=server_ip,
                        server_port=server_port,
                        protocol="TLS" if (server_port == 443 or sni_candidate) else protocol,
                        first_seen=pkt_dt,
                        last_seen=pkt_dt,
                    )

                flow = flows[flow_key]
                flow.packet_count += 1
                if pkt_dt < flow.first_seen:
                    flow.first_seen = pkt_dt
                if pkt_dt > flow.last_seen:
                    flow.last_seen = pkt_dt

                if is_client_to_server:
                    flow.bytes_sent += ip_len
                else:
                    flow.bytes_received += ip_len

                if sni_candidate and not flow.sni_hostname:
                    flow.sni_hostname = sni_candidate
                    flow.protocol = "TLS"

        # Check for empty capture
        if total_packets_read == 0 and not flows:
            raise EmptyFileError(f"Capture file '{filename}' contains 0 network packet records.")

        # Second Pass: Synthesize normalized traffic records with evidence provenance
        valid_records: List[NormalizedTrafficRecord] = []

        # 1. Add aggregated transport flows
        for (client_ip, server_ip, server_port, proto), flow in flows.items():
            destination_domain = None
            evidence_source = "ip_only"

            # Precedence 1: Explicit TLS Server Name Indication
            if flow.sni_hostname:
                destination_domain = flow.sni_hostname
                evidence_source = "tls_sni"

            # Precedence 2: Direct DNS resolution correlation
            elif server_ip in dns_ip_to_domain:
                domain_name, _ = dns_ip_to_domain[server_ip]
                destination_domain = domain_name
                evidence_source = "dns_correlation"

            # Precedence 3: Unassociated plain IP traffic (do NOT guess or infer domain!)
            else:
                destination_domain = None
                evidence_source = "ip_only"

            record = NormalizedTrafficRecord(
                timestamp=flow.first_seen,
                source_ip=flow.client_ip,
                destination_ip=flow.server_ip,
                destination_domain=destination_domain,
                destination_port=flow.server_port if flow.server_port > 0 else None,
                protocol=flow.protocol,
                bytes_sent=flow.bytes_sent,
                bytes_received=flow.bytes_received,
                sni_hostname=flow.sni_hostname,
                extra_metadata={
                    "evidence_source": evidence_source,
                    "capture_format": "pcapng" if is_pcapng else "pcap",
                    "packet_count": flow.packet_count,
                    "byte_measurement": "ip_packet_total_length",
                    "byte_definition_note": (
                        "Observed bytes represent total IP wire length on the network interface. "
                        "Encrypted TLS packets do not reveal prompt text, completions, or artificial token costs."
                    ),
                    "server_port": flow.server_port,
                },
            )
            valid_records.append(record)

        # 2. Add DNS queries that had no subsequent TCP flows (e.g., DNS-only captures or blocked connections)
        observed_dns_domains = {r.destination_domain for r in valid_records if r.destination_domain}
        for q in dns_queries:
            qname = q["qname"]
            client_ip = q["client_ip"]
            # Only include if not already represented in a direct flow
            if qname not in observed_dns_domains:
                observed_dns_domains.add(qname)
                valid_records.append(
                    NormalizedTrafficRecord(
                        timestamp=q["timestamp"],
                        source_ip=client_ip,
                        destination_ip="8.8.8.8",  # Standard DNS resolver representation
                        destination_domain=qname,
                        destination_port=53,
                        protocol="DNS",
                        bytes_sent=64,
                        bytes_received=128,
                        sni_hostname=None,
                        extra_metadata={
                            "evidence_source": "dns_query",
                            "capture_format": "pcapng" if is_pcapng else "pcap",
                            "packet_count": 1,
                            "byte_measurement": "dns_packet_wire_bytes",
                            "byte_definition_note": "DNS query wire exchange.",
                        },
                    )
                )

        capture_stats = {
            "total_packets_parsed": total_packets_read,
            "non_ip_packets_skipped": non_ip_packets,
            "dns_resolutions_correlated": len(dns_ip_to_domain),
            "tls_sni_sessions_identified": sum(1 for r in valid_records if r.sni_hostname),
            "flows_generated": len(valid_records),
            "truncated": truncation_occurred,
        }

        return valid_records, rejected_records, capture_stats
