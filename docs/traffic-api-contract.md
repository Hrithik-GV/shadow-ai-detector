# Shadow AI Detector - Complete System API Contract & Integration Reference

**Version:** `0.2.0`  
**Base URL:** `http://localhost:8000`  
**API Prefixes:**
- Unversioned routes: `/api/traffic`, `/api/dashboard`, `/api/inventory`, `/api/risks`, `/api/reports`, `/api/policies`, `/api/auth`
- Versioned aliases: `/api/v1/*`
- System health checks: `/health`, `/api/v1/health`

---

## 1. Architectural Overview & Ingestion Semantics

The **Shadow AI Detector** provides automated detection, telemetry analysis, and enterprise risk assessment of unsanctioned generative AI services across organizational network traffic.

### Data & Processing Semantics
1. **Network Events vs. Connections**:
   - `valid_records` / `total_valid_records` denotes parsed, schema-validated traffic log entries or extracted packet flows.
   - For PCAP/PCAPNG captures, packets sharing `(src_ip, dst_ip, dst_port, protocol)` within a flow aggregation window are correlated into structured traffic observations with aggregated wire byte counts.
2. **Missing Metadata Handling**:
   - Missing optional values (`null`) are preserved as unknown, never fabricated or zeroed out.
   - Byte counts (`total_bytes_sent`, `total_bytes_received`) sum only records where non-null numbers were supplied.
   - Missing counts are reported explicitly via `missing_bytes_sent_count`, `missing_bytes_received_count`, `missing_protocol_count`.
3. **Deterministic Governance Conflict Resolution**:
   - Database policies take precedence over environment defaults.
   - **Denial / Unapproved Overrides Approval in Any Conflict**: If ANY active policy marks a provider or domain as `unapproved`, `blocked`, or `restricted`, the resolution is strictly unapproved.

---

## 2. Ingestion Formats & Record Schema

### Supported Capture Formats
- **CSV (`.csv`)**: Delimited tabular logs with header row. Automatic case-insensitive header mapping.
- **JSON (`.json`)**: Array of records (`[{...}]`), wrapper object (`{"records": [...]}`), or single record.
- **JSON Lines (`.jsonl`, `.ndjson`)**: Streaming newline-delimited JSON objects.
- **PCAP / PCAPNG (`.pcap`, `.pcapng`)**: Raw packet captures parsed securely via Scapy with streaming packet limits (`MAX_PCAP_PACKETS=50,000`, `MAX_PCAP_PROCESSING_SECONDS=30`). Extracts source/destination IP, transport ports, DNS QNAME queries and answers, TLS SNI hostnames, and wire frame byte counts.

### Schema Attributes & Header Aliases

| Canonical Field | Accepted Aliases | Type | Requirement | Semantics |
|---|---|---|---|---|
| `destination_domain` | `dest_domain`, `domain`, `host`, `hostname` | string | Required if `destination_ip` missing | Target domain or hostname (e.g. `api.openai.com`) |
| `destination_ip` | `dest_ip`, `dst_ip`, `dst`, `destination_address` | string | Required if `destination_domain` missing | IPv4 or IPv6 destination address |
| `source_ip` | `src_ip`, `src`, `client_ip` | string | Optional | IPv4 or IPv6 client origin address |
| `destination_port` | `dest_port`, `dst_port`, `port`, `dport` | integer | Optional | Port number (1–65535) |
| `protocol` | `proto`, `transport_protocol` | string | Optional | Normalized uppercase (TCP, UDP, TLS, HTTP, DNS) |
| `bytes_sent` | `bytes_out`, `out_bytes`, `bytes_tx`, `tx_bytes` | integer | Optional | Client outbound wire/payload bytes (>= 0) |
| `bytes_received` | `bytes_in`, `in_bytes`, `bytes_rx`, `rx_bytes` | integer | Optional | Client inbound wire/payload bytes (>= 0) |
| `timestamp` | `time`, `ts`, `datetime`, `@timestamp` | string/num | Optional | ISO 8601, RFC 2822, or epoch timestamps normalized to UTC |
| `http_method` | `method` | string | Optional | HTTP method (GET, POST, etc.) |
| `http_uri` | `uri`, `path`, `url` | string | Optional | Target request path |
| `http_status_code` | `status_code`, `status` | integer | Optional | Response status code (100–599) |
| `user_agent` | `useragent`, `http_user_agent` | string | Optional | Client user-agent string |
| `sni_hostname` | `sni`, `tls_sni` | string | Optional | TLS Server Name Indication hostname |

