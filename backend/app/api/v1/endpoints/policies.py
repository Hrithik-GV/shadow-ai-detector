import logging
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import AdminUser, get_current_admin
from app.db.session import get_db
from app.schemas.governance import (
    PolicyAuditLogResponse,
    PolicyCreateRequest,
    PolicyResponse,
    PolicyStatusUpdateRequest,
    PolicySummaryMetricsResponse,
    PolicyUpdateRequest,
)
from app.services.policy_service import PolicyService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=List[PolicyResponse],
    status_code=status.HTTP_200_OK,
    summary="List enterprise AI governance policies",
    description="Retrieves catalog of active and historical AI provider approval policies.",
)
def list_policies(
    is_enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    approval_status: Optional[str] = Query(None, description="Filter by approval status ('approved' or 'unapproved')"),
    search: Optional[str] = Query(None, description="Search by provider name, description, or policy rule"),
    db: Session = Depends(get_db),
) -> List[PolicyResponse]:
    """Retrieves policies from PostgreSQL."""
    policies = PolicyService.list_policies(
        db=db,
        is_enabled=is_enabled,
        approval_status=approval_status,
        search=search,
    )
    return [
        PolicyResponse(
            id=p.id,
            externalId=p.external_id,
            external_id=p.external_id,
            providerName=p.provider_name,
            provider_name=p.provider_name,
            domainSignatures=list(p.domain_signatures or []),
            domain_signatures=list(p.domain_signatures or []),
            approvalStatus=p.approval_status,
            approval_status=p.approval_status,
            isApproved=(p.approval_status.lower() == "approved"),
            isEnabled=p.is_enabled,
            is_enabled=p.is_enabled,
            policyRule=p.policy_rule,
            policy_rule=p.policy_rule,
            description=p.description,
            createdBy=p.created_by,
            created_by=p.created_by,
            updatedBy=p.updated_by,
            updated_by=p.updated_by,
            createdAt=p.created_at,
            created_at=p.created_at,
            updatedAt=p.updated_at,
            updated_at=p.updated_at,
        )
        for p in policies
    ]


@router.get(
    "/summary",
    response_model=PolicySummaryMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get policy summary metrics",
    description="Returns aggregate counts of approved, unapproved, and disabled AI provider policies.",
)
def get_policy_summary(
    db: Session = Depends(get_db),
) -> PolicySummaryMetricsResponse:
    """Returns overview statistics of AI governance policies."""
    all_policies = PolicyService.list_policies(db=db)
    total = len(all_policies)
    disabled = sum(1 for p in all_policies if not p.is_enabled)
    approved = sum(1 for p in all_policies if p.is_enabled and p.approval_status.lower() == "approved")
    unapproved = sum(1 for p in all_policies if p.is_enabled and p.approval_status.lower() in ["unapproved", "blocked", "restricted"])
    active_approved = PolicyService.get_effective_approved_providers(db)

    return PolicySummaryMetricsResponse(
        totalPolicies=total,
        total_policies=total,
        approvedPolicies=approved,
        approved_policies=approved,
        unapprovedPolicies=unapproved,
        unapproved_policies=unapproved,
        disabledPolicies=disabled,
        disabled_policies=disabled,
        activeApprovedProviders=active_approved,
        active_approved_providers=active_approved,
    )


