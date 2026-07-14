import { useAuthStore } from '@/store/auth';

interface RequireAuthOptions {
  message?: string;
  redirect?: string;
}

let loginPromptOpen = false;

/**
 * 检查当前是否已登录。
 * 未登录时由用户决定是否进入登录页；取消后保留当前页面。
 */
export function requireAuth(options: RequireAuthOptions = {}): boolean {
  const auth = useAuthStore();
  if (auth.isLogged) return true;
  if (loginPromptOpen) return false;

  const redirect = options.redirect;
  const url = redirect
    ? `/pages/login/onboarding?redirect=${encodeURIComponent(redirect)}`
    : '/pages/login/onboarding';

  loginPromptOpen = true;
  uni.showModal({
    title: '登录后可使用此功能',
    content: options.message || '登录后可保存和同步你的数据。',
    cancelText: '暂不登录',
    confirmText: '去登录',
    success: ({ confirm }) => {
      loginPromptOpen = false;
      if (confirm) uni.navigateTo({ url });
    },
    fail: () => { loginPromptOpen = false; },
  });

  return false;
}
