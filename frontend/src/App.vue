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

  if (!auth.token) {
    uni.reLaunch({ url: '/pages/login/onboarding' });
    return;
  }

  try {
    const me = await userApi.getMe();
    if (!me.agreement_confirmed) {
      uni.reLaunch({ url: '/pages/login/onboarding' });
      return;
    }
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
@use '@/styles/common.scss';

/* 液态玻璃全局背景 */
page {
  background: $gradient-page-bg;
  background-attachment: fixed;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
  color: $text-1;
  font-size: 28rpx;
  line-height: 1.5;
}
</style>