@router.get(
    "/audit-logs",
    response_model=List[PolicyAuditLogResponse],
    status_code=status.HTTP_200_OK,
    summary="Get policy audit logs",
    description="Retrieves chronological audit trail of administrative policy modifications. Requires administrative authentication.",
)
def get_audit_logs(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of log records to return"),
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> List[PolicyAuditLogResponse]:
    """Retrieves policy audit history with pagination and admin authentication."""
    logs = PolicyService.get_audit_logs(db=db, skip=skip, limit=limit)
    return [
        PolicyAuditLogResponse(
            id=log.id,
            policyId=log.policy_id,
            policy_id=log.policy_id,
            action=log.action,
            providerName=log.provider_name,
            provider_name=log.provider_name,
            previousState=log.previous_state,
            previous_state=log.previous_state,
            newState=log.new_state,
            new_state=log.new_state,
            performedBy=log.performed_by,
            performed_by=log.performed_by,
            details=log.details,
            outcome=(log.new_state or {}).get("outcome", "SUCCESS") if isinstance(log.new_state, dict) else "SUCCESS",
            timestamp=log.timestamp,
        )
        for log in logs
    ]


@router.get(
    "/{policy_id}",
    response_model=PolicyResponse,
    status_code=status.HTTP_200_OK,
    summary="Get individual AI governance policy",
    description="Retrieves a specific policy by its ID or external ID.",
)
def get_policy(
    policy_id: str,
    db: Session = Depends(get_db),
) -> PolicyResponse:
    """Retrieves single policy."""
    policy = PolicyService.get_policy(db=db, policy_id=policy_id)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Governance policy '{policy_id}' was not found.",
        )
    return PolicyResponse(
        id=policy.id,
        externalId=policy.external_id,
        external_id=policy.external_id,
        providerName=policy.provider_name,
        provider_name=policy.provider_name,
        domainSignatures=list(policy.domain_signatures or []),
        domain_signatures=list(policy.domain_signatures or []),
        approvalStatus=policy.approval_status,
        approval_status=policy.approval_status,
        isApproved=(policy.approval_status.lower() == "approved"),
        isEnabled=policy.is_enabled,
        is_enabled=policy.is_enabled,
        policyRule=policy.policy_rule,
        policy_rule=policy.policy_rule,
        description=policy.description,
        createdBy=policy.created_by,
        created_by=policy.created_by,
        updatedBy=policy.updated_by,
        updated_by=policy.updated_by,
        createdAt=policy.created_at,
        created_at=policy.created_at,
        updatedAt=policy.updated_at,
        updated_at=policy.updated_at,
    )


