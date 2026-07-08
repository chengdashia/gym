import { defineStore } from 'pinia';
import { setToken, clearAuth } from '@/utils/request';
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
      // 主动清理旧版本残留的登录信息（v1 / v2 / v3 都清掉）
      try {
        uni.removeStorageSync('gym_token');
        uni.removeStorageSync('gym_user');
        uni.removeStorageSync('gym_token_v2');
        uni.removeStorageSync('gym_user_v2');
      } catch {}

      // 修复：冷启动时不自动恢复上次登录态，默认以游客身份进入小程序。
      // 登录状态仅在本次使用期间保持；下次冷启动需要重新登录。
      // 这样新用户/重新编译后不会直接显示旧用户。
      clearAuth();
      this.token = '';
      this.user = null;

      this.bootstrapped = true;
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