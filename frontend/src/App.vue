<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app';
import { useAuthStore } from '@/store/auth';
import { useAppStore } from '@/store/app';

onLaunch(() => {
  console.log('[App] launched');
  const appStore = useAppStore();
  appStore.init();
  const auth = useAuthStore();
  auth.bootstrap();
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