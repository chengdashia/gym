from datetime import date, datetime
from decimal import Decimal
import unittest

from pydantic import ValidationError

from app.services import validation
from app.schemas import DietRecordIn, DietRecordUpdateIn, PlanIn, ReminderItem
from app.services.validation import (
    should_reassess_goal,
    validate_diet_quantity,
    validate_plan_days,
)
from app.utils.date import day_bounds


class BusinessRulesTest(unittest.TestCase):
    def test_day_bounds_are_half_open(self):
        start, end = day_bounds(date(2026, 7, 10))
        self.assertEqual(start, datetime(2026, 7, 10))
        self.assertEqual(end, datetime(2026, 7, 11))

    def test_diet_quantity_requires_positive_selected_unit(self):
        with self.assertRaises(ValueError):
            validate_diet_quantity("g", None, None)
        self.assertEqual(
            validate_diet_quantity("serving", None, 1),
            ("serving", None, 1),
        )

    def test_diet_quantity_rejects_decimal_zero_and_negative_values(self):
        invalid_quantities = [
            ("g", Decimal("0"), None),
            ("g", Decimal("-0.1"), None),
            ("serving", None, Decimal("0")),
            ("serving", None, Decimal("-0.1")),
        ]
        for unit_type, amount_g, serving_count in invalid_quantities:
            with self.subTest(unit_type=unit_type, value=amount_g or serving_count):
                with self.assertRaises(ValueError):
                    validate_diet_quantity(unit_type, amount_g, serving_count)

    def test_weekly_plan_rejects_duplicate_weekdays(self):
        days = [
            {
                "day_name": "胸",
                "weekday": 1,
                "is_rest_day": False,
                "exercises": [1],
            },
            {
                "day_name": "背",
                "weekday": 1,
                "is_rest_day": False,
                "exercises": [1],
            },
        ]
        with self.assertRaises(ValueError):
            validate_plan_days("weekly", days)

    def test_weekly_plan_rejects_weekdays_outside_one_to_seven(self):
        for weekday in (0, 8):
            days = [
                {
                    "day_name": "胸",
                    "weekday": weekday,
                    "is_rest_day": False,
                    "exercises": [1],
                }
            ]
            with self.subTest(weekday=weekday):
                with self.assertRaises(ValueError):
                    validate_plan_days("weekly", days)

    def test_weekly_plan_rejects_non_integer_weekday(self):
        days = [
            {
                "day_name": "胸",
                "weekday": 1.0,
                "is_rest_day": False,
                "exercises": [1],
            }
        ]
        with self.assertRaises(ValueError):
            validate_plan_days("weekly", days)

    def test_rest_days_may_have_no_exercises(self):
        days = [
            {
                "day_name": "休息",
                "weekday": None,
                "is_rest_day": True,
                "exercises": [],
            }
        ]
        self.assertEqual(validate_plan_days("cycle", days), days)

    def test_non_rest_days_require_exercises(self):
        days = [
            {
                "day_name": "胸",
                "weekday": None,
                "is_rest_day": False,
                "exercises": [],
            }
        ]
        with self.assertRaises(ValueError):
            validate_plan_days("cycle", days)

    def test_reassessment_starts_at_fourteen_days(self):
        self.assertFalse(should_reassess_goal("fat_loss", 70, 70, 13))
        self.assertTrue(should_reassess_goal("fat_loss", 70, 70, 14))

    def test_maintain_reassessment_uses_exact_two_percent_boundary(self):
        cases = [
            (71.4, False),
            (71.4001, True),
            (71.3999, False),
            (68.6, False),
            (68.5999, True),
            (68.6001, False),
        ]
        for latest, expected in cases:
            with self.subTest(latest=latest):
                self.assertEqual(
                    should_reassess_goal("maintain", 70, latest, 14),
                    expected,
                )

    def test_unknown_goal_does_not_trigger_reassessment(self):
        self.assertFalse(should_reassess_goal("shaping", 70, 72, 30))

    def test_diet_record_schema_validates_selected_quantity(self):
        values = {
            "record_date": date(2026, 7, 10),
            "record_time": "12:00",
            "meal_type": "lunch",
            "food_source": "system",
            "food_id": 1,
            "unit_type": "g",
            "amount_g": 0,
        }
        with self.assertRaises(ValidationError):
            DietRecordIn.model_validate(values)

    def test_diet_update_schema_preserves_partial_updates(self):
        DietRecordUpdateIn.model_validate({"note": "少盐"})
        DietRecordUpdateIn.model_validate({"unit_type": "g"})
        DietRecordUpdateIn.model_validate({"amount_g": 10})

        with self.assertRaises(ValidationError):
            DietRecordUpdateIn.model_validate(
                {"unit_type": "g", "amount_g": 0}
            )

    def test_diet_update_validates_quantity_after_merging_original_values(self):
        merge_quantity = getattr(
            validation,
            "merge_and_validate_diet_quantity",
            None,
        )
        self.assertIsNotNone(merge_quantity)
        self.assertEqual(
            merge_quantity(
                DietRecordUpdateIn.model_validate({"amount_g": Decimal("25")}),
                "g",
                Decimal("100"),
                None,
            ),
            ("g", Decimal("25"), None),
        )

        with self.assertRaises(ValueError):
            merge_quantity(
                DietRecordUpdateIn.model_validate({"amount_g": Decimal("0")}),
                "g",
                Decimal("100"),
                None,
            )
        with self.assertRaises(ValueError):
            merge_quantity(
                DietRecordUpdateIn.model_validate(
                    {"serving_count": Decimal("0")}
                ),
                "serving",
                Decimal("100"),
                Decimal("1"),
            )

    def test_plan_schema_uses_plan_day_rules(self):
        values = {
            "name": "周计划",
            "schedule_type": "weekly",
            "days": [
                {
                    "day_index": 1,
                    "day_name": "胸",
                    "weekday": 1,
                    "exercises": [{"exercise_id": 1}],
                },
                {
                    "day_index": 2,
                    "day_name": "背",
                    "weekday": 1,
                    "exercises": [{"exercise_id": 2}],
                },
            ],
        }
        with self.assertRaises(ValidationError):
            PlanIn.model_validate(values)

    def test_reminder_weekdays_are_unique_values_from_one_to_seven(self):
        ReminderItem(
            reminder_type="training",
            weekdays="1,3,7",
        )
        with self.assertRaises(ValidationError):
            ReminderItem(
                reminder_type="training",
                weekdays="1,1",
            )
        with self.assertRaises(ValidationError):
            ReminderItem(
                reminder_type="training",
                weekdays="1,8",
            )
        for invalid in ("", "1, 2", " 1"):
            with self.assertRaises(ValidationError):
                ReminderItem(reminder_type="training", weekdays=invalid)


if __name__ == "__main__":
    unittest.main()
