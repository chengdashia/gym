"""add adaptive diet program tables and food fiber

Revision ID: 20260711_1200
Revises: 8e3bd2a8638d
Create Date: 2026-07-11 12:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260711_1200"
down_revision = "8e3bd2a8638d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("foods", sa.Column("fiber_per_100g", sa.Numeric(8, 2), nullable=True))
    op.add_column("user_custom_foods", sa.Column("fiber_per_100g", sa.Numeric(8, 2), nullable=True))

    op.create_table(
        "diet_preferences",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("meal_count", sa.Integer(), nullable=False),
        sa.Column("allergens_json", sa.JSON(), nullable=False),
        sa.Column("preference_rules_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index("idx_diet_preferences_user", "diet_preferences", ["user_id"])

    op.create_table(
        "diet_program_templates",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("rules_json", sa.JSON(), nullable=False),
        sa.Column("applicability_json", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.UniqueConstraint("code", "version", name="uk_diet_program_template_code_version"),
    )
    op.create_index("idx_diet_program_templates_status", "diet_program_templates", ["status"])

    op.create_table(
        "user_diet_programs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("template_id", sa.BigInteger(), sa.ForeignKey("diet_program_templates.id"), nullable=False),
        sa.Column("template_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("eligibility_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("preference_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index("idx_user_diet_programs_user", "user_diet_programs", ["user_id"])
    op.create_index("idx_user_diet_programs_user_status", "user_diet_programs", ["user_id", "status"])

    op.create_table(
        "diet_program_stages",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("program_id", sa.BigInteger(), sa.ForeignKey("user_diet_programs.id"), nullable=False),
        sa.Column("stage_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("calories_kcal", sa.Numeric(8, 2), nullable=False),
        sa.Column("carbs_g", sa.Numeric(8, 2), nullable=False),
        sa.Column("protein_g", sa.Numeric(8, 2), nullable=False),
        sa.Column("fat_g", sa.Numeric(8, 2), nullable=False),
        sa.Column("observation_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("evaluation_snapshot_json", sa.JSON(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.UniqueConstraint("program_id", "stage_number", name="uk_diet_program_stage_number"),
    )
    op.create_index("idx_diet_program_stages_program", "diet_program_stages", ["program_id"])

    op.create_table(
        "meal_plan_days",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("program_id", sa.BigInteger(), sa.ForeignKey("user_diet_programs.id"), nullable=False),
        sa.Column("stage_id", sa.BigInteger(), sa.ForeignKey("diet_program_stages.id"), nullable=False),
        sa.Column("plan_date", sa.Date(), nullable=False),
        sa.Column("target_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.UniqueConstraint("program_id", "plan_date", name="uk_meal_plan_program_date"),
    )
    op.create_index("idx_meal_plan_days_stage", "meal_plan_days", ["stage_id"])

    op.create_table(
        "meal_plan_meals",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("day_id", sa.BigInteger(), sa.ForeignKey("meal_plan_days.id"), nullable=False),
        sa.Column("meal_type", sa.String(32), nullable=False),
        sa.Column("planned_time", sa.Time(), nullable=True),
        sa.Column("target_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index("idx_meal_plan_meals_day", "meal_plan_meals", ["day_id"])

    op.create_table(
        "meal_plan_items",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("meal_id", sa.BigInteger(), sa.ForeignKey("meal_plan_meals.id"), nullable=False),
        sa.Column("food_source", sa.String(32), nullable=False),
        sa.Column("food_id", sa.BigInteger(), nullable=True),
        sa.Column("custom_food_id", sa.BigInteger(), nullable=True),
        sa.Column("food_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("amount_g", sa.Numeric(8, 2), nullable=False),
        sa.Column("nutrition_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("constraint_snapshot_json", sa.JSON(), nullable=True),
        sa.Column("replaced_from_item_id", sa.BigInteger(), sa.ForeignKey("meal_plan_items.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index("idx_meal_plan_items_meal", "meal_plan_items", ["meal_id"])


def downgrade() -> None:
    op.drop_index("idx_meal_plan_items_meal", table_name="meal_plan_items")
    op.drop_table("meal_plan_items")
    op.drop_index("idx_meal_plan_meals_day", table_name="meal_plan_meals")
    op.drop_table("meal_plan_meals")
    op.drop_index("idx_meal_plan_days_stage", table_name="meal_plan_days")
    op.drop_table("meal_plan_days")
    op.drop_index("idx_diet_program_stages_program", table_name="diet_program_stages")
    op.drop_table("diet_program_stages")
    op.drop_index("idx_user_diet_programs_user_status", table_name="user_diet_programs")
    op.drop_index("idx_user_diet_programs_user", table_name="user_diet_programs")
    op.drop_table("user_diet_programs")
    op.drop_index("idx_diet_program_templates_status", table_name="diet_program_templates")
    op.drop_table("diet_program_templates")
    op.drop_index("idx_diet_preferences_user", table_name="diet_preferences")
    op.drop_table("diet_preferences")
    op.drop_column("user_custom_foods", "fiber_per_100g")
    op.drop_column("foods", "fiber_per_100g")
