from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


PosInt = Annotated[int, Field(ge=0)]
PosDec = Annotated[Decimal, Field(ge=0)]


# ============ Auth ============
class WechatLoginIn(BaseModel):
    code: str = Field(..., min_length=1, max_length=128)
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None


class UserSummary(BaseModel):
    id: int
    openid: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    is_new_user: bool = False
    agreement_confirmed: bool = False
    is_member: bool = False
    member_expired_at: Optional[datetime] = None


class WechatLoginOut(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    user: UserSummary


# ============ Users / Profile / Agreement ============
class UserProfileIn(BaseModel):
    gender: Optional[Literal["male", "female", "other"]] = None
    age: Optional[int] = Field(default=None, ge=10, le=120)
    height_cm: Optional[Decimal] = Field(default=None, ge=50, le=250)
    current_weight_kg: Optional[Decimal] = Field(default=None, ge=20, le=250)
    target_weight_kg: Optional[Decimal] = Field(default=None, ge=20, le=250)
    fitness_goal: Optional[Literal["fat_loss", "muscle_gain", "maintain", "shaping"]] = None
    training_frequency: Optional[str] = None


class UserMeIn(BaseModel):
    nickname: Optional[str] = Field(default=None, max_length=100)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    profile: Optional[UserProfileIn] = None


class UserProfileOut(UserProfileIn, ORMBase):
    pass


class UserMeOut(BaseModel):
    id: int
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    is_member: bool = False
    member_expired_at: Optional[datetime] = None
    agreement_confirmed: bool = False
    agreement_version: Optional[str] = None
    agreement_confirmed_at: Optional[datetime] = None
    profile: Optional[UserProfileOut] = None


class AgreementConfirmIn(BaseModel):
    agreement_version: str = Field(default="v1.0", max_length=32)
    privacy_version: str = Field(default="v1.0", max_length=32)


# ============ Nutrition Goal ============
class NutritionGoalIn(BaseModel):
    calories_kcal: Decimal = Field(..., ge=0)
    carbs_g: Decimal = Field(..., ge=0)
    protein_g: Decimal = Field(..., ge=0)
    fat_g: Decimal = Field(..., ge=0)


class NutritionGoalOut(NutritionGoalIn, ORMBase):
    user_id: int
    source: str = "manual"


class NutritionRecommendOut(BaseModel):
    calories_kcal: Decimal
    carbs_g: Decimal
    protein_g: Decimal
    fat_g: Decimal
    formula_note: str


# ============ Reminders ============
class ReminderItem(BaseModel):
    reminder_type: Literal["diet", "training", "weight"]
    enabled: bool = False
    reminder_time: Optional[str] = Field(default=None, description="HH:MM")
    weekdays: Optional[str] = Field(default=None, description="逗号分隔 1-7")


class RemindersUpdateIn(BaseModel):
    items: list[ReminderItem]


class RemindersOut(BaseModel):
    items: list[ReminderItem]


# ============ Foods ============
class FoodOut(BaseModel):
    id: int
    source: Literal["system", "custom"]
    name: str
    category: Optional[str] = None
    calories_per_100g: Decimal
    carbs_per_100g: Decimal
    protein_per_100g: Decimal
    fat_per_100g: Decimal
    default_unit: str
    serving_weight_g: Optional[Decimal] = None


class FoodSearchOut(BaseModel):
    items: list[FoodOut]
    total: int


class FoodCustomIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = None
    calories_per_100g: Decimal = Field(..., ge=0)
    carbs_per_100g: Decimal = Field(..., ge=0)
    protein_per_100g: Decimal = Field(..., ge=0)
    fat_per_100g: Decimal = Field(..., ge=0)
    default_unit: Literal["g", "serving"] = "g"
    serving_weight_g: Optional[Decimal] = None


# ============ Diet ============
class DietRecordIn(BaseModel):
    record_date: date
    record_time: time
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    food_source: Literal["system", "custom"]
    food_id: Optional[int] = None
    custom_food_id: Optional[int] = None
    unit_type: Literal["g", "serving"]
    amount_g: Optional[Decimal] = Field(default=None, ge=0)
    serving_count: Optional[Decimal] = Field(default=None, ge=0)
    image_url: Optional[str] = None
    save_image: bool = False
    note: Optional[str] = Field(default=None, max_length=500)


class DietRecordUpdateIn(BaseModel):
    record_date: Optional[date] = None
    record_time: Optional[time] = None
    meal_type: Optional[Literal["breakfast", "lunch", "dinner", "snack"]] = None
    unit_type: Optional[Literal["g", "serving"]] = None
    amount_g: Optional[Decimal] = Field(default=None, ge=0)
    serving_count: Optional[Decimal] = Field(default=None, ge=0)
    image_url: Optional[str] = None
    save_image: Optional[bool] = None
    note: Optional[str] = Field(default=None, max_length=500)


class DietRecordOut(ORMBase):
    id: int
    record_date: date
    record_time: time
    meal_type: str
    food_source: str
    food_id: Optional[int]
    custom_food_id: Optional[int]
    food_name_snapshot: str
    unit_type: str
    amount_g: Optional[Decimal]
    serving_count: Optional[Decimal]
    image_url: Optional[str]
    calories_kcal: Decimal
    carbs_g: Decimal
    protein_g: Decimal
    fat_g: Decimal
    note: Optional[str]


class DietSummary(BaseModel):
    calories_kcal: Decimal
    carbs_g: Decimal
    protein_g: Decimal
    fat_g: Decimal


class DietDayOut(BaseModel):
    date: date
    summary: DietSummary
    meals: dict[Literal["breakfast", "lunch", "dinner", "snack"], list[DietRecordOut]]


# ============ Uploads / AI ============
class UploadOut(BaseModel):
    file_id: int
    file_url: str
    is_temporary: bool


class AIRecognizeIn(BaseModel):
    file_id: int
    image_url: Optional[str] = None


class AICandidate(BaseModel):
    food_id: Optional[int] = None
    custom_food_id: Optional[int] = None
    source: Literal["system", "custom"]
    name: str
    confidence: float


class AIRecognizeOut(BaseModel):
    recognition_id: int
    provider: str
    candidates: list[AICandidate]


# ============ Exercises ============
class ExerciseOut(BaseModel):
    id: int
    source: Literal["system", "custom"]
    name: str
    body_part: str
    description: Optional[str] = None


class ExerciseSearchOut(BaseModel):
    items: list[ExerciseOut]
    total: int


class ExerciseCustomIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    body_part: Literal["胸", "背", "肩", "腿", "手臂", "核心", "有氧", "其他"]
    description: Optional[str] = Field(default=None, max_length=1000)


# ============ Training ============
class TemplateExerciseOut(BaseModel):
    id: int
    exercise_id: int
    name: str
    body_part: str
    sort_order: int
    target_sets: int
    target_reps: int
    target_weight_kg: Optional[Decimal]
    rest_seconds: int
    note: Optional[str]


class TemplateDayOut(BaseModel):
    id: int
    day_index: int
    day_name: str
    is_rest_day: bool
    weekday: Optional[int]
    exercises: list[TemplateExerciseOut]


class TemplateOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    split_type: str
    difficulty: Optional[str]
    goal: Optional[str]
    days: list[TemplateDayOut]


class TemplateListOut(BaseModel):
    items: list[TemplateOut]


# ---- Plans ----
class PlanExerciseIn(BaseModel):
    exercise_source: Literal["system", "custom"] = "system"
    exercise_id: Optional[int] = None
    custom_exercise_id: Optional[int] = None
    target_sets: int = Field(default=4, ge=1, le=20)
    target_reps: int = Field(default=10, ge=1, le=100)
    target_weight_kg: Optional[Decimal] = None
    rest_seconds: int = Field(default=90, ge=10, le=600)
    sort_order: int = 0
    note: Optional[str] = Field(default=None, max_length=500)


class PlanDayIn(BaseModel):
    day_index: int = Field(..., ge=1)
    day_name: str = Field(..., min_length=1, max_length=100)
    is_rest_day: bool = False
    weekday: Optional[int] = Field(default=None, ge=1, le=7)
    sort_order: int = 0
    exercises: list[PlanExerciseIn] = []


class PlanIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    schedule_type: Literal["sequence", "weekly"]
    source_template_id: Optional[int] = None
    days: list[PlanDayIn]


class PlanExerciseOut(BaseModel):
    id: int
    exercise_source: str
    exercise_id: Optional[int]
    custom_exercise_id: Optional[int]
    exercise_name_snapshot: str
    body_part_snapshot: Optional[str]
    sort_order: int
    target_sets: int
    target_reps: int
    target_weight_kg: Optional[Decimal]
    rest_seconds: int
    note: Optional[str]


class PlanDayOut(BaseModel):
    id: int
    day_index: int
    day_name: str
    is_rest_day: bool
    weekday: Optional[int]
    sort_order: int
    exercises: list[PlanExerciseOut]


class PlanOut(BaseModel):
    id: int
    name: str
    schedule_type: str
    source_template_id: Optional[int]
    current_day_index: int
    is_active: bool
    status: str
    days: list[PlanDayOut]


class PlanListOut(BaseModel):
    items: list[PlanOut]


class TrainingTodayOut(BaseModel):
    date: date
    has_plan: bool = False
    plan_id: Optional[int] = None
    schedule_type: Optional[str] = None
    plan_day_id: Optional[int] = None
    is_rest_day: bool = False
    session_id: Optional[int] = None
    session_status: Optional[str] = None
    title: Optional[str] = None
    exercise_count: int = 0
    # 兼容字段：保留给旧客户端使用
    plan: Optional[PlanOut] = None
    today_day: Optional[PlanDayOut] = None
    incomplete_session: Optional["SessionOut"] = None


# ---- Sessions ----
class SessionCreateIn(BaseModel):
    plan_id: int
    plan_day_id: int
    session_date: date


class SessionSetIn(BaseModel):
    set_id: Optional[int] = None
    set_index: int
    actual_reps: Optional[int] = Field(default=None, ge=0)
    actual_weight_kg: Optional[Decimal] = None
    completed: bool = False


class SessionExerciseUpdateIn(BaseModel):
    session_exercise_id: int
    sets: list[SessionSetIn] = []


class SessionUpdateIn(BaseModel):
    status: Optional[Literal["in_progress", "paused"]] = None
    exercises: list[SessionExerciseUpdateIn] = []


class SessionSetOut(ORMBase):
    id: int
    set_index: int
    target_reps: Optional[int]
    target_weight_kg: Optional[Decimal]
    actual_reps: Optional[int]
    actual_weight_kg: Optional[Decimal]
    completed: bool
    completed_at: Optional[datetime]
    volume: Decimal
    note: Optional[str]


class SessionExerciseOut(ORMBase):
    id: int
    exercise_name_snapshot: str
    body_part_snapshot: Optional[str]
    sort_order: int
    planned_sets: int
    completed_sets: int
    rest_seconds: int
    note: Optional[str]
    sets: list[SessionSetOut]


class SessionOut(ORMBase):
    id: int
    plan_id: Optional[int]
    plan_day_id: Optional[int]
    session_date: date
    session_name: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: int
    total_volume: Decimal
    note: Optional[str]
    exercises: list[SessionExerciseOut] = []


TrainingTodayOut.model_rebuild()


# ============ Weight ============
class WeightRecordIn(BaseModel):
    record_date: date
    record_time: time
    weight_kg: Decimal = Field(..., ge=20, le=250)
    note: Optional[str] = Field(default=None, max_length=500)


class WeightRecordUpdateIn(BaseModel):
    record_date: Optional[date] = None
    record_time: Optional[time] = None
    weight_kg: Optional[Decimal] = Field(default=None, ge=20, le=250)
    note: Optional[str] = Field(default=None, max_length=500)


class WeightRecordOut(ORMBase):
    id: int
    record_date: date
    record_time: time
    weight_kg: Decimal
    note: Optional[str]


class WeightListOut(BaseModel):
    items: list[WeightRecordOut]


# ============ Stats ============
class DietStatDay(BaseModel):
    date: date
    calories_kcal: Decimal
    carbs_g: Decimal
    protein_g: Decimal
    fat_g: Decimal
    calories_goal: Decimal
    completion_rate: Decimal


class TrainingStatDay(BaseModel):
    date: date
    session_count: int
    duration_seconds: int
    total_volume: Decimal


class WeightStatDay(BaseModel):
    date: date
    weight_kg: Optional[Decimal]
    target_weight_kg: Optional[Decimal]
    diff_kg: Optional[Decimal]
    change_from_start: Optional[Decimal]


class DietStatOut(BaseModel):
    range: int
    items: list[DietStatDay]


class TrainingStatOut(BaseModel):
    range: int
    items: list[TrainingStatDay]


class WeightStatOut(BaseModel):
    range: int
    items: list[WeightStatDay]


# ============ Home ============
class HomeDietSummary(BaseModel):
    calories_kcal: Decimal
    calories_goal: Decimal
    carbs_g: Decimal
    carbs_goal: Decimal
    protein_g: Decimal
    protein_goal: Decimal
    fat_g: Decimal
    fat_goal: Decimal
    record_count: int


class HomeTrainingSummary(BaseModel):
    status: Literal["not_started", "in_progress", "paused", "completed", "rest_day", "no_plan"]
    plan_id: Optional[int]
    plan_day_id: Optional[int]
    session_id: Optional[int]
    title: Optional[str]
    exercise_count: int
    is_rest_day: bool


class HomeWeightSummary(BaseModel):
    current_weight_kg: Optional[Decimal]
    target_weight_kg: Optional[Decimal]
    diff_kg: Optional[Decimal]
    last_recorded_at: Optional[datetime]


class HomeSummaryOut(BaseModel):
    date: date
    diet: HomeDietSummary
    training: HomeTrainingSummary
    weight: HomeWeightSummary