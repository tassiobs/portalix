"""add fanout and task comments

Revision ID: b7e1a4f2c8d3
Revises: a3f8c2d1e5b9
Create Date: 2026-09-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7e1a4f2c8d3'
down_revision: Union[str, None] = 'a3f8c2d1e5b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('task_definitions', sa.Column('fan_out', sa.Boolean(), nullable=False, server_default='false'))

    op.create_table(
        'task_comments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('task_instance_id', sa.UUID(), nullable=False),
        sa.Column('author_user_id', sa.UUID(), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('file_url', sa.String(), nullable=True),
        sa.Column('file_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['task_instance_id'], ['task_instances.id']),
        sa.ForeignKeyConstraint(['author_user_id'], ['org_users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_task_comments_task_instance_id', 'task_comments', ['task_instance_id'])


def downgrade() -> None:
    op.drop_index('ix_task_comments_task_instance_id', table_name='task_comments')
    op.drop_table('task_comments')
    op.drop_column('task_definitions', 'fan_out')
