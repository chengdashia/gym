<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app';
import { useAuthStore } from '@/store/auth';
import { useAppStore } from '@/store/app';
import { useUserStore } from '@/store/user';
import { userApi } from '@/api/user';

onLaunch(async () => {
  console.log('[App] launched');
  const appStore = useAppStore();
  appStore.init();
  const auth = useAuthStore();
  auth.bootstrap();

  // 根据本地缓存的 token 决定入口路由
  // - 没有 token → 去 onboarding 登录
  // - 有 token 但未确认协议 → 去 onboarding 协议页
  // - 有 token 且已确认 → 留在首页（pages.json 默认页）
  if (!auth.token) {
    uni.reLaunch({ url: '/pages/login/onboarding' });
    return;
  }

  // 有 token，用 /users/me 校验并刷新用户状态
  try {
    const me = await userApi.getMe();
    if (!me.agreement_confirmed) {
      uni.reLaunch({ url: '/pages/login/onboarding' });
      return;
    }
    // 把后端最新状态写回 store/storage
    const u = useUserStore();
    u.me = me;
    auth.setUser({
      id: me.id,
      nickname: me.nickname,
      avatar_url: me.avatar_url,
      is_new_user: false,
      agreement_confirmed: me.agreement_confirmed,
      is_member: me.is_member,
    });
  } catch {
    // token 失效，清除并回到 onboarding
    auth.logout();
    uni.reLaunch({ url: '/pages/login/onboarding' });
  }
});

onShow(() => {
  console.log('[App] show');
});

onHide(() => {
  console.log('[App] hide');
});
</script>

<style lang="scss">
@import '@/styles/common.scss';

page {
  background: $bg;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
  color: $text-1;
  font-size: 28rpx;
  line-height: 1.5;
}
</style>