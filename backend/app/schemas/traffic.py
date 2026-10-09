import ipaddress
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid

import dateutil.parser
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# Common aliases for network traffic log columns across formats (CSV, JSON, Netflow, Bro/Zeek, Proxy)
COLUMN_ALIASES: Dict[str, str] = {
    # Timestamp aliases
    "time": "timestamp",
    "ts": "timestamp",
    "datetime": "timestamp",
    "date_time": "timestamp",
    "@timestamp": "timestamp",
    "event_time": "timestamp",
    "packet_time": "timestamp",
    "start_time": "timestamp",

    # Source IP aliases
    "src_ip": "source_ip",
    "srcip": "source_ip",
    "client_ip": "source_ip",
    "clientip": "source_ip",
    "source_address": "source_ip",
    "src_addr": "source_ip",
    "src": "source_ip",
    "source": "source_ip",

    # Destination IP aliases
    "dst_ip": "destination_ip",
    "dstip": "destination_ip",
    "dest_ip": "destination_ip",
    "server_ip": "destination_ip",
    "destination_address": "destination_ip",
    "dst_addr": "destination_ip",
    "dst": "destination_ip",
    "destination": "destination_ip",

    # Destination domain aliases
    "dst_domain": "destination_domain",
    "dest_domain": "destination_domain",
    "domain": "destination_domain",
    "host": "destination_domain",
    "hostname": "destination_domain",
    "server_name": "destination_domain",
    "target_domain": "destination_domain",
    "query": "destination_domain",

    # Destination port aliases
    "dst_port": "destination_port",
    "dest_port": "destination_port",
    "dstport": "destination_port",
    "dport": "destination_port",
    "port": "destination_port",
    "server_port": "destination_port",

    # Protocol aliases
    "proto": "protocol",
    "ip_proto": "protocol",
    "transport": "protocol",

    # Bytes sent / received aliases
    "sent_bytes": "bytes_sent",
    "bytes_out": "bytes_sent",
    "bytes_tx": "bytes_sent",
    "tx_bytes": "bytes_sent",
    "out_bytes": "bytes_sent",
    "payload_bytes_sent": "bytes_sent",
    "bytes_sent": "bytes_sent",

    "recv_bytes": "bytes_received",
    "received_bytes": "bytes_received",
    "bytes_in": "bytes_received",
    "bytes_rx": "bytes_received",
    "rx_bytes": "bytes_received",
    "in_bytes": "bytes_received",
    "payload_bytes_recv": "bytes_received",
    "bytes_received": "bytes_received",

    # Format-specific HTTP and TLS metadata aliases
    "method": "http_method",
    "verb": "http_method",
    "uri": "http_uri",
    "path": "http_uri",
    "url": "http_uri",
    "status": "http_status_code",
    "status_code": "http_status_code",
    "response_code": "http_status_code",
    "ua": "user_agent",
    "agent": "user_agent",
    "user_agent_string": "user_agent",
    "sni": "sni_hostname",
    "tls_sni": "sni_hostname",
    "server_name_indication": "sni_hostname",
}

EMPTY_STRING_SENTINELS: Set[str] = {
    "",
    "-",
    "none",
    "null",
    "nil",
    "n/a",
    "na",
    "undefined",
    "unknown",
}

SENSITIVE_FIELD_NAMES: Set[str] = {
    "password",
    "passwd",
    "secret",
    "token",
    "auth",
    "authorization",
    "cookie",
    "cookies",
    "api_key",
    "apikey",
    "credential",
    "credentials",
    "bearer",
    "session",
    "session_id",
}

VALID_HTTP_METHODS: Set[str] = {
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "PATCH",
    "HEAD",
    "OPTIONS",
    "CONNECT",
    "TRACE",
}

DOMAIN_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$|^localhost$"
)


