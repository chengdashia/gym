<template>
  <view v-if="visible" class="rest-timer">
    <view class="rest-bar">
      <view class="rest-time">{{ formatted }}</view>
      <view class="rest-actions">
        <view class="rest-btn" @tap="$emit('adjust', -15)">-15s</view>
        <view class="rest-btn primary" @tap="$emit('toggle')">{{ running ? '暂停' : '继续' }}</view>
        <view class="rest-btn primary" @tap="$emit('skip')">跳过</view>
        <view class="rest-btn" @tap="$emit('adjust', 15)">+15s</view>
        <view class="rest-btn close" @tap="$emit('close')">✕</view>
      </view>
    </view>
    <view class="rest-progress">
      <view class="rest-progress-fill" :style="{ width: pct + '%' }" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { formatCountdown } from '@/utils/date';

const props = withDefaults(defineProps<{
  visible: boolean;
  remaining: number;
  total: number;
  running?: boolean;
}>(), {
  running: true,
});

defineEmits<{
  (e: 'toggle'): void;
  (e: 'skip'): void;
  (e: 'adjust', delta: number): void;
  (e: 'close'): void;
}>();

const formatted = computed(() => formatCountdown(props.remaining));

const pct = computed(() => {
  if (!props.total) return 0;
  return Math.max(0, Math.min(100, ((props.total - props.remaining) / props.total) * 100));
});
</script>

<style lang="scss" scoped>
.rest-timer {
  position: fixed;
  bottom: calc(#{$tabbar-height} + #{$gap-3});
  left: $gap-3;
  right: $gap-3;
  background: $card;
  border-radius: $r-20;
  padding: $gap-3;
  box-shadow: $shadow-lg;
  z-index: 50;
}
.rest-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.rest-time {
  font-size: 60rpx;
  font-weight: 700;
  color: $primary;
  font-variant-numeric: tabular-nums;
  letter-spacing: 2rpx;
}
.rest-actions {
  display: flex;
  gap: 12rpx;
}
.rest-btn {
  padding: 10rpx 16rpx;
  background: $bg-2;
  border-radius: $r-12;
  color: $text-2;
  font-size: $fs-xs;
  &.primary {
    background: $primary-tint;
    color: $primary-deep;
  }
  &.close {
    background: #FFE2E2;
    color: $danger;
  }
}
.rest-progress {
  margin-top: $gap-2;
  height: 8rpx;
  background: $bg-2;
  border-radius: $r-pill;
  overflow: hidden;
}
.rest-progress-fill {
  height: 100%;
  background: $gradient-primary;
  border-radius: $r-pill;
  transition: width 0.6s linear;
}
</style>