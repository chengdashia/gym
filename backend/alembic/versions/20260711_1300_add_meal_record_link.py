"""link recorded diet snapshots to their source meal-plan meal

Revision ID: 20260711_1300
Revises: 20260711_1200
Create Date: 2026-07-11 13:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260711_1300"
down_revision = "20260711_1200"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable keeps every pre-existing ordinary diet record valid.
    op.add_column("diet_records", sa.Column("plan_meal_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key("fk_diet_records_plan_meal", "diet_records", "meal_plan_meals", ["plan_meal_id"], ["id"])
    # A plan meal may produce several food snapshots, but any individual food
    # snapshot may only be recorded once from that meal.  The first duplicate
    # insert aborts the whole transaction, making retry/concurrent requests
    # idempotent without marking planned food as actually consumed in advance.
    op.create_unique_constraint("uk_diet_record_plan_meal_food", "diet_records", ["plan_meal_id", "food_name_snapshot"])
    op.create_index("idx_diet_records_plan_meal", "diet_records", ["plan_meal_id"])


def downgrade() -> None:
    op.drop_index("idx_diet_records_plan_meal", table_name="diet_records")
    op.drop_constraint("uk_diet_record_plan_meal_food", "diet_records", type_="unique")
    op.drop_constraint("fk_diet_records_plan_meal", "diet_records", type_="foreignkey")
    op.drop_column("diet_records", "plan_meal_id")
