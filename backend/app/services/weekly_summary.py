from datetime import date

from sqlalchemy.orm import Session

from app.models import NutritionGoal
from app.services.stats_service import diet_series, training_series, weight_series


def build_actions(
    *,
    diet_days: int,
    protein_goal_days: int,
    has_protein_goal: bool,
    training_sessions: int,
) -> list[str]:
    if diet_days == 0:
        return ["记录更多数据后生成总结，先从今天记录一餐开始"]
    actions = []
    if diet_days < 3:
        actions.append(f"本周记录了 {diet_days} 天，先尝试每天至少记录一餐")
    if has_protein_goal and protein_goal_days < 4:
        actions.append(f"本周蛋白质达标 {protein_goal_days} 天，下一餐优先补充优质蛋白")
    if training_sessions < 2:
        actions.append(f"本周完成 {training_sessions} 次训练，可安排下一次训练时间")
    if not actions:
        actions.append("本周记录和训练节奏稳定，继续保持")
    return actions[:3]


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
    streak = 0
    for row in reversed(diet):
        if row["calories_kcal"] <= 0:
            break
        streak += 1
    result = {
        "diet_days": len(recorded),
        "average_calories": round(sum(row["calories_kcal"] for row in recorded) / len(recorded), 1) if recorded else 0,
        "protein_goal_days": protein_goal_days,
        "training_sessions": sessions,
        "total_volume": round(sum(row["total_volume"] for row in training), 2),
        "weight_change": round(weight_values[-1] - weight_values[0], 2) if len(weight_values) >= 2 else None,
        "streak_days": streak,
    }
    result["actions"] = build_actions(
        diet_days=result["diet_days"],
        protein_goal_days=protein_goal_days,
        has_protein_goal=protein_goal > 0,
        training_sessions=sessions,
    )
    return result
