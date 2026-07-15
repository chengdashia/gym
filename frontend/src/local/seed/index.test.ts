import { beforeEach, describe, expect, it } from 'vitest';

import { createMemoryDatabase } from '@/local/db/memory';
import { migrateDatabase } from '@/local/db/migrations';
import type { SqlDatabase } from '@/local/db/types';
import { installSeeds, SEED_VERSION } from './index';

describe('offline seed installation', () => {
  let db: SqlDatabase;

  beforeEach(async () => {
    db = await createMemoryDatabase();
    await migrateDatabase(db);
  });

  it('installs every bundled domain and records its version', async () => {
    await installSeeds(db);

    expect((await db.query('SELECT id FROM foods')).length).toBeGreaterThan(30);
    expect((await db.query('SELECT id FROM exercises')).length).toBeGreaterThan(30);
    expect((await db.query('SELECT id FROM training_templates')).length).toBe(5);
    expect(
      await db.query("SELECT value FROM app_meta WHERE key = 'seed_version'"),
    ).toEqual([{ value: String(SEED_VERSION) }]);
  });

  it('is idempotent and never overwrites custom rows', async () => {
    await installSeeds(db);
    await db.execute(
      `INSERT INTO custom_foods(
        name, calories_centi, carbs_centi, protein_centi, fat_centi,
        created_at, updated_at
      ) VALUES(?, ?, 0, 0, 0, ?, ?)`,
      ['我的燕麦', 38000, '2026-07-15T00:00:00Z', '2026-07-15T00:00:00Z'],
    );

    await installSeeds(db);

    expect(await db.query('SELECT name FROM custom_foods')).toEqual([
      { name: '我的燕麦' },
    ]);
    expect((await db.query('SELECT id FROM foods')).length).toBeGreaterThan(30);
  });
});
