"""soft_delete_locations

Revision ID: 9a9e891bb23e
Revises: eed5157011f7
Create Date: 2023-11-08 16:06:27.290498

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9a9e891bb23e"
down_revision = "eed5157011f7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "alert_events_location_id_fkey", "alert_events", type_="foreignkey"
    )
    op.create_foreign_key(
        "alert_events_location_id_fkey",
        "alert_events",
        "locations",
        ["location_id"],
        ["id"],
    )
    op.drop_constraint("computers_location_id_fkey", "computers", type_="foreignkey")
    op.create_foreign_key(
        "computers_location_id_fkey", "computers", "locations", ["location_id"], ["id"]
    )
    op.add_column(
        "locations",
        sa.Column(
            "is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=True
        ),
    )
    op.add_column("locations", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.create_unique_constraint(
        "unique_location_per_company", "locations", ["company_id", "name"]
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("unique_location_per_company", "locations", type_="unique")
    op.drop_column("locations", "deleted_at")
    op.drop_column("locations", "is_deleted")
    op.drop_constraint("computers_location_id_fkey", "computers", type_="foreignkey")
    op.create_foreign_key(
        "computers_location_id_fkey",
        "computers",
        "locations",
        ["location_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "alert_events_location_id_fkey", "alert_events", type_="foreignkey"
    )
    op.create_foreign_key(
        "alert_events_location_id_fkey",
        "alert_events",
        "locations",
        ["location_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # ### end Alembic commands ###
