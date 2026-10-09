import logging
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.traffic_api import DashboardStatsResponse
from app.services.traffic_summary_service import TrafficSummaryService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dashboard overview summary statistics",
    description=(
        "Returns reliable summary statistics derived strictly from actual persisted traffic records. "
        "If analysis_id is provided, statistics are scoped to that specific analysis run. "
        "If omitted, statistics aggregate across all saved analysis runs in PostgreSQL."
    ),
)
def get_dashboard_stats(
    analysis_id: Optional[uuid.UUID] = Query(
        None,
        description="Optional analysis ID to scope statistics to a specific capture run. If omitted, aggregates across all analyses.",
    ),
    db: Session = Depends(get_db),
) -> DashboardStatsResponse:
    """Retrieve real summary statistics for the frontend Overview page."""
    stats = TrafficSummaryService.get_dashboard_stats(db=db, analysis_id=analysis_id)
    if stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID '{analysis_id}' was not found",
        )
    return stats
