from datetime import date, datetime, time

from sqlalchemy.orm import Session

from app.models import TrainingPlan, TrainingPlanDay, TrainingSession


def _has_completed_session_today(db: Session, plan: TrainingPlan, plan_day_id: int, d: date) -> bool:
    """同 plan 同 day 当天是否已有已完成的训练。"""
    start_dt = datetime.combine(d, time(0, 0))
    end_dt = datetime.combine(d, time(23, 59, 59))
    return db.query(TrainingSession).filter(
        TrainingSession.plan_id == plan.id,
        TrainingSession.plan_day_id == plan_day_id,
        TrainingSession.deleted_at.is_(None),
        TrainingSession.status == "completed",
        TrainingSession.session_date >= start_dt,
        TrainingSession.session_date <= end_dt,
    ).first() is not None


def resolve_today_day(
    db: Session, plan: TrainingPlan, d: date
) -> TrainingPlanDay | None:
    """按计划排期规则返回今日训练日。

    sequence: 顺序循环，current_day_index 起步；若当天已在该 day 完成训练则停留在该 day，
              否则前进到下一个非休息日（逻辑在 advance 时处理）。
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
    # sequence is calendar-driven: every calendar day occupies one slot,
    # including rest days.  A missed or partial session is historical data;
    # it must never hold tomorrow's plan hostage.
    anchor = plan.created_at.date() if plan.created_at else d
    offset = max(0, (d - anchor).days)
    return days[offset % len(days)]


def next_sequence_day_index(days: list[TrainingPlanDay], current_day_index: int | None) -> int | None:
    """Return the next non-rest day's actual day_index, wrapping once."""
    ordered = sorted(days, key=lambda x: x.sort_order or x.day_index or 0)
    if not ordered:
        return None
    start = next((i for i, row in enumerate(ordered) if row.day_index == current_day_index), -1)
    for offset in range(1, len(ordered) + 1):
        candidate = ordered[(start + offset) % len(ordered)]
        if not candidate.is_rest_day:
            return candidate.day_index
    return current_day_index


def advance_sequence_plan(db: Session, plan: TrainingPlan, today: date | None = None) -> None:
    """顺序循环推进：完成一次训练后 current_day_index 向后移一位。

    仅用于训练 session 完成接口。
    注意：完成训练后不立刻推进指针，避免训练页面 hero 立刻切到下一天。
    """
    days = sorted(plan.days, key=lambda x: x.sort_order or x.day_index or 0)
    if not days:
        return
    new_index = next_sequence_day_index(days, plan.current_day_index)
    if new_index is not None:
        plan.current_day_index = new_index
