"""add redirect_url to email_verification_tokens

Revision ID: c4d2e8f1a3b6
Revises: b7e1a4f2c8d3
Create Date: 2026-11-17

"""
from alembic import op
import sqlalchemy as sa

revision = 'c4d2e8f1a3b6'
down_revision = 'b7e1a4f2c8d3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('email_verification_tokens', sa.Column('redirect_url', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('email_verification_tokens', 'redirect_url')
