"""add departments

Revision ID: d1e3f5a2b4c7
Revises: c4d2e8f1a3b6
Create Date: 2026-11-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = 'd1e3f5a2b4c7'
down_revision = 'c4d2e8f1a3b6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'departments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'department_members',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('department_id', UUID(as_uuid=True), sa.ForeignKey('departments.id'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('org_users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('department_id', 'user_id'),
    )

    op.create_foreign_key(
        'fk_task_definitions_department_id',
        'task_definitions', 'departments',
        ['department_id'], ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_task_definitions_department_id', 'task_definitions', type_='foreignkey')
    op.drop_table('department_members')
    op.drop_table('departments')
