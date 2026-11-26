"""Add type_text to stoette_til_bil.

Revision ID: 3f1c2a7b8d4e
Revises: 9db5b062c1a7
"""
from alembic import op
import sqlalchemy as sa


revision = '3f1c2a7b8d4e'
down_revision = '9db5b062c1a7'
branch_labels = None
depends_on = None

SCHEMA = 'xflow_nexus'
TABLE = 'stoette_til_bil'
COLUMN = 'type_text'


def _has_column():
    inspector = sa.inspect(op.get_bind())
    return any(col['name'] == COLUMN for col in inspector.get_columns(TABLE, schema=SCHEMA))


def upgrade():
    # Some environments may already have the column (created via create_all before migrations existed)
    if _has_column():
        return
    op.add_column(
        TABLE,
        sa.Column(COLUMN, sa.String(255), nullable=False, server_default='§ 114 trivsel'),
        schema=SCHEMA,
    )
    op.alter_column(TABLE, COLUMN, server_default=None, schema=SCHEMA)


def downgrade():
    if _has_column():
        op.drop_column(TABLE, COLUMN, schema=SCHEMA)
