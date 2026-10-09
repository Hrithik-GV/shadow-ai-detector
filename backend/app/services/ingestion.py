from dataclasses import dataclass, field
import io
import json
import os
from typing import Any, BinaryIO, Dict, List, Optional, TextIO, Tuple, Union

import pandas as pd

from app.core.config import settings
from app.schemas.traffic import (
    NormalizedTrafficRecord,
    RecordValidationError,
    TrafficAnalysisSummary,
    ValidationErrorDetail,
    sanitize_record_for_logging,
    validate_traffic_record,
)
from app.services.exceptions import (
    EmptyFileError,
    FileParsingError,
    FileTooLargeError,
    RowLimitExceededError,
    UnsupportedFileFormatError,
)

SUPPORTED_EXTENSIONS = {
    ".csv": "csv",
    ".json": "json",
    ".jsonl": "jsonl",
    ".ndjson": "jsonl",
}


@dataclass
class IngestionResult:
    """Outcome of parsing and validating an uploaded traffic log file."""
    filename: str
    file_format: str
    total_rows: int
    valid_count: int
    rejected_count: int
    valid_records: List[NormalizedTrafficRecord] = field(default_factory=list)
    rejected_records: List[RecordValidationError] = field(default_factory=list)

    @property
    def is_successful(self) -> bool:
        """Indicates whether ingestion processed successfully with at least one valid record."""
        return self.valid_count > 0

    def to_summary(self, status: Optional[str] = None) -> TrafficAnalysisSummary:
        """Converts result into a standardized TrafficAnalysisSummary model."""
        computed_status = status or ("completed" if self.valid_count > 0 else "failed")
        return TrafficAnalysisSummary(
            original_filename=self.filename,
            file_format=self.file_format,
            status=computed_status,
            total_rows_received=self.total_rows,
            valid_rows=self.valid_count,
            rejected_rows=self.rejected_count,
            sample_errors=self.rejected_records[:50],
        )


