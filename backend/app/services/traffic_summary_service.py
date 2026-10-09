import logging
from typing import Dict, List, Optional
import uuid

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.traffic import TrafficAnalysis, TrafficRecord
from app.schemas.traffic_api import DashboardStatsResponse, TrafficMetricsSummary

logger = logging.getLogger(__name__)


class TrafficSummaryService:
    """Dedicated service for calculating real summary statistics from persisted traffic records.

    Calculation Rules & Definitions:
    1. Record Counts vs. Network Connections:
       - 'valid_records' / 'total_valid_records' represent the count of parsed, valid log
         entries ingested from capture files. A single log entry does not necessarily equate to
         a unique TCP socket or network connection unless the ingestion source format explicitly guarantees it.
    2. Missing Metadata (Bytes, IPs, Domains, Timestamps):
       - Missing values (NULL) are treated as unknown, NOT as zero.
       - 'total_bytes_sent' and 'total_bytes_received' sum exclusively non-null values.
         Missing byte values are tracked in 'missing_bytes_sent_count' and 'missing_bytes_received_count'.
       - Unique IP and domain counts specifically exclude NULL / omitted fields via SQL COUNT(DISTINCT col).
       - Timestamps: earliest and latest timestamps reflect MIN and MAX over non-null timestamps.
    3. Protocol Distribution:
       - Aggregated over observed non-null protocol strings, normalized to uppercase, mapped to frequency counts.
       - Omitted/null protocols are tracked in 'missing_protocol_count'.
    """

    @staticmethod
    def calculate_analysis_summary(
        db: Session,
        analysis: TrafficAnalysis,
    ) -> TrafficMetricsSummary:
        """Computes comprehensive summary metrics for a given analysis record."""
        # Query 1: Main aggregates on traffic records for this analysis
        stmt = select(
            func.count(TrafficRecord.id).label("total_valid_records"),
            func.coalesce(func.sum(TrafficRecord.bytes_sent), 0).label("total_bytes_sent"),
            func.coalesce(func.sum(TrafficRecord.bytes_received), 0).label("total_bytes_received"),
            func.count(distinct(TrafficRecord.source_ip)).label("unique_source_ips"),
            func.count(distinct(TrafficRecord.destination_ip)).label("unique_destination_ips"),
            func.count(distinct(TrafficRecord.destination_domain)).label("unique_destination_domains"),
            func.count(TrafficRecord.bytes_sent).label("bytes_sent_reported_count"),
            func.count(TrafficRecord.bytes_received).label("bytes_received_reported_count"),
            func.count(TrafficRecord.timestamp).label("records_with_timestamp"),
            func.min(TrafficRecord.timestamp).label("earliest_timestamp"),
            func.max(TrafficRecord.timestamp).label("latest_timestamp"),
        ).where(TrafficRecord.analysis_id == analysis.id)

        row = db.execute(stmt).one()

        total_valid = row.total_valid_records or 0
        bytes_sent_reported = row.bytes_sent_reported_count or 0
        bytes_received_reported = row.bytes_received_reported_count or 0
        records_with_ts = row.records_with_timestamp or 0

        # Missing counts = total valid records minus reported non-null records
        missing_bytes_sent = max(0, total_valid - bytes_sent_reported)
        missing_bytes_received = max(0, total_valid - bytes_received_reported)
        missing_timestamp = max(0, total_valid - records_with_ts)

        # Query 2: Protocol distribution grouping
        proto_stmt = (
            select(
                TrafficRecord.protocol,
                func.count(TrafficRecord.id).label("record_count"),
            )
            .where(TrafficRecord.analysis_id == analysis.id)
            .group_by(TrafficRecord.protocol)
            .order_by(func.count(TrafficRecord.id).desc())
        )
        proto_rows = db.execute(proto_stmt).all()

        protocol_dist: Dict[str, int] = {}
        distinct_protocols: List[str] = []
        missing_protocol_count = 0

        for proto_row in proto_rows:
            p_val = proto_row.protocol
            cnt = proto_row.record_count
            if p_val is None or str(p_val).strip() == "":
                missing_protocol_count += cnt
            else:
                proto_str = str(p_val).strip().upper()
                protocol_dist[proto_str] = protocol_dist.get(proto_str, 0) + cnt
                if proto_str not in distinct_protocols:
                    distinct_protocols.append(proto_str)

        distinct_protocols.sort()

        return TrafficMetricsSummary(
            total_records_received=analysis.total_rows_received or 0,
            valid_records=total_valid,
            total_valid_records=total_valid,
            rejected_records=analysis.rejected_rows or 0,
            unique_source_ips=row.unique_source_ips or 0,
            unique_destination_ips=row.unique_destination_ips or 0,
            unique_destination_domains=row.unique_destination_domains or 0,
            total_bytes_sent=int(row.total_bytes_sent or 0),
            total_bytes_received=int(row.total_bytes_received or 0),
            bytes_sent_reported_count=bytes_sent_reported,
            bytes_received_reported_count=bytes_received_reported,
            missing_bytes_sent_count=missing_bytes_sent,
            missing_bytes_received_count=missing_bytes_received,
            protocols=distinct_protocols,
            protocol_distribution=protocol_dist,
            missing_protocol_count=missing_protocol_count,
            earliest_timestamp=row.earliest_timestamp,
            latest_timestamp=row.latest_timestamp,
            records_with_timestamp=records_with_ts,
            missing_timestamp_count=missing_timestamp,
        )

    @staticmethod
    def get_analysis_summary_by_id(
        db: Session,
        analysis_id: uuid.UUID,
    ) -> Optional[TrafficMetricsSummary]:
        """Fetches an analysis by ID and calculates its metrics summary, or returns None if not found."""
        analysis = db.scalar(
            select(TrafficAnalysis).where(TrafficAnalysis.id == analysis_id)
        )
        if not analysis:
            return None
        return TrafficSummaryService.calculate_analysis_summary(db, analysis)

    @staticmethod
    def get_dashboard_stats(
        db: Session,
        analysis_id: Optional[uuid.UUID] = None,
    ) -> Optional[DashboardStatsResponse]:
        """Calculates real summary statistics for the frontend Overview page.

        If `analysis_id` is specified:
          - Scoped exclusively to that analysis.
          - Returns None if the analysis ID does not exist in the database.
        If `analysis_id` is None:
          - Aggregated across all saved analyses and traffic records in the database.
        """
        if analysis_id is not None:
            # Scoped to single analysis
            analysis = db.scalar(
                select(TrafficAnalysis).where(TrafficAnalysis.id == analysis_id)
            )
            if not analysis:
                return None

            summary = TrafficSummaryService.calculate_analysis_summary(db, analysis)
            return DashboardStatsResponse(
                scope="selected_analysis",
                analysis_id=analysis.id,
                analyses_count=1,
                scope_description=f"Statistics calculated exclusively for analysis run '{analysis.id}' ('{analysis.original_filename}').",
                total_records_received=summary.total_records_received,
                valid_records=summary.valid_records,
                rejected_records=summary.rejected_records,
                unique_source_ips=summary.unique_source_ips,
                unique_destination_ips=summary.unique_destination_ips,
                unique_destination_domains=summary.unique_destination_domains,
                total_bytes_sent=summary.total_bytes_sent,
                total_bytes_received=summary.total_bytes_received,
                bytes_sent_reported_count=summary.bytes_sent_reported_count,
                bytes_received_reported_count=summary.bytes_received_reported_count,
                missing_bytes_sent_count=summary.missing_bytes_sent_count,
                missing_bytes_received_count=summary.missing_bytes_received_count,
                protocols=summary.protocols,
                protocol_distribution=summary.protocol_distribution,
                missing_protocol_count=summary.missing_protocol_count,
                earliest_timestamp=summary.earliest_timestamp,
                latest_timestamp=summary.latest_timestamp,
                records_with_timestamp=summary.records_with_timestamp,
                missing_timestamp_count=summary.missing_timestamp_count,
            )

        # Global aggregation across all analyses in database
        analysis_totals_stmt = select(
            func.count(TrafficAnalysis.id).label("analyses_count"),
            func.coalesce(func.sum(TrafficAnalysis.total_rows_received), 0).label("total_records_received"),
            func.coalesce(func.sum(TrafficAnalysis.valid_rows), 0).label("valid_records"),
            func.coalesce(func.sum(TrafficAnalysis.rejected_rows), 0).label("rejected_records"),
        )
        analysis_totals = db.execute(analysis_totals_stmt).one()
        analyses_count = analysis_totals.analyses_count or 0

        # Aggregate across all records in DB
        records_totals_stmt = select(
            func.count(TrafficRecord.id).label("total_valid_records"),
            func.coalesce(func.sum(TrafficRecord.bytes_sent), 0).label("total_bytes_sent"),
            func.coalesce(func.sum(TrafficRecord.bytes_received), 0).label("total_bytes_received"),
            func.count(distinct(TrafficRecord.source_ip)).label("unique_source_ips"),
            func.count(distinct(TrafficRecord.destination_ip)).label("unique_destination_ips"),
            func.count(distinct(TrafficRecord.destination_domain)).label("unique_destination_domains"),
            func.count(TrafficRecord.bytes_sent).label("bytes_sent_reported_count"),
            func.count(TrafficRecord.bytes_received).label("bytes_received_reported_count"),
            func.count(TrafficRecord.timestamp).label("records_with_timestamp"),
            func.min(TrafficRecord.timestamp).label("earliest_timestamp"),
            func.max(TrafficRecord.timestamp).label("latest_timestamp"),
        )
        rec_row = db.execute(records_totals_stmt).one()

        total_valid = rec_row.total_valid_records or 0
        bytes_sent_reported = rec_row.bytes_sent_reported_count or 0
        bytes_received_reported = rec_row.bytes_received_reported_count or 0
        records_with_ts = rec_row.records_with_timestamp or 0

        missing_bytes_sent = max(0, total_valid - bytes_sent_reported)
        missing_bytes_received = max(0, total_valid - bytes_received_reported)
        missing_timestamp = max(0, total_valid - records_with_ts)

        # Protocol distribution across all records
        proto_stmt = (
            select(
                TrafficRecord.protocol,
                func.count(TrafficRecord.id).label("record_count"),
            )
            .group_by(TrafficRecord.protocol)
            .order_by(func.count(TrafficRecord.id).desc())
        )
        proto_rows = db.execute(proto_stmt).all()

        protocol_dist: Dict[str, int] = {}
        distinct_protocols: List[str] = []
        missing_protocol_count = 0

        for proto_row in proto_rows:
            p_val = proto_row.protocol
            cnt = proto_row.record_count
            if p_val is None or str(p_val).strip() == "":
                missing_protocol_count += cnt
            else:
                proto_str = str(p_val).strip().upper()
                protocol_dist[proto_str] = protocol_dist.get(proto_str, 0) + cnt
                if proto_str not in distinct_protocols:
                    distinct_protocols.append(proto_str)

        distinct_protocols.sort()

        return DashboardStatsResponse(
            scope="all_analyses",
            analysis_id=None,
            analyses_count=analyses_count,
            scope_description=f"Statistics aggregated across all {analyses_count} saved analysis runs in the database.",
            total_records_received=int(analysis_totals.total_records_received or 0),
            valid_records=total_valid,
            rejected_records=int(analysis_totals.rejected_records or 0),
            unique_source_ips=rec_row.unique_source_ips or 0,
            unique_destination_ips=rec_row.unique_destination_ips or 0,
            unique_destination_domains=rec_row.unique_destination_domains or 0,
            total_bytes_sent=int(rec_row.total_bytes_sent or 0),
            total_bytes_received=int(rec_row.total_bytes_received or 0),
            bytes_sent_reported_count=bytes_sent_reported,
            bytes_received_reported_count=bytes_received_reported,
            missing_bytes_sent_count=missing_bytes_sent,
            missing_bytes_received_count=missing_bytes_received,
            protocols=distinct_protocols,
            protocol_distribution=protocol_dist,
            missing_protocol_count=missing_protocol_count,
            earliest_timestamp=rec_row.earliest_timestamp,
            latest_timestamp=rec_row.latest_timestamp,
            records_with_timestamp=records_with_ts,
            missing_timestamp_count=missing_timestamp,
        )
