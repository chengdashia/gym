from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.services.validation import validate_diet_quantity, validate_plan_days


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


PosInt = Annotated[int, Field(ge=0)]
PosDec = Annotated[Decimal, Field(ge=0)]


# ============ Auth ============
class WechatLoginIn(BaseModel):
    code: str = Field(..., min_length=1, max_length=128)
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None


class PhoneLoginIn(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11, pattern=r"^1[3-9]\d{9}$")
    password: str = Field(..., min_length=6, max_length=64)


class RegisterIn(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11, pattern=r"^1[3-9]\d{9}$")
    password: str = Field(..., min_length=6, max_length=64)
    confirm_password: str = Field(..., min_length=6, max_length=64)
    captcha_id: str = Field(..., min_length=1)
    captcha_code: str = Field(..., min_length=1, max_length=10)
    nickname: Optional[str] = Field(default=None, max_length=100)
    avatar_url: Optional[str] = Field(default=None, max_length=500)


class CaptchaOut(BaseModel):
    captcha_id: str
    svg: str


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


# ============ Diet Programs ============
class DietEligibilityIn(BaseModel):
    under_18: bool
    pregnant_or_breastfeeding: bool
    diabetes: bool
    serious_liver_kidney_gallbladder: bool
    eating_disorder_history: bool


class DietPreferenceIn(BaseModel):
    meal_count: int = Field(..., ge=2, le=6)
    allergens: list[Literal[
        "dairy", "egg", "peanut", "tree_nut", "wheat", "soy",
        "fish", "shellfish", "sesame", "other",
    ]]
    vegetarian_type: Literal["none", "lacto_ovo", "lacto", "ovo", "vegan"] = "none"
    avoid_foods: list[str] = Field(default_factory=list)
    eats_breakfast: Optional[bool] = None
    budget_level: Optional[Literal["low", "medium", "high"]] = None
    cooking_setup: Optional[Literal["full_kitchen", "simple_heating", "none"]] = None
    cuisine_preference: Optional[Literal["home_chinese", "light_meal", "takeout"]] = None
    eating_window_start: Optional[time] = None
    eating_window_end: Optional[time] = None

    @field_validator("allergens")
    @classmethod
    def validate_unique_allergens(cls, value):
        if len(value) != len(set(value)):
            raise ValueError("过敏原不能重复")
        return value

    @model_validator(mode="after")
    def validate_eating_window(self):
        if (self.eating_window_start is None) != (self.eating_window_end is None):
            raise ValueError("进食时间窗必须同时提供开始和结束时间")
        if self.eating_window_start is not None and self.eating_window_start >= self.eating_window_end:
            raise ValueError("进食时间窗结束时间必须晚于开始时间")
        return self

    def to_snapshot(self) -> dict:
        values = self.model_dump(mode="json")
        return {
            "schema_version": 1,
            "meal_count": values.pop("meal_count"),
            "hard_constraints": {
                "allergens": values.pop("allergens"),
                "vegetarian_type": values.pop("vegetarian_type"),
                "avoid_foods": values.pop("avoid_foods"),
            },
            "preferences": values,
        }


class DietPreferenceOut(DietPreferenceIn):
    snapshot: dict


class DietProgramCreateIn(BaseModel):
    template_code: Literal["balanced_cut", "time_restricted_16_8", "carb_taper_532", "ketogenic"]
    activity_level: Literal["sedentary", "light", "moderate", "very_active"]
    calories_kcal: Decimal = Field(..., ge=1200)
    macro_ratio: Literal["532", "442"] = "532"
    target_loss_rate: Decimal = Field(default=Decimal("0.005"), ge=Decimal("0.005"), le=Decimal("0.01"))
    eligibility: DietEligibilityIn


class DietProgramEvaluateIn(BaseModel):
    end_date: date = Field(default_factory=date.today)
    target_loss_rate: Decimal = Field(default=Decimal("0.005"), ge=Decimal("0.005"), le=Decimal("0.01"))
    reduction_g: Literal[15, 20, 25] = 20


class DietProgramStageOut(ORMBase):
    id: int
    stage_number: int
    status: str
    start_date: Optional[date]
    end_date: Optional[date]
    calories_kcal: Decimal
    carbs_g: Decimal
    protein_g: Decimal
    fat_g: Decimal
    observation_days: int
    evaluation_snapshot_json: Optional[dict]


class MealPlanItemReplaceIn(BaseModel):
    food_id: int = Field(..., ge=1)
    food_source: Literal["system"] = "system"


class MealPlanItemAmountIn(BaseModel):
    amount_g: Decimal = Field(..., gt=0, le=5000)


class MealPlanMealReplaceIn(BaseModel):
    items: list[MealPlanItemReplaceIn] = Field(..., min_length=1, max_length=12)


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

    @model_validator(mode="after")
    def validate_weekdays(self):
        if self.weekdays is None:
            return self
        days = self.weekdays.split(",")
        if any(day not in {"1", "2", "3", "4", "5", "6", "7"} for day in days):
            raise ValueError("weekdays must be comma-separated values from 1 to 7")
        if len(days) != len(set(days)):
            raise ValueError("weekdays must not contain duplicates")
        return self


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
    image_file_id: Optional[int] = Field(default=None, ge=1)
    save_image: bool = False
    note: Optional[str] = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_quantity(self):
        validate_diet_quantity(self.unit_type, self.amount_g, self.serving_count)
        return self


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

    @model_validator(mode="after")
    def validate_quantity(self):
        if "unit_type" not in self.model_fields_set:
            return self
        quantity_field = "amount_g" if self.unit_type == "g" else "serving_count"
        if quantity_field not in self.model_fields_set:
            return self
        validate_diet_quantity(self.unit_type, self.amount_g, self.serving_count)
        return self


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


class AIRecognizedItem(AICandidate):
    estimated_amount_g: float = Field(..., gt=0)

    @model_validator(mode="after")
    def validate_source_id(self):
        item_id = self.food_id if self.source == "system" else self.custom_food_id
        if item_id is None:
            raise ValueError(f"{self.source} recognized item requires its source ID")
        return self


class AIRecognizeOut(BaseModel):
    recognition_id: int
    provider: str
    recognized_items: list[AIRecognizedItem]
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

    @model_validator(mode="after")
    def validate_days(self):
        validate_plan_days(self.schedule_type, self.days)
        return self


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
    completed: Optional[bool] = None


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
