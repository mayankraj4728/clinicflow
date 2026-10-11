"""create appointments table

Revision ID: 0001_create_appointments
Revises:
Create Date: 2026-10-11
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_create_appointments"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("patient_name", sa.String(length=150), nullable=False),
        sa.Column("patient_email", sa.String(length=150), nullable=False, server_default=""),
        sa.Column("doctor", sa.String(length=150), nullable=False, server_default="Unassigned"),
        sa.Column("department", sa.String(length=100), nullable=False, server_default="General Medicine"),
        sa.Column("appointment_type", sa.String(length=30), nullable=False, server_default="CONSULTATION"),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="SCHEDULED"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_appointments_status", "appointments", ["status"])


def downgrade() -> None:
    op.drop_index("ix_appointments_status", table_name="appointments")
    op.drop_table("appointments")
