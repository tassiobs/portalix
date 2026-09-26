"""add workflow tasks

Revision ID: a3f8c2d1e5b9
Revises: 1986076e4d48
Create Date: 2026-09-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


revision: str = 'a3f8c2d1e5b9'
down_revision: Union[str, None] = '1986076e4d48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'workflows',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('request_type_id', sa.UUID(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['request_type_id'], ['request_types.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('request_type_id'),
    )

    op.create_table(
        'task_definitions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('workflow_id', sa.UUID(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('department_id', sa.UUID(), nullable=True),
        sa.Column('assignee_role', sa.String(), nullable=True),
        sa.Column('assignee_user_id', sa.UUID(), nullable=True),
        sa.Column('deadline_offset_hours', sa.Integer(), nullable=True),
        sa.Column('depends_on', ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id']),
        sa.ForeignKeyConstraint(['assignee_user_id'], ['org_users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workflow_id', 'key'),
    )

    op.create_table(
        'task_instances',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('request_id', sa.UUID(), nullable=False),
        sa.Column('task_definition_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('outcome', sa.String(), nullable=True),
        sa.Column('assigned_to_user_id', sa.UUID(), nullable=True),
        sa.Column('activated_at', sa.DateTime(), nullable=True),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['request_id'], ['requests.id']),
        sa.ForeignKeyConstraint(['task_definition_id'], ['task_definitions.id']),
        sa.ForeignKeyConstraint(['assigned_to_user_id'], ['org_users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_task_instances_request_id', 'task_instances', ['request_id'])


def downgrade() -> None:
    op.drop_index('ix_task_instances_request_id', table_name='task_instances')
    op.drop_table('task_instances')
    op.drop_table('task_definitions')
    op.drop_table('workflows')