---

## 3. Authentication & Authorization Specification

Administrative operations (AI governance policies, audit reviews) are guarded by role-based authorization.

### Credentials & Security Design
- **Password Storage**: Passwords are never stored in plaintext. They are hashed using PBKDF2-HMAC-SHA256 with 100,000 iterations and 16-byte cryptographic salts (`pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>`).
- **Signing Keys**: Kept in server environment variables (`SECRET_KEY`).
- **Access Tokens**: Compact signed tokens with UTC expiration (`<payload_b64>.<sig_b64>`).
- **HTTP Authorization Header**: `Authorization: Bearer <token>` or `X-Admin-Token: <token>`.
- **Status Codes**:
  - `401 Unauthorized`: Missing credentials, expired token, or invalid cryptographic signature. Includes `WWW-Authenticate: Bearer` header.
  - `403 Forbidden`: Authenticated user lacks administrative privileges (e.g., standard operator or viewer role).
- **Leakage Prevention**: Secrets, passwords, authorization headers, and internal stack traces are redacted and never returned in error responses.

### 3.1. `POST /api/auth/login`
Authenticates administrator credentials against the stored password hash.

- **Request Body**:
```json
{
  "username": "admin",
  "password": "your_secure_password"
}
```
- **Success Response (`200 OK`)**:
```json
{
  "access_token": "eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImlhdCI6MTc2MDAwMDAwMCwiZXhwIjoxNzYwMDI4ODAwfQ.sig",
  "token_type": "bearer",
  "expires_in": 28800,
  "role": "admin",
  "username": "admin"
}
```

### 3.2. `GET /api/auth/me`
Retrieves authenticated user profile. Requires administrative token.

---

## 4. AI Governance Policies & Audit Trail Endpoints

### 4.1. `GET /api/policies`
Retrieves catalog of AI provider governance policies. Supports filtering.
- **Query Parameters**:
  - `is_enabled` (optional boolean): Filter by active status.
  - `approval_status` (optional string): Filter by `approved`, `unapproved`, `blocked`, `restricted`.
  - `search` (optional string): Search by provider name, description, or policy rule.

### 4.2. `GET /api/policies/summary`
Returns aggregate statistics of approved, unapproved, and disabled AI provider policies.

### 4.3. `GET /api/policies/{policy_id}`
Retrieves a specific policy by UUID or external identifier (`POL-...`).

### 4.4. `POST /api/policies`
Creates a new AI governance policy. **Requires admin authorization (`401/403`).**
- **Request Body**:
```json
{
  "provider_name": "Anthropic",
  "domain_signatures": ["anthropic.com", "claude.ai", "api.anthropic.com"],
  "approval_status": "approved",
  "is_enabled": true,
  "policy_rule": "POLICY-AI-00: Approved Enterprise Provider",
  "description": "Authorized enterprise LLM subscription for engineering teams."
}
```
- **Success Response (`201 Created`)**: Returns created `PolicyResponse`. Automatically logs audit record with `outcome: "SUCCESS"`.

### 4.5. `PUT /api/policies/{policy_id}`
Updates policy configuration, domains, or rule descriptions. **Requires admin authorization (`401/403`).**
- **Success Response (`200 OK`)**: Returns updated `PolicyResponse`. Audit record logs sanitized previous and new states.

### 4.6. `PATCH /api/policies/{policy_id}/status`
Quickly toggles approval status between `approved` and `unapproved` / `blocked`. **Requires admin authorization (`401/403`).**
- **Request Body**:
```json
{
  "approval_status": "blocked",
  "notes": "Emergency restriction per security incident SEC-104."
}
```

### 4.7. `POST /api/policies/{policy_id}/disable`
Safely disables an active policy without deleting history. **Requires admin authorization (`401/403`).**

### 4.8. `DELETE /api/policies/{policy_id}`
Deletes a policy record after recording the deletion event in the audit trail. **Requires admin authorization (`401/403`).**

### 4.9. `GET /api/policies/audit-logs`
Retrieves chronological audit trail of all administrative actions. **Requires admin authorization (`401/403`).**
- **Query Parameters**:
  - `skip` (optional integer, default 0, min 0): Number of records to skip for pagination.
  - `limit` (optional integer, default 50, max 500): Number of records per page.
