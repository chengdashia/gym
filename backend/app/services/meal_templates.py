"""Small, explicit meal-template catalogue used by the deterministic planner.

Each food has a role and constraint metadata.  The planner receives nutrition
from the database when it persists a plan; these defaults make the pure rule
engine testable and provide a safe fallback for seeded foods.
"""

FOODS = (
    {"name": "米饭", "role": "carb", "calories_per_100g": 116, "carbs_per_100g": 25.6, "protein_per_100g": 2.6, "fat_per_100g": .3, "fiber_per_100g": 0, "allergens": [], "vegetarian": True, "vegan": True, "budget": "low", "cooking": "full_kitchen", "cuisines": ["home_chinese"]},
    {"name": "燕麦", "role": "carb", "calories_per_100g": 389, "carbs_per_100g": 66.3, "protein_per_100g": 13, "fat_per_100g": 6.5, "fiber_per_100g": 10.1, "allergens": ["wheat"], "vegetarian": True, "vegan": True, "budget": "low", "cooking": "simple_heating", "cuisines": ["light_meal"]},
    {"name": "苹果", "role": "carb", "calories_per_100g": 52, "carbs_per_100g": 13.8, "protein_per_100g": .3, "fat_per_100g": .2, "fiber_per_100g": 2.4, "allergens": [], "vegetarian": True, "vegan": True, "budget": "low", "cooking": "none", "cuisines": ["takeout", "light_meal"]},
    {"name": "鸡胸肉", "role": "protein", "calories_per_100g": 165, "carbs_per_100g": 0, "protein_per_100g": 31, "fat_per_100g": 3.6, "fiber_per_100g": 0, "allergens": [], "vegetarian": False, "vegan": False, "budget": "low", "cooking": "none", "cuisines": ["home_chinese", "takeout", "light_meal"]},
    {"name": "豆腐", "role": "protein", "calories_per_100g": 116, "carbs_per_100g": 6.2, "protein_per_100g": 12, "fat_per_100g": 7, "fiber_per_100g": 0, "allergens": ["soy"], "vegetarian": True, "vegan": True, "budget": "low", "cooking": "simple_heating", "cuisines": ["home_chinese", "light_meal"]},
    {"name": "西兰花", "role": "vegetable", "calories_per_100g": 34, "carbs_per_100g": 6.6, "protein_per_100g": 2.8, "fat_per_100g": .4, "fiber_per_100g": 2.6, "allergens": [], "vegetarian": True, "vegan": True, "budget": "low", "cooking": "none", "cuisines": ["home_chinese", "takeout", "light_meal"]},
    {"name": "杏仁", "role": "fat", "calories_per_100g": 579, "carbs_per_100g": 21.6, "protein_per_100g": 21.2, "fat_per_100g": 49.9, "fiber_per_100g": 12.5, "allergens": ["tree_nut"], "vegetarian": True, "vegan": True, "budget": "low", "cooking": "none", "cuisines": ["takeout", "light_meal"]},
    {"name": "橄榄油", "role": "fat", "calories_per_100g": 884, "carbs_per_100g": 0, "protein_per_100g": 0, "fat_per_100g": 100, "fiber_per_100g": 0, "allergens": [], "vegetarian": True, "vegan": True, "budget": "high", "cooking": "full_kitchen", "cuisines": ["home_chinese", "light_meal"]},
)


def default_foods() -> list[dict]:
    return [dict(food) for food in FOODS]
