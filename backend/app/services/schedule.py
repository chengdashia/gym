from datetime import date

from sqlalchemy.orm import Session

from app.models import TrainingPlan, TrainingPlanDay


def resolve_today_day(
    db: Session, plan: TrainingPlan, d: date
) -> TrainingPlanDay | None:
    """按计划排期规则返回今日训练日。

    sequence: 顺序循环，current_day_index 起步，遇到完成训练则顺序前进到下一个非休息日。
    weekly:   按 weekday 字段（周一=1 ... 周日=7）匹配。
    """
    days = sorted(plan.days, key=lambda x: x.sort_order or x.day_index or 0)
    if not days:
        return None
    if plan.schedule_type == "weekly":
        weekday = d.isoweekday()
        for d_row in days:
            if d_row.is_rest_day:
                continue
            if d_row.weekday == weekday:
                return d_row
        # 未匹配到指定星期 -> 该日休息
        return None
    # sequence
    idx = (plan.current_day_index or 1) - 1
    if idx < 0 or idx >= len(days):
        idx = 0
    chosen = days[idx]
    if chosen.is_rest_day:
        # 找到下一个非休息日；不修改 current_day_index
        return chosen
    return chosen


def advance_sequence_plan(db: Session, plan: TrainingPlan) -> None:
    """顺序循环推进：完成一次训练后 current_day_index 向后移一位。

    仅用于训练 session 完成接口。
    """
    days = sorted(plan.days, key=lambda x: x.sort_order or x.day_index or 0)
    if not days:
        return
    nxt = (plan.current_day_index or 1) % len(days) + 0
    new_index = ((plan.current_day_index or 1) % len(days)) + 1
    plan.current_day_index = new_index