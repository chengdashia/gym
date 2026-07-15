import { defineStore } from 'pinia';

import { userApi } from '@/api/user';
import { useUserStore } from '@/store/user';

interface LocalUserBrief {
  id: 1;
  nickname: string | null;
  avatar_url: string | null;
  is_new_user: boolean;
  agreement_confirmed: boolean;
  onboarding_step: 'profile' | 'goal' | 'complete';
  is_member: false;
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: '' as '' | 'local',
    user: null as LocalUserBrief | null,
    bootstrapped: false,
    ready: false,
    initPromise: null as Promise<void> | null,
  }),

  getters: {
    isLogged: (state) => state.ready && state.token === 'local',
    needOnboarding: (state) => state.user?.onboarding_step !== 'complete',
  },

  actions: {
    bootstrap(): Promise<void> {
      if (this.initPromise) return this.initPromise;
      this.initPromise = this._doBootstrap();
      return this.initPromise;
    },

    async _doBootstrap(): Promise<void> {
      try {
        const me = await userApi.getMe();
        const userStore = useUserStore();
        userStore.me = me;
        this.token = 'local';
        this.user = {
          id: 1,
          nickname: me.nickname,
          avatar_url: me.avatar_url,
          is_new_user: me.onboarding_step !== 'complete',
          agreement_confirmed: true,
          onboarding_step: me.onboarding_step,
          is_member: false,
        };
        this.bootstrapped = true;
      } finally {
        this.ready = true;
      }
    },

    setUser(update: Partial<LocalUserBrief>): void {
      if (!this.user) return;
      this.user = { ...this.user, ...update };
      const userStore = useUserStore();
      if (userStore.me) {
        userStore.me = {
          ...userStore.me,
          nickname: this.user.nickname,
          avatar_url: this.user.avatar_url,
          onboarding_step: this.user.onboarding_step,
        };
      }
    },

    async refresh(): Promise<void> {
      this.initPromise = null;
      await this.bootstrap();
    },

    logout(): void {
      // Compatibility no-op. Offline mode always has one local user.
    },
  },
});
