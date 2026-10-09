# Shadow AI Detector - Traffic Analysis API Contract

**Version:** `0.1.0`  
**Base URL:** `http://localhost:8000`  
**API Prefixes:**
- Main API routes: `/api/traffic`, `/api/dashboard`
- Versioned aliases: `/api/v1/traffic`, `/api/v1/dashboard`
- Health check: `/health`, `/api/v1/health`

---

## 1. Overview & Integration Notes

This document specifies the exact REST API contract implemented by the Traffic Analyzer backend module of the Shadow AI Detector. This contract is the authoritative reference for the React frontend application.

### Important Data Semantics
1. **Record Counts vs. Network Connections**:
   - `valid_records` / `total_valid_records` represents the number of parsed, validated log entries/events ingested from capture files.
   - A single log entry does **not** necessarily map 1:1 to a distinct TCP connection or HTTP session unless guaranteed by the source capture format. Every summary response includes `record_type_note` reminding clients of this distinction.
2. **Missing Metadata Handling**:
   - Missing optional values (`null`) are treated as **unknown**, not zero.
   - Byte counts (`total_bytes_sent`, `total_bytes_received`) sum only records where non-null values were provided. Omitted byte counts are tracked in `missing_bytes_sent_count` and `missing_bytes_received_count`.
   - Unique IP and domain counts strictly ignore `null` values.

---

## 2. Ingestion Format & Record Schema

### Supported File Types
- **CSV (`.csv`)**: Must include a header row. Case-insensitive header aliases are automatically resolved.
- **JSON (`.json`)**: Array of record objects (`[{...}]`), wrapper object with records array (`{"records": [...]}`), or single record object (`{...}`).
- **JSON Lines (`.jsonl`, `.ndjson`)**: One JSON object per line.
- **BOM Handling**: UTF-8 BOM byte marks are automatically stripped.

### Supported Field Names & Aliases

| Canonical Field | Accepted Aliases | Type | Required? | Validation Rules |
|---|---|---|---|---|
| `destination_domain` | `dest_domain`, `domain`, `host`, `hostname` | string | **Required if `dest_ip` missing** | Valid domain name format (e.g. `api.openai.com`), max 255 chars |
| `destination_ip` | `dest_ip`, `dst_ip`, `destination_address`, `dst` | string | **Required if `domain` missing** | Valid IPv4 or IPv6 address string |
| `source_ip` | `src_ip`, `src`, `source_address`, `client_ip` | string | Optional | Valid IPv4 or IPv6 address string |
| `destination_port` | `dest_port`, `dst_port`, `port`, `dport` | integer | Optional | Port integer between `1` and `65535` |
| `protocol` | `proto`, `transport_protocol`, `network_protocol` | string | Optional | Normalized to uppercase (e.g., `TCP`, `UDP`, `TLS`, `HTTP`) |
| `bytes_sent` | `bytes_out`, `out_bytes`, `bytes_tx`, `tx_bytes`, `bytes_uploaded` | integer | Optional | Integer `>= 0` |
| `bytes_received` | `bytes_in`, `in_bytes`, `bytes_rx`, `rx_bytes`, `bytes_downloaded` | integer | Optional | Integer `>= 0` |
| `timestamp` | `time`, `ts`, `event_time`, `datetime`, `date_time`, `@timestamp` | string / number | Optional | ISO 8601, RFC 2822, or UNIX epoch seconds/milliseconds. Normalized to UTC. |
| `http_method` | `method` | string | Optional | Uppercase method: `GET`, `POST`, `PUT`, `DELETE`, etc. |
| `http_uri` | `uri`, `path`, `url` | string | Optional | Target request URI path |
| `http_status_code` | `status_code`, `status` | integer | Optional | Valid HTTP status code `100` to `599` |
| `user_agent` | `useragent`, `http_user_agent` | string | Optional | Raw User-Agent string |
| `sni_hostname` | `sni`, `tls_sni` | string | Optional | TLS Server Name Indication string |

---

