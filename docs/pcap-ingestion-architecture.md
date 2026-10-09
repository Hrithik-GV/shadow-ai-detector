# PCAP and PCAPNG Capture Ingestion Architecture & Limitations

## Overview
The Shadow AI Detector supports direct ingestion of network capture files (`.pcap`, `.pcapng`, `.cap`) alongside structured logs (`.csv`, `.json`, `.jsonl`, `.ndjson`). Capture analysis operates in userspace using Python's **Scapy** library to parse raw packets into standardized bidirectional network observations and correlates evidence with the AI Provider Registry and Risk Engine.

---

## Supported Capture Formats
1. **Standard PCAP (`.pcap`, `.cap`)**:
   - Libpcap format (magic bytes `0xd4c3b2a1` [Little-Endian] and `0xa1b2c3d4` [Big-Endian]).
   - Nanosecond-resolution PCAP (magic bytes `0x4d3cb2a1` and `0xa1b23c4d`).
2. **PCAP Next Generation (`.pcapng`)**:
   - PCAPNG Section Header Block format (`0x0a0d0d0a`).
   - Automatically utilizes Scapy's `PcapNgReader` with graceful fallback to `PcapReader`.

---

## Extracted Network Metadata
For every valid IPv4 and IPv6 packet, the ingestion engine extracts:
1. **Timestamp**: High-precision UTC timestamp derived from the capture frame header.
2. **IP 5-Tuple**:
   - Client and Server IP addresses (IPv4 and IPv6).
   - Transport Protocol (`TCP`, `UDP`, `ICMP`, or `OTHER`).
   - Source and Destination transport port numbers.
3. **DNS Query & Response Metadata**:
   - Resolves DNS Query Names (`DNSQR.qname`) from UDP/TCP port 53.
   - Extracts DNS Resource Record Answers (`DNSRR.an`, types `A` and `AAAA`) to build an in-memory IP-to-Domain correlation map.
4. **TLS Server Name Indication (SNI)**:
   - Evaluates TLS ClientHello handshake records (`0x16`, handshake type `0x01`).
   - Parses the RFC 6066 Server Name Indication extension to extract cleartext destination hostnames without decrypting payloads.
5. **Bidirectional Flow Aggregation**:
   - Directional disambiguation between ephemeral client ports and well-known server ports (e.g., 443, 80, 53, 8080).
   - Aggregates multi-packet connections into consolidated conversations with `bytes_sent` and `bytes_received`.

---

## Wire Byte Count Measurement Definition
> [!IMPORTANT]
> **Byte Count Semantics**:
> - Byte counts represent **Layer 3 IP wire length** (`IP.len` or `IPv6.plen + 40`) observed on the network interface.
> - Outbound bytes (`bytes_sent`) measure total client-to-server IP datagram bytes, including TCP/IP headers, TLS handshake frames, and encrypted application data.
> - Inbound bytes (`bytes_received`) measure total server-to-client IP datagram bytes.
> - **No Token/Prompt Reconstruction**: Raw wire bytes reflect network transmission overhead and payload volume. They do **NOT** represent prompt token counts, prompt text contents, or provider billing costs.

---

## Evidence Provenance & Correlation Rules
To maintain audit integrity, every normalized record carries an `evidence_source` tag:
- `tls_sni`: Hostname directly observed in a TLS ClientHello handshake extension (highest confidence).
- `dns_correlation`: Hostname mapped from an authoritative DNS `A` or `AAAA` response observed within the same capture session.
- `dns_query`: Isolated DNS query observed without corresponding TCP flows.
- `csv_direct` / `json_direct`: Domain supplied directly by structured log entries.
- `ip_only`: Unassociated network IP traffic where no SNI was present and no DNS resolution was captured.

### Zero-Guessing Rule
If an IP packet does not present TLS SNI and was not resolved by DNS within the capture, **no hostname is inferred or guessed**. The traffic is recorded strictly by destination IP and port.

---

## Safety Limits & Handling of Malformed Captures
To prevent resource exhaustion and denial-of-service, the ingestion pipeline enforces strict configurable boundaries:
1. **File Size Limit**: Capped at `50 MB` (`settings.MAX_UPLOAD_SIZE_BYTES`).
2. **Packet Ceiling**: Maximum `50,000` packets per file (`settings.MAX_PCAP_PACKETS`). Captures exceeding this ceiling are safely truncated and processed up to the ceiling.
3. **Processing Timeout**: Maximum `30` seconds wall-clock time (`settings.MAX_PCAP_PROCESSING_SECONDS`).
4. **Truncated/Corrupted Captures**: Truncated frames or corrupted magic headers generate structured `RecordValidationError` entries rather than unhandled 500 server crashes.
5. **Empty Captures**: 0-byte files or captures containing 0 IP packets raise an explicit `EmptyFileError`.

---

## Architectural & Platform Limitations
1. **No Live Packet Sniffing**: The detector operates exclusively on static, uploaded capture files. No root/administrator socket privileges or `libpcap` promiscuous capture interfaces are required.
2. **No Payload Decryption / TLS Interception**: The system does not perform HTTPS man-in-the-middle decryption, private key injection, or certificate spoofing. Payload confidentiality is preserved.
3. **Fragmented TLS Handshakes**: ClientHello messages split across multiple TCP segments without reassembly may result in unparsed SNI, falling back cleanly to DNS correlation or IP-only records.
