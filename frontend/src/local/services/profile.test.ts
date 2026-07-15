import { beforeEach, describe, expect, it } from 'vitest';

import { createMemoryDatabase } from '@/local/db/memory';
import { migrateDatabase } from '@/local/db/migrations';
import type { SqlDatabase } from '@/local/db/types';
import { createProfileService } from './profile';

describe('local profile service', () => {
  let db: SqlDatabase;

  beforeEach(async () => {
    db = await createMemoryDatabase();
    await migrateDatabase(db);
  });

  it('creates a single local profile that requires onboarding', async () => {
    const service = createProfileService(db);

    const profile = await service.get();

    expect(profile.id).toBe(1);
    expect(profile.onboarding_step).toBe('profile');
    expect(profile.nickname).toBeNull();
  });

  it('saves profile, goals, and onboarding completion atomically', async () => {
    const service = createProfileService(db);

    await service.finishOnboarding({
      nickname: '东',
      gender: 'male',
      age: 30,
      height_cm: 175,
      current_weight_kg: 75,
      target_weight_kg: 70,
      fitness_goal: 'fat_loss',
      training_frequency: '3-4',
      calories_kcal: 2000,
      carbs_g: 250,
      protein_g: 150,
      fat_g: 60,
    });

    expect((await service.get()).onboarding_step).toBe('complete');
    expect(await service.getNutritionGoal()).toEqual({
      calories_kcal: 2000,
      carbs_g: 250,
      protein_g: 150,
      fat_g: 60,
    });
    expect(await db.query('SELECT weight_centi FROM weight_records')).toEqual([
      { weight_centi: 7500 },
    ]);
  });

  it('rolls back every onboarding row when validation fails', async () => {
    const service = createProfileService(db);

    await expect(service.finishOnboarding({
      nickname: '',
      fitness_goal: 'fat_loss',
      calories_kcal: 2000,
      carbs_g: 250,
      protein_g: 150,
      fat_g: 60,
    })).rejects.toThrow('请输入昵称');

    expect((await service.get()).onboarding_step).toBe('profile');
    expect(await db.query('SELECT id FROM nutrition_goals')).toEqual([]);
    expect(await db.query('SELECT id FROM weight_records')).toEqual([]);
  });

  it('updates profile fields and goals after onboarding', async () => {
    const service = createProfileService(db);
    await service.finishOnboarding({
      nickname: '东',
      fitness_goal: 'fat_loss',
      calories_kcal: 2000,
      carbs_g: 250,
      protein_g: 150,
      fat_g: 60,
    });

    const updated = await service.updateProfile({
      nickname: '本地用户',
      profile: { height_cm: 178, current_weight_kg: 74.5 },
    });
    await service.updateNutritionGoal({
      calories_kcal: 1900,
      carbs_g: 210,
      protein_g: 160,
      fat_g: 55,
    });

    expect(updated.nickname).toBe('本地用户');
    expect(updated.profile.height_cm).toBe(178);
    expect(updated.profile.current_weight_kg).toBe(74.5);
    expect(await service.getNutritionGoal()).toEqual({
      calories_kcal: 1900,
      carbs_g: 210,
      protein_g: 160,
      fat_g: 55,
    });
  });
});
