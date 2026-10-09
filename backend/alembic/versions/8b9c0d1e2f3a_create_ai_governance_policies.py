"""create ai governance policies and audit logs tables

Revision ID: 8b9c0d1e2f3a
Revises: 7a8b9c0d1e2f
Create Date: 2026-10-10 03:00:00.000000

"""
from typing import Sequence, Union
import uuid
import json

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b9c0d1e2f3a'
down_revision: Union[str, Sequence[str], None] = '7a8b9c0d1e2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create ai_governance_policies table
    op.create_table(
        'ai_governance_policies',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('external_id', sa.String(length=64), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('domain_signatures', sa.JSON(), nullable=False),
        sa.Column('approval_status', sa.String(length=50), nullable=False, server_default='approved'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('policy_rule', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=100), nullable=True, server_default='system_admin'),
        sa.Column('updated_by', sa.String(length=100), nullable=True, server_default='system_admin'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_ai_governance_policies_id', 'ai_governance_policies', ['id'], unique=False)
    op.create_index('ix_ai_governance_policies_external_id', 'ai_governance_policies', ['external_id'], unique=True)
    op.create_index('ix_ai_governance_policies_provider_name', 'ai_governance_policies', ['provider_name'], unique=False)
    op.create_index('ix_ai_governance_policies_approval_status', 'ai_governance_policies', ['approval_status'], unique=False)
    op.create_index('ix_ai_governance_policies_is_enabled', 'ai_governance_policies', ['is_enabled'], unique=False)
    op.create_index('ix_ai_governance_policies_created_at', 'ai_governance_policies', ['created_at'], unique=False)
    op.create_index('ix_ai_gov_policy_provider_enabled', 'ai_governance_policies', ['provider_name', 'is_enabled'], unique=False)

    # 2. Create policy_audit_logs table
    op.create_table(
        'policy_audit_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('policy_id', sa.Uuid(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('previous_state', sa.JSON(), nullable=True),
        sa.Column('new_state', sa.JSON(), nullable=True),
        sa.Column('performed_by', sa.String(length=100), nullable=False, server_default='system_admin'),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_policy_audit_logs_id', 'policy_audit_logs', ['id'], unique=False)
    op.create_index('ix_policy_audit_logs_policy_id', 'policy_audit_logs', ['policy_id'], unique=False)
    op.create_index('ix_policy_audit_logs_action', 'policy_audit_logs', ['action'], unique=False)
    op.create_index('ix_policy_audit_logs_provider_name', 'policy_audit_logs', ['provider_name'], unique=False)
    op.create_index('ix_policy_audit_logs_timestamp', 'policy_audit_logs', ['timestamp'], unique=False)

    # 3. Seed baseline approved enterprise policy for OpenAI
    default_policy_id = uuid.uuid4()
    default_external_id = f"POL-{uuid.uuid4().hex[:10].upper()}"
    default_domains = [
        "api.openai.com",
        "chatgpt.com",
        "platform.openai.com",
        "oaistatic.com",
        "oaiusercontent.com",
    ]

    policies_table = sa.table(
        'ai_governance_policies',
        sa.column('id', sa.Uuid),
        sa.column('external_id', sa.String),
        sa.column('provider_name', sa.String),
        sa.column('domain_signatures', sa.JSON),
        sa.column('approval_status', sa.String),
        sa.column('is_enabled', sa.Boolean),
        sa.column('policy_rule', sa.String),
        sa.column('description', sa.Text),
        sa.column('created_by', sa.String),
        sa.column('updated_by', sa.String),
    )

    op.bulk_insert(
        policies_table,
        [
            {
                'id': default_policy_id,
                'external_id': default_external_id,
                'provider_name': 'OpenAI',
                'domain_signatures': default_domains,
                'approval_status': 'approved',
                'is_enabled': True,
                'policy_rule': 'POLICY-AI-00: Authorized Enterprise Provider',
                'description': 'Default authorized enterprise LLM provider configured per organization governance.',
                'created_by': 'system_initialization',
                'updated_by': 'system_initialization',
            }
        ]
    )

    audit_table = sa.table(
        'policy_audit_logs',
        sa.column('id', sa.Uuid),
        sa.column('policy_id', sa.Uuid),
        sa.column('action', sa.String),
        sa.column('provider_name', sa.String),
        sa.column('previous_state', sa.JSON),
        sa.column('new_state', sa.JSON),
        sa.column('performed_by', sa.String),
        sa.column('details', sa.Text),
    )

    op.bulk_insert(
        audit_table,
        [
            {
                'id': uuid.uuid4(),
                'policy_id': default_policy_id,
                'action': 'create',
                'provider_name': 'OpenAI',
                'previous_state': None,
                'new_state': {
                    'approval_status': 'approved',
                    'is_enabled': True,
                    'provider_name': 'OpenAI',
                },
                'performed_by': 'system_initialization',
                'details': 'Baseline policy seeded during migration.',
            }
        ]
    )


def downgrade() -> None:
    op.drop_table('policy_audit_logs')
    op.drop_table('ai_governance_policies')
