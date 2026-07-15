import { ProfileRepository, type LocalProfileRow } from '@/local/repositories/profile';
import type { SqlDatabase } from '@/local/db/types';

export interface NutritionGoalValue {
  calories_kcal: number;
  carbs_g: number;
  protein_g: number;
  fat_g: number;
}

export interface LocalProfileValue {
  id: 1;
  nickname: string | null;
  avatar_url: string | null;
  onboarding_step: 'profile' | 'goal' | 'complete';
  profile: {
    gender: string | null;
    age: number | null;
    height_cm: number | null;
    current_weight_kg: number | null;
    target_weight_kg: number | null;
    fitness_goal: string | null;
    training_frequency: string | null;
  };
}

export interface FinishOnboardingInput extends Partial<NutritionGoalValue> {
  nickname: string;
  avatar_url?: string | null;
  gender?: string | null;
  age?: number | null;
  height_cm?: number | null;
  current_weight_kg?: number | null;
  target_weight_kg?: number | null;
  fitness_goal: string;
  training_frequency?: string | null;
}

const fromCenti = (value: number | null): number | null => value == null ? null : value / 100;
const toCenti = (value: number | null | undefined): number | null => value == null ? null : Math.round(value * 100);
const nowIso = () => new Date().toISOString();

function mapProfile(row: LocalProfileRow): LocalProfileValue {
  return {
    id: 1,
    nickname: row.nickname,
    avatar_url: row.avatar_path,
    onboarding_step: row.onboarding_step,
    profile: {
      gender: row.gender,
      age: row.age,
      height_cm: fromCenti(row.height_centi),
      current_weight_kg: fromCenti(row.current_weight_centi),
      target_weight_kg: fromCenti(row.target_weight_centi),
      fitness_goal: row.fitness_goal,
      training_frequency: row.training_frequency,
    },
  };
}

export function createProfileService(db: SqlDatabase) {
  const repository = new ProfileRepository(db);

  return {
    async get(): Promise<LocalProfileValue> {
      return mapProfile(await repository.ensureProfile(nowIso()));
    },

    async getNutritionGoal(): Promise<NutritionGoalValue> {
      const row = await repository.getGoal();
      return {
        calories_kcal: fromCenti(row?.calories_centi ?? 0) || 0,
        carbs_g: fromCenti(row?.carbs_centi ?? 0) || 0,
        protein_g: fromCenti(row?.protein_centi ?? 0) || 0,
        fat_g: fromCenti(row?.fat_centi ?? 0) || 0,
      };
    },

    async finishOnboarding(input: FinishOnboardingInput): Promise<LocalProfileValue> {
      const nickname = input.nickname.trim();
      if (!nickname) throw new Error('请输入昵称');
      if (!input.fitness_goal) throw new Error('请选择健身目标');
      const goal = {
        calories_centi: toCenti(input.calories_kcal ?? 0) || 0,
        carbs_centi: toCenti(input.carbs_g ?? 0) || 0,
        protein_centi: toCenti(input.protein_g ?? 0) || 0,
        fat_centi: toCenti(input.fat_g ?? 0) || 0,
      };
      const now = nowIso();

      await db.transaction(async (tx) => {
        const scoped = new ProfileRepository(tx);
        await scoped.ensureProfile(now);
        await scoped.updateProfile({
          nickname,
          avatar_path: input.avatar_url ?? null,
          gender: input.gender ?? null,
          age: input.age ?? null,
          height_centi: toCenti(input.height_cm),
          current_weight_centi: toCenti(input.current_weight_kg),
          target_weight_centi: toCenti(input.target_weight_kg),
          fitness_goal: input.fitness_goal,
          training_frequency: input.training_frequency ?? null,
          onboarding_step: 'complete',
          updated_at: now,
        });
        await scoped.upsertGoal(goal, now);
        const weight = toCenti(input.current_weight_kg);
        if (weight != null) await scoped.insertInitialWeight(weight, now);
      });

      const row = await repository.getProfile();
      if (!row) throw new Error('本地资料保存失败');
      return mapProfile(row);
    },
  };
}
