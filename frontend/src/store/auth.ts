import { defineStore } from 'pinia';
import { getToken, setToken, clearAuth } from '@/utils/request';
import { authApi } from '@/api/auth';
import { STORAGE_KEYS } from '@/utils/constants';

interface UserBrief {
  id: number;
  nickname: string | null;
  avatar_url: string | null;
  is_new_user: boolean;
  agreement_confirmed: boolean;
  is_member: boolean;
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: '' as string,
    user: null as UserBrief | null,
    bootstrapped: false,
  }),

  getters: {
    isLogged: (s) => !!s.token,
    needOnboarding: (s) => !s.user?.agreement_confirmed,
  },

  actions: {
    bootstrap() {
      const t = getToken();
      if (t) this.token = t;
      try {
        const cached = uni.getStorageSync(STORAGE_KEYS.user) as UserBrief | null;
        if (cached) this.user = cached;
      } catch {}
      this.bootstrapped = true;
    },

    async login(payload?: { nickname?: string; avatar_url?: string }) {
      let wechatCode = '';
      try {
        // #ifdef MP-WEIXIN
        const loginRes = await new Promise<UniApp.LoginRes>((resolve, reject) => {
          uni.login({ provider: 'weixin', success: resolve, fail: reject });
        });
        wechatCode = loginRes.code || '';
        // #endif
      } catch {
        wechatCode = '';
      }
      if (!wechatCode) {
        wechatCode = `mock_openid_${Date.now()}`;
      }

      const data = await authApi.wechatLogin({
        code: wechatCode,
        nickname: payload?.nickname,
        avatar_url: payload?.avatar_url,
      });
      this.token = data.access_token;
      setToken(data.access_token);
      this.user = data.user;
      uni.setStorageSync(STORAGE_KEYS.user, data.user);
      return data;
    },

    setUser(u: Partial<UserBrief>) {
      this.user = { ...(this.user as any), ...u } as UserBrief;
      uni.setStorageSync(STORAGE_KEYS.user, this.user);
    },

    logout() {
      this.token = '';
      this.user = null;
      clearAuth();
    },
  },
});