## 3. Endpoints Specification

### 3.1. `POST /api/traffic/analyze`
Upload a network traffic capture file for validation, normalization, and PostgreSQL persistence.

- **Method:** `POST`
- **Path:** `/api/traffic/analyze` (or `/api/v1/traffic/analyze`)
- **Content-Type:** `multipart/form-data`
- **Request Body:**
  - `file`: (binary, **required**) The capture file to upload (`.csv`, `.json`, `.jsonl`, `.ndjson`).

#### Success Response (`201 Created`):
```json
{
  "id": "e8d67a14-8f4b-4b12-b13c-7501062089f3",
  "original_filename": "firewall_logs.csv",
  "file_format": "csv",
  "status": "completed",
  "total_rows_received": 3,
  "valid_rows": 2,
  "rejected_rows": 1,
  "error_details": null,
  "created_at": "2026-10-09T23:00:00Z",
  "updated_at": "2026-10-09T23:00:01Z",
  "summary": {
    "total_records_received": 3,
    "valid_records": 2,
    "total_valid_records": 2,
    "rejected_records": 1,
    "unique_source_ips": 2,
    "unique_destination_ips": 0,
    "unique_destination_domains": 2,
    "total_bytes_sent": 2000,
    "total_bytes_received": 57000,
    "bytes_sent_reported_count": 2,
    "bytes_received_reported_count": 2,
    "missing_bytes_sent_count": 0,
    "missing_bytes_received_count": 0,
    "protocols": ["TCP"],
    "protocol_distribution": {
      "TCP": 2
    },
    "missing_protocol_count": 0,
    "earliest_timestamp": "2026-10-09T18:00:00Z",
    "latest_timestamp": "2026-10-09T18:01:00Z",
    "records_with_timestamp": 2,
    "missing_timestamp_count": 0,
    "record_type_note": "Counts represent ingested log records/events, which may or may not map 1:1 to unique TCP/network connections.",
    "byte_calculation_note": "Missing byte counts are treated as unknown (null) and excluded from summation, not counted as zero."
  },
  "rejected_records": [
    {
      "row_index": 3,
      "errors": [
        {
          "field": "destination_ip",
          "message": "Invalid IP address: '999.999.999.999'",
          "invalid_value": "999.999.999.999"
        }
      ],
      "raw_record": {
        "src_ip": "10.0.0.1",
        "destination_ip": "999.999.999.999",
        "Authorization": "[REDACTED]"
      }
    }
  ]
}
```

#### Error Responses:
- `400 Bad Request`:
  ```json
  {"detail": "Unsupported file extension '.xml'. Supported formats: .csv, .json, .jsonl, .ndjson"}
  ```
- `413 Request Entity Too Large`:
  ```json
  {"detail": "Uploaded file size (52.5 MB) exceeds maximum limit of 50.0 MB"}
  ```
- `500 Internal Server Error`:
  ```json
  {"detail": "Database error during processing: ..."}
  ```

---

### 3.2. `GET /api/traffic/{analysis_id}`
Retrieve a single analysis job by its UUID, including file metadata, processing status, and real metrics summary.

- **Method:** `GET`
- **Path:** `/api/traffic/{analysis_id}` (or `/api/v1/traffic/{analysis_id}`)
- **Path Parameters:**
  - `analysis_id`: (UUID, **required**) Unique identifier of the analysis.

#### Success Response (`200 OK`):
```json
{
  "id": "e8d67a14-8f4b-4b12-b13c-7501062089f3",
  "original_filename": "firewall_logs.csv",
  "file_format": "csv",
  "status": "completed",
  "total_rows_received": 3,
  "valid_rows": 2,
  "rejected_rows": 1,
  "error_details": null,
  "created_at": "2026-10-09T23:00:00Z",
  "updated_at": "2026-10-09T23:00:01Z",
  "summary": { ... }
}
```

#### Error Responses:
- `404 Not Found`:
  ```json
  {"detail": "Analysis with ID '00000000-0000-0000-0000-000000000000' was not found"}
  ```

