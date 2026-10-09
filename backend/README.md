# Shadow AI Detector - Traffic Analyzer Backend

Backend service for the **Shadow AI Detector** platform, responsible for analyzing network traffic, identifying unauthorized AI service usage, and evaluating organizational AI risk.

---

## Architecture & Project Structure

The backend is structured according to modular FastAPI production conventions with PostgreSQL persistence via SQLAlchemy and Alembic:

```text
shadow-ai-detector/
├── docker-compose.yml           # Multi-container orchestration (PostgreSQL + FastAPI)
├── .gitignore                   # Repository git exclusions
└── backend/
    ├── Dockerfile               # Container build definition for backend
    ├── .dockerignore            # Container build exclusions
    ├── alembic.ini              # Alembic configuration
    ├── alembic/                 # Database migration scripts
    │   ├── env.py               # Dynamic settings and model metadata binding
    │   └── versions/            # Migration version files
    │       └── 574751755ecb_create_traffic_analyses_and_records_.py
    ├── app/
    │   ├── __init__.py
    │   ├── main.py              # FastAPI application entrypoint & middleware
    │   ├── api/                 # API routers and endpoints
    │   │   ├── __init__.py
    │   │   └── v1/
    │   │       ├── __init__.py
    │   │       ├── router.py    # Centralized v1 router
    │   │       └── endpoints/
    │   │           ├── __init__.py
    │   │           └── health.py # Health check endpoint with real DB verification
    │   ├── core/                # Core configuration and logging
    │   │   ├── __init__.py
    │   │   ├── config.py        # Pydantic Settings management (env vars)
    │   │   └── logging.py       # Structured logging configuration
    │   ├── db/                  # Database connectivity & session handling
    │   │   ├── __init__.py
    │   │   ├── base.py          # SQLAlchemy DeclarativeBase
    │   │   └── session.py       # Engine, sessionmaker, get_db & health check
    │   ├── models/              # SQLAlchemy ORM models
    │   │   ├── __init__.py
    │   │   └── traffic.py       # TrafficAnalysis & TrafficRecord models
    │   ├── schemas/             # Pydantic validation schemas
    │   │   ├── __init__.py
    │   │   └── health.py        # Health response schemas
    │   └── services/            # Business logic services (upcoming phases)
    │       └── __init__.py
    ├── tests/                   # Automated test suite
    │   ├── __init__.py
    │   ├── conftest.py          # TestClient and isolated DB session fixtures
    │   ├── test_health.py       # Health check and root endpoint tests
    │   ├── test_models.py       # Model instantiation and default value tests
    │   └── test_db_operations.py # Isolated DB CRUD, cascade and relationship tests
    ├── .env.example             # Example environment variables
    ├── requirements.txt         # Production and development dependencies
    └── README.md                # Documentation and run instructions
```

---

## Database Architecture

### Models

1. **`TrafficAnalysis` (`traffic_analyses`)**:
   - `id`: Primary key (`UUID`, auto-generated).
   - `original_filename`: Source capture filename (`VARCHAR(255)`, not null).
   - `file_format`: File format, e.g. `pcap`, `csv`, `json`, `netflow` (`VARCHAR(50)`, not null).
   - `status`: Processing state (`pending`, `processing`, `completed`, `failed`, indexed).
   - `total_rows_received`: Row count from source input (`INTEGER`, default `0`).
   - `valid_rows`: Processed rows meeting parsing criteria (`INTEGER`, default `0`).
   - `rejected_rows`: Corrupt or unparseable rows (`INTEGER`, default `0`).
   - `error_details`: Exception or validation trace for failed runs (`TEXT`, nullable).
   - `created_at`: UTC timestamp of task creation (`TIMESTAMP WITH TIME ZONE`, indexed).
   - `updated_at`: UTC timestamp of last update (`TIMESTAMP WITH TIME ZONE`).
   - Relationship: One-to-many relationship with `TrafficRecord` with cascading delete (`cascade="all, delete-orphan"`).

