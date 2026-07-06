"""initial schema

Revision ID: 0001_init
Revises:
Create Date: 2026-07-05

"""
from alembic import op
import sqlalchemy as sa


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("openid", sa.String(128), nullable=False, unique=True),
        sa.Column("unionid", sa.String(128), nullable=True),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("nickname", sa.String(100), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("is_member", sa.Integer, nullable=False, server_default="0"),
        sa.Column("member_expired_at", sa.DateTime, nullable=True),
        sa.Column("membership_level", sa.String(32), nullable=True),
        sa.Column("photo_recognition_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_login_at", sa.DateTime, nullable=True),
        sa.Column("agreement_version", sa.String(32), nullable=True),
        sa.Column("agreement_confirmed_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )
    op.create_index("idx_users_phone", "users", ["phone"])
    op.create_index("idx_users_status", "users", ["status"])

    op.create_table(
        "user_profiles",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("gender", sa.String(16), nullable=True),
        sa.Column("age", sa.Integer, nullable=True),
        sa.Column("height_cm", sa.Numeric(6, 2), nullable=True),
        sa.Column("current_weight_kg", sa.Numeric(6, 2), nullable=True),
        sa.Column("target_weight_kg", sa.Numeric(6, 2), nullable=True),
        sa.Column("fitness_goal", sa.String(32), nullable=True),
        sa.Column("training_frequency", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
    )

    op.create_table(
        "nutrition_goals",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("calories_kcal", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("carbs_g", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("protein_g", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("fat_g", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("source", sa.String(32), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
    )

    op.create_table(
        "user_reminders",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reminder_type", sa.String(32), nullable=False),
        sa.Column("enabled", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reminder_time", sa.Time, nullable=True),
        sa.Column("weekdays", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
        sa.UniqueConstraint("user_id", "reminder_type", name="uk_user_reminder_type"),
    )

    op.create_table(
        "foods",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("calories_per_100g", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("carbs_per_100g", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("protein_per_100g", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("fat_per_100g", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("default_unit", sa.String(16), nullable=False, server_default="g"),
        sa.Column("serving_weight_g", sa.Numeric(8, 2), nullable=True),
        sa.Column("is_system", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
    )
    op.create_index("idx_foods_name", "foods", ["name"])
    op.create_index("idx_foods_category", "foods", ["category"])

    op.create_table(
        "user_custom_foods",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("calories_per_100g", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("carbs_per_100g", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("protein_per_100g", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("fat_per_100g", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("default_unit", sa.String(16), nullable=False, server_default="g"),
        sa.Column("serving_weight_g", sa.Numeric(8, 2), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )
    op.create_index("idx_custom_foods_user_name", "user_custom_foods", ["user_id", "name"])

    op.create_table(
        "diet_records",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("record_date", sa.DateTime, nullable=False),
        sa.Column("record_time", sa.Time, nullable=False),
        sa.Column("meal_type", sa.String(32), nullable=False),
        sa.Column("food_source", sa.String(32), nullable=False),
        sa.Column("food_id", sa.BigInteger, nullable=True),
        sa.Column("custom_food_id", sa.BigInteger, nullable=True),
        sa.Column("food_name_snapshot", sa.String(100), nullable=False),
        sa.Column("unit_type", sa.String(16), nullable=False),
        sa.Column("amount_g", sa.Numeric(8, 2), nullable=True),
        sa.Column("serving_count", sa.Numeric(8, 2), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("save_image", sa.Integer, nullable=False, server_default="0"),
        sa.Column("calories_kcal", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("carbs_g", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("protein_g", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("fat_g", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )
    op.create_index("idx_diet_user_date", "diet_records", ["user_id", "record_date"])
    op.create_index("idx_diet_user_meal", "diet_records", ["user_id", "meal_type"])

    op.create_table(
        "food_recognition_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("image_url", sa.String(500), nullable=False),
        sa.Column("recognition_status", sa.String(32), nullable=False, server_default="success"),
        sa.Column("candidates_json", sa.JSON, nullable=True),
        sa.Column("selected_food_id", sa.BigInteger, nullable=True),
        sa.Column("selected_custom_food_id", sa.BigInteger, nullable=True),
        sa.Column("provider", sa.String(64), nullable=False, server_default="mock"),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index("idx_recognition_user_created", "food_recognition_logs", ["user_id", "created_at"])

    op.create_table(
        "exercises",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("body_part", sa.String(64), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("is_system", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
    )
    op.create_index("idx_exercises_name", "exercises", ["name"])
    op.create_index("idx_exercises_body_part", "exercises", ["body_part"])

    op.create_table(
        "user_custom_exercises",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("body_part", sa.String(64), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )
    op.create_index("idx_user_custom_exercises", "user_custom_exercises", ["user_id", "name"])

    op.create_table(
        "training_templates",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("split_type", sa.String(32), nullable=False),
        sa.Column("difficulty", sa.String(32), nullable=True),
        sa.Column("goal", sa.String(32), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
    )

    op.create_table(
        "training_template_days",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("template_id", sa.BigInteger, sa.ForeignKey("training_templates.id"), nullable=False),
        sa.Column("day_index", sa.Integer, nullable=False),
        sa.Column("day_name", sa.String(100), nullable=False),
        sa.Column("is_rest_day", sa.Integer, nullable=False, server_default="0"),
        sa.Column("weekday", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
    )

    op.create_table(
        "training_template_exercises",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("template_day_id", sa.BigInteger, sa.ForeignKey("training_template_days.id"), nullable=False),
        sa.Column("exercise_id", sa.BigInteger, sa.ForeignKey("exercises.id"), nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("target_sets", sa.Integer, nullable=False, server_default="4"),
        sa.Column("target_reps", sa.Integer, nullable=False, server_default="10"),
        sa.Column("target_weight_kg", sa.Numeric(8, 2), nullable=True),
        sa.Column("rest_seconds", sa.Integer, nullable=False, server_default="90"),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
    )

    op.create_table(
        "training_plans",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("schedule_type", sa.String(32), nullable=False),
        sa.Column("source_template_id", sa.BigInteger, nullable=True),
        sa.Column("current_day_index", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_active", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )
    op.create_index("idx_training_plans_user", "training_plans", ["user_id"])

    op.create_table(
        "training_plan_days",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("plan_id", sa.BigInteger, sa.ForeignKey("training_plans.id"), nullable=False),
        sa.Column("day_index", sa.Integer, nullable=False),
        sa.Column("day_name", sa.String(100), nullable=False),
        sa.Column("is_rest_day", sa.Integer, nullable=False, server_default="0"),
        sa.Column("weekday", sa.Integer, nullable=True),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
    )

    op.create_table(
        "training_plan_exercises",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("plan_day_id", sa.BigInteger, sa.ForeignKey("training_plan_days.id"), nullable=False),
        sa.Column("exercise_source", sa.String(32), nullable=False),
        sa.Column("exercise_id", sa.BigInteger, nullable=True),
        sa.Column("custom_exercise_id", sa.BigInteger, nullable=True),
        sa.Column("exercise_name_snapshot", sa.String(100), nullable=False),
        sa.Column("body_part_snapshot", sa.String(64), nullable=True),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("target_sets", sa.Integer, nullable=False, server_default="4"),
        sa.Column("target_reps", sa.Integer, nullable=False, server_default="10"),
        sa.Column("target_weight_kg", sa.Numeric(8, 2), nullable=True),
        sa.Column("rest_seconds", sa.Integer, nullable=False, server_default="90"),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
    )

    op.create_table(
        "training_sessions",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", sa.BigInteger, nullable=True),
        sa.Column("plan_day_id", sa.BigInteger, nullable=True),
        sa.Column("session_date", sa.DateTime, nullable=False),
        sa.Column("session_name", sa.String(100), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="in_progress"),
        sa.Column("started_at", sa.DateTime, nullable=False),
        sa.Column("ended_at", sa.DateTime, nullable=True),
        sa.Column("duration_seconds", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_volume", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("note", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )
    op.create_index("idx_training_sessions_user_date", "training_sessions", ["user_id", "session_date"])
    op.create_index("idx_training_sessions_status", "training_sessions", ["user_id", "status"])

    op.create_table(
        "training_session_exercises",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.BigInteger, sa.ForeignKey("training_sessions.id"), nullable=False),
        sa.Column("exercise_name_snapshot", sa.String(100), nullable=False),
        sa.Column("body_part_snapshot", sa.String(64), nullable=True),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("planned_sets", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completed_sets", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rest_seconds", sa.Integer, nullable=False, server_default="90"),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
    )

    op.create_table(
        "training_session_sets",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("session_exercise_id", sa.BigInteger, sa.ForeignKey("training_session_exercises.id"), nullable=False),
        sa.Column("set_index", sa.Integer, nullable=False),
        sa.Column("target_reps", sa.Integer, nullable=True),
        sa.Column("target_weight_kg", sa.Numeric(8, 2), nullable=True),
        sa.Column("actual_reps", sa.Integer, nullable=True),
        sa.Column("actual_weight_kg", sa.Numeric(8, 2), nullable=True),
        sa.Column("completed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("volume", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
    )

    op.create_table(
        "weight_records",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("record_date", sa.DateTime, nullable=False),
        sa.Column("record_time", sa.Time, nullable=False),
        sa.Column("weight_kg", sa.Numeric(6, 2), nullable=False),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False,
                  server_default=sa.func.current_timestamp(), onupdate=sa.func.current_timestamp()),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )
    op.create_index("idx_weight_user_date", "weight_records", ["user_id", "record_date"])

    op.create_table(
        "uploaded_files",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("file_type", sa.String(32), nullable=False),
        sa.Column("usage_type", sa.String(32), nullable=False),
        sa.Column("file_url", sa.String(500), nullable=False),
        sa.Column("storage_provider", sa.String(64), nullable=False, server_default="local"),
        sa.Column("original_name", sa.String(255), nullable=True),
        sa.Column("file_size", sa.BigInteger, nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("is_temporary", sa.Integer, nullable=False, server_default="1"),
        sa.Column("expired_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index("idx_uploaded_files_user", "uploaded_files", ["user_id", "created_at"])

    op.create_table(
        "operation_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(64), nullable=True),
        sa.Column("target_id", sa.BigInteger, nullable=True),
        sa.Column("ip", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("detail_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
    )
    op.create_index("idx_operation_logs_user", "operation_logs", ["user_id", "created_at"])
    op.create_index("idx_operation_logs_action", "operation_logs", ["action"])


def downgrade() -> None:
    for tbl in [
        "operation_logs", "uploaded_files", "weight_records",
        "training_session_sets", "training_session_exercises", "training_sessions",
        "training_plan_exercises", "training_plan_days", "training_plans",
        "training_template_exercises", "training_template_days", "training_templates",
        "user_custom_exercises", "exercises", "food_recognition_logs",
        "diet_records", "user_custom_foods", "foods",
        "user_reminders", "nutrition_goals", "user_profiles", "users",
    ]:
        op.drop_table(tbl)