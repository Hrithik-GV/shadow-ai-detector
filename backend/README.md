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
