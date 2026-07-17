import { defineStore } from 'pinia';
import { getToken, setToken, clearAuth } from '@/utils/request';
import { authApi, AuthResult } from '@/api/auth';
import { STORAGE_KEYS } from '@/utils/constants';

interface UserBrief {
  id: number;
  nickname: string | null;
  avatar_url: string | null;
  is_new_user: boolean;
  agreement_confirmed: boolean;
  onboarding_step: 'agreement' | 'profile' | 'complete';
  is_member: boolean;
  experimental_features: Array<'diet_programs' | 'food_recognition'>;
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: '' as string,
    user: null as UserBrief | null,
    bootstrapped: false,
    ready: false,
    initPromise: null as Promise<void> | null,
  }),

  getters: {
    isLogged: (s) => !!s.token,
    needOnboarding: (s) => s.user?.onboarding_step !== 'complete',
  },

  actions: {
    bootstrap(): Promise<void> {
      if (this.initPromise) return this.initPromise;
      this.initPromise = this._doBootstrap();
      return this.initPromise;
    },

    async _doBootstrap() {
      const savedToken = getToken();
      if (savedToken) this.token = savedToken;

      try {
        const cached = uni.getStorageSync(STORAGE_KEYS.user) as UserBrief | null;
        if (cached) this.user = cached;
      } catch {
        // storage unavailable
      }

      this.bootstrapped = true;
      if (!this.token) {
        this.ready = true;
        return;
      }

      try {
        const me = await (await import('@/api/user')).userApi.getMe();
        const userStore = (await import('@/store/user')).useUserStore();
        userStore.me = me;
        this.setUser({
          id: me.id,
          nickname: me.nickname,
          avatar_url: me.avatar_url,
          is_new_user: false,
          agreement_confirmed: me.agreement_confirmed,
          onboarding_step: me.onboarding_step,
          is_member: me.is_member,
          member_expired_at: me.member_expired_at,
          experimental_features: me.experimental_features,
        });
      } catch (error: any) {
        if (error?.code === 40101 || error?.statusCode === 401) this.logout();
      } finally {
        this.ready = true;
      }
    },

    _setAuthData(data: AuthResult) {
      this.token = data.access_token;
      setToken(data.access_token);
      this.user = data.user;
      uni.setStorageSync(STORAGE_KEYS.user, data.user);
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

      if (!wechatCode) throw new Error('微信登录失败，请重试');

      const data = await authApi.wechatLogin({
        code: wechatCode,
        nickname: payload?.nickname,
        avatar_url: payload?.avatar_url,
      });
      this._setAuthData(data);
      return data;
    },

    async phoneLogin(phone: string, password: string) {
      const data = await authApi.phoneLogin({ phone, password });
      this._setAuthData(data);
      return data;
    },

    async register(phone: string, password: string, confirmPassword: string, captchaId: string, captchaCode: string) {
      const data = await authApi.register({
        phone,
        password,
        confirm_password: confirmPassword,
        captcha_id: captchaId,
        captcha_code: captchaCode,
      });
      this._setAuthData(data);
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