@router.post(
    "",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create AI governance policy",
    description="Creates a new provider governance policy. Requires administrative authentication.",
)
def create_policy(
    data: PolicyCreateRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> PolicyResponse:
    """Creates a new policy with admin authentication."""
    policy = PolicyService.create_policy(db=db, data=data, admin=admin)
    return PolicyResponse(
        id=policy.id,
        externalId=policy.external_id,
        external_id=policy.external_id,
        providerName=policy.provider_name,
        provider_name=policy.provider_name,
        domainSignatures=list(policy.domain_signatures or []),
        domain_signatures=list(policy.domain_signatures or []),
        approvalStatus=policy.approval_status,
        approval_status=policy.approval_status,
        isApproved=(policy.approval_status.lower() == "approved"),
        isEnabled=policy.is_enabled,
        is_enabled=policy.is_enabled,
        policyRule=policy.policy_rule,
        policy_rule=policy.policy_rule,
        description=policy.description,
        createdBy=policy.created_by,
        created_by=policy.created_by,
        updatedBy=policy.updated_by,
        updated_by=policy.updated_by,
        createdAt=policy.created_at,
        created_at=policy.created_at,
        updatedAt=policy.updated_at,
        updated_at=policy.updated_at,
    )


@router.put(
    "/{policy_id}",
    response_model=PolicyResponse,
    status_code=status.HTTP_200_OK,
    summary="Update AI governance policy",
    description="Updates policy configuration settings. Requires administrative authentication.",
)
def update_policy(
    policy_id: str,
    data: PolicyUpdateRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> PolicyResponse:
    """Updates a policy."""
    policy = PolicyService.update_policy(db=db, policy_id=policy_id, data=data, admin=admin)
    return PolicyResponse(
        id=policy.id,
        externalId=policy.external_id,
        external_id=policy.external_id,
        providerName=policy.provider_name,
        provider_name=policy.provider_name,
        domainSignatures=list(policy.domain_signatures or []),
        domain_signatures=list(policy.domain_signatures or []),
        approvalStatus=policy.approval_status,
        approval_status=policy.approval_status,
        isApproved=(policy.approval_status.lower() == "approved"),
        isEnabled=policy.is_enabled,
        is_enabled=policy.is_enabled,
        policyRule=policy.policy_rule,
        policy_rule=policy.policy_rule,
        description=policy.description,
        createdBy=policy.created_by,
        created_by=policy.created_by,
        updatedBy=policy.updated_by,
        updated_by=policy.updated_by,
        createdAt=policy.created_at,
        created_at=policy.created_at,
        updatedAt=policy.updated_at,
        updated_at=policy.updated_at,
    )


@router.patch(
    "/{policy_id}/status",
    response_model=PolicyResponse,
    status_code=status.HTTP_200_OK,
    summary="Change approval status of policy",
    description="Quickly toggles policy between approved and unapproved/blocked. Requires administrative authentication.",
)
def update_policy_status(
    policy_id: str,
    data: PolicyStatusUpdateRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> PolicyResponse:
    """Toggles or updates approval status."""
    policy = PolicyService.update_policy_status(
        db=db,
        policy_id=policy_id,
        new_status=data.approval_status,
        admin=admin,
        notes=data.notes,
    )
    return PolicyResponse(
        id=policy.id,
        externalId=policy.external_id,
        external_id=policy.external_id,
        providerName=policy.provider_name,
        provider_name=policy.provider_name,
        domainSignatures=list(policy.domain_signatures or []),
        domain_signatures=list(policy.domain_signatures or []),
        approvalStatus=policy.approval_status,
        approval_status=policy.approval_status,
        isApproved=(policy.approval_status.lower() == "approved"),
        isEnabled=policy.is_enabled,
        is_enabled=policy.is_enabled,
        policyRule=policy.policy_rule,
        policy_rule=policy.policy_rule,
        description=policy.description,
        createdBy=policy.created_by,
        created_by=policy.created_by,
        updatedBy=policy.updated_by,
        updated_by=policy.updated_by,
        createdAt=policy.created_at,
        created_at=policy.created_at,
        updatedAt=policy.updated_at,
        updated_at=policy.updated_at,
    )


@router.post(
    "/{policy_id}/disable",
    response_model=PolicyResponse,
    status_code=status.HTTP_200_OK,
    summary="Disable an AI governance policy",
    description="Disables an active policy rule safely. Requires administrative authentication.",
)
def disable_policy(
    policy_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> PolicyResponse:
    """Disables policy rule."""
    policy = PolicyService.disable_policy(db=db, policy_id=policy_id, admin=admin)
    return PolicyResponse(
        id=policy.id,
        externalId=policy.external_id,
        external_id=policy.external_id,
        providerName=policy.provider_name,
        provider_name=policy.provider_name,
        domainSignatures=list(policy.domain_signatures or []),
        domain_signatures=list(policy.domain_signatures or []),
        approvalStatus=policy.approval_status,
        approval_status=policy.approval_status,
        isApproved=(policy.approval_status.lower() == "approved"),
        isEnabled=policy.is_enabled,
        is_enabled=policy.is_enabled,
        policyRule=policy.policy_rule,
        policy_rule=policy.policy_rule,
        description=policy.description,
        createdBy=policy.created_by,
        created_by=policy.created_by,
        updatedBy=policy.updated_by,
        updated_by=policy.updated_by,
        createdAt=policy.created_at,
        created_at=policy.created_at,
        updatedAt=policy.updated_at,
        updated_at=policy.updated_at,
    )


@router.delete(
    "/{policy_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an AI governance policy",
    description="Deletes policy record with audit trail. Requires administrative authentication.",
)
def delete_policy(
    policy_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Deletes policy record."""
    PolicyService.delete_policy(db=db, policy_id=policy_id, admin=admin)
    return {"success": True, "message": f"Governance policy '{policy_id}' was successfully deleted."}
