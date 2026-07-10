from decimal import Decimal
import unittest

from app.services.nutrition import calc_nutrition_per_100g, calc_nutrition_per_serving


class NutritionTest(unittest.TestCase):
    def setUp(self):
        self.food = {
            "calories_per_100g": 130,
            "carbs_per_100g": 28,
            "protein_per_100g": 2.7,
            "fat_per_100g": 0.3,
        }

    def test_grams_scale_all_nutrients(self):
        result = calc_nutrition_per_100g(self.food, 150)
        self.assertEqual(result["calories_kcal"], Decimal("195.00"))
        self.assertEqual(result["carbs_g"], Decimal("42.00"))

    def test_servings_return_actual_grams(self):
        result = calc_nutrition_per_serving(self.food, 50, 2)
        self.assertEqual(result["amount_g"], Decimal("100.00"))
        self.assertEqual(result["calories_kcal"], Decimal("130.00"))
