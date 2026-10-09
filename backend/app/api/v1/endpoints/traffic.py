import logging
import uuid
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.traffic_api import (
    PaginatedTrafficAnalysesResponse,
    PaginatedTrafficRecordsResponse,
    TrafficAnalysisDetailResponse,
    TrafficAnalysisListItem,
    TrafficAnalyzeResponse,
    TrafficMetricsSummary,
    TrafficRecordResponse,
)
from app.services.exceptions import (
    EmptyFileError,
    FileParsingError,
    FileTooLargeError,
    RowLimitExceededError,
    UnsupportedFileFormatError,
)
from app.services.traffic_analysis_service import (
    get_analysis_by_id,
    get_paginated_analyses,
    get_paginated_records,
    process_and_persist_traffic_file,
)
from app.services.traffic_summary_service import TrafficSummaryService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/analyze",
    response_model=TrafficAnalyzeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and analyze a traffic capture or log file",
    description=(
        "Ingests network capture files (.pcap, .pcapng, .cap) and structured logs (.csv, .json, .jsonl, .ndjson). "
        "Extracts IP 5-tuples, DNS queries/responses, and TLS SNI handshakes via Scapy userspace parsing, "
        "validates rows, and persists valid records to PostgreSQL without decrypting payloads."
    ),
)
async def analyze_traffic(
    file: UploadFile = File(..., description="Traffic capture or log file (.pcap, .pcapng, .cap, .csv, .json, .jsonl, .ndjson)"),
    db: Session = Depends(get_db),
) -> TrafficAnalyzeResponse:
    """Upload a network capture or log file, process observations, and persist results."""
    filename = file.filename or "unknown.pcap"

    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(exc)}",
        )

    try:
        analysis, ingestion_result, summary = process_and_persist_traffic_file(
            db=db,
            file_content=content,
            filename=filename,
        )

        return TrafficAnalyzeResponse(
            id=analysis.id,
            original_filename=analysis.original_filename,
            file_format=analysis.file_format,
            status=analysis.status.value,
            total_rows_received=analysis.total_rows_received,
            valid_rows=analysis.valid_rows,
            rejected_rows=analysis.rejected_rows,
            error_details=analysis.error_details,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
            summary=summary,
            rejected_records=ingestion_result.rejected_records,
        )

    except UnsupportedFileFormatError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except EmptyFileError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except FileParsingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except FileTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))
    except RowLimitExceededError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))
    except HTTPException:
        raise
    except RuntimeError as exc:
        logger.error(f"Database runtime error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred during processing. The transaction was rolled back.",
        )
    except Exception as exc:
        logger.exception(f"Unexpected error processing traffic file: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during traffic analysis.",
        )


@router.get(
    "/{analysis_id}/records",
    response_model=PaginatedTrafficRecordsResponse,
    summary="Get paginated records for an analysis",
    description="Returns persisted individual traffic records for a specified analysis ID.",
)
def get_analysis_records(
    analysis_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records to return (1-500)"),
    offset: int = Query(0, ge=0, description="Zero-based record offset"),
    db: Session = Depends(get_db),
) -> PaginatedTrafficRecordsResponse:
    """Retrieve paginated flow records associated with a specific analysis job."""
    result = get_paginated_records(db, analysis_id, limit=limit, offset=offset)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID '{analysis_id}' was not found",
        )

    total_records, records = result
    return PaginatedTrafficRecordsResponse(
        analysis_id=analysis_id,
        total_records=total_records,
        limit=limit,
        offset=offset,
        records=[TrafficRecordResponse.model_validate(r) for r in records],
    )


@router.get(
    "/{analysis_id}/summary",
    response_model=TrafficMetricsSummary,
    summary="Get summary statistics for an analysis",
    description="Returns reliable summary statistics calculated strictly from actual persisted records for this analysis.",
)
def get_analysis_summary(
    analysis_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> TrafficMetricsSummary:
    """Retrieve real summary statistics for a single analysis run."""
    summary = TrafficSummaryService.get_analysis_summary_by_id(db, analysis_id)
    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID '{analysis_id}' was not found",
        )
    return summary


@router.get(
    "/{analysis_id}",
    response_model=TrafficAnalysisDetailResponse,
    summary="Get analysis by ID",
    description="Retrieves status, file metadata, and real aggregated metrics for a single analysis run.",
)
def get_analysis(
    analysis_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> TrafficAnalysisDetailResponse:
    """Retrieve details and real metrics summary for a single analysis."""
    result = get_analysis_by_id(db, analysis_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID '{analysis_id}' was not found",
        )

    analysis, summary = result
    return TrafficAnalysisDetailResponse(
        id=analysis.id,
        original_filename=analysis.original_filename,
        file_format=analysis.file_format,
        status=analysis.status.value,
        total_rows_received=analysis.total_rows_received,
        valid_rows=analysis.valid_rows,
        rejected_rows=analysis.rejected_rows,
        error_details=analysis.error_details,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
        summary=summary,
    )


@router.get(
    "",
    response_model=PaginatedTrafficAnalysesResponse,
    summary="List traffic analyses history",
    description="Returns saved analysis jobs ordered chronologically descending.",
)
def list_analyses(
    limit: int = Query(20, ge=1, le=100, description="Maximum analyses per page (1-100)"),
    offset: int = Query(0, ge=0, description="Zero-based page offset"),
    db: Session = Depends(get_db),
) -> PaginatedTrafficAnalysesResponse:
    """Retrieve paginated analysis history."""
    total_analyses, analyses = get_paginated_analyses(db, limit=limit, offset=offset)

    items = [
        TrafficAnalysisListItem(
            id=a.id,
            original_filename=a.original_filename,
            file_format=a.file_format,
            status=a.status.value,
            total_rows_received=a.total_rows_received,
            valid_rows=a.valid_rows,
            rejected_rows=a.rejected_rows,
            error_details=a.error_details,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in analyses
    ]

    return PaginatedTrafficAnalysesResponse(
        total_analyses=total_analyses,
        limit=limit,
        offset=offset,
        analyses=items,
    )
