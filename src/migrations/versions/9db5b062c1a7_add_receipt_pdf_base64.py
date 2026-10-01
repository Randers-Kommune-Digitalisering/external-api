"""Add receipt PDF to existing Nexus tables.

Revision ID: 9db5b062c1a7
Revises: e0b89e51ce83
"""
from alembic import op
import sqlalchemy as sa


revision = '9db5b062c1a7'
down_revision = 'e0b89e51ce83'
branch_labels = None
depends_on = None

TABLES = (
    'personligt_hjaelpemiddel',
    'staastoettestol',
    'elscooter',
    'servicehund',
    'kommunikationshjaelpemiddel',
    'hjaelpemiddel_andre_typer_af_hjaelpemidler',
    'hjaelpemiddel_til_barn',
    'stoette_til_bil',
    'saerlig_indretning_af_bil_koerekort',
    'boligindretning',
)


def upgrade():
    for table in TABLES:
        op.add_column(table, sa.Column('receipt_pdf_base64', sa.Text(), nullable=True), schema='xflow_nexus')


def downgrade():
    for table in reversed(TABLES):
        op.drop_column(table, 'receipt_pdf_base64', schema='xflow_nexus')