---

### 3.3. `GET /api/traffic/{analysis_id}/summary`
Retrieve dedicated summary statistics calculated from PostgreSQL for a specific analysis run.

- **Method:** `GET`
- **Path:** `/api/traffic/{analysis_id}/summary` (or `/api/v1/traffic/{analysis_id}/summary`)
- **Path Parameters:**
  - `analysis_id`: (UUID, **required**) Unique identifier of the analysis.

#### Success Response (`200 OK`):
```json
{
  "total_records_received": 3,
  "valid_records": 2,
  "total_valid_records": 2,
  "rejected_records": 1,
  "unique_source_ips": 2,
  "unique_destination_ips": 0,
  "unique_destination_domains": 2,
  "total_bytes_sent": 2000,
  "total_bytes_received": 57000,
  "bytes_sent_reported_count": 2,
  "bytes_received_reported_count": 2,
  "missing_bytes_sent_count": 0,
  "missing_bytes_received_count": 0,
  "protocols": ["TCP"],
  "protocol_distribution": {
    "TCP": 2
  },
  "missing_protocol_count": 0,
  "earliest_timestamp": "2026-10-09T18:00:00Z",
  "latest_timestamp": "2026-10-09T18:01:00Z",
  "records_with_timestamp": 2,
  "missing_timestamp_count": 0,
  "record_type_note": "Counts represent ingested log records/events, which may or may not map 1:1 to unique TCP/network connections.",
  "byte_calculation_note": "Missing byte counts are treated as unknown (null) and excluded from summation, not counted as zero."
}
```

---

### 3.4. `GET /api/traffic/{analysis_id}/records`
Retrieve individual persisted traffic flow records for an analysis run, with pagination support.

- **Method:** `GET`
- **Path:** `/api/traffic/{analysis_id}/records` (or `/api/v1/traffic/{analysis_id}/records`)
- **Path Parameters:**
  - `analysis_id`: (UUID, **required**) Unique identifier of the analysis.
- **Query Parameters:**
  - `limit`: (integer, optional, default: `50`, min: `1`, max: `500`) Number of records per page.
  - `offset`: (integer, optional, default: `0`, min: `0`) Zero-based page offset.

#### Success Response (`200 OK`):
```json
{
  "analysis_id": "e8d67a14-8f4b-4b12-b13c-7501062089f3",
  "total_records": 2,
  "limit": 50,
  "offset": 0,
  "records": [
    {
      "id": "18cfc527-2c93-4a11-b0fe-25a805fef914",
      "analysis_id": "e8d67a14-8f4b-4b12-b13c-7501062089f3",
      "timestamp": "2026-10-09T18:00:00Z",
      "source_ip": "192.168.1.50",
      "destination_ip": null,
      "destination_domain": "api.openai.com",
      "destination_port": 443,
      "protocol": "TCP",
      "bytes_sent": 1200,
      "bytes_received": 45000,
      "http_method": null,
      "http_uri": null,
      "http_status_code": null,
      "user_agent": null,
      "sni_hostname": null
    }
  ]
}
```

---

### 3.5. `GET /api/traffic`
Retrieve chronological history of all saved traffic analyses.

- **Method:** `GET`
- **Path:** `/api/traffic` (or `/api/v1/traffic`)
- **Query Parameters:**
  - `limit`: (integer, optional, default: `20`, min: `1`, max: `100`) Analyses per page.
  - `offset`: (integer, optional, default: `0`, min: `0`) Zero-based offset.

#### Success Response (`200 OK`):
```json
{
  "total_analyses": 1,
  "limit": 20,
  "offset": 0,
  "analyses": [
    {
      "id": "e8d67a14-8f4b-4b12-b13c-7501062089f3",
      "original_filename": "firewall_logs.csv",
      "file_format": "csv",
      "status": "completed",
      "total_rows_received": 3,
      "valid_rows": 2,
      "rejected_rows": 1,
      "error_details": null,
      "created_at": "2026-10-09T23:00:00Z",
      "updated_at": "2026-10-09T23:00:01Z"
    }
  ]
}
```

