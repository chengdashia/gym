from datetime import date

from sqlalchemy.orm import Session

from app.models import NutritionGoal
from app.services.stats_service import diet_series, training_series, weight_series


def behavior_streak(diet: list[dict], training: list[dict], weights: list[dict]) -> int:
    streak = 0
    for diet_row, training_row, weight_row in reversed(list(zip(diet, training, weights))):
        active = (
            diet_row["calories_kcal"] > 0
            or training_row["session_count"] > 0
            or weight_row["weight_kg"] is not None
        )
        if not active:
            break
        streak += 1
    return streak


def nutrition_target_days(rows: list[dict], calories_goal: float) -> int:
    if calories_goal <= 0:
        return 0
    return sum(1 for row in rows if calories_goal * .85 <= row["calories_kcal"] <= calories_goal * 1.15)


def build_actions(
    *,
    diet_days: int,
    protein_goal_days: int,
    has_protein_goal: bool,
    training_sessions: int,
    weight_days: int = 0,
) -> list[str]:
    actions = []
    if diet_days == 0:
        actions.append("今天先完整记录一餐，建立饮食基线")
    elif diet_days < 5:
        actions.append(f"本周记录了 {diet_days} 天，先尝试每天至少记录一餐")
    elif has_protein_goal and protein_goal_days < 4:
        actions.append(f"本周蛋白质达标 {protein_goal_days} 天，下一餐优先补充优质蛋白")
    else:
        actions.append(f"本周饮食已记录 {diet_days} 天，继续保持当前节奏")

    if training_sessions == 0:
        actions.append("选择一个入门训练模板，并安排第一次训练")
    elif training_sessions < 2:
        actions.append(f"本周完成 {training_sessions} 次训练，可安排下一次训练时间")
    else:
        actions.append(f"本周已完成 {training_sessions} 次训练，下一次按计划继续")

    if weight_days < 3:
        actions.append(f"本周记录体重 {weight_days} 天，固定晨起同一时段补足 3 天")
    else:
        actions.append(f"本周记录体重 {weight_days} 天，继续保持同一时段测量")
    return actions


def build_weekly_summary(db: Session, user_id: int, end: date | None = None) -> dict:
    end = end or date.today()
    goal = db.query(NutritionGoal).filter(NutritionGoal.user_id == user_id).first()
    diet = diet_series(db, user_id, 7, end=end, calories_goal=float(goal.calories_kcal or 0) if goal else 0)
    training = training_series(db, user_id, 7, end=end)
    weights = weight_series(db, user_id, 7, end=end)
    recorded = [row for row in diet if row["calories_kcal"] > 0]
    protein_goal = float(goal.protein_g or 0) if goal else 0
    protein_goal_days = sum(1 for row in recorded if protein_goal > 0 and row["protein_g"] >= protein_goal)
    sessions = sum(row["session_count"] for row in training)
    weight_values = [row["weight_kg"] for row in weights if row["weight_kg"] is not None]
    result = {
        "diet_days": len(recorded),
        "average_calories": round(sum(row["calories_kcal"] for row in recorded) / len(recorded), 1) if recorded else 0,
        "protein_goal_days": protein_goal_days,
        "training_sessions": sessions,
        "total_volume": round(sum(row["total_volume"] for row in training), 2),
        "weight_change": round(weight_values[-1] - weight_values[0], 2) if len(weight_values) >= 2 else None,
        "nutrition_target_days": nutrition_target_days(recorded, float(goal.calories_kcal or 0) if goal else 0),
        "weight_days": len(weight_values),
        "streak_days": behavior_streak(diet, training, weights),
    }
    result["actions"] = build_actions(
        diet_days=result["diet_days"],
        protein_goal_days=protein_goal_days,
        has_protein_goal=protein_goal > 0,
        training_sessions=sessions,
        weight_days=result["weight_days"],
    )
    return result
