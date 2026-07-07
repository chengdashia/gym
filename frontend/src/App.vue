<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app';
import { useAuthStore } from '@/store/auth';
import { useAppStore } from '@/store/app';

onLaunch(async () => {
  console.log('[App] launched');
  const appStore = useAppStore();
  appStore.init();
  const auth = useAuthStore();
  await auth.bootstrap();

  if (auth.token && auth.user && !auth.user.agreement_confirmed) {
    uni.reLaunch({ url: '/pages/login/onboarding' });
    return;
  }

  if (!auth.token) {
    console.log('[App] no token, browsing as guest');
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