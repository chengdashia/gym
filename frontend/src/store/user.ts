import { defineStore } from 'pinia';
import { userApi, UserMe, UserProfile, NutritionGoal, ReminderItem } from '@/api/user';
import { resolveStaticUrl } from '@/utils/request';

export const useUserStore = defineStore('user', {
  state: () => ({
    me: null as UserMe | null,
    goal: { calories_kcal: 0, carbs_g: 0, protein_g: 0, fat_g: 0 } as NutritionGoal,
    reminders: [] as ReminderItem[],
    loading: false,
    avatarDataUrl: '',
  }),

  getters: {
    hasProfile: (s) => !!s.me?.profile,
    nickname: (s) => s.me?.nickname || '健身伙伴',
    avatar: (s) => s.avatarDataUrl || resolveStaticUrl(s.me?.avatar_url),
  },

  actions: {
    reset() {
      this.me = null;
      this.goal = { calories_kcal: 0, carbs_g: 0, protein_g: 0, fat_g: 0 };
      this.reminders = [];
      this.avatarDataUrl = '';
    },
    async fetchMe() {
      this.loading = true;
      try {
        this.me = await userApi.getMe();
        this.avatarDataUrl = this.me.avatar_url
          ? (await userApi.getAvatarData()).data_url || ''
          : '';
      } finally {
        this.loading = false;
      }
    },
    async updateProfile(payload: { nickname?: string; avatar_url?: string; profile?: Partial<UserProfile> }) {
      this.me = await userApi.updateMe(payload);
      if (payload.avatar_url) {
        this.avatarDataUrl = (await userApi.getAvatarData()).data_url || '';
      }
      return this.me;
    },
    async confirmAgreement(version = 'v1.0') {
      await userApi.confirmAgreement({ agreement_version: version, privacy_version: version });
      if (this.me) {
        this.me.agreement_confirmed = true;
        this.me.agreement_version = version;
        this.me.agreement_confirmed_at = new Date().toISOString();
      }
    },
    async fetchGoal() {
      this.goal = await userApi.getNutritionGoal() || {
        calories_kcal: 0,
        carbs_g: 0,
        protein_g: 0,
        fat_g: 0,
      };
    },
    async updateGoal(payload: NutritionGoal) {
      this.goal = await userApi.updateNutritionGoal(payload);
    },
    async recommendGoal() {
      const data = await userApi.recommendNutritionGoal();
      this.goal = {
        calories_kcal: data.calories_kcal,
        carbs_g: data.carbs_g,
        protein_g: data.protein_g,
        fat_g: data.fat_g,
      };
      return this.goal;
    },
    async fetchReminders() {
      const res = await userApi.getReminders();
      this.reminders = res.items || [];
    },
    async updateReminders(items: ReminderItem[]) {
      const res = await userApi.updateReminders(items);
      this.reminders = res.items || [];
    },
    async deleteData() {
      await userApi.deleteData();
    },
    async cancelAccount() {
      await userApi.cancelAccount();
    },
  },
});
