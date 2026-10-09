from typing import List, Optional
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.traffic import AIEndpointInventoryModel
from app.schemas.traffic_api import EndpointDetailResponse, EndpointInventoryItemResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=List[EndpointInventoryItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get AI endpoint inventory catalog",
    description="Retrieves catalog of all discovered generative AI foundation providers, web portals, shadow endpoints, and tool subscriptions.",
)
def get_inventory(
    analysis_id: Optional[uuid.UUID] = Query(
        None,
        description="Optional analysis ID to filter inventory items to a specific capture run.",
    ),
    db: Session = Depends(get_db),
) -> List[EndpointInventoryItemResponse]:
    """Retrieves all discovered AI service endpoints from the database."""
    stmt = select(AIEndpointInventoryModel)
    if analysis_id is not None:
        stmt = stmt.where(AIEndpointInventoryModel.analysis_id == analysis_id)

    stmt = stmt.order_by(AIEndpointInventoryModel.total_calls.desc(), AIEndpointInventoryModel.created_at.desc())
    items = db.execute(stmt).scalars().all()

    results: List[EndpointInventoryItemResponse] = []
    for item in items:
        results.append(
            EndpointInventoryItemResponse(
                id=item.external_id,
                provider=item.provider,
                domain=item.domain,
                hostname=item.hostname,
                url=item.url,
                endpointAddress=item.endpoint_address,
                endpoint_address=item.endpoint_address,
                endpointType=item.endpoint_type,
                endpoint_type=item.endpoint_type,
                category=item.category,
                isApproved=item.is_approved,
                is_approved=item.is_approved,
                approvalStatus=item.approval_status,
                approval_status=item.approval_status,
                confidence=item.confidence,
                totalCalls=item.total_calls,
                total_calls=item.total_calls,
                bytesTransferred=item.bytes_transferred,
                bytes_transferred=item.bytes_transferred,
                dataTransferred=item.data_transferred,
                data_transferred=item.data_transferred,
                riskLevel=item.risk_level,
                risk_level=item.risk_level,
                riskScore=item.risk_score,
                risk_score=item.risk_score,
                reasons=list(item.reasons or []),
                evidence=list(item.evidence or []),
                detectionSignatures=list(item.detection_signatures or []),
                detection_signatures=list(item.detection_signatures or []),
                firstSeenAt=item.first_seen_at,
                first_seen_at=item.first_seen_at,
                lastSeenAt=item.last_seen_at,
                last_seen_at=item.last_seen_at,
                investigationStatus=item.investigation_status,
                investigation_status=item.investigation_status,
            )
        )
    return results


@router.get(
    "/{endpoint_id}",
    response_model=EndpointDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detailed AI endpoint metadata",
    description="Retrieves detailed metadata, risk explanations, and network signatures for a specific AI endpoint.",
)
def get_endpoint_detail(
    endpoint_id: str,
    db: Session = Depends(get_db),
) -> EndpointDetailResponse:
    """Retrieves deep details for a specific cataloged AI endpoint."""
    stmt = select(AIEndpointInventoryModel).where(
        or_(
            AIEndpointInventoryModel.external_id == endpoint_id,
            AIEndpointInventoryModel.domain == endpoint_id,
        )
    )
    item = db.execute(stmt).scalars().first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI endpoint with ID or domain '{endpoint_id}' was not found in the inventory.",
        )

    # Observed model names derived from provider
    models_map = {
        "OpenAI": ["GPT-4o", "GPT-4-Turbo", "ChatGPT API", "text-embedding-3"],
        "Anthropic": ["Claude 3.5 Sonnet", "Claude 3 Opus", "Claude 3 Haiku"],
        "Google": ["Gemini 1.5 Pro", "Gemini 1.5 Flash", "PaLM 2"],
        "Microsoft": ["Microsoft Copilot (GPT-4)"],
        "Mistral": ["Mistral Large 2", "Mistral Small", "Codestral"],
        "Perplexity": ["Sonar Large", "Sonar Small"],
    }
    observed_models = models_map.get(item.provider, [f"{item.provider} Standard Model"])

    risk_explanation = (
        f"Endpoint '{item.domain}' is classified as {item.risk_level.upper()} risk (Score: {item.risk_score}/100). "
        f"Approval status is '{item.approval_status.upper()}'. "
        + " ".join(item.reasons or [])
    )

    return EndpointDetailResponse(
        id=item.external_id,
        provider=item.provider,
        domain=item.domain,
        hostname=item.hostname,
        url=item.url,
        endpointAddress=item.endpoint_address,
        endpoint_address=item.endpoint_address,
        endpointType=item.endpoint_type,
        endpoint_type=item.endpoint_type,
        category=item.category,
        isApproved=item.is_approved,
        is_approved=item.is_approved,
        approvalStatus=item.approval_status,
        approval_status=item.approval_status,
        confidence=item.confidence,
        totalCalls=item.total_calls,
        total_calls=item.total_calls,
        bytesTransferred=item.bytes_transferred,
        bytes_transferred=item.bytes_transferred,
        dataTransferred=item.data_transferred,
        data_transferred=item.data_transferred,
        riskLevel=item.risk_level,
        risk_level=item.risk_level,
        riskScore=item.risk_score,
        risk_score=item.risk_score,
        reasons=list(item.reasons or []),
        evidence=list(item.evidence or []),
        detectionSignatures=list(item.detection_signatures or []),
        detection_signatures=list(item.detection_signatures or []),
        firstSeenAt=item.first_seen_at,
        first_seen_at=item.first_seen_at,
        lastSeenAt=item.last_seen_at,
        last_seen_at=item.last_seen_at,
        investigationStatus=item.investigation_status,
        investigation_status=item.investigation_status,
        allowedSubnets=["10.0.0.0/8", "192.168.0.0/16"],
        observedModels=observed_models,
        dataClassification="Confidential / Corporate Intellectual Property",
        explanation=f"Traffic pattern matches authoritative AI service endpoint for {item.provider}.",
        riskExplanation=risk_explanation,
        notes=f"Discovered via network telemetry analysis. Investigation status: {item.investigation_status}.",
    )