2. **`TrafficRecord` (`traffic_records`)**:
   - `id`: Primary key (`UUID`, auto-generated).
   - `analysis_id`: Foreign key referencing `traffic_analyses.id` (`UUID`, cascade on delete, indexed).
   - `timestamp`: Event or packet capture timestamp (`TIMESTAMP WITH TIME ZONE`, nullable, indexed).
   - `source_ip`: Client IP address supporting IPv4/IPv6 (`VARCHAR(45)`, nullable, indexed).
   - `destination_ip`: Target host IP address (`VARCHAR(45)`, nullable, indexed).
   - `destination_domain`: Target domain name (`VARCHAR(255)`, nullable, indexed).
   - `destination_port`: Destination port number (`INTEGER`, nullable).
   - `protocol`: Transport/Application protocol (`VARCHAR(20)`, nullable).
   - `bytes_sent`: Outbound bytes (`BIGINT`, nullable).
   - `bytes_received`: Inbound bytes (`BIGINT`, nullable).
   - `http_method`: HTTP method (`VARCHAR(10)`, nullable).
   - `http_uri`: Request path/URI (`TEXT`, nullable).
   - `http_status_code`: HTTP response status (`INTEGER`, nullable).
   - `user_agent`: Client user agent string (`TEXT`, nullable).
   - `sni_hostname`: TLS Server Name Indication header (`VARCHAR(255)`, nullable, indexed).
   - Composite Indexes: `(analysis_id, timestamp)`, `(destination_domain, timestamp)`.

---

## Traffic Record Schema & Validation Rules

Incoming network records are parsed, alias-normalized, and validated using Pydantic schemas in `app/schemas/traffic.py`.

### 1. Canonical Fields & Validation

| Field | Type | Required? | Validation Rules |
|---|---|---|---|
| `timestamp` | `datetime` (UTC) | Optional | Accepts ISO 8601 strings, UNIX epoch seconds, epoch milliseconds, and standard datetime strings. Normalized to UTC timezone. |
| `source_ip` | `str` | Optional | Validated against IPv4 and IPv6 syntax via Python `ipaddress`. |
| `destination_ip` | `str` | Conditional* | Validated IPv4 or IPv6 address. (*At least one of `destination_ip` or `destination_domain` must be provided). |
| `destination_domain` | `str` | Conditional* | Validated domain name or FQDN (<= 253 chars, labels <= 63 chars, no URL schemes or paths, lowercase). (*At least one of `destination_ip` or `destination_domain` must be provided). |
| `destination_port` | `int` | Optional | Integer in range `1 <= port <= 65535`. |
| `protocol` | `str` | Optional | Uppercase transport/app protocol (`TCP`, `UDP`, `TLS`, `HTTP`, etc.). Whitespace disallowed. |
| `bytes_sent` | `int` | Optional | Non-negative integer (`>= 0`). |
| `bytes_received` | `int` | Optional | Non-negative integer (`>= 0`). |
| `http_method` | `str` | Optional | Uppercase standard HTTP verb (`GET`, `POST`, `PUT`, `DELETE`, etc.). |
| `http_uri` | `str` | Optional | Preserved raw request path or URI. |
| `http_status_code` | `int` | Optional | Integer between `100` and `599`. |
| `user_agent` | `str` | Optional | Raw client user-agent string. |
| `sni_hostname` | `str` | Optional | Lowercase TLS Server Name Indication domain. |
| `extra_metadata` | `dict` | Optional | Any extraneous log columns are preserved here without causing validation failure. |

### 2. Supported Column Aliases (Case-Insensitive)

- **Timestamp**: `time`, `ts`, `datetime`, `date_time`, `@timestamp`, `event_time`, `packet_time`
- **Source IP**: `src_ip`, `srcip`, `client_ip`, `clientip`, `src_addr`, `source_address`, `src`, `source`
- **Destination IP**: `dst_ip`, `dstip`, `dest_ip`, `server_ip`, `dst_addr`, `destination_address`, `dst`, `destination`
- **Destination Domain**: `dst_domain`, `dest_domain`, `domain`, `host`, `hostname`, `server_name`, `target_domain`, `query`
- **Destination Port**: `dst_port`, `dest_port`, `dstport`, `dport`, `port`, `server_port`
- **Protocol**: `proto`, `ip_proto`, `transport`
- **Bytes Sent**: `sent_bytes`, `bytes_out`, `bytes_tx`, `tx_bytes`, `out_bytes`, `payload_bytes_sent`
- **Bytes Received**: `recv_bytes`, `received_bytes`, `bytes_in`, `bytes_rx`, `rx_bytes`, `in_bytes`, `payload_bytes_recv`
- **HTTP / TLS**: `method`/`verb`, `uri`/`url`/`path`, `status`/`status_code`/`response_code`, `ua`/`agent`, `sni`/`tls_sni`/`server_name_indication`

