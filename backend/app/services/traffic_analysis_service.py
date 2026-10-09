import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.traffic import (
    AnalysisStatus,
    TrafficAnalysis,
    TrafficRecord,
    AIEndpointInventoryModel,
    RiskFindingModel,
)
from app.schemas.traffic import RecordValidationError
from app.schemas.traffic_api import TrafficMetricsSummary
from app.services.ingestion import IngestionResult, TrafficIngestionService
from app.services.ai_detector import default_detector
from app.services.risk_engine import RiskEngine, default_risk_engine, EndpointTrafficAggregate
from app.services.traffic_summary_service import TrafficSummaryService

logger = logging.getLogger(__name__)


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

            # Step 3.5: Run AI Detection and Risk Assessment on valid records
            endpoint_aggregates: Dict[str, EndpointTrafficAggregate] = {}
            detector = default_detector
            risk_engine = RiskEngine(db=db)

            for rec in ingestion_result.valid_records:
                target_host = rec.destination_domain or rec.sni_hostname
                det = detector.classify_target(
                    domain=rec.destination_domain,
                    sni_hostname=rec.sni_hostname,
                    destination_ip=rec.destination_ip,
                    http_uri=rec.http_uri,
                )

                # Only confirmed AI detections are aggregated into AI inventory and risk engine!
                # Unknown / uncertain domains (like unverified-ai-test.invalid) are NOT treated as AI
                if det.is_ai and det.provider and target_host:
                    if target_host not in endpoint_aggregates:
                        endpoint_aggregates[target_host] = EndpointTrafficAggregate(
                            target=target_host,
                            provider=det.provider,
                            category=det.category or "LLM API / Foundation Models",
                            detection_signatures=list(det.detection_signatures),
                        )

                    agg = endpoint_aggregates[target_host]
                    agg.total_calls += 1
                    agg.bytes_sent += rec.bytes_sent or 0
                    agg.bytes_received += rec.bytes_received or 0
                    if rec.source_ip:
                        agg.source_ips.append(rec.source_ip)
                    if rec.extra_metadata and "evidence_source" in rec.extra_metadata:
                        src = rec.extra_metadata["evidence_source"]
                        if src and src not in agg.evidence_sources:
                            agg.evidence_sources.append(src)
                    if rec.timestamp:
                        if agg.first_seen_at is None or rec.timestamp < agg.first_seen_at:
                            agg.first_seen_at = rec.timestamp
                        if agg.last_seen_at is None or rec.timestamp > agg.last_seen_at:
                            agg.last_seen_at = rec.timestamp

            # Evaluate each detected AI endpoint with the Risk Engine and persist
            for target_host, agg in endpoint_aggregates.items():
                inv_item, risk_finding = risk_engine.evaluate_endpoint(agg)

                db_inv = AIEndpointInventoryModel(
                    analysis_id=analysis.id,
                    external_id=inv_item.id,
                    provider=inv_item.provider,
                    domain=inv_item.domain,
                    hostname=inv_item.hostname,
                    url=inv_item.url,
                    endpoint_address=inv_item.endpoint_address,
                    endpoint_type=inv_item.endpoint_type,
                    category=inv_item.category,
                    is_approved=inv_item.is_approved,
                    approval_status=inv_item.approval_status,
                    confidence=inv_item.confidence,
                    total_calls=inv_item.total_calls,
                    bytes_transferred=inv_item.bytes_transferred,
                    data_transferred=inv_item.data_transferred,
                    risk_level=inv_item.risk_level,
                    risk_score=inv_item.risk_score,
                    reasons=inv_item.reasons,
                    evidence=inv_item.evidence,
                    detection_signatures=inv_item.detection_signatures,
                    first_seen_at=inv_item.first_seen_at,
                    last_seen_at=inv_item.last_seen_at,
                    investigation_status=inv_item.investigation_status,
                )
                db.add(db_inv)

                if risk_finding:
                    db_finding = RiskFindingModel(
                        analysis_id=analysis.id,
                        external_id=risk_finding.id,
                        target=risk_finding.target,
                        provider=risk_finding.provider,
                        endpoint=risk_finding.endpoint,
                        endpoint_hostname=risk_finding.endpoint_hostname,
                        risk_score=risk_finding.risk_score,
                        risk_level=risk_finding.risk_level,
                        is_approved=risk_finding.is_approved,
                        approval_status=risk_finding.approval_status,
                        policy_rule=risk_finding.policy_rule,
                        description=risk_finding.description,
                        reasons=risk_finding.reasons,
                        evidence=risk_finding.evidence,
                        first_seen_at=risk_finding.first_seen_at,
                        assessed_at=risk_finding.assessed_at,
                        investigation_status=risk_finding.investigation_status,
                        status=risk_finding.status,
                    )
                    db.add(db_finding)

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
