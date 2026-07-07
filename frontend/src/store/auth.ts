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
  is_member: boolean;
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
    needOnboarding: (s) => !s.user?.agreement_confirmed,
  },

  actions: {
    bootstrap(): Promise<void> {
      if (this.initPromise) return this.initPromise;
      this.initPromise = this._doBootstrap();
      return this.initPromise;
    },

    async _doBootstrap() {
      const t = getToken();
      if (t) this.token = t;
      try {
        const cached = uni.getStorageSync(STORAGE_KEYS.user) as UserBrief | null;
        if (cached) this.user = cached;
      } catch {}
      this.bootstrapped = true;

      if (!this.token) {
        this.ready = true;
        return;
      }

      try {
        const me = await (await import('@/api/user')).userApi.getMe();
        const u = (await import('@/store/user')).useUserStore();
        u.me = me;
        this.setUser({
          id: me.id,
          nickname: me.nickname,
          avatar_url: me.avatar_url,
          is_new_user: false,
          agreement_confirmed: me.agreement_confirmed,
          is_member: me.is_member,
        });
      } catch {
        // Token invalid or network error - clear it
        this.token = '';
        this.user = null;
        clearAuth();
      }
      this.ready = true;
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

      // 开发/无 wechat 凭据场景：后端把 code 直接当 openid 使用，
      // 每次拿到的 code 都不同会创建新用户。这里复用首次缓存的稳定 id。
      if (!wechatCode || wechatCode === 'mock_openid_undefined') {
        const cachedId = (() => {
          try { return uni.getStorageSync('gym_dev_openid') as string; } catch { return ''; }
        })();
        if (cachedId) {
          wechatCode = cachedId;
        } else {
          const stable = `dev_${Date.now()}_${Math.floor(Math.random() * 1e6)}`;
          try { uni.setStorageSync('gym_dev_openid', stable); } catch { /* ignore */ }
          wechatCode = stable;
        }
      }

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