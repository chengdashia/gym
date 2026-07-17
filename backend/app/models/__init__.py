from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    DECIMAL,
    JSON,
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    openid: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True)
    unionid: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), unique=True, nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    nickname: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    is_member: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    member_expired_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    membership_level: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    photo_recognition_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    agreement_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    agreement_confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    profile: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    nutrition_goal: Mapped[Optional["NutritionGoal"]] = relationship(
        "NutritionGoal", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_users_phone", "phone"),
        Index("idx_users_status", "status"),
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    gender: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height_cm: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(6, 2), nullable=True)
    current_weight_kg: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(6, 2), nullable=True)
    target_weight_kg: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(6, 2), nullable=True)
    fitness_goal: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    training_frequency: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")


class NutritionGoal(Base):
    __tablename__ = "nutrition_goals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    calories_kcal: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False, default=0)
    carbs_g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False, default=0)
    protein_g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False, default=0)
    fat_g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False, default=0)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    user: Mapped["User"] = relationship("User", back_populates="nutrition_goal")


class UserReminder(Base):
    __tablename__ = "user_reminders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reminder_type: Mapped[str] = mapped_column(String(32), nullable=False)
    enabled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reminder_time: Mapped[Optional[datetime]] = mapped_column(Time, nullable=True)
    weekdays: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "reminder_type", name="uk_user_reminder_type"),
    )


class Food(Base):
    __tablename__ = "foods"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    calories_per_100g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False, default=0)
    carbs_per_100g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False, default=0)
    protein_per_100g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False, default=0)
    fat_per_100g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False, default=0)
    fiber_per_100g: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 2), nullable=True)
    default_unit: Mapped[str] = mapped_column(String(16), nullable=False, default="g")
    serving_weight_g: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 2), nullable=True)
    is_system: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    __table_args__ = (
        Index("idx_foods_name", "name"),
        Index("idx_foods_category", "category"),
    )


class UserCustomFood(Base):
    __tablename__ = "user_custom_foods"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    calories_per_100g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False, default=0)
    carbs_per_100g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False, default=0)
    protein_per_100g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False, default=0)
    fat_per_100g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False, default=0)
    fiber_per_100g: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 2), nullable=True)
    default_unit: Mapped[str] = mapped_column(String(16), nullable=False, default="g")
    serving_weight_g: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_custom_foods_user_name", "user_id", "name"),
    )


class DietPreference(Base):
    __tablename__ = "diet_preferences"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    meal_count: Mapped[int] = mapped_column(Integer, nullable=False)
    allergens_json: Mapped[list] = mapped_column(JSON, nullable=False)
    preference_rules_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    __table_args__ = (Index("idx_diet_preferences_user", "user_id"),)


class DietProgramTemplate(Base):
    __tablename__ = "diet_program_templates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rules_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    applicability_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    programs: Mapped[list["UserDietProgram"]] = relationship("UserDietProgram", back_populates="template")

    __table_args__ = (
        UniqueConstraint("code", "version", name="uk_diet_program_template_code_version"),
        Index("idx_diet_program_templates_status", "status"),
    )


class UserDietProgram(Base):
    __tablename__ = "user_diet_programs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    template_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("diet_program_templates.id"), nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    eligibility_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    preference_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    template: Mapped["DietProgramTemplate"] = relationship("DietProgramTemplate", back_populates="programs")
    stages: Mapped[list["DietProgramStage"]] = relationship(
        "DietProgramStage", back_populates="program", cascade="all, delete-orphan", order_by="DietProgramStage.stage_number"
    )
    meal_plan_days: Mapped[list["MealPlanDay"]] = relationship(
        "MealPlanDay", back_populates="program", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_user_diet_programs_user", "user_id"),
        Index("idx_user_diet_programs_user_status", "user_id", "status"),
    )


class DietProgramStage(Base):
    __tablename__ = "diet_program_stages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    program_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_diet_programs.id", ondelete="CASCADE"), nullable=False)
    stage_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    calories_kcal: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False)
    carbs_g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False)
    protein_g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False)
    fat_g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False)
    observation_days: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
    evaluation_snapshot_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    program: Mapped["UserDietProgram"] = relationship("UserDietProgram", back_populates="stages")
    meal_plan_days: Mapped[list["MealPlanDay"]] = relationship(
        "MealPlanDay", back_populates="stage", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("program_id", "stage_number", name="uk_diet_program_stage_number"),
        Index("idx_diet_program_stages_program", "program_id"),
    )


