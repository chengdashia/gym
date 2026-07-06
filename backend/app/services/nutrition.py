"""Nutrition computation for diet records (per 100g / per serving)."""
from __future__ import annotations

from decimal import Decimal


def _dec(x) -> Decimal:
    return Decimal(str(x or 0))


def calc_nutrition_per_100g(nutrition_per_100g: dict, amount_g) -> dict:
    factor = _dec(amount_g) / Decimal(100)
    return {
        "calories_kcal": _round(_dec(nutrition_per_100g["calories_per_100g"]) * factor),
        "carbs_g": _round(_dec(nutrition_per_100g["carbs_per_100g"]) * factor),
        "protein_g": _round(_dec(nutrition_per_100g["protein_per_100g"]) * factor),
        "fat_g": _round(_dec(nutrition_per_100g["fat_per_100g"]) * factor),
    }


def calc_nutrition_per_serving(nutrition_per_100g: dict, serving_weight_g, serving_count) -> dict:
    weight = _dec(serving_weight_g) * _dec(serving_count)
    factor = weight / Decimal(100)
    return {
        "calories_kcal": _round(_dec(nutrition_per_100g["calories_per_100g"]) * factor),
        "carbs_g": _round(_dec(nutrition_per_100g["carbs_per_100g"]) * factor),
        "protein_g": _round(_dec(nutrition_per_100g["protein_per_100g"]) * factor),
        "fat_g": _round(_dec(nutrition_per_100g["fat_per_100g"]) * factor),
        "amount_g": _round(weight),
    }


def _round(d) -> Decimal:
    return Decimal(f"{round(float(d), 2):.2f}")


def sum_nutrition(items: list[dict]) -> dict:
    return {
        "calories_kcal": _round(sum((x.get("calories_kcal") or Decimal(0)) for x in items)),
        "carbs_g": _round(sum((x.get("carbs_g") or Decimal(0)) for x in items)),
        "protein_g": _round(sum((x.get("protein_g") or Decimal(0)) for x in items)),
        "fat_g": _round(sum((x.get("fat_g") or Decimal(0)) for x in items)),
    }