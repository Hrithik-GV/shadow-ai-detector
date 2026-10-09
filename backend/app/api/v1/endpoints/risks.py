from typing import List, Optional
import uuid
import logging

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.traffic import RiskFindingModel
from app.schemas.traffic_api import RiskAssessmentResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=List[RiskAssessmentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all risk findings",
    description="Returns security evaluations, data egress alerts, and unapproved shadow AI classifications derived from endpoint telemetry.",
)
def get_risk_findings(
    analysis_id: Optional[uuid.UUID] = Query(
        None,
        description="Optional analysis ID to filter risk findings to a specific capture run.",
    ),
    db: Session = Depends(get_db),
) -> List[RiskAssessmentResponse]:
    """Retrieves all persisted risk findings from the database."""
    stmt = select(RiskFindingModel)
    if analysis_id is not None:
        stmt = stmt.where(RiskFindingModel.analysis_id == analysis_id)

    stmt = stmt.order_by(RiskFindingModel.risk_score.desc(), RiskFindingModel.created_at.desc())
    findings = db.execute(stmt).scalars().all()

    results: List[RiskAssessmentResponse] = []
    for f in findings:
        results.append(
            RiskAssessmentResponse(
                id=f.external_id,
                target=f.target,
                provider=f.provider,
                endpoint=f.endpoint,
                endpointHostname=f.endpoint_hostname,
                endpoint_hostname=f.endpoint_hostname,
                riskScore=f.risk_score,
                risk_score=f.risk_score,
                riskLevel=f.risk_level,
                risk_level=f.risk_level,
                isApproved=f.is_approved,
                is_approved=f.is_approved,
                approvalStatus=f.approval_status,
                approval_status=f.approval_status,
                policyRule=f.policy_rule,
                policy_rule=f.policy_rule,
                description=f.description,
                reasons=list(f.reasons or []),
                evidence=list(f.evidence or []),
                firstSeenAt=f.first_seen_at,
                first_seen_at=f.first_seen_at,
                assessedAt=f.assessed_at,
                assessed_at=f.assessed_at,
                investigationStatus=f.investigation_status,
                investigation_status=f.investigation_status,
                status=f.status,
            )
        )
    return results