class TrafficIngestionService:
    """Service responsible for reading, parsing, and validating raw traffic log files."""

    def __init__(
        self,
        max_upload_size: Optional[int] = None,
        max_rows: Optional[int] = None,
    ) -> None:
        self.max_upload_size = (
            max_upload_size
            if max_upload_size is not None
            else settings.MAX_UPLOAD_SIZE_BYTES
        )
        self.max_rows = (
            max_rows if max_rows is not None else settings.MAX_INGESTION_ROWS
        )

    def ingest(
        self,
        content: Union[bytes, str, BinaryIO, TextIO],
        filename: str,
    ) -> IngestionResult:
        """Ingests and validates a traffic log file from bytes, string, or file stream.
        
        Args:
            content: Raw file data or stream.
            filename: Original name of the file (used for format detection).
            
        Returns:
            IngestionResult containing partitioned valid and rejected records.
            
        Raises:
            UnsupportedFileFormatError: If file extension is unsupported.
            EmptyFileError: If file has 0 bytes or only whitespace.
            FileTooLargeError: If file size exceeds maximum upload limit.
            RowLimitExceededError: If records exceed maximum row count.
            FileParsingError: If file syntax is corrupt or cannot be parsed.
        """
        fmt = self._detect_format(filename)
        raw_bytes, text = self._read_and_validate_size(content, filename)

        if fmt == "csv":
            return self._ingest_csv(text, filename)
        elif fmt == "json":
            return self._ingest_json(text, filename, is_jsonl=False)
        elif fmt == "jsonl":
            return self._ingest_json(text, filename, is_jsonl=True)
        else:
            raise UnsupportedFileFormatError(
                f"Unsupported format '{fmt}' for file '{filename}'"
            )

    def _detect_format(self, filename: str) -> str:
        """Determines expected format from file extension."""
        if not filename or not isinstance(filename, str):
            raise UnsupportedFileFormatError("Filename must be a non-empty string")

        _, ext = os.path.splitext(filename.lower())
        if not ext:
            raise UnsupportedFileFormatError(
                f"Filename '{filename}' is missing an extension. Supported extensions: .csv, .json, .jsonl, .ndjson"
            )

        if ext not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileFormatError(
                f"Unsupported file extension '{ext}' for '{filename}'. Supported: .csv, .json, .jsonl, .ndjson"
            )

        return SUPPORTED_EXTENSIONS[ext]

    def _read_and_validate_size(
        self,
        content: Union[bytes, str, BinaryIO, TextIO],
        filename: str,
    ) -> Tuple[bytes, str]:
        """Reads content, verifies size constraints, and decodes to text."""
        # Extract raw bytes or text
        if hasattr(content, "read"):
            data = content.read()
            if isinstance(data, str):
                text = data
                raw_bytes = data.encode("utf-8")
            else:
                raw_bytes = data
                text = self._decode_bytes(raw_bytes, filename)
        elif isinstance(content, bytes):
            raw_bytes = content
            text = self._decode_bytes(raw_bytes, filename)
        elif isinstance(content, str):
            text = content
            raw_bytes = content.encode("utf-8")
        else:
            raise FileParsingError(
                f"Unsupported content type '{type(content).__name__}'. Expected bytes, str, or file stream."
            )

        # Check for empty content
        if len(raw_bytes) == 0 or not text.strip():
            raise EmptyFileError(f"Uploaded file '{filename}' is empty")

        # Check maximum file size
        if len(raw_bytes) > self.max_upload_size:
            raise FileTooLargeError(
                f"File '{filename}' ({len(raw_bytes)} bytes) exceeds the maximum allowed size of {self.max_upload_size} bytes"
            )

        return raw_bytes, text

    def _decode_bytes(self, data: bytes, filename: str) -> str:
        """Decodes bytes using standard UTF-8/UTF-8-SIG or Latin-1 fallback."""
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                return data.decode(enc)
            except UnicodeDecodeError:
                continue
        raise FileParsingError(
            f"Unable to decode '{filename}' using UTF-8 or Latin-1 character encodings"
        )

    def _ingest_csv(self, text: str, filename: str) -> IngestionResult:
        """Parses and validates CSV traffic logs using Pandas with row-level tracking."""
        try:
            # dtype=str prevents automatic float conversion; keep_default_na=False avoids float('nan')
            df = pd.read_csv(
                io.StringIO(text),
                dtype=str,
                keep_default_na=False,
                on_bad_lines="error",
            )
        except pd.errors.EmptyDataError:
            raise EmptyFileError(f"CSV file '{filename}' contains no header or rows")
        except Exception as exc:
            raise FileParsingError(f"Malformed CSV in '{filename}': {str(exc)}") from exc

        if len(df.columns) == 0:
            raise FileParsingError(f"CSV file '{filename}' must contain a header row")

        total_rows = len(df)
        if total_rows > self.max_rows:
            raise RowLimitExceededError(
                f"CSV row count ({total_rows}) exceeds configured limit of {self.max_rows} rows"
            )

        valid_records: List[NormalizedTrafficRecord] = []
        rejected_records: List[RecordValidationError] = []

        raw_rows = df.to_dict(orient="records")
        for idx, row in enumerate(raw_rows):
            # Line numbers in CSV: line 1 is header, data starts on line 2
            line_no = idx + 2
            clean_row = {
                k: (None if pd.isna(v) or v == "" else v) for k, v in row.items()
            }

            res = validate_traffic_record(clean_row, row_index=line_no)
            if res.is_valid and res.record:
                valid_records.append(res.record)
            else:
                sanitized = sanitize_record_for_logging(clean_row)
                rejected_records.append(
                    RecordValidationError(
                        row_index=line_no,
                        errors=res.errors,
                        raw_record=sanitized,
                    )
                )

        return IngestionResult(
            filename=filename,
            file_format="csv",
            total_rows=total_rows,
            valid_count=len(valid_records),
            rejected_count=len(rejected_records),
            valid_records=valid_records,
            rejected_records=rejected_records,
        )

    def _ingest_json(
        self,
        text: str,
        filename: str,
        is_jsonl: bool = False,
    ) -> IngestionResult:
        """Parses and validates JSON (array, wrapped object, or line-delimited JSON)."""
        raw_items: List[Tuple[int, Any]] = []

        # If explicitly .jsonl / .ndjson, parse line by line
        if is_jsonl:
            return self._parse_json_lines(text, filename)

        # Standard .json file
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            # Fallback: check if the file is formatted as NDJSON with multiple valid lines
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            if len(lines) > 1:
                try:
                    parsed_objects = [json.loads(l) for l in lines]
                    if all(isinstance(obj, dict) for obj in parsed_objects):
                        return self._parse_json_lines(text, filename)
                except Exception:
                    pass
            raise FileParsingError(
                f"Malformed JSON in '{filename}': {str(exc)}"
            ) from exc

        # Extract items based on JSON structure
        if isinstance(parsed, list):
            raw_items = [(idx + 1, item) for idx, item in enumerate(parsed)]
        elif isinstance(parsed, dict):
            # Check for standard wrapping keys: "records", "traffic", "data", "items"
            wrapper_keys = ("records", "traffic", "data", "items")
            found_list = None
            for key in wrapper_keys:
                if isinstance(parsed.get(key), list):
                    found_list = parsed[key]
                    break

            if found_list is not None:
                raw_items = [(idx + 1, item) for idx, item in enumerate(found_list)]
            else:
                # Accept a single JSON object as a 1-item batch
                raw_items = [(1, parsed)]
        else:
            raise FileParsingError(
                f"JSON in '{filename}' must contain an array of objects or an object containing a records array"
            )

        total_rows = len(raw_items)
        if total_rows > self.max_rows:
            raise RowLimitExceededError(
                f"JSON record count ({total_rows}) exceeds configured limit of {self.max_rows} rows"
            )

        valid_records: List[NormalizedTrafficRecord] = []
        rejected_records: List[RecordValidationError] = []

        for line_no, item in raw_items:
            if not isinstance(item, dict):
                rejected_records.append(
                    RecordValidationError(
                        row_index=line_no,
                        errors=[
                            ValidationErrorDetail(
                                field=None,
                                message=f"Record must be a JSON object, received {type(item).__name__}",
                                invalid_value=None,
                            )
                        ],
                        raw_record={"raw_value": str(item)},
                    )
                )
                continue

            res = validate_traffic_record(item, row_index=line_no)
            if res.is_valid and res.record:
                valid_records.append(res.record)
            else:
                sanitized = sanitize_record_for_logging(item)
                rejected_records.append(
                    RecordValidationError(
                        row_index=line_no,
                        errors=res.errors,
                        raw_record=sanitized,
                    )
                )

        return IngestionResult(
            filename=filename,
            file_format="json",
            total_rows=total_rows,
            valid_count=len(valid_records),
            rejected_count=len(rejected_records),
            valid_records=valid_records,
            rejected_records=rejected_records,
        )

    def _parse_json_lines(self, text: str, filename: str) -> IngestionResult:
        """Parses line-delimited JSON (JSON Lines / NDJSON)."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            raise EmptyFileError(f"JSON Lines file '{filename}' contains no records")

        total_rows = len(lines)
        if total_rows > self.max_rows:
            raise RowLimitExceededError(
                f"JSON Lines row count ({total_rows}) exceeds configured limit of {self.max_rows} rows"
            )

        valid_records: List[NormalizedTrafficRecord] = []
        rejected_records: List[RecordValidationError] = []

        for line_no, line_content in enumerate(lines, start=1):
            try:
                item = json.loads(line_content)
            except json.JSONDecodeError as exc:
                rejected_records.append(
                    RecordValidationError(
                        row_index=line_no,
                        errors=[
                            ValidationErrorDetail(
                                field=None,
                                message=f"Malformed JSON on line: {str(exc)}",
                                invalid_value=None,
                            )
                        ],
                        raw_record={"raw_line": line_content[:200]},
                    )
                )
                continue

            if not isinstance(item, dict):
                rejected_records.append(
                    RecordValidationError(
                        row_index=line_no,
                        errors=[
                            ValidationErrorDetail(
                                field=None,
                                message=f"Line must contain a JSON object, received {type(item).__name__}",
                                invalid_value=None,
                            )
                        ],
                        raw_record={"raw_value": str(item)},
                    )
                )
                continue

            res = validate_traffic_record(item, row_index=line_no)
            if res.is_valid and res.record:
                valid_records.append(res.record)
            else:
                sanitized = sanitize_record_for_logging(item)
                rejected_records.append(
                    RecordValidationError(
                        row_index=line_no,
                        errors=res.errors,
                        raw_record=sanitized,
                    )
                )

        # If every line failed to parse as JSON, reject the whole file as malformed
        if len(rejected_records) == len(lines) and all(
            any("Malformed JSON on line" in e.message for e in r.errors)
            for r in rejected_records
        ):
            raise FileParsingError(
                f"Malformed JSON Lines file '{filename}': no valid JSON lines could be decoded"
            )

        return IngestionResult(
            filename=filename,
            file_format="jsonl",
            total_rows=total_rows,
            valid_count=len(valid_records),
            rejected_count=len(rejected_records),
            valid_records=valid_records,
            rejected_records=rejected_records,
        )


def ingest_traffic_file(
    content: Union[bytes, str, BinaryIO, TextIO],
    filename: str,
    max_upload_size: Optional[int] = None,
    max_rows: Optional[int] = None,
) -> IngestionResult:
    """Convenience functional interface for ingesting traffic log files."""
    service = TrafficIngestionService(
        max_upload_size=max_upload_size,
        max_rows=max_rows,
    )
    return service.ingest(content, filename)
