#!/usr/bin/env python3
"""Generate deterministic offline seed JSON without importing the backend app."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "backend" / "app" / "seed" / "seed_data.py"
OUTPUT = ROOT / "frontend" / "src" / "local" / "seed"


def assigned_literal(tree: ast.Module, name: str):
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                return ast.literal_eval(node.value)
    raise ValueError(f"Missing literal assignment: {name}")


def template_literals(tree: ast.Module) -> list[tuple]:
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_seed_templates"
    )
    templates = []
    for node in ast.walk(function):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "_ensure_template":
            continue
        templates.append(tuple(ast.literal_eval(arg) for arg in node.args[1:7]))
    return templates


def stable_rows(tree: ast.Module) -> tuple[list[dict], list[dict], list[dict]]:
    fiber = assigned_literal(tree, "FIBER_PER_100G")
    foods = []
    for item in assigned_literal(tree, "FOODS"):
        name, category, calories, carbs, protein, fat, *serving = item
        foods.append({
            "stable_key": f"food:{name}",
            "name": name,
            "category": category,
            "calories": calories,
            "carbs": carbs,
            "protein": protein,
            "fat": fat,
            "fiber": fiber.get(name),
            "default_unit": serving[0] if serving else "g",
            "serving_weight": serving[1] if len(serving) > 1 else None,
        })

    exercises = [
        {
            "stable_key": f"exercise:{name}",
            "name": name,
            "body_part": body_part,
            "description": description,
        }
        for name, body_part, description in assigned_literal(tree, "EXERCISES")
    ]

    templates = []
    for name, description, split_type, difficulty, goal, days in template_literals(tree):
        templates.append({
            "stable_key": f"template:{name}",
            "name": name,
            "description": description,
            "split_type": split_type,
            "difficulty": difficulty,
            "goal": goal,
            "days": [
                {
                    "name": day_name,
                    "is_rest_day": is_rest,
                    "weekday": weekday,
                    "exercises": [
                        {
                            "name": exercise_name,
                            "sets": sets,
                            "reps": reps,
                            "weight": float(weight) if weight is not None else None,
                            "rest_seconds": rest_seconds,
                        }
                        for exercise_name, sets, reps, weight, rest_seconds in day_exercises
                    ],
                }
                for day_name, is_rest, weekday, day_exercises in days
            ],
        })

    return (
        sorted(foods, key=lambda row: row["stable_key"]),
        sorted(exercises, key=lambda row: row["stable_key"]),
        sorted(templates, key=lambda row: row["stable_key"]),
    )


def write_json(name: str, rows: list[dict]) -> None:
    keys = [row["stable_key"] for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError(f"Duplicate stable key in {name}")
    path = OUTPUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    foods, exercises, templates = stable_rows(tree)
    write_json("foods.v1.json", foods)
    write_json("exercises.v1.json", exercises)
    write_json("training-templates.v1.json", templates)
    print(json.dumps({"foods": len(foods), "exercises": len(exercises), "templates": len(templates)}))


if __name__ == "__main__":
    main()