class MealPlanDay(Base):
    __tablename__ = "meal_plan_days"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    program_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("user_diet_programs.id", ondelete="CASCADE"), nullable=False)
    stage_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("diet_program_stages.id", ondelete="CASCADE"), nullable=False)
    plan_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    program: Mapped["UserDietProgram"] = relationship("UserDietProgram", back_populates="meal_plan_days")
    stage: Mapped["DietProgramStage"] = relationship("DietProgramStage", back_populates="meal_plan_days")
    meals: Mapped[list["MealPlanMeal"]] = relationship(
        "MealPlanMeal", back_populates="day", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("program_id", "plan_date", name="uk_meal_plan_program_date"),
        Index("idx_meal_plan_days_stage", "stage_id"),
    )


class MealPlanMeal(Base):
    __tablename__ = "meal_plan_meals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    day_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("meal_plan_days.id", ondelete="CASCADE"), nullable=False)
    meal_type: Mapped[str] = mapped_column(String(32), nullable=False)
    planned_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    target_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    day: Mapped["MealPlanDay"] = relationship("MealPlanDay", back_populates="meals")
    items: Mapped[list["MealPlanItem"]] = relationship(
        "MealPlanItem", back_populates="meal", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_meal_plan_meals_day", "day_id"),)


class MealPlanItem(Base):
    __tablename__ = "meal_plan_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    meal_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("meal_plan_meals.id", ondelete="CASCADE"), nullable=False)
    food_source: Mapped[str] = mapped_column(String(32), nullable=False)
    food_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    custom_food_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    food_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    amount_g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False)
    nutrition_snapshot_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    constraint_snapshot_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    replaced_from_item_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("meal_plan_items.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    meal: Mapped["MealPlanMeal"] = relationship("MealPlanMeal", back_populates="items")

    __table_args__ = (Index("idx_meal_plan_items_meal", "meal_id"),)


class DietRecord(Base):
    __tablename__ = "diet_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    record_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    record_time: Mapped[datetime] = mapped_column(Time, nullable=False)
    meal_type: Mapped[str] = mapped_column(String(32), nullable=False)
    food_source: Mapped[str] = mapped_column(String(32), nullable=False)
    food_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    custom_food_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    plan_meal_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("meal_plan_meals.id", ondelete="SET NULL"), nullable=True
    )
    food_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    unit_type: Mapped[str] = mapped_column(String(16), nullable=False)
    amount_g: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 2), nullable=True)
    serving_count: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 2), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    save_image: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    calories_kcal: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False, default=0)
    carbs_g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False, default=0)
    protein_g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False, default=0)
    fat_g: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), nullable=False, default=0)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_diet_user_date", "user_id", "record_date"),
        Index("idx_diet_user_meal", "user_id", "meal_type"),
        UniqueConstraint("plan_meal_id", "food_name_snapshot", name="uk_diet_record_plan_meal_food"),
    )


class SavedMealTemplate(Base):
    __tablename__ = "saved_meal_templates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_meal_type: Mapped[str] = mapped_column(String(32), nullable=False)
    items_json: Mapped[list] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    __table_args__ = (Index("idx_saved_meal_templates_user", "user_id", "created_at"),)


class FoodRecognitionLog(Base):
    __tablename__ = "food_recognition_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    recognition_status: Mapped[str] = mapped_column(String(32), nullable=False, default="success")
    candidates_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    selected_food_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    selected_custom_food_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="mock")
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    __table_args__ = (
        Index("idx_recognition_user_created", "user_id", "created_at"),
    )


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    body_part: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    is_system: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    __table_args__ = (
        Index("idx_exercises_name", "name"),
        Index("idx_exercises_body_part", "body_part"),
    )


class UserCustomExercise(Base):
    __tablename__ = "user_custom_exercises"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    body_part: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_user_custom_exercises", "user_id", "name"),
    )


class TrainingTemplate(Base):
    __tablename__ = "training_templates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    split_type: Mapped[str] = mapped_column(String(32), nullable=False)
    difficulty: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    goal: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    days: Mapped[list["TrainingTemplateDay"]] = relationship(
        "TrainingTemplateDay", back_populates="template", cascade="all, delete-orphan",
        order_by="TrainingTemplateDay.day_index",
    )


class TrainingTemplateDay(Base):
    __tablename__ = "training_template_days"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("training_templates.id"), nullable=False)
    day_index: Mapped[int] = mapped_column(Integer, nullable=False)
    day_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_rest_day: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    weekday: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    template: Mapped["TrainingTemplate"] = relationship("TrainingTemplate", back_populates="days")
    exercises: Mapped[list["TrainingTemplateExercise"]] = relationship(
        "TrainingTemplateExercise", back_populates="day", cascade="all, delete-orphan",
        order_by="TrainingTemplateExercise.sort_order",
    )


class TrainingTemplateExercise(Base):
    __tablename__ = "training_template_exercises"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    template_day_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("training_template_days.id"), nullable=False)
    exercise_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("exercises.id"), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target_sets: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    target_reps: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    target_weight_kg: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 2), nullable=True)
    rest_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    day: Mapped["TrainingTemplateDay"] = relationship("TrainingTemplateDay", back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship("Exercise")


class TrainingPlan(Base):
    __tablename__ = "training_plans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    schedule_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_template_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    current_day_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    sequence_anchor_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sequence_anchor_day_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    days: Mapped[list["TrainingPlanDay"]] = relationship(
        "TrainingPlanDay", back_populates="plan", cascade="all, delete-orphan",
        order_by="TrainingPlanDay.sort_order",
    )

    __table_args__ = (
        Index("idx_training_plans_user", "user_id"),
    )


class TrainingPlanDay(Base):
    __tablename__ = "training_plan_days"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("training_plans.id", ondelete="CASCADE"), nullable=False)
    day_index: Mapped[int] = mapped_column(Integer, nullable=False)
    day_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_rest_day: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    weekday: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    plan: Mapped["TrainingPlan"] = relationship("TrainingPlan", back_populates="days")
    exercises: Mapped[list["TrainingPlanExercise"]] = relationship(
        "TrainingPlanExercise", back_populates="day", cascade="all, delete-orphan",
        order_by="TrainingPlanExercise.sort_order",
    )


class TrainingPlanExercise(Base):
    __tablename__ = "training_plan_exercises"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    plan_day_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("training_plan_days.id", ondelete="CASCADE"), nullable=False)
    exercise_source: Mapped[str] = mapped_column(String(32), nullable=False)
    exercise_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    custom_exercise_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    exercise_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    body_part_snapshot: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target_sets: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    target_reps: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    target_weight_kg: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 2), nullable=True)
    rest_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    day: Mapped["TrainingPlanDay"] = relationship("TrainingPlanDay", back_populates="exercises")


class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    plan_day_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    session_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    session_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="in_progress")
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_volume: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False, default=0)
    note: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    exercises: Mapped[list["TrainingSessionExercise"]] = relationship(
        "TrainingSessionExercise", back_populates="session", cascade="all, delete-orphan",
        order_by="TrainingSessionExercise.sort_order",
    )

    __table_args__ = (
        Index("idx_training_sessions_user_date", "user_id", "session_date"),
        Index("idx_training_sessions_status", "user_id", "status"),
    )


class TrainingSessionExercise(Base):
    __tablename__ = "training_session_exercises"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("training_sessions.id", ondelete="CASCADE"), nullable=False)
    exercise_name_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    body_part_snapshot: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    planned_sets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_sets: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rest_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=90)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    session: Mapped["TrainingSession"] = relationship("TrainingSession", back_populates="exercises")
    sets: Mapped[list["TrainingSessionSet"]] = relationship(
        "TrainingSessionSet", back_populates="session_exercise", cascade="all, delete-orphan",
        order_by="TrainingSessionSet.set_index",
    )


class TrainingSessionSet(Base):
    __tablename__ = "training_session_sets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_exercise_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("training_session_exercises.id", ondelete="CASCADE"), nullable=False
    )
    set_index: Mapped[int] = mapped_column(Integer, nullable=False)
    target_reps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_weight_kg: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 2), nullable=True)
    actual_reps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actual_weight_kg: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 2), nullable=True)
    completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    volume: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False, default=0)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    session_exercise: Mapped["TrainingSessionExercise"] = relationship(
        "TrainingSessionExercise", back_populates="sets"
    )


class WeightRecord(Base):
    __tablename__ = "weight_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    record_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    record_time: Mapped[datetime] = mapped_column(Time, nullable=False)
    weight_kg: Mapped[Decimal] = mapped_column(DECIMAL(6, 2), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_weight_user_date", "user_id", "record_date"),
    )


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), nullable=False)
    usage_type: Mapped[str] = mapped_column(String(32), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_provider: Mapped[str] = mapped_column(String(64), nullable=False, default="local")
    original_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_temporary: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    expired_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    __table_args__ = (
        Index("idx_uploaded_files_user", "user_id", "created_at"),
    )


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    target_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    detail_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.current_timestamp())

    __table_args__ = (
        Index("idx_operation_logs_user", "user_id", "created_at"),
        Index("idx_operation_logs_action", "action"),
    )
