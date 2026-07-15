import { getLocalDatabase } from '@/local/db';
import { createProfileService } from '@/local/services/profile';

export interface UserProfile {
  gender?: string | null;
  age?: number | null;
  height_cm?: number | null;
  current_weight_kg?: number | null;
  target_weight_kg?: number | null;
  fitness_goal?: string | null;
  training_frequency?: string | null;
}

export interface UserMe {
  id: number;
  nickname: string | null;
  avatar_url: string | null;
  phone: null;
  is_member: false;
  member_expired_at: null;
  agreement_confirmed: true;
  onboarding_step: 'profile' | 'goal' | 'complete';
  agreement_version: null;
  agreement_confirmed_at: null;
  profile: UserProfile | null;
}

export interface NutritionGoal {
  calories_kcal: number;
  carbs_g: number;
  protein_g: number;
  fat_g: number;
}

export interface ReminderItem {
  reminder_type: 'diet' | 'training' | 'weight';
  enabled: boolean;
  reminder_time: string;
  weekdays: string;
}

function service() {
  return createProfileService(getLocalDatabase());
}

function asUserMe(local: Awaited<ReturnType<ReturnType<typeof createProfileService>['get']>>): UserMe {
  return {
    ...local,
    phone: null,
    is_member: false,
    member_expired_at: null,
    agreement_confirmed: true,
    agreement_version: null,
    agreement_confirmed_at: null,
  };
}

const DEFAULT_REMINDERS: ReminderItem[] = [
  { reminder_type: 'diet', enabled: false, reminder_time: '08:00', weekdays: '1,2,3,4,5,6,7' },
  { reminder_type: 'training', enabled: false, reminder_time: '18:00', weekdays: '1,2,3,4,5,6,7' },
  { reminder_type: 'weight', enabled: false, reminder_time: '07:00', weekdays: '1,2,3,4,5,6,7' },
];

export const userApi = {
  async getMe(): Promise<UserMe> {
    return asUserMe(await service().get());
  },

  async getAvatarData(): Promise<{ data_url: string | null }> {
    return { data_url: null };
  },

  async updateMe(payload: { nickname?: string; avatar_url?: string; profile?: Partial<UserProfile> }): Promise<UserMe> {
    return asUserMe(await service().updateProfile(payload));
  },

  async confirmAgreement(_payload?: { agreement_version: string; privacy_version: string }): Promise<void> {
    // Local privacy information remains visible, but it is not an auth gate.
  },

  async finishOnboarding(payload: Parameters<ReturnType<typeof createProfileService>['finishOnboarding']>[0]): Promise<UserMe> {
    return asUserMe(await service().finishOnboarding(payload));
  },

  getNutritionGoal(): Promise<NutritionGoal> {
    return service().getNutritionGoal();
  },

  updateNutritionGoal(payload: NutritionGoal): Promise<NutritionGoal> {
    return service().updateNutritionGoal(payload);
  },

  async recommendNutritionGoal(): Promise<NutritionGoal & { formula_note: string }> {
    const me = await service().get();
    const weight = me.profile.current_weight_kg || 70;
    const calories = Math.round(weight * 28);
    return {
      calories_kcal: calories,
      carbs_g: Math.round(calories * 0.45 / 4),
      protein_g: Math.round(weight * 1.6),
      fat_g: Math.round(calories * 0.25 / 9),
      formula_note: '根据本地体重估算，可手动调整',
    };
  },

  async getReminders(): Promise<{ items: ReminderItem[] }> {
    const rows = await getLocalDatabase().query<{ value: string }>(
      "SELECT value FROM app_meta WHERE key = 'reminders'",
    );
    return { items: rows[0] ? JSON.parse(rows[0].value) : DEFAULT_REMINDERS };
  },

  async updateReminders(items: ReminderItem[]): Promise<{ items: ReminderItem[] }> {
    await getLocalDatabase().execute(
      `INSERT INTO app_meta(key, value) VALUES('reminders', ?)
       ON CONFLICT(key) DO UPDATE SET value=excluded.value`,
      [JSON.stringify(items)],
    );
    return { items };
  },

  async exportData(): Promise<string> {
    throw new Error('请使用离线备份功能');
  },

  async deleteData(): Promise<void> {
    throw new Error('本地数据清空将在备份功能中提供');
  },

  async cancelAccount(): Promise<void> {
    throw new Error('离线模式没有账号');
  },
};
