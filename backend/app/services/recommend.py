from decimal import Decimal

# Mifflin-Storer BMR
ACTIVITY_FACTOR = {
    "1-2": 1.3,
    "3-4": 1.45,
    "5-6": 1.55,
    "7+": 1.7,
}

GOAL_DELTA = {
    "fat_loss": -500,
    "muscle_gain": 300,
    "maintain": 0,
    "shaping": -100,
}


def _activity_factor(freq: str | None) -> float:
    if not freq:
        return 1.45
    return ACTIVITY_FACTOR.get(freq, 1.45)


def _goal_delta(goal: str | None) -> int:
    return GOAL_DELTA.get(goal or "maintain", 0)


def recommend(profile: dict | None) -> dict:
    """根据基础信息推荐每日营养目标。

    profile keys: gender, age, height_cm, current_weight_kg, target_weight_kg,
                  fitness_goal, training_frequency
    """
    if not profile:
        return {
            "calories_kcal": Decimal("2000.00"),
            "carbs_g": Decimal("250.00"),
            "protein_g": Decimal("120.00"),
            "fat_g": Decimal("60.00"),
            "formula_note": "未提供基础信息，使用默认值",
        }
    try:
        gender = profile.get("gender") or "male"
        age = float(profile.get("age") or 25)
        height = float(profile.get("height_cm") or 170)
        weight = float(profile.get("current_weight_kg") or 65)
    except Exception:
        return {
            "calories_kcal": Decimal("2000.00"),
            "carbs_g": Decimal("250.00"),
            "protein_g": Decimal("120.00"),
            "fat_g": Decimal("60.00"),
            "formula_note": "基础信息缺失，使用默认值",
        }

    if gender == "female":
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age + 5

    tdee = bmr * _activity_factor(profile.get("training_frequency"))
    target_kcal = tdee + _goal_delta(profile.get("fitness_goal"))
    target_kcal = max(1200.0, target_kcal)

    protein_g = max(0.8 * weight, weight * 1.6 if (profile.get("fitness_goal") in ("muscle_gain", "shaping")) else weight * 1.2)
    fat_pct = 0.25
    fat_kcal = target_kcal * fat_pct
    fat_g = fat_kcal / 9.0
    protein_kcal = protein_g * 4.0
    carb_kcal = max(target_kcal - protein_kcal - fat_kcal, 0)
    carb_g = carb_kcal / 4.0

    return {
        "calories_kcal": Decimal(f"{round(target_kcal, 2):.2f}"),
        "carbs_g": Decimal(f"{round(carb_g, 2):.2f}"),
        "protein_g": Decimal(f"{round(protein_g, 2):.2f}"),
        "fat_g": Decimal(f"{round(fat_g, 2):.2f}"),
        "formula_note": "Mifflin-Storer × 活动系数 + 目标调整；蛋白/脂肪占比拆分，碳水补足",
    }