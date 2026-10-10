import uuid
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.auth import AdminUser
from app.core.config import settings
from app.models.governance import AIGovernancePolicyModel, PolicyAuditLogModel
from app.schemas.governance import PolicyCreateRequest, PolicyUpdateRequest

logger = logging.getLogger(__name__)


class PolicyService:
    """Service governing AI enterprise policies, deterministic precedence, and audit logging."""

    @staticmethod
    def list_policies(
        db: Session,
        is_enabled: Optional[bool] = None,
        approval_status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[AIGovernancePolicyModel]:
        """Retrieves policies from PostgreSQL with optional filtering."""
        stmt = select(AIGovernancePolicyModel)
        if is_enabled is not None:
            stmt = stmt.where(AIGovernancePolicyModel.is_enabled == is_enabled)
        if approval_status is not None:
            stmt = stmt.where(AIGovernancePolicyModel.approval_status == approval_status.lower())
        if search:
            pattern = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    AIGovernancePolicyModel.provider_name.ilike(pattern),
                    AIGovernancePolicyModel.policy_rule.ilike(pattern),
                    AIGovernancePolicyModel.description.ilike(pattern),
                )
            )

        stmt = stmt.order_by(AIGovernancePolicyModel.created_at.desc())
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def get_policy(db: Session, policy_id: Union[str, uuid.UUID]) -> Optional[AIGovernancePolicyModel]:
        """Looks up a policy by primary UUID or external_id."""
        if isinstance(policy_id, uuid.UUID):
            return db.get(AIGovernancePolicyModel, policy_id)

        try:
            val_uuid = uuid.UUID(str(policy_id))
            stmt = select(AIGovernancePolicyModel).where(
                or_(
                    AIGovernancePolicyModel.id == val_uuid,
                    AIGovernancePolicyModel.external_id == str(policy_id),
                )
            )
        except ValueError:
            stmt = select(AIGovernancePolicyModel).where(
                AIGovernancePolicyModel.external_id == str(policy_id)
            )

        return db.execute(stmt).scalars().first()

    @staticmethod
    def create_policy(
        db: Session,
        data: PolicyCreateRequest,
        admin: AdminUser,
    ) -> AIGovernancePolicyModel:
        """Creates an enterprise AI governance policy and logs the audit event."""
        try:
            # Check for duplicate active policy with the same provider name
            existing_stmt = select(AIGovernancePolicyModel).where(
                AIGovernancePolicyModel.provider_name.ilike(data.provider_name),
                AIGovernancePolicyModel.is_enabled == True,  # noqa: E712
            )
            existing = db.execute(existing_stmt).scalars().first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"An active policy for provider '{data.provider_name}' already exists (ID: {existing.external_id}). Update the existing policy instead of creating a duplicate.",
                )

            external_id = f"POL-{uuid.uuid4().hex[:10].upper()}"
            is_approved = data.approval_status.lower() == "approved"
            rule = data.policy_rule or (
                "POLICY-AI-00: Approved Enterprise Provider"
                if is_approved
                else "POLICY-AI-01: Prohibited Shadow AI Provider"
            )

            policy = AIGovernancePolicyModel(
                external_id=external_id,
                provider_name=data.provider_name,
                domain_signatures=data.domain_signatures,
                approval_status=data.approval_status.lower(),
                is_enabled=data.is_enabled,
                policy_rule=rule,
                description=data.description,
                created_by=admin.username,
                updated_by=admin.username,
            )
            db.add(policy)
            db.flush()

            # Audit log entry with outcome and before/after values
            audit_log = PolicyAuditLogModel(
                policy_id=policy.id,
                action="create",
                provider_name=policy.provider_name,
                previous_state=None,
                new_state={
                    "external_id": policy.external_id,
                    "provider_name": policy.provider_name,
                    "approval_status": policy.approval_status,
                    "domain_signatures": policy.domain_signatures,
                    "is_enabled": policy.is_enabled,
                    "policy_rule": policy.policy_rule,
                    "outcome": "SUCCESS",
                },
                performed_by=admin.username,
                details=f"Outcome: SUCCESS. Created policy for '{policy.provider_name}' with status '{policy.approval_status}'.",
            )
            db.add(audit_log)
            db.commit()
            db.refresh(policy)
            logger.info("Admin '%s' created AI governance policy '%s' (%s)", admin.username, policy.provider_name, policy.external_id)
            return policy
        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Database error while creating policy for '%s': %s", data.provider_name, exc)
            raise

    @staticmethod
    def update_policy(
        db: Session,
        policy_id: Union[str, uuid.UUID],
        data: PolicyUpdateRequest,
        admin: AdminUser,
    ) -> AIGovernancePolicyModel:
        """Updates an existing policy and writes an audit log."""
        try:
            policy = PolicyService.get_policy(db, policy_id)
            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Governance policy '{policy_id}' was not found.",
                )

            prev_state = {
                "provider_name": policy.provider_name,
                "approval_status": policy.approval_status,
                "domain_signatures": list(policy.domain_signatures or []),
                "is_enabled": policy.is_enabled,
                "policy_rule": policy.policy_rule,
                "description": policy.description,
            }

            # If changing provider_name, ensure no other active policy has that name
            if data.provider_name and data.provider_name.lower() != policy.provider_name.lower():
                conflict_stmt = select(AIGovernancePolicyModel).where(
                    AIGovernancePolicyModel.provider_name.ilike(data.provider_name),
                    AIGovernancePolicyModel.is_enabled == True,  # noqa: E712
                    AIGovernancePolicyModel.id != policy.id,
                )
                if db.execute(conflict_stmt).scalars().first():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Another active policy for provider '{data.provider_name}' already exists.",
                    )
                policy.provider_name = data.provider_name

            if data.domain_signatures is not None:
                policy.domain_signatures = data.domain_signatures
            if data.approval_status is not None:
                policy.approval_status = data.approval_status.lower()
            if data.is_enabled is not None:
                policy.is_enabled = data.is_enabled
            if data.policy_rule is not None:
                policy.policy_rule = data.policy_rule
            if data.description is not None:
                policy.description = data.description

            policy.updated_by = admin.username
            policy.updated_at = datetime.now(timezone.utc)

            new_state = {
                "provider_name": policy.provider_name,
                "approval_status": policy.approval_status,
                "domain_signatures": list(policy.domain_signatures or []),
                "is_enabled": policy.is_enabled,
                "policy_rule": policy.policy_rule,
                "description": policy.description,
                "outcome": "SUCCESS",
            }

            audit_log = PolicyAuditLogModel(
                policy_id=policy.id,
                action="update",
                provider_name=policy.provider_name,
                previous_state=prev_state,
                new_state=new_state,
                performed_by=admin.username,
                details=f"Outcome: SUCCESS. Updated policy configuration for '{policy.provider_name}'.",
            )
            db.add(audit_log)
            db.commit()
            db.refresh(policy)
            logger.info("Admin '%s' updated AI policy '%s' (%s)", admin.username, policy.provider_name, policy.external_id)
            return policy
        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Database error while updating policy '%s': %s", policy_id, exc)
            raise

    @staticmethod
    def update_policy_status(
        db: Session,
        policy_id: Union[str, uuid.UUID],
        new_status: str,
        admin: AdminUser,
        notes: Optional[str] = None,
    ) -> AIGovernancePolicyModel:
        """Toggles or updates the approval status of an existing policy."""
        try:
            policy = PolicyService.get_policy(db, policy_id)
            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Governance policy '{policy_id}' was not found.",
                )

            prev_status = policy.approval_status
            cleaned_status = new_status.strip().lower()
            policy.approval_status = cleaned_status
            policy.updated_by = admin.username
            policy.updated_at = datetime.now(timezone.utc)

            # Update default rule text if using standard rules
            if cleaned_status == "approved" and "POLICY-AI-01" in policy.policy_rule:
                policy.policy_rule = "POLICY-AI-00: Approved Enterprise Provider"
            elif cleaned_status != "approved" and "POLICY-AI-00" in policy.policy_rule:
                policy.policy_rule = "POLICY-AI-01: Prohibited Shadow AI Provider"

            audit_log = PolicyAuditLogModel(
                policy_id=policy.id,
                action="status_change",
                provider_name=policy.provider_name,
                previous_state={"approval_status": prev_status},
                new_state={"approval_status": cleaned_status, "outcome": "SUCCESS"},
                performed_by=admin.username,
                details=notes or f"Outcome: SUCCESS. Approval status changed from '{prev_status}' to '{cleaned_status}'.",
            )
            db.add(audit_log)
            db.commit()
            db.refresh(policy)
            logger.info("Admin '%s' changed status of policy '%s' from %s to %s", admin.username, policy.provider_name, prev_status, cleaned_status)
            return policy
        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Database error while updating status of policy '%s': %s", policy_id, exc)
            raise

    @staticmethod
    def disable_policy(
        db: Session,
        policy_id: Union[str, uuid.UUID],
        admin: AdminUser,
    ) -> AIGovernancePolicyModel:
        """Disables an AI governance policy safely without deleting history."""
        try:
            policy = PolicyService.get_policy(db, policy_id)
            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Governance policy '{policy_id}' was not found.",
                )

            policy.is_enabled = False
            policy.updated_by = admin.username
            policy.updated_at = datetime.now(timezone.utc)

            audit_log = PolicyAuditLogModel(
                policy_id=policy.id,
                action="disable",
                provider_name=policy.provider_name,
                previous_state={"is_enabled": True},
                new_state={"is_enabled": False, "outcome": "SUCCESS"},
                performed_by=admin.username,
                details=f"Outcome: SUCCESS. Policy disabled by admin '{admin.username}'.",
            )
            db.add(audit_log)
            db.commit()
            db.refresh(policy)
            logger.info("Admin '%s' disabled policy '%s' (%s)", admin.username, policy.provider_name, policy.external_id)
            return policy
        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Database error while disabling policy '%s': %s", policy_id, exc)
            raise

    @staticmethod
    def delete_policy(
        db: Session,
        policy_id: Union[str, uuid.UUID],
        admin: AdminUser,
    ) -> bool:
        """Deletes a policy record after preserving the audit log trail."""
        try:
            policy = PolicyService.get_policy(db, policy_id)
            if not policy:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Governance policy '{policy_id}' was not found.",
                )

            audit_log = PolicyAuditLogModel(
                policy_id=policy.id,
                action="delete",
                provider_name=policy.provider_name,
                previous_state={
                    "external_id": policy.external_id,
                    "provider_name": policy.provider_name,
                    "approval_status": policy.approval_status,
                    "is_enabled": policy.is_enabled,
                },
                new_state={"outcome": "SUCCESS"},
                performed_by=admin.username,
                details=f"Outcome: SUCCESS. Policy '{policy.provider_name}' deleted.",
            )
            db.add(audit_log)
            db.delete(policy)
            db.commit()
            logger.info("Admin '%s' deleted policy '%s'", admin.username, policy.provider_name)
            return True
        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            logger.error("Database error while deleting policy '%s': %s", policy_id, exc)
            raise

    @staticmethod
    def get_audit_logs(db: Session, skip: int = 0, limit: int = 100) -> List[PolicyAuditLogModel]:
        """Retrieves history of administrative changes with offset and limit pagination."""
        stmt = (
            select(PolicyAuditLogModel)
            .order_by(PolicyAuditLogModel.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def resolve_effective_approval(
        db: Session,
        provider_name: str,
        target_domain: Optional[str] = None,
    ) -> Tuple[bool, str, str]:
        """Resolves effective approval status enforcing deterministic conflict precedence.

        Deterministic Precedence Rules:
          1. Disabled policies (is_enabled=False) are ignored.
          2. Denial / Unapproved Overrides Approval in Any Conflict:
             If ANY active policy marks this provider or domain as 'unapproved', 'blocked',
             or 'restricted', the resolution is strictly UNAPPROVED (is_approved=False).
             An ambiguous or conflicting policy NEVER silently yields an approval.
          3. Specific domain match: If domain is explicitly governed by an approved policy,
             and no unapproved rule exists for this provider or domain -> APPROVED.
          4. General provider match: If provider is governed by an approved policy,
             and no unapproved rule exists -> APPROVED.
          5. Fallback: If no database policy exists, fallback to settings.APPROVED_AI_PROVIDERS.

        Returns:
          tuple[is_approved: bool, approval_status: str, policy_rule: str]
        """
        # Load all active policies
        stmt = select(AIGovernancePolicyModel).where(AIGovernancePolicyModel.is_enabled == True)  # noqa: E712
        active_policies = list(db.execute(stmt).scalars().all())

        if not active_policies:
            # Fallback to configured environment defaults
            approved_list = [p.lower() for p in settings.APPROVED_AI_PROVIDERS]
            is_app = provider_name.lower() in approved_list
            status_str = "approved" if is_app else "unapproved"
            rule_str = (
                "POLICY-AI-00: Approved Enterprise Provider"
                if is_app
                else "POLICY-AI-01: Unapproved Shadow AI Provider"
            )
            return is_app, status_str, rule_str

        # Find applicable policies for this provider or domain
        matching_policies: List[AIGovernancePolicyModel] = []
        for p in active_policies:
            if p.provider_name.strip().lower() == provider_name.strip().lower():
                matching_policies.append(p)
            elif target_domain and p.domain_signatures:
                clean_target = target_domain.strip().lower()
                for sig in p.domain_signatures:
                    clean_sig = sig.strip().lower()
                    if clean_target == clean_sig or clean_target.endswith(f".{clean_sig}"):
                        matching_policies.append(p)
                        break

        # Rule 2: Deterministic Conflict Precedence -> UNAPPROVED WINS
        has_unapproved_conflict = any(
            p.approval_status.lower() in ["unapproved", "blocked", "restricted"]
            for p in matching_policies
        )
        if has_unapproved_conflict:
            # At least one active policy prohibits this service
            prohibiting_policy = next(
                p for p in matching_policies
                if p.approval_status.lower() in ["unapproved", "blocked", "restricted"]
            )
            return (
                False,
                prohibiting_policy.approval_status.lower(),
                prohibiting_policy.policy_rule or "POLICY-AI-01: Prohibited Shadow AI Provider",
            )

        # Rule 3 & 4: If matching active policies exist and all indicate approval
        has_approved = any(
            p.approval_status.lower() == "approved"
            for p in matching_policies
        )
        if has_approved:
            approving_policy = next(
                p for p in matching_policies
                if p.approval_status.lower() == "approved"
            )
            return (
                True,
                "approved",
                approving_policy.policy_rule or "POLICY-AI-00: Approved Enterprise Provider",
            )

        # Rule 5: Fallback if no specific database rule matches this provider or domain
        approved_list = [p.lower() for p in settings.APPROVED_AI_PROVIDERS]
        is_app = provider_name.lower() in approved_list
        status_str = "approved" if is_app else "unapproved"
        rule_str = (
            "POLICY-AI-00: Approved Enterprise Provider"
            if is_app
            else "POLICY-AI-01: Unapproved Shadow AI Provider"
        )
        return is_app, status_str, rule_str

    @staticmethod
    def get_effective_approved_providers(db: Session) -> List[str]:
        """Returns the list of provider names currently resolving to approved in the database."""
        stmt = select(AIGovernancePolicyModel).where(AIGovernancePolicyModel.is_enabled == True)  # noqa: E712
        policies = list(db.execute(stmt).scalars().all())

        if not policies:
            return list(settings.APPROVED_AI_PROVIDERS)

        approved_providers: set[str] = set()
        unapproved_providers: set[str] = set()

        for p in policies:
            if p.approval_status.lower() in ["unapproved", "blocked", "restricted"]:
                unapproved_providers.add(p.provider_name.strip())
            elif p.approval_status.lower() == "approved":
                approved_providers.add(p.provider_name.strip())

        # Unapproved strictly overrides approved in any conflict
        effective = {p for p in approved_providers if p not in unapproved_providers}
        return sorted(list(effective))


default_policy_service = PolicyService()
