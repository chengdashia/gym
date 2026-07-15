import type { SqlDatabase, SqlPrimitive } from '@/local/db/types';

export interface LocalProfileRow extends Record<string, unknown> {
  id: number;
  nickname: string | null;
  avatar_path: string | null;
  gender: string | null;
  age: number | null;
  height_centi: number | null;
  current_weight_centi: number | null;
  target_weight_centi: number | null;
  fitness_goal: string | null;
  training_frequency: string | null;
  onboarding_step: 'profile' | 'goal' | 'complete';
  created_at: string;
  updated_at: string;
}

export interface NutritionGoalRow extends Record<string, unknown> {
  calories_centi: number;
  carbs_centi: number;
  protein_centi: number;
  fat_centi: number;
}

export class ProfileRepository {
  constructor(private readonly db: SqlDatabase) {}

  async ensureProfile(now: string): Promise<LocalProfileRow> {
    await this.db.execute(
      `INSERT OR IGNORE INTO local_profile(id, onboarding_step, created_at, updated_at)
       VALUES(1, 'profile', ?, ?)`,
      [now, now],
    );
    const rows = await this.db.query<LocalProfileRow>('SELECT * FROM local_profile WHERE id = 1');
    if (!rows[0]) throw new Error('本地资料初始化失败');
    return rows[0];
  }

  async getProfile(): Promise<LocalProfileRow | null> {
    return (await this.db.query<LocalProfileRow>('SELECT * FROM local_profile WHERE id = 1'))[0] || null;
  }

  async updateProfile(fields: Partial<LocalProfileRow>): Promise<void> {
    const entries = Object.entries(fields).filter(([key, value]) => key !== 'id' && value !== undefined);
    if (!entries.length) return;
    await this.db.execute(
      `UPDATE local_profile SET ${entries.map(([key]) => `${key} = ?`).join(', ')} WHERE id = 1`,
      entries.map(([, value]) => value as SqlPrimitive),
    );
  }

  async getGoal(): Promise<NutritionGoalRow | null> {
    return (await this.db.query<NutritionGoalRow>('SELECT * FROM nutrition_goals WHERE id = 1'))[0] || null;
  }

  async upsertGoal(goal: NutritionGoalRow, now: string): Promise<void> {
    await this.db.execute(
      `INSERT INTO nutrition_goals(
        id, calories_centi, carbs_centi, protein_centi, fat_centi, source, created_at, updated_at
      ) VALUES(1, ?, ?, ?, ?, 'manual', ?, ?)
      ON CONFLICT(id) DO UPDATE SET
        calories_centi=excluded.calories_centi,
        carbs_centi=excluded.carbs_centi,
        protein_centi=excluded.protein_centi,
        fat_centi=excluded.fat_centi,
        source='manual',
        updated_at=excluded.updated_at`,
      [goal.calories_centi, goal.carbs_centi, goal.protein_centi, goal.fat_centi, now, now],
    );
  }

  async insertInitialWeight(weightCenti: number, now: string): Promise<void> {
    await this.db.execute(
      `INSERT INTO weight_records(weight_centi, recorded_at, created_at, updated_at)
       SELECT ?, ?, ?, ? WHERE NOT EXISTS(SELECT 1 FROM weight_records WHERE deleted_at IS NULL)`,
      [weightCenti, now, now, now],
    );
  }

  async insertWeightIfChanged(weightCenti: number, now: string): Promise<void> {
    const latest = await this.db.query<{ weight_centi: number }>(
      `SELECT weight_centi FROM weight_records
       WHERE deleted_at IS NULL ORDER BY recorded_at DESC, id DESC LIMIT 1`,
    );
    if (latest[0]?.weight_centi === weightCenti) return;
    await this.db.execute(
      `INSERT INTO weight_records(weight_centi, recorded_at, created_at, updated_at)
       VALUES(?, ?, ?, ?)`,
      [weightCenti, now, now, now],
    );
  }
}
