"""create ai inventory and risk tables

Revision ID: 7a8b9c0d1e2f
Revises: 574751755ecb
Create Date: 2026-10-10 02:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a8b9c0d1e2f'
down_revision: Union[str, Sequence[str], None] = '574751755ecb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('ai_endpoint_inventory',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('analysis_id', sa.Uuid(), nullable=False),
        sa.Column('external_id', sa.String(length=64), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('hostname', sa.String(length=255), nullable=False),
        sa.Column('url', sa.String(length=512), nullable=False),
        sa.Column('endpoint_address', sa.String(length=255), nullable=False),
        sa.Column('endpoint_type', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('is_approved', sa.Boolean(), nullable=False),
        sa.Column('approval_status', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('total_calls', sa.Integer(), nullable=False),
        sa.Column('bytes_transferred', sa.BigInteger(), nullable=False),
        sa.Column('data_transferred', sa.String(length=50), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=False),
        sa.Column('reasons', sa.JSON(), nullable=True),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column('detection_signatures', sa.JSON(), nullable=True),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('investigation_status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['traffic_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_endpoint_inventory_id'), 'ai_endpoint_inventory', ['id'], unique=False)
    op.create_index(op.f('ix_ai_endpoint_inventory_analysis_id'), 'ai_endpoint_inventory', ['analysis_id'], unique=False)
    op.create_index(op.f('ix_ai_endpoint_inventory_domain'), 'ai_endpoint_inventory', ['domain'], unique=False)
    op.create_index(op.f('ix_ai_endpoint_inventory_external_id'), 'ai_endpoint_inventory', ['external_id'], unique=False)
    op.create_index(op.f('ix_ai_endpoint_inventory_provider'), 'ai_endpoint_inventory', ['provider'], unique=False)
    op.create_index(op.f('ix_ai_endpoint_inventory_is_approved'), 'ai_endpoint_inventory', ['is_approved'], unique=False)
    op.create_index(op.f('ix_ai_endpoint_inventory_approval_status'), 'ai_endpoint_inventory', ['approval_status'], unique=False)
    op.create_index(op.f('ix_ai_endpoint_inventory_risk_level'), 'ai_endpoint_inventory', ['risk_level'], unique=False)

    op.create_table('risk_findings',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('analysis_id', sa.Uuid(), nullable=False),
        sa.Column('external_id', sa.String(length=64), nullable=False),
        sa.Column('target', sa.String(length=255), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('endpoint', sa.String(length=255), nullable=False),
        sa.Column('endpoint_hostname', sa.String(length=255), nullable=False),
        sa.Column('risk_score', sa.Integer(), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('is_approved', sa.Boolean(), nullable=False),
        sa.Column('approval_status', sa.String(length=50), nullable=False),
        sa.Column('policy_rule', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('reasons', sa.JSON(), nullable=True),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('investigation_status', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['analysis_id'], ['traffic_analyses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_findings_id'), 'risk_findings', ['id'], unique=False)
    op.create_index(op.f('ix_risk_findings_analysis_id'), 'risk_findings', ['analysis_id'], unique=False)
    op.create_index(op.f('ix_risk_findings_external_id'), 'risk_findings', ['external_id'], unique=False)
    op.create_index(op.f('ix_risk_findings_target'), 'risk_findings', ['target'], unique=False)
    op.create_index(op.f('ix_risk_findings_provider'), 'risk_findings', ['provider'], unique=False)
    op.create_index(op.f('ix_risk_findings_risk_score'), 'risk_findings', ['risk_score'], unique=False)
    op.create_index(op.f('ix_risk_findings_risk_level'), 'risk_findings', ['risk_level'], unique=False)
    op.create_index(op.f('ix_risk_findings_is_approved'), 'risk_findings', ['is_approved'], unique=False)


def downgrade() -> None:
    op.drop_table('risk_findings')
    op.drop_table('ai_endpoint_inventory')
