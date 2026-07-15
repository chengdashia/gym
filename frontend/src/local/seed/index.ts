import exercises from './exercises.v1.json';
import foods from './foods.v1.json';
import templates from './training-templates.v1.json';

import type { SqlDatabase } from '@/local/db/types';

export const SEED_VERSION = 1;

const centi = (value: number | null): number | null =>
  value == null ? null : Math.round(value * 100);

export async function installSeeds(db: SqlDatabase): Promise<void> {
  await db.transaction(async (tx) => {
    for (const food of foods) {
      await tx.execute(
        `INSERT INTO foods(
          stable_key, name, category, calories_centi, carbs_centi,
          protein_centi, fat_centi, fiber_centi, default_unit,
          serving_weight_centi, status
        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
        ON CONFLICT(stable_key) DO UPDATE SET
          name=excluded.name,
          category=excluded.category,
          calories_centi=excluded.calories_centi,
          carbs_centi=excluded.carbs_centi,
          protein_centi=excluded.protein_centi,
          fat_centi=excluded.fat_centi,
          fiber_centi=excluded.fiber_centi,
          default_unit=excluded.default_unit,
          serving_weight_centi=excluded.serving_weight_centi,
          status='active'`,
        [
          food.stable_key,
          food.name,
          food.category,
          centi(food.calories),
          centi(food.carbs),
          centi(food.protein),
          centi(food.fat),
          centi(food.fiber),
          food.default_unit,
          centi(food.serving_weight),
        ],
      );
    }

    for (const exercise of exercises) {
      await tx.execute(
        `INSERT INTO exercises(stable_key, name, body_part, equipment, status)
         VALUES(?, ?, ?, ?, 'active')
         ON CONFLICT(stable_key) DO UPDATE SET
           name=excluded.name,
           body_part=excluded.body_part,
           equipment=excluded.equipment,
           status='active'`,
        [exercise.stable_key, exercise.name, exercise.body_part, exercise.description],
      );
    }

    for (const template of templates) {
      await tx.execute(
        `INSERT INTO training_templates(stable_key, name, description, payload_json, status)
         VALUES(?, ?, ?, ?, 'active')
         ON CONFLICT(stable_key) DO UPDATE SET
           name=excluded.name,
           description=excluded.description,
           payload_json=excluded.payload_json,
           status='active'`,
        [template.stable_key, template.name, template.description, JSON.stringify(template)],
      );
    }

    await tx.execute(
      `INSERT INTO app_meta(key, value) VALUES('seed_version', ?)
       ON CONFLICT(key) DO UPDATE SET value=excluded.value`,
      [String(SEED_VERSION)],
    );
  });
}
