from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any


def validate_diet_quantity(
    unit_type: str,
    amount_g: Any,
    serving_count: Any,
) -> tuple[str, Any, Any]:
    if unit_type == "g" and (amount_g is None or amount_g <= 0):
        raise ValueError("amount_g must be positive when unit_type is g")
    if unit_type == "serving" and (
        serving_count is None or serving_count <= 0
    ):
        raise ValueError(
            "serving_count must be positive when unit_type is serving"
        )
    return unit_type, amount_g, serving_count


def merge_and_validate_diet_quantity(
    update: Any,
    unit_type: str,
    amount_g: Any,
    serving_count: Any,
) -> tuple[str, Any, Any]:
    merged = (
        update.unit_type if update.unit_type is not None else unit_type,
        update.amount_g if update.amount_g is not None else amount_g,
        (
            update.serving_count
            if update.serving_count is not None
            else serving_count
        ),
    )
    return validate_diet_quantity(*merged)


def _day_value(day: Any, field: str) -> Any:
    if isinstance(day, Mapping):
        return day.get(field)
    return getattr(day, field)


def validate_plan_days(schedule_type: str, days: Sequence[Any]) -> Sequence[Any]:
    if not days:
        raise ValueError("plan must contain at least one day")

    weekdays: set[int] = set()
    for day in days:
        if not _day_value(day, "is_rest_day") and not _day_value(day, "exercises"):
            raise ValueError("non-rest days must contain at least one exercise")
        if schedule_type == "weekly":
            weekday = _day_value(day, "weekday")
            if type(weekday) is not int or not 1 <= weekday <= 7:
                raise ValueError("weekly plan weekdays must be integers from 1 to 7")
            if weekday in weekdays:
                raise ValueError("weekly plan weekdays must be unique")
            weekdays.add(weekday)
    return days


def should_reassess_goal(
    goal: str | None,
    first: float,
    latest: float,
    span_days: int,
) -> bool:
    if span_days < 14 or first <= 0:
        return False
    if goal == "fat_loss":
        return latest >= first
    if goal == "muscle_gain":
        return latest <= first
    if goal == "maintain":
        first_decimal = Decimal(str(first))
        latest_decimal = Decimal(str(latest))
        return (
            abs(latest_decimal - first_decimal) / first_decimal
            > Decimal("0.02")
        )
    return False
