import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.traffic import AnalysisStatus, TrafficAnalysis, TrafficRecord
from app.schemas.traffic import RecordValidationError
from app.schemas.traffic_api import TrafficMetricsSummary
from app.services.ingestion import IngestionResult, TrafficIngestionService

logger = logging.getLogger(__name__)


from app.services.traffic_summary_service import TrafficSummaryService


def compute_analysis_metrics(db: Session, analysis_id: uuid.UUID) -> TrafficMetricsSummary:
    """Computes real aggregate metrics from persisted traffic records in PostgreSQL."""
    summary = TrafficSummaryService.get_analysis_summary_by_id(db, analysis_id)
    if summary is None:
        raise ValueError(f"Analysis with ID '{analysis_id}' does not exist.")
    return summary



def process_and_persist_traffic_file(
    db: Session,
    file_content: Union[bytes, str],
    filename: str,
) -> Tuple[TrafficAnalysis, IngestionResult, TrafficMetricsSummary]:
    """Parses and validates traffic file, persisting records and metadata transactionally."""
    # Step 1: Run ingestion validation
    ingestion_service = TrafficIngestionService()
    ingestion_result = ingestion_service.ingest(file_content, filename)

    try:
        # Step 2: Create initial TrafficAnalysis record
        analysis = TrafficAnalysis(
            original_filename=filename,
            file_format=ingestion_result.file_format,
            status=AnalysisStatus.PROCESSING,
        )
        db.add(analysis)
        db.flush()

        # Step 3: Persist valid records linked to this analysis
        if ingestion_result.valid_records:
            db_records = [
                TrafficRecord(**record.to_db_dict(analysis_id=analysis.id))
                for record in ingestion_result.valid_records
            ]
            db.add_all(db_records)
            db.flush()

        # Step 4: Finalize analysis metadata
        analysis.total_rows_received = ingestion_result.total_rows
        analysis.valid_rows = ingestion_result.valid_count
        analysis.rejected_rows = ingestion_result.rejected_count

        if ingestion_result.valid_count > 0:
            analysis.status = AnalysisStatus.COMPLETED
            analysis.error_details = None
        else:
            analysis.status = AnalysisStatus.FAILED
            analysis.error_details = (
                f"Ingestion completed with 0 valid records. "
                f"All {ingestion_result.total_rows} row(s) failed validation."
            )

        # Step 5: Derive real metrics summary from database
        summary = TrafficSummaryService.calculate_analysis_summary(db, analysis)

        # Commit transaction
        db.commit()
        db.refresh(analysis)

        return analysis, ingestion_result, summary

    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to process and persist traffic file '{filename}': {exc}")
        raise


def get_analysis_by_id(
    db: Session,
    analysis_id: uuid.UUID,
) -> Optional[Tuple[TrafficAnalysis, TrafficMetricsSummary]]:
    """Retrieves an analysis by ID along with its computed metrics."""
    stmt = select(TrafficAnalysis).where(TrafficAnalysis.id == analysis_id)
    analysis = db.scalar(stmt)
    if not analysis:
        return None

    summary = TrafficSummaryService.calculate_analysis_summary(db, analysis)
    return analysis, summary


def get_paginated_records(
    db: Session,
    analysis_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
) -> Optional[Tuple[int, List[TrafficRecord]]]:
    """Retrieves paginated records for an analysis. Returns None if analysis does not exist."""
    # Check analysis existence
    exists_stmt = select(TrafficAnalysis.id).where(TrafficAnalysis.id == analysis_id)
    if db.scalar(exists_stmt) is None:
        return None

    # Total matching records count
    count_stmt = (
        select(func.count(TrafficRecord.id))
        .where(TrafficRecord.analysis_id == analysis_id)
    )
    total_records = db.scalar(count_stmt) or 0

    # Paginated records
    records_stmt = (
        select(TrafficRecord)
        .where(TrafficRecord.analysis_id == analysis_id)
        .order_by(TrafficRecord.timestamp.asc().nulls_last(), TrafficRecord.id.asc())
        .limit(limit)
        .offset(offset)
    )
    records = list(db.scalars(records_stmt).all())

    return total_records, records


def get_paginated_analyses(
    db: Session,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[int, List[TrafficAnalysis]]:
    """Retrieves saved analysis runs ordered by creation time descending."""
    count_stmt = select(func.count(TrafficAnalysis.id))
    total_analyses = db.scalar(count_stmt) or 0

    analyses_stmt = (
        select(TrafficAnalysis)
        .order_by(TrafficAnalysis.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    analyses = list(db.scalars(analyses_stmt).all())

    return total_analyses, analyses
