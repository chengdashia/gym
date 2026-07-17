import { http } from '@/utils/request';

export interface AuthUserSummary {
  id: number;
  openid: string | null;
  nickname: string | null;
  avatar_url: string | null;
  is_new_user: boolean;
  agreement_confirmed: boolean;
  onboarding_step: 'agreement' | 'profile' | 'complete';
  is_member: boolean;
  member_expired_at: string | null;
  experimental_features: Array<'diet_programs' | 'food_recognition'>;
}

export interface AuthResult {
  access_token: string;
  token_type: string;
  user: AuthUserSummary;
}

export interface WechatLoginPayload {
  code: string;
  nickname?: string;
  avatar_url?: string;
}

export interface PhoneLoginPayload {
  phone: string;
  password: string;
}

export interface RegisterPayload {
  phone: string;
  password: string;
  confirm_password: string;
  captcha_id: string;
  captcha_code: string;
}

export interface CaptchaResult {
  captcha_id: string;
  svg: string;
}

export const authApi = {
  wechatLogin(payload: WechatLoginPayload) {
    return http.post<AuthResult>('/auth/wechat-login', payload, { silent: true });
  },
  phoneLogin(payload: PhoneLoginPayload) {
    return http.post<AuthResult>('/auth/phone-login', payload, { silent: true });
  },
  register(payload: RegisterPayload) {
    return http.post<AuthResult>('/auth/register', payload, { silent: true });
  },
  getCaptcha() {
    return http.get<CaptchaResult>('/auth/captcha', undefined, { silent: true });
  },
};
