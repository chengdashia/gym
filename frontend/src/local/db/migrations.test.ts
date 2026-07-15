import { describe, expect, it } from 'vitest';

import { createMemoryDatabase } from './memory';
import { migrateDatabase } from './migrations';

describe('local database migrations', () => {
  it('creates the phase-one schema once', async () => {
    const db = await createMemoryDatabase();

    await migrateDatabase(db);
    await migrateDatabase(db);

    expect(await db.query('PRAGMA user_version')).toEqual([{ user_version: 1 }]);
    expect(
      (
        await db.query<{ name: string }>(
          "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name",
        )
      ).map((row) => row.name),
    ).toEqual(
      expect.arrayContaining([
        'app_meta',
        'custom_exercises',
        'custom_foods',
        'diet_records',
        'exercises',
        'foods',
        'local_profile',
        'nutrition_goals',
        'training_plan_days',
        'training_plan_exercises',
        'training_plans',
        'training_session_exercises',
        'training_session_sets',
        'training_sessions',
        'training_templates',
        'uploaded_files',
        'weight_records',
      ]),
    );
  });

  it('rolls a failed transaction back', async () => {
    const db = await createMemoryDatabase();
    await migrateDatabase(db);

    await expect(
      db.transaction(async (tx) => {
        await tx.execute("INSERT INTO app_meta(key, value) VALUES('probe', 'written')");
        throw new Error('stop');
      }),
    ).rejects.toThrow('stop');

    expect(await db.query("SELECT value FROM app_meta WHERE key = 'probe'"))
      .toEqual([]);
  });
});
