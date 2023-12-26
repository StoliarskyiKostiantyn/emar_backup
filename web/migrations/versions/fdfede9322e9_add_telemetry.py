"""add_telemetry

Revision ID: fdfede9322e9
Revises: 9f7003fad01d
Create Date: 2023-12-06 16:51:17.578333

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fdfede9322e9'
down_revision = '9f7003fad01d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('telemetry_settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('send_printer_info', sa.Boolean(), nullable=True),
    sa.Column('send_agent_logs', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('company_settings_link_table',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=True),
    sa.Column('telemetry_settings_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.ForeignKeyConstraint(['telemetry_settings_id'], ['telemetry_settings.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('location_settings_link_table',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('location_id', sa.Integer(), nullable=True),
    sa.Column('telemetry_settings_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
    sa.ForeignKeyConstraint(['telemetry_settings_id'], ['telemetry_settings.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('computer_settings_link_table',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('computer_id', sa.Integer(), nullable=True),
    sa.Column('telemetry_settings_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['computer_id'], ['computers.id'], ),
    sa.ForeignKeyConstraint(['telemetry_settings_id'], ['telemetry_settings.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('computer_settings_link_table')
    op.drop_table('location_settings_link_table')
    op.drop_table('company_settings_link_table')
    op.drop_table('telemetry_settings')
    # ### end Alembic commands ###
