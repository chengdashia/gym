"""Constraint-first seven-day meal planning with no hidden optimisation step."""

from __future__ import annotations

from datetime import date, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable

from app.services.meal_templates import default_foods


class MealPlanConflict(ValueError):
    def __init__(self, fields: Iterable[str], suggestions: Iterable[str]):
        self.fields, self.suggestions = list(fields), list(suggestions)
        super().__init__("无法在当前硬约束下生成安全菜单")

    def to_dict(self) -> dict[str, list[str]]:
        return {"fields": self.fields, "suggestions": self.suggestions}


def _d(value: Any) -> Decimal:
    return Decimal(str(value))


def _round(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _hard(preferences: dict) -> dict:
    return preferences.get("hard_constraints", preferences)


def _allowed(food: dict, hard: dict) -> bool:
    if set(food.get("allergens", [])) & set(hard.get("allergens", [])):
        return False
    if any(term and term in food["name"] for term in hard.get("avoid_foods", [])):
        return False
    kind = hard.get("vegetarian_type", "none")
    return kind == "none" or food.get("vegan" if kind == "vegan" else "vegetarian", False)


def _pick(foods: list[dict], role: str, hard: dict) -> dict:
    choices = [food for food in foods if food.get("role") == role and _allowed(food, hard)]
    if not choices:
        raise MealPlanConflict([role, "allergens", "vegetarian_type", "avoid_foods"], ["放宽忌口或选择普通饮食记录"])
    return choices[0]


def _item(food: dict, amount_g: Decimal, *, macro: dict[str, Decimal]) -> dict:
    amount = _round(amount_g)
    return {
        "name": food["name"], "role": food["role"], "amount_g": amount,
        "allergens": list(food.get("allergens", [])), "food": dict(food), "nutrition": macro,
    }


def _portion(food: dict, grams: Decimal, share: Decimal, targets: dict[str, Decimal]) -> dict:
    # Targets are the authoritative stage target.  Macro energy is used for
    # calories so rounded food-database calories cannot silently break ±5%.
    macro = {key: _round(value * share) for key, value in targets.items() if key != "calories_kcal"}
    macro["calories_kcal"] = _round(
        macro["carbs_g"] * 4 + macro["protein_g"] * 4 + macro["fat_g"] * 9
    )
    return _item(food, grams * share, macro=macro)


def _times(count: int, code: str, prefs: dict) -> list[time]:
    if code == "time_restricted_16_8":
        p = prefs.get("preferences", prefs)
        start, end = p.get("eating_window_start"), p.get("eating_window_end")
        if not start or not end:
            raise MealPlanConflict(["eating_window"], ["16:8 方案请先设置连续 8 小时进食窗口"])
        start = time.fromisoformat(str(start)); end = time.fromisoformat(str(end))
        if (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute) != 8 * 60:
            raise MealPlanConflict(["eating_window"], ["16:8 方案的进食窗口必须为连续 8 小时"])
        start_minutes = start.hour * 60 + start.minute
        span = (end.hour * 60 + end.minute) - start_minutes
        return [
            time((start_minutes + span * i // max(count - 1, 1)) // 60, (start_minutes + span * i // max(count - 1, 1)) % 60)
            for i in range(count)
        ]
    return [time(hour, 0) for hour in (8, 12, 18, 20, 21, 22)[:count]]


def _day(targets: dict[str, Decimal], prefs: dict, code: str, foods: list[dict], day_date: date) -> dict:
    hard = _hard(prefs)
    if code == "ketogenic" and any(food.get("fiber_per_100g") is None for food in foods):
        raise MealPlanConflict(["fiber_per_100g"], ["严格生酮菜单需要所有候选食物具备可靠膳食纤维数据"])
    protein, carb, fat, vegetable = (_pick(foods, role, hard) for role in ("protein", "carb", "fat", "vegetable"))
    meal_count = int(prefs.get("meal_count", 3))
    names = ["breakfast", "lunch", "dinner", "snack", "snack", "snack"][:meal_count]
    times = _times(meal_count, code, prefs)
    # Keto uses a strict 30g net-carbohydrate ceiling; the target remains
    # explicit and the failure is structured rather than silently altered.
    carbs = _d(targets["carbs_g"])
    if code == "ketogenic" and carbs > Decimal("30"):
        raise MealPlanConflict(["carbs_g"], ["严格生酮方案需要将每日净碳水目标设为不高于 30g"])
    base = {"carbs_g": carbs, "protein_g": _d(targets["protein_g"]), "fat_g": _d(targets["fat_g"])}
    protein_g = base["protein_g"] / _d(protein["protein_per_100g"]) * 100
    carb_g = base["carbs_g"] / _d(carb["carbs_per_100g"]) * 100 if carbs else Decimal("0")
    fat_needed = max(Decimal("0"), base["fat_g"] - protein_g * _d(protein["fat_per_100g"]) / 100 - carb_g * _d(carb["fat_per_100g"]) / 100)
    fat_g = fat_needed / _d(fat["fat_per_100g"]) * 100
    meals = []
    for index, (meal_type, planned_time) in enumerate(zip(names, times)):
        share = Decimal("1") / Decimal(meal_count)
        items = [
            _portion(protein, protein_g, share, {"protein_g": base["protein_g"], "carbs_g": Decimal("0"), "fat_g": Decimal("0")} ),
            _portion(carb, carb_g, share, {"protein_g": Decimal("0"), "carbs_g": base["carbs_g"], "fat_g": Decimal("0")} ),
            _portion(fat, fat_g, share, {"protein_g": Decimal("0"), "carbs_g": Decimal("0"), "fat_g": base["fat_g"]}),
            _item(vegetable, Decimal("150") * share, macro={"calories_kcal": Decimal("0"), "carbs_g": Decimal("0"), "protein_g": Decimal("0"), "fat_g": Decimal("0")}),
        ]
        meals.append({"meal_type": meal_type, "planned_time": planned_time, "items": items})
    totals = {key: _round(sum((item["nutrition"][key] for meal in meals for item in meal["items"]), Decimal("0"))) for key in ("calories_kcal", "carbs_g", "protein_g", "fat_g")}
    return {"plan_date": day_date, "meals": meals, "totals": totals}


def generate_seven_day_plan(targets: dict, preferences: dict, *, code: str = "balanced_cut", start_date: date | None = None, foods: list[dict] | None = None) -> dict:
    if code not in {"balanced_cut", "time_restricted_16_8", "carb_taper_532", "ketogenic"}:
        raise MealPlanConflict(["template_code"], ["选择支持的饮食方案"])
    normalized = {key: _d(value) for key, value in targets.items()}
    start = start_date or date.today()
    library = foods or default_foods()
    return {"code": code, "days": [_day(normalized, preferences, code, library, start + timedelta(days=index)) for index in range(7)]}


def validate_meal_plan(day: dict, targets: dict) -> None:
    target = _d(targets["calories_kcal"])
    actual = _d(day["totals"]["calories_kcal"])
    if abs(actual - target) > target * Decimal("0.05"):
        raise MealPlanConflict(["calories_kcal"], ["调整目标热量或餐数后重新生成菜单"])


def replace_item(item: dict, candidate: dict, preferences: dict) -> dict:
    """Return a same-role, hard-constraint-safe replacement candidate."""
    if candidate.get("role") != item.get("role"):
        raise MealPlanConflict(["role"], ["请优先用同一营养角色的食物替换"])
    if not _allowed(candidate, _hard(preferences)):
        raise MealPlanConflict(["allergens", "vegetarian_type", "avoid_foods"], ["请选择符合饮食偏好的替换食物"])
    replacement = dict(item)
    replacement.update({"name": candidate["name"], "allergens": list(candidate.get("allergens", [])), "food": dict(candidate)})
    return replacement


def replace_meal(meal: dict, candidates: list[dict], preferences: dict) -> dict:
    by_role = {food.get("role"): food for food in candidates}
    replacement = dict(meal)
    replacement["items"] = [replace_item(item, by_role.get(item.get("role"), item.get("food", {})), preferences) for item in meal["items"]]
    return replacement
