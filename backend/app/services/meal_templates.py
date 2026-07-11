"""Small, explicit meal-template catalogue used by the deterministic planner.

Each food has a role and constraint metadata.  The planner receives nutrition
from the database when it persists a plan; these defaults make the pure rule
engine testable and provide a safe fallback for seeded foods.
"""

FOODS = (
    {"name": "米饭", "role": "carb", "calories_per_100g": 116, "carbs_per_100g": 25.6, "protein_per_100g": 2.6, "fat_per_100g": .3, "fiber_per_100g": 0, "allergens": [], "vegetarian": True, "vegan": True, "budget": "low", "cooking": "full_kitchen"},
    {"name": "燕麦", "role": "carb", "calories_per_100g": 389, "carbs_per_100g": 66.3, "protein_per_100g": 13, "fat_per_100g": 6.5, "fiber_per_100g": 10.1, "allergens": ["wheat"], "vegetarian": True, "vegan": True, "budget": "low", "cooking": "simple_heating"},
    {"name": "鸡胸肉", "role": "protein", "calories_per_100g": 165, "carbs_per_100g": 0, "protein_per_100g": 31, "fat_per_100g": 3.6, "fiber_per_100g": 0, "allergens": [], "vegetarian": False, "vegan": False, "budget": "medium", "cooking": "full_kitchen"},
    {"name": "豆腐", "role": "protein", "calories_per_100g": 116, "carbs_per_100g": 6.2, "protein_per_100g": 12, "fat_per_100g": 7, "fiber_per_100g": 0, "allergens": ["soy"], "vegetarian": True, "vegan": True, "budget": "low", "cooking": "simple_heating"},
    {"name": "西兰花", "role": "vegetable", "calories_per_100g": 34, "carbs_per_100g": 6.6, "protein_per_100g": 2.8, "fat_per_100g": .4, "fiber_per_100g": 2.6, "allergens": [], "vegetarian": True, "vegan": True, "budget": "low", "cooking": "simple_heating"},
    {"name": "橄榄油", "role": "fat", "calories_per_100g": 884, "carbs_per_100g": 0, "protein_per_100g": 0, "fat_per_100g": 100, "fiber_per_100g": 0, "allergens": [], "vegetarian": True, "vegan": True, "budget": "high", "cooking": "full_kitchen"},
)


def default_foods() -> list[dict]:
    return [dict(food) for food in FOODS]