- **Success Response (`200 OK`)**:
```json
[
  {
    "id": "c1f7b8d4-5a9e-4b72-a1f6-9c4e2b8d0a1f",
    "policyId": "d2e3f4a5-b6c7-4d8e-9f0a-1b2c3d4e5f6a",
    "action": "status_change",
    "providerName": "Anthropic",
    "previousState": {
      "approval_status": "approved"
    },
    "newState": {
      "approval_status": "blocked",
      "outcome": "SUCCESS"
    },
    "performedBy": "admin",
    "details": "Outcome: SUCCESS. Approval status changed from 'approved' to 'blocked'.",
    "outcome": "SUCCESS",
    "timestamp": "2026-10-10T04:15:30Z"
  }
]
```
- **Audit Immutability**: Ordinary users cannot alter or delete audit records. No mutation or deletion endpoints exist for audit logs.

---

## 5. Traffic Ingestion, Inventory, Risks, & Reports Endpoints

### 5.1. `POST /api/traffic/analyze`
Upload a capture file (`.csv`, `.json`, `.jsonl`, `.ndjson`, `.pcap`, `.pcapng`) for analysis and PostgreSQL persistence.
- **Content-Type**: `multipart/form-data`
- **Response (`201 Created`)**: Returns `TrafficAnalysisResponse` including execution ID, valid record count, and computed `summary`.

### 5.2. `GET /api/dashboard/stats`
Returns live operational summary metrics strictly calculated from database records:
- `valid_records`: Total valid network events analyzed.
- `aiRelatedRecords`: Records targeting confirmed AI providers.
- `totalAiEndpoints`: Distinct AI destination domains cataloged.
- `activeProvidersCount`: Distinct active AI providers observed.
- `unapprovedEndpointsCount`: Unapproved shadow AI endpoints detected.
- `flaggedRiskCount`: Total active security/policy risk findings.
- `riskBreakdown`: Severity counts (`critical`, `high`, `medium`, `low`).
- `providerDistribution`: Traffic breakdown by AI provider.

### 5.3. `GET /api/inventory` & `GET /api/inventory/{endpoint_id}`
Returns cataloged generative AI endpoints, confidence scores, observed byte totals, approval status, and detailed risk factors.

### 5.4. `GET /api/risks`
Returns all security risk assessments derived from endpoint telemetry, egress volumes, and unapproved shadow AI classifications.

### 5.5. `GET /api/reports/metrics`
Calculates empirical precision, recall, false-positive rate, and provider identification accuracy benchmarks on versioned ground-truth datasets. Missing metrics are returned as `null` and displayed as `"Not available"`.

### 5.6. `GET /health`
Returns health check status for backend application and PostgreSQL database connection pool independently.

---

## 6. Standard Error Responses & Privacy Guarantees

All error responses follow the standard format:
```json
{
  "detail": "Human-readable description of the error."
}
```

- `400 Bad Request`: Syntax or format errors.
- `401 Unauthorized`: Missing or invalid authentication token.
- `403 Forbidden`: Insufficient user privileges.
- `404 Not Found`: Unknown resource identifier.
- `409 Conflict`: Duplicate active policy for provider.
- `413 Request Entity Too Large`: File exceeds upload limits (50 MB).
- `500 Internal Server Error`: Generic internal error without internal stack trace leakage.

### Privacy Guarantees
- Raw sensitive headers (`Authorization`, `Cookie`) and tokens are never written to audit logs or diagnostic responses.
- Database rollbacks are triggered on transactional failures to prevent partial writes.

---

## 7. Clean Operational Commands

### Development & Container Startup
```bash
# Clean container rebuild and startup
docker compose down -v
docker compose up --build -d

# Verify container health
docker compose ps
curl http://localhost:8000/health
```

### Database Migrations
```bash
# Run pending migrations
docker compose exec backend alembic upgrade head

# Rollback one migration revision if needed
docker compose exec backend alembic downgrade -1
```

### Test Suites Execution
```bash
# Backend pytest suite
docker compose exec backend pytest -v

# Frontend unit & integration tests
cd frontend && npm test -- --run

# Frontend production build
cd frontend && npm run build
```

### Clean Shutdown
```bash
docker compose down
```
