import { http } from '@/utils/request';
import { API_BASE } from '@/utils/constants';
import { getToken } from '@/utils/request';

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
  phone: string | null;
  is_member: boolean;
  member_expired_at: string | null;
  agreement_confirmed: boolean;
  onboarding_step: 'agreement' | 'profile' | 'complete';
  agreement_version: string | null;
  agreement_confirmed_at: string | null;
  experimental_features: Array<'diet_programs' | 'food_recognition'>;
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

export const userApi = {
  exportData() {
    return new Promise<string>((resolve, reject) => {
      const token = getToken();
      uni.downloadFile({
        url: `${API_BASE}/users/export.csv`,
        header: token ? { Authorization: `Bearer ${token}` } : {},
        success: (res) => res.statusCode === 200
          ? resolve(res.tempFilePath)
          : reject({ statusCode: res.statusCode, message: '导出失败' }),
        fail: reject,
      });
    });
  },
  getMe() {
    return http.get<UserMe>('/users/me');
  },
  getAvatarData() {
    return http.get<{ data_url: string | null }>('/users/me/avatar-data');
  },
  updateMe(payload: { nickname?: string; avatar_url?: string; profile?: Partial<UserProfile> }) {
    return http.put<UserMe>('/users/me', payload);
  },
  confirmAgreement(payload: { agreement_version: string; privacy_version: string }) {
    return http.post('/users/agreement-confirm', payload);
  },
  getNutritionGoal() {
    return http.get<NutritionGoal>('/users/nutrition-goal');
  },
  updateNutritionGoal(payload: NutritionGoal) {
    return http.put<NutritionGoal>('/users/nutrition-goal', payload);
  },
  recommendNutritionGoal() {
    return http.post<NutritionGoal & { formula_note?: string }>('/users/nutrition-goal/recommend');
  },
  getReminders() {
    return http.get<{ items: ReminderItem[] }>('/users/reminders');
  },
  updateReminders(items: ReminderItem[]) {
    return http.put<{ items: ReminderItem[] }>('/users/reminders', { items });
  },
  deleteData() {
    return http.post('/users/delete-data');
  },
  cancelAccount() {
    return http.post('/users/cancel-account');
  },
};
