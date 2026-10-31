"""create_cancellation_cases_table

Revision ID: a1b2c3d4e5f6
Revises: 9d7d58fe9eaf
Create Date: 2026-10-31 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '9d7d58fe9eaf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'cancellation_cases',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('commitment_id', sa.UUID(), nullable=False),
        sa.Column('merchant_id', sa.UUID(), nullable=True),
        sa.Column('cancellation_event_id', sa.UUID(), nullable=True),
        sa.Column('payment_mechanism', sa.String(length=50), nullable=False),
        sa.Column('playbook_key', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('completed_steps', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('evidence_references', sa.Text(), nullable=True),
        sa.Column('user_reported_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['cancellation_event_id'], ['cancellation_events.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['commitment_id'], ['commitments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['demo_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cancellation_cases_commitment', 'cancellation_cases', ['commitment_id'], unique=False)
    op.create_index('ix_cancellation_cases_created_at', 'cancellation_cases', ['created_at'], unique=False)
    op.create_index('ix_cancellation_cases_user_status', 'cancellation_cases', ['user_id', 'status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_cancellation_cases_user_status', table_name='cancellation_cases')
    op.drop_index('ix_cancellation_cases_created_at', table_name='cancellation_cases')
    op.drop_index('ix_cancellation_cases_commitment', table_name='cancellation_cases')
    op.drop_table('cancellation_cases')
