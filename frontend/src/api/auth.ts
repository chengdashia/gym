import { http } from '@/utils/request';

export interface WechatLoginPayload {
  code: string;
  nickname?: string;
  avatar_url?: string;
}

export interface WechatLoginResult {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    openid: string | null;
    nickname: string | null;
    avatar_url: string | null;
    is_new_user: boolean;
    agreement_confirmed: boolean;
    is_member: boolean;
    member_expired_at: string | null;
  };
}

export const authApi = {
  wechatLogin(payload: WechatLoginPayload) {
    return http.post<WechatLoginResult>('/auth/wechat-login', payload, { silent: true });
  },
};