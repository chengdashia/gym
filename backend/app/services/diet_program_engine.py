"""Deterministic calculations for adaptive diet-program stages.

This module deliberately has no database dependencies so the safety rules are
shared by creation, evaluation and future menu generation code.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Mapping, Sequence


MIN_CALORIES_KCAL = Decimal("1200")
MIN_CARBS_G = Decimal("100")
MIN_OBSERVATION_DAYS = 10
MAX_OBSERVATION_DAYS = 14
MIN_WEIGHT_RECORDS_PER_WINDOW = 5
MIN_ADHERENCE_RATE = Decimal("0.80")
MAX_WEEKLY_LOSS_KG = Decimal("0.90")
ACTIVITY_FACTORS = {
    "sedentary": Decimal("1.20"),
    "light": Decimal("1.375"),
    "moderate": Decimal("1.55"),
    "very_active": Decimal("1.725"),
}
RATIO_PERCENTAGES = {
    "532": (Decimal("0.50"), Decimal("0.30"), Decimal("0.20")),
    "442": (Decimal("0.40"), Decimal("0.40"), Decimal("0.20")),
}
PROGRAM_MACROS = {
    # Both ordinary calorie control and 16:8 use a moderate, explainable
    # baseline.  16:8 changes timing, not the calorie deficit contract.
    "balanced_cut": (Decimal("0.40"), Decimal("0.30"), Decimal("0.30")),
    "time_restricted_16_8": (Decimal("0.40"), Decimal("0.30"), Decimal("0.30")),
}
KETO_MAX_NET_CARBS_G = Decimal("30")
_TWO_PLACES = Decimal("0.01")


class DietSafetyError(ValueError):
    """The proposed target would cross a non-negotiable safety boundary."""


class TargetLossRateError(DietSafetyError):
    """A percentage target would exceed the absolute weekly-loss ceiling."""

    def __init__(self, weekly_loss_kg: Decimal):
        self.weekly_loss_kg = weekly_loss_kg
        super().__init__("目标减重速度超过每周 0.9kg 安全上限")


@dataclass(frozen=True)
class EvaluationResult:
    status: str
    reason: str
    previous_average_kg: Decimal | None = None
    current_average_kg: Decimal | None = None
    weekly_loss_rate: Decimal | None = None
    pending_adjustment: dict[str, Decimal] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "previous_average_kg": self.previous_average_kg,
            "current_average_kg": self.current_average_kg,
            "weekly_loss_rate": self.weekly_loss_rate,
            "pending_adjustment": self.pending_adjustment,
        }


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def _round(value: Decimal) -> Decimal:
    return value.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)


def validate_target_loss_rate(target_loss_rate: Any, reference_weight_kg: Any) -> Decimal:
    """Validate the percentage target against the 0.9kg/week absolute cap."""
    rate = _decimal(target_loss_rate)
    weekly_loss = _round(rate * _decimal(reference_weight_kg))
    if weekly_loss > MAX_WEEKLY_LOSS_KG:
        raise TargetLossRateError(weekly_loss)
    return weekly_loss


def estimate_tdee(profile: Mapping[str, Any] | Any, activity_level: str) -> Decimal | dict[str, Any]:
    """Return Mifflin–St Jeor TDEE, or explicitly name missing required data.

    No gender, age, height or weight defaults are used: a guessed input would
    make a safety-looking target falsely precise.
    """
    def get(name: str):
        return profile.get(name) if isinstance(profile, Mapping) else getattr(profile, name, None)

    required = ("gender", "age", "height_cm", "current_weight_kg")
    missing = [name for name in required if get(name) is None]
    if missing:
        return {"status": "needs_profile", "missing_fields": missing}
    if activity_level not in ACTIVITY_FACTORS:
        raise ValueError("activity_level must be sedentary, light, moderate, or very_active")

    gender = get("gender")
    if gender not in {"male", "female"}:
        return {
            "status": "unsupported_profile",
            "missing_fields": [],
            "unsupported_fields": ["gender"],
        }
    weight = _decimal(get("current_weight_kg"))
    height = _decimal(get("height_cm"))
    age = _decimal(get("age"))
    base = Decimal("10") * weight + Decimal("6.25") * height - Decimal("5") * age
    base += Decimal("5") if gender == "male" else Decimal("-161")
    return _round(base * ACTIVITY_FACTORS[activity_level])


def create_initial_targets(calories_kcal: Any, *, ratio: str = "532") -> dict[str, Decimal]:
    """Convert an approved calorie target to 5/3/2 or 4/4/2 gram targets."""
    calories = _decimal(calories_kcal)
    if calories < MIN_CALORIES_KCAL:
        raise DietSafetyError("目标热量低于 1200kcal，不能创建自动方案")
    if ratio not in RATIO_PERCENTAGES:
        raise ValueError("ratio must be 532 or 442")
    carbs_ratio, protein_ratio, fat_ratio = RATIO_PERCENTAGES[ratio]
    return {
        "calories_kcal": _round(calories),
        "carbs_g": _round(calories * carbs_ratio / Decimal("4")),
        "protein_g": _round(calories * protein_ratio / Decimal("4")),
        "fat_g": _round(calories * fat_ratio / Decimal("9")),
    }


def create_program_initial_targets(template_code: str, calories_kcal: Any, *, ratio: str = "532") -> dict[str, Decimal]:
    """Create explicit, safe targets for every currently offered program.

    Ketogenic targets cap net carbohydrate at 30g; the remainder is allocated
    to fat after a moderate protein target.  Net-carb validation is performed
    again by the planner against foods with known fibre data.
    """
    if template_code == "carb_taper_532":
        return create_initial_targets(calories_kcal, ratio=ratio)
    calories = _decimal(calories_kcal)
    if calories < MIN_CALORIES_KCAL:
        raise DietSafetyError("目标热量低于 1200kcal，不能创建自动方案")
    if template_code in PROGRAM_MACROS:
        carbs_ratio, protein_ratio, fat_ratio = PROGRAM_MACROS[template_code]
        return {
            "calories_kcal": _round(calories),
            "carbs_g": _round(calories * carbs_ratio / Decimal("4")),
            "protein_g": _round(calories * protein_ratio / Decimal("4")),
            "fat_g": _round(calories * fat_ratio / Decimal("9")),
        }
    if template_code == "ketogenic":
        protein = _round(calories * Decimal("0.30") / Decimal("4"))
        fat = _round((calories - KETO_MAX_NET_CARBS_G * 4 - protein * 4) / Decimal("9"))
        if fat < 0:
            raise DietSafetyError("目标热量无法满足严格生酮的最低蛋白质与净碳水边界")
        return {
            "calories_kcal": _round(calories), "carbs_g": KETO_MAX_NET_CARBS_G,
            "protein_g": protein, "fat_g": fat,
        }
    raise ValueError("unsupported diet program template")


def apply_carb_reduction(stage: Mapping[str, Any], *, grams: int = 20) -> dict[str, Decimal]:
    """Produce a proposed next stage; protein and fat are intentionally locked."""
    if grams not in {15, 20, 25}:
        raise ValueError("grams must be one of 15, 20, 25")
    carbs = _decimal(stage["carbs_g"])
    new_carbs = carbs - Decimal(grams)
    if new_carbs < MIN_CARBS_G:
        raise DietSafetyError("降低后碳水将低于每日 100g 安全下限")
    new_calories = _decimal(stage["calories_kcal"]) - Decimal(grams) * Decimal("4")
    if new_calories < MIN_CALORIES_KCAL:
        raise DietSafetyError("降低后总热量将低于 1200kcal 安全下限")
    protein = _decimal(stage["protein_g"])
    fat = _decimal(stage["fat_g"])
    return {
        # Keep the stage's displayed calorie target authoritative.  Macro grams
        # are rounded to 0.01g, so recomputing from rounded fat would otherwise
        # leak a few hundredths of a kcal into every subsequent stage.
        "calories_kcal": _round(new_calories),
        "carbs_g": _round(new_carbs),
        "protein_g": _round(protein),
        "fat_g": _round(fat),
    }


def _average(values: Sequence[Any]) -> Decimal:
    return _round(sum((_decimal(value) for value in values), Decimal("0")) / Decimal(len(values)))


def evaluate_532(
    *,
    previous_weights: Sequence[Any],
    current_weights: Sequence[Any],
    adherence_rate: Any,
    target_loss_rate: Any,
    stage: Mapping[str, Any],
    observation_days: int,
    target_weight_kg: Any | None = None,
    reference_weight_kg: Any | None = None,
    reduction_g: int = 20,
) -> EvaluationResult:
    """Evaluate two adjacent seven-day windows without mutating the stage.

    A suggested change is only returned as ``pending_adjustment``. Persistence
    and the user confirmation that creates the next stage remain API concerns.
    """
    if reference_weight_kg is not None:
        validate_target_loss_rate(target_loss_rate, reference_weight_kg)
    if observation_days < MIN_OBSERVATION_DAYS:
        return EvaluationResult("needs_observation", "当前阶段观察不足 10 天")
    if len(previous_weights) < MIN_WEIGHT_RECORDS_PER_WINDOW or len(current_weights) < MIN_WEIGHT_RECORDS_PER_WINDOW:
        return EvaluationResult("needs_data", "相邻两个七日窗口各至少需要 5 次有效称重")
    adherence = _decimal(adherence_rate)
    if adherence < MIN_ADHERENCE_RATE:
        return EvaluationResult("improve_adherence", "饮食记录执行率不足 80%，暂不调整碳水")

    previous_average = _average(previous_weights)
    current_average = _average(current_weights)
    if target_weight_kg is not None and current_average <= _decimal(target_weight_kg):
        return EvaluationResult("stop", "已达到目标体重", previous_average, current_average)
    carbs = _decimal(stage["carbs_g"])
    calories = _decimal(stage["calories_kcal"])
    if carbs <= MIN_CARBS_G or calories <= MIN_CALORIES_KCAL:
        return EvaluationResult("stop", "已触及碳水或热量安全下限", previous_average, current_average)

    loss_rate = _round((previous_average - current_average) / previous_average)
    if loss_rate >= _decimal(target_loss_rate):
        return EvaluationResult("continue", "七日平均体重下降速度达到目标", previous_average, current_average, loss_rate)
    try:
        proposed = apply_carb_reduction(stage, grams=reduction_g)
    except DietSafetyError:
        return EvaluationResult("stop", "继续降低碳水将触及每日 100g 安全下限", previous_average, current_average, loss_rate)
    pending = {
        "current_carbs_g": _round(carbs),
        "new_carbs_g": proposed["carbs_g"],
        "calorie_change_kcal": _round(proposed["calories_kcal"] - calories),
        "reduction_g": Decimal(reduction_g),
    }
    return EvaluationResult(
        "suggest_carb_reduction", "下降速度低于目标，建议确认后降低碳水",
        previous_average, current_average, loss_rate, pending,
    )