---

### 3.6. `GET /api/dashboard/stats`
Retrieve aggregated summary statistics for the frontend Overview and Dashboard cards.

- **Method:** `GET`
- **Path:** `/api/dashboard/stats` (or `/api/v1/dashboard/stats`)
- **Query Parameters:**
  - `analysis_id`: (UUID, optional) When supplied, scopes metrics to that specific analysis (`scope="selected_analysis"`). When omitted, aggregates across all analyses in PostgreSQL (`scope="all_analyses"`).

#### Success Response (`200 OK`):
```json
{
  "scope": "all_analyses",
  "analysis_id": null,
  "analyses_count": 5,
  "scope_description": "Statistics aggregated across all 5 saved analysis runs in the database.",
  "total_records_received": 15000,
  "valid_records": 14850,
  "rejected_records": 150,
  "unique_source_ips": 42,
  "unique_destination_ips": 88,
  "unique_destination_domains": 19,
  "total_bytes_sent": 14205000,
  "total_bytes_received": 95400200,
  "bytes_sent_reported_count": 14500,
  "bytes_received_reported_count": 14500,
  "missing_bytes_sent_count": 350,
  "missing_bytes_received_count": 350,
  "protocols": ["HTTP", "HTTPS", "TCP", "TLS"],
  "protocol_distribution": {
    "TCP": 8500,
    "TLS": 5000,
    "HTTPS": 1000,
    "HTTP": 350
  },
  "missing_protocol_count": 0,
  "earliest_timestamp": "2026-10-09T08:00:00Z",
  "latest_timestamp": "2026-10-09T22:30:00Z",
  "records_with_timestamp": 14850,
  "missing_timestamp_count": 0,
  "record_type_note": "Counts represent ingested log records/events, which may or may not map 1:1 to unique TCP/network connections.",
  "byte_calculation_note": "Missing byte counts are treated as unknown (null) and excluded from summation, not counted as zero."
}
```

---

### 3.7. `GET /health`
System operational status check reporting application and database components independently.

- **Method:** `GET`
- **Path:** `/health` (or `/api/v1/health`)

#### Success Response (`200 OK`):
```json
{
  "status": "healthy",
  "app_name": "Shadow AI Detector - Traffic Analyzer",
  "version": "0.1.0",
  "environment": "development",
  "components": {
    "app": {
      "status": "up",
      "details": "Service is running and responsive"
    },
    "database": {
      "status": "up",
      "details": "PostgreSQL connection pool healthy"
    }
  }
}
```
*(If the database is unreachable, `status` reports `"degraded"` and `components.database.status` reports `"down"` with connection error details, avoiding false healthy status).*

---

## 4. Standard Error Format

All error responses return standard FastAPI `HTTPException` payloads:

```json
{
  "detail": "Human-readable description of the error"
}
```

HTTP Status Codes used:
- `200 OK`: Successful retrieval.
- `201 Created`: Successful file upload and persistence.
- `400 Bad Request`: Malformed file syntax, unsupported extension, or empty upload.
- `404 Not Found`: Unknown `analysis_id`.
- `413 Request Entity Too Large`: File exceeds 50 MB or record count exceeds 100,000.
- `422 Unprocessable Entity`: Invalid query parameter format (e.g., non-integer limit, malformed UUID).
- `500 Internal Server Error`: Unexpected database failure or transactional rollback.

---

## 5. Security & Privacy Guarantees

1. **No Payload Leakage**: Raw sensitive headers (e.g., `Authorization`, `Cookie`) and request bodies are redacted during validation and are **never** logged or returned in error payloads.
2. **Credential Protection**: Database passwords and connection URIs are loaded exclusively via environment variables and never logged or exposed in API responses.
3. **CORS Restrictions**: Configured via `BACKEND_CORS_ORIGINS`. Default permitted origins include local React development servers (`http://localhost:3000`, `http://localhost:5173`).
