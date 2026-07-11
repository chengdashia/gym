"""anchor calendar-driven training sequences

Revision ID: 20260711_1400
Revises: 20260711_1300
Create Date: 2026-07-11 14:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260711_1400"
down_revision = "20260711_1300"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("training_plans", sa.Column("sequence_anchor_date", sa.Date(), nullable=True))
    op.add_column("training_plans", sa.Column("sequence_anchor_day_index", sa.Integer(), nullable=True))
    # Preserve every existing plan's currently displayed day on upgrade; from
    # tomorrow it advances one calendar slot at a time.
    op.execute("UPDATE training_plans SET sequence_anchor_date = CURDATE(), sequence_anchor_day_index = current_day_index WHERE schedule_type = 'sequence'")


def downgrade() -> None:
    op.drop_column("training_plans", "sequence_anchor_day_index")
    op.drop_column("training_plans", "sequence_anchor_date")
