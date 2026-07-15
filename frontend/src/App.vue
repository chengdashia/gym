<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app';
import { useAuthStore } from '@/store/auth';
import { useAppStore } from '@/store/app';
import { initializeLocalDatabase } from '@/local/db';

onLaunch(async () => {
  console.log('[App] launched');
  await initializeLocalDatabase();
  const appStore = useAppStore();
  appStore.init();
  const auth = useAuthStore();
  await auth.bootstrap();
  // 不在 onLaunch 中调 uni.reLaunch —— 此时首页 webview 尚未 ready，
  // 会触发「routeDone with a webviewId X is not found」错误。
  // needOnboarding 检查改由首页 onMounted 中处理。
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