def sanitize_record_for_logging(record: Dict[str, Any]) -> Dict[str, Any]:
    """Redacts sensitive values to prevent logging secrets or security credentials."""
    sanitized: Dict[str, Any] = {}
    for key, val in record.items():
        key_lower = str(key).lower()
        if any(sensitive in key_lower for sensitive in SENSITIVE_FIELD_NAMES):
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = val
    return sanitized


def parse_and_normalize_timestamp(val: Any) -> datetime:
    """Parses ISO 8601, UNIX epoch, and date strings, normalizing to UTC."""
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)

    if isinstance(val, (int, float)):
        # Epoch seconds or milliseconds
        ts = val / 1000.0 if val > 1e11 else float(val)
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    if isinstance(val, str):
        val_str = val.strip()
        # Check if numeric epoch string
        try:
            num = float(val_str)
            ts = num / 1000.0 if num > 1e11 else num
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except ValueError:
            pass

        # Parse formatted datetime string
        try:
            dt = dateutil.parser.parse(val_str)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception as exc:
            raise ValueError(f"Invalid timestamp format: '{val_str}'") from exc

    raise ValueError(f"Unsupported timestamp type: {type(val).__name__}")


class ValidationErrorDetail(BaseModel):
    """Specific field-level validation error."""
    field: Optional[str] = Field(None, description="Name of the invalid field")
    message: str = Field(..., description="Human-readable explanation of why validation failed")
    invalid_value: Optional[Any] = Field(None, description="The value that triggered the error")


class RecordValidationError(BaseModel):
    """Container for record rejection details, preserving row context safely."""
    row_index: Optional[int] = Field(None, description="0-indexed or 1-indexed row number in the source file")
    errors: List[ValidationErrorDetail] = Field(..., description="List of errors encountered in this record")
    raw_record: Dict[str, Any] = Field(..., description="Sanitized original row data")