### 3. Validation & Sanitization Policies

1. **Empty Values**: Empty strings (`""`, `"   "`), hyphens (`"-"`), and sentinels (`"null"`, `"none"`, `"N/A"`) are converted to `None` rather than triggering type conversion errors.
2. **Missing Metadata**: A record is never rejected merely because optional fields (like `source_ip`, `protocol`, or `bytes`) are absent.
3. **Required Identifiers**: To be actionable for Shadow AI detection, each record must specify at least one target: `destination_domain` OR `destination_ip`.
4. **Secret Redaction**: When validation fails, any field matching credential patterns (`password`, `secret`, `token`, `auth`, `cookie`, `key`) is redacted to `[REDACTED]` in the error report.

---

## Traffic File Ingestion Service

Implemented in [`app/services/ingestion.py`](file:///c:/projects/shadow-ai-detector/backend/app/services/ingestion.py), the ingestion service is decoupled from HTTP transport and can parse bytes, strings, or file streams directly.

### Supported File Formats
1. **CSV (`.csv`)**: Header row required. Parses arbitrary delimiter formats and handles duplicate column headers safely using Pandas with `dtype=str`. Supports UTF-8 and UTF-8-SIG (Excel BOM).
2. **JSON (`.json`)**:
   - Standard array of objects: `[ { ... }, { ... } ]`
   - Wrapper objects containing a records array: `{"records": [...]}` or `{"traffic": [...]}` or `{"data": [...]}`
   - Single object record: `{ ... }`
3. **JSON Lines (`.jsonl`, `.ndjson`)**: One JSON object per line.
4. **Fallback Handling**: If a file with a `.json` extension contains line-delimited JSON, it falls back to NDJSON parsing automatically.

### Limits & Safeguards
- **Maximum Upload Size**: Configurable via `MAX_UPLOAD_SIZE_BYTES` (default: 50 MB / `52,428,800` bytes). Rejects oversized files with `FileTooLargeError`.
- **Maximum Row Count**: Configurable via `MAX_INGESTION_ROWS` (default: `100,000` rows). Rejects unbounded files with `RowLimitExceededError`.
- **Empty Files**: Files with 0 bytes or whitespace only raise `EmptyFileError`.
- **Malformed Files**: Corrupt CSV/JSON syntax raises `FileParsingError`.
- **Line Tracking**: Returns original row numbers (CSV header = line 1, data starts on line 2; JSON = line 1..N).

---

## Traffic Analysis API Endpoints

### 1. `POST /api/traffic/analyze`
Accepts a single `.csv`, `.json`, `.jsonl`, or `.ndjson` capture file via multipart form data (`file`), parses rows, and persists valid records to PostgreSQL.

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/traffic/analyze" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@proxy_logs.csv;type=text/csv"
```

**Example Response (`201 Created`):**
```json
{
  "id": "e8d67a14-8f4b-4b12-b13c-7501062089f3",
  "original_filename": "proxy_logs.csv",
  "file_format": "csv",
  "status": "completed",
  "total_rows_received": 3,
  "valid_rows": 2,
  "rejected_rows": 1,
  "error_details": null,
  "created_at": "2026-10-09T23:00:00Z",
  "updated_at": "2026-10-09T23:00:01Z",
  "summary": {
    "total_valid_records": 2,
    "total_bytes_sent": 2000,
    "total_bytes_received": 57000,
    "unique_source_ips": 2,
    "unique_destination_domains": 2,
    "unique_destination_ips": 0,
    "protocols": ["TCP"],
    "earliest_timestamp": "2026-10-09T18:00:00Z",
    "latest_timestamp": "2026-10-09T18:01:00Z"
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

---

### 2. `GET /api/traffic/{analysis_id}`
Retrieves a single saved analysis by ID, returning its status, file metadata, counts, and actual metrics derived from PostgreSQL.

**Example Request:**
```bash
curl "http://localhost:8000/api/traffic/e8d67a14-8f4b-4b12-b13c-7501062089f3"
```

**Example Response (`200 OK`):**
```json
{
  "id": "e8d67a14-8f4b-4b12-b13c-7501062089f3",
  "original_filename": "proxy_logs.csv",
  "file_format": "csv",
  "status": "completed",
  "total_rows_received": 3,
  "valid_rows": 2,
  "rejected_rows": 1,
  "error_details": null,
  "created_at": "2026-10-09T23:00:00Z",
  "updated_at": "2026-10-09T23:00:01Z",
  "summary": {
    "total_valid_records": 2,
    "total_bytes_sent": 2000,
    "total_bytes_received": 57000,
    "unique_source_ips": 2,
    "unique_destination_domains": 2,
    "unique_destination_ips": 0,
    "protocols": ["TCP"],
    "earliest_timestamp": "2026-10-09T18:00:00Z",
    "latest_timestamp": "2026-10-09T18:01:00Z"
  }
}
```
*Returns `404 Not Found` if `analysis_id` does not exist.*

---

### 3. `GET /api/traffic/{analysis_id}/records`
Returns individual persisted records for an analysis with pagination support.

**Parameters:**
- `limit`: Number of records to return (Default: `50`, Min: `1`, Max: `500`).
- `offset`: Zero-based pagination offset (Default: `0`).

**Example Request:**
```bash
curl "http://localhost:8000/api/traffic/e8d67a14-8f4b-4b12-b13c-7501062089f3/records?limit=2&offset=0"
```

**Example Response (`200 OK`):**
```json
{
  "analysis_id": "e8d67a14-8f4b-4b12-b13c-7501062089f3",
  "total_records": 2,
  "limit": 2,
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

### 4. `GET /api/traffic`
Returns analysis run history ordered by creation time descending.

**Parameters:**
- `limit`: Number of jobs per page (Default: `20`, Min: `1`, Max: `100`).
- `offset`: Zero-based pagination offset (Default: `0`).

**Example Request:**
```bash
curl "http://localhost:8000/api/traffic?limit=10&offset=0"
```

**Example Response (`200 OK`):**
```json
{
  "total_analyses": 5,
  "limit": 10,
  "offset": 0,
  "analyses": [
    {
      "id": "e8d67a14-8f4b-4b12-b13c-7501062089f3",
      "original_filename": "proxy_logs.csv",
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

### 5. `GET /api/traffic/{analysis_id}/summary`
Returns comprehensive aggregated summary statistics calculated strictly from actual persisted records for a single analysis run.

**Example Request:**
```bash
curl "http://localhost:8000/api/traffic/e8d67a14-8f4b-4b12-b13c-7501062089f3/summary"
```

**Example Response (`200 OK`):**
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
*Returns `404 Not Found` if `analysis_id` does not exist.*

---

### 6. `GET /api/dashboard/stats`
Provides real summary statistics for the frontend Overview and Dashboard pages. Calculates aggregate statistics from saved database records.

**Parameters:**
- `analysis_id` (optional): UUID of a specific analysis run. If provided, statistics are scoped exclusively to that run (`scope="selected_analysis"`). If omitted, statistics aggregate across all saved analyses in the database (`scope="all_analyses"`).

**Example Request (All Analyses):**
```bash
curl "http://localhost:8000/api/dashboard/stats"
```

**Example Response (`200 OK`):**
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

**Example Request (Scoped to Single Analysis):**
```bash
curl "http://localhost:8000/api/dashboard/stats?analysis_id=e8d67a14-8f4b-4b12-b13c-7501062089f3"
```
*Returns `404 Not Found` if `analysis_id` is supplied but does not exist in the database.*

---

## Traffic Summary Statistics & Calculation Rules

The summary statistics service adheres to strict calculation rules grounded strictly in real database records:

### 1. Distinction Between Record Counts & Network Connections
- **Log Records vs. Network Connections**: `valid_records` measures individual validated log entries ingested from CSV/JSON captures. A CSV row or JSON entry represents an event record; it must **not** be assumed to map 1:1 to discrete TCP socket connections or HTTP sessions unless explicitly guaranteed by the capture source format.
- Every summary response includes `record_type_note` explicitly stating this distinction.

### 2. Missing Metadata (Unknown vs. Zero)
- Missing values (`NULL`) in optional fields (`bytes_sent`, `bytes_received`, `timestamp`, `protocol`, `source_ip`, `destination_domain`, `destination_ip`) are treated as **unknown**, never as zero.
- **Byte Totals**: `total_bytes_sent` and `total_bytes_received` are calculated strictly as `SUM(...)` over rows where the value is non-null. Rows with omitted byte values are excluded from the sum (not counted as 0).
- **Completeness Tracking**: Omissions are explicitly tracked via `missing_bytes_sent_count`, `missing_bytes_received_count`, `missing_timestamp_count`, and `missing_protocol_count`.

### 3. Calculation Field Matrix

| Field | Source / Rule | Handling of Missing / Null Values |
|---|---|---|
| `total_records_received` | `TrafficAnalysis.total_rows_received` | Always integer >= 0 |
| `valid_records` | `COUNT(TrafficRecord.id)` | Integer >= 0 |
| `rejected_records` | `TrafficAnalysis.rejected_rows` | Integer >= 0 |
| `unique_source_ips` | `COUNT(DISTINCT TrafficRecord.source_ip)` | Nulls explicitly excluded |
| `unique_destination_ips` | `COUNT(DISTINCT TrafficRecord.destination_ip)` | Nulls explicitly excluded |
| `unique_destination_domains` | `COUNT(DISTINCT TrafficRecord.destination_domain)` | Nulls explicitly excluded |
| `total_bytes_sent` | `SUM(TrafficRecord.bytes_sent)` | Nulls excluded from sum; 0 if no values |
| `total_bytes_received` | `SUM(TrafficRecord.bytes_received)` | Nulls excluded from sum; 0 if no values |
| `missing_bytes_sent_count` | `valid_records - COUNT(TrafficRecord.bytes_sent)` | Tracks records with omitted bytes_sent |
| `missing_bytes_received_count` | `valid_records - COUNT(TrafficRecord.bytes_received)` | Tracks records with omitted bytes_received |
| `protocol_distribution` | `GROUP BY protocol` | Normalized to uppercase; maps `{ [protocol]: count }` |
| `missing_protocol_count` | Count of rows where `protocol IS NULL` | Tracked separately from observed protocols |
| `earliest_timestamp` | `MIN(TrafficRecord.timestamp)` | Null if no records with timestamps |
| `latest_timestamp` | `MAX(TrafficRecord.timestamp)` | Null if no records with timestamps |
| `records_with_timestamp` | `COUNT(TrafficRecord.timestamp)` | Count of records with non-null timestamp |
| `missing_timestamp_count` | `valid_records - records_with_timestamp` | Count of records with missing timestamp |

---

## Getting Started

### 1. Prerequisites
- **Python**: 3.10+ (tested on Python 3.13)
- **Git**
- **Docker & Docker Compose** (or local PostgreSQL 14+)

---

### 2. Starting PostgreSQL

#### Option A: Using Docker Compose (Recommended)
To run only the PostgreSQL container in the background with persistent volume:

```bash
docker compose up -d db
```

#### Option B: Full Application Stack via Docker Compose
To run both the PostgreSQL database and FastAPI backend:

```bash
docker compose up -d
```

#### Option C: Native PostgreSQL Service
Ensure your local PostgreSQL server is running and create the database:

```sql
CREATE DATABASE shadow_ai_detector;
```

---

### 3. Local Virtual Environment Setup

Navigate to the `backend/` directory:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:
- **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Linux / macOS**:
  ```bash
  source .venv/bin/activate
  ```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

### 4. Configuring Environment Variables

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Configure your PostgreSQL credentials in `.env`:

```env
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=shadow_ai_detector
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/shadow_ai_detector
```

> [!NOTE]
> Database credentials are never hardcoded or tracked in Git. The `.env` file is excluded in `.gitignore`.

---

### 5. Database Schema Initialization & Migrations

Alembic manages all schema migrations. The migration runner reads credentials directly from your environment settings.

To apply all migrations to the latest revision:

```bash
alembic upgrade head
```

To create a new migration after updating SQLAlchemy models:

```bash
alembic revision --autogenerate -m "describe changes"
```

To roll back a migration:

```bash
alembic downgrade -1
```

---

### 6. Running the Application

Start the development server with Uvicorn:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Accessible endpoints:
- **Root**: [http://localhost:8000/](http://localhost:8000/)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### 7. Running Tests

The test suite includes:
- **Unit Tests**: Model instantiation, field types, enums, representations.
- **Health Verification**: Endpoints under both configured and unconfigured states.
- **Isolated DB Operations**: CRUD, relationships, cascade deletes, and sparse/nullable field tests run inside an isolated transaction rollback on PostgreSQL to prevent database pollution.

Run all tests:

```bash
$env:PYTHONPATH="backend"
pytest -v
```

---

## Health Check Details

`GET /health` verifies component availability in real time:
- `components.app`: Process status (`up`).
- `components.database`:
  - `up`: Executes real `SELECT 1` ping against PostgreSQL.
  - `not_configured`: No database credentials configured.
  - `down`: Database configured but unreachable.