class TrafficRecordInput(BaseModel):
    """Schema for parsing, alias normalizing, and validating an incoming traffic record."""
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    timestamp: Optional[datetime] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    destination_domain: Optional[str] = None
    destination_port: Optional[int] = None
    protocol: Optional[str] = None
    bytes_sent: Optional[int] = None
    bytes_received: Optional[int] = None

    # Format-specific HTTP / TLS fields
    http_method: Optional[str] = None
    http_uri: Optional[str] = None
    http_status_code: Optional[int] = None
    user_agent: Optional[str] = None
    sni_hostname: Optional[str] = None

    # Storage for unmapped/custom log attributes
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases_and_empty_values(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized: Dict[str, Any] = {}
        extras: Dict[str, Any] = {}
        known_canonical = {
            "timestamp",
            "source_ip",
            "destination_ip",
            "destination_domain",
            "destination_port",
            "protocol",
            "bytes_sent",
            "bytes_received",
            "http_method",
            "http_uri",
            "http_status_code",
            "user_agent",
            "sni_hostname",
        }

        for raw_k, v in data.items():
            clean_k = str(raw_k).strip().lower().replace("-", "_")

            # Clean empty strings and sentinels to None
            if isinstance(v, str) and v.strip().lower() in EMPTY_STRING_SENTINELS:
                v = None

            # Resolve canonical field name using alias mapping
            target_key = COLUMN_ALIASES.get(clean_k, clean_k)

            if target_key in known_canonical:
                # If canonical field not yet populated or was None, assign
                if target_key not in normalized or normalized[target_key] is None:
                    normalized[target_key] = v
            else:
                extras[raw_k] = v

        if extras:
            normalized["extra_metadata"] = extras

        return normalized

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, v: Any) -> Optional[datetime]:
        if v is None:
            return None
        return parse_and_normalize_timestamp(v)

    @field_validator("source_ip", "destination_ip", mode="before")
    @classmethod
    def validate_ip_address(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        v_str = str(v).strip()
        try:
            ip = ipaddress.ip_address(v_str)
            return str(ip)
        except ValueError:
            raise ValueError(f"Invalid IP address: '{v_str}'")

    @field_validator("destination_port", mode="before")
    @classmethod
    def validate_port(cls, v: Any) -> Optional[int]:
        if v is None:
            return None
        try:
            port_num = int(v)
        except (ValueError, TypeError):
            raise ValueError(f"Port must be a valid integer, received '{v}'")

        if port_num < 1 or port_num > 65535:
            raise ValueError(f"Port {port_num} is outside valid range (1-65535)")
        return port_num

    @field_validator("destination_domain", "sni_hostname", mode="before")
    @classmethod
    def validate_domain(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        domain = str(v).strip().lower().rstrip(".")

        if "://" in domain or "/" in domain:
            raise ValueError(f"Invalid domain format: '{v}' contains URL scheme or path separator")

        if len(domain) > 253:
            raise ValueError(f"Domain name exceeds 253 characters limit: '{domain}'")

        if not DOMAIN_REGEX.match(domain):
            raise ValueError(f"Invalid domain format: '{domain}'")

        return domain

    @field_validator("protocol", mode="before")
    @classmethod
    def validate_protocol(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        proto = str(v).strip().upper()
        if not proto:
            return None
        if " " in proto:
            raise ValueError(f"Invalid protocol: '{proto}' contains whitespace")
        return proto

    @field_validator("bytes_sent", "bytes_received", mode="before")
    @classmethod
    def validate_bytes(cls, v: Any) -> Optional[int]:
        if v is None:
            return None
        try:
            val = int(v)
        except (ValueError, TypeError):
            raise ValueError(f"Byte count must be an integer, received '{v}'")

        if val < 0:
            raise ValueError(f"Byte count cannot be negative: {val}")
        return val

    @field_validator("http_method", mode="before")
    @classmethod
    def validate_http_method(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        method = str(v).strip().upper()
        if method not in VALID_HTTP_METHODS:
            raise ValueError(f"Invalid HTTP method: '{method}'")
        return method

    @field_validator("http_status_code", mode="before")
    @classmethod
    def validate_http_status_code(cls, v: Any) -> Optional[int]:
        if v is None:
            return None
        try:
            status = int(v)
        except (ValueError, TypeError):
            raise ValueError(f"HTTP status code must be an integer, received '{v}'")

        if status < 100 or status > 599:
            raise ValueError(f"HTTP status code {status} is outside valid range (100-599)")
        return status

    @model_validator(mode="after")
    def validate_required_destination(self) -> "TrafficRecordInput":
        """A network flow record must have at least one target identifier to be actionable."""
        if not self.destination_domain and not self.destination_ip:
            raise ValueError(
                "Missing destination: at least 'destination_domain' or 'destination_ip' must be provided"
            )
        return self


class NormalizedTrafficRecord(BaseModel):
    """Standardized, validated traffic record model ready for downstream processing or persistence."""
    timestamp: Optional[datetime] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    destination_domain: Optional[str] = None
    destination_port: Optional[int] = None
    protocol: Optional[str] = None
    bytes_sent: Optional[int] = None
    bytes_received: Optional[int] = None

    # Format-specific metadata
    http_method: Optional[str] = None
    http_uri: Optional[str] = None
    http_status_code: Optional[int] = None
    user_agent: Optional[str] = None
    sni_hostname: Optional[str] = None

    # Retained extraneous fields
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_db_dict(self, analysis_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """Convert normalized record into a dictionary compatible with the TrafficRecord ORM model."""
        db_dict = {
            "timestamp": self.timestamp,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "destination_domain": self.destination_domain,
            "destination_port": self.destination_port,
            "protocol": self.protocol,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "http_method": self.http_method,
            "http_uri": self.http_uri,
            "http_status_code": self.http_status_code,
            "user_agent": self.user_agent,
            "sni_hostname": self.sni_hostname,
        }
        if analysis_id is not None:
            db_dict["analysis_id"] = analysis_id
        return db_dict


class TrafficRecordValidationResult(BaseModel):
    """Validation outcome for a single record row."""
    is_valid: bool
    record: Optional[NormalizedTrafficRecord] = None
    errors: List[ValidationErrorDetail] = Field(default_factory=list)
    row_index: Optional[int] = None


class TrafficAnalysisSummary(BaseModel):
    """Schema summarizing the results of a traffic analysis ingestion/validation run."""
    analysis_id: Optional[uuid.UUID] = None
    original_filename: str
    file_format: str
    status: str
    total_rows_received: int
    valid_rows: int
    rejected_rows: int
    sample_errors: List[RecordValidationError] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


def validate_traffic_record(
    raw_record: Dict[str, Any],
    row_index: Optional[int] = None,
) -> TrafficRecordValidationResult:
    """Validates and normalizes an individual raw traffic record dictionary."""
    if not isinstance(raw_record, dict):
        return TrafficRecordValidationResult(
            is_valid=False,
            row_index=row_index,
            errors=[
                ValidationErrorDetail(
                    field=None,
                    message=f"Record must be a dictionary, received {type(raw_record).__name__}",
                    invalid_value=None,
                )
            ],
        )

    try:
        validated_input = TrafficRecordInput(**raw_record)
        normalized = NormalizedTrafficRecord(
            timestamp=validated_input.timestamp,
            source_ip=validated_input.source_ip,
            destination_ip=validated_input.destination_ip,
            destination_domain=validated_input.destination_domain,
            destination_port=validated_input.destination_port,
            protocol=validated_input.protocol,
            bytes_sent=validated_input.bytes_sent,
            bytes_received=validated_input.bytes_received,
            http_method=validated_input.http_method,
            http_uri=validated_input.http_uri,
            http_status_code=validated_input.http_status_code,
            user_agent=validated_input.user_agent,
            sni_hostname=validated_input.sni_hostname,
            extra_metadata=validated_input.extra_metadata,
        )
        return TrafficRecordValidationResult(
            is_valid=True,
            record=normalized,
            row_index=row_index,
            errors=[],
        )
    except Exception as exc:
        error_details: List[ValidationErrorDetail] = []
        if hasattr(exc, "errors") and callable(getattr(exc, "errors")):
            for pydantic_err in exc.errors():
                loc_list = pydantic_err.get("loc", ())
                field_name = ".".join(str(loc) for loc in loc_list) if loc_list else None
                msg = pydantic_err.get("msg", str(exc)).replace("Value error, ", "")
                inp = pydantic_err.get("input")
                error_details.append(
                    ValidationErrorDetail(
                        field=field_name,
                        message=msg,
                        invalid_value=inp,
                    )
                )
        else:
            error_details.append(
                ValidationErrorDetail(
                    field=None,
                    message=str(exc),
                    invalid_value=None,
                )
            )

        return TrafficRecordValidationResult(
            is_valid=False,
            row_index=row_index,
            errors=error_details,
        )


def validate_traffic_batch(
    raw_records: List[Dict[str, Any]],
    max_sample_errors: int = 100,
) -> Tuple[List[NormalizedTrafficRecord], List[RecordValidationError]]:
    """Validates a batch of raw records, partitioning into valid records and error reports."""
    valid_records: List[NormalizedTrafficRecord] = []
    validation_errors: List[RecordValidationError] = []

    for idx, raw in enumerate(raw_records):
        res = validate_traffic_record(raw, row_index=idx + 1)
        if res.is_valid and res.record:
            valid_records.append(res.record)
        else:
            if len(validation_errors) < max_sample_errors:
                sanitized_raw = sanitize_record_for_logging(raw)
                validation_errors.append(
                    RecordValidationError(
                        row_index=res.row_index,
                        errors=res.errors,
                        raw_record=sanitized_raw,
                    )
                )

    return valid_records, validation_errors
