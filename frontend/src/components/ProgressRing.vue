<template>
  <view class="ring-wrapper" :style="{ width: `${size}rpx`, height: `${size}rpx` }">
    <view class="ring-bg" :style="bgStyle" />
    <view class="ring-progress" :style="progressStyle" />
    <view class="ring-center">
      <slot>
        <view class="ring-value">{{ Math.round(displayPct) }}%</view>
      </slot>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, type CSSProperties } from 'vue';

const props = withDefaults(defineProps<{
  value: number;
  goal: number;
  size?: number;
  thickness?: number;
  color?: string;
  bgColor?: string;
  max?: number;
}>(), {
  size: 200,
  thickness: 14,
  color: '#5BC89A',
  bgColor: '#EAF8F1',
  max: 1.5,
});

const pct = computed(() => {
  if (!props.goal) return 0;
  return Math.min(props.value / props.goal, props.max);
});

const displayPct = computed(() => Math.min(100, pct.value * 100));

const bgStyle = computed<CSSProperties>(() => ({
  width: `${props.size}rpx`,
  height: `${props.size}rpx`,
  borderRadius: '50%',
  border: `${props.thickness}rpx solid ${props.bgColor}`,
  boxSizing: 'border-box',
}));

const progressStyle = computed(() => {
  const angle = Math.min(360, Math.max(0, pct.value * 360));
  const mask = `conic-gradient(${props.color} 0deg, ${props.color} ${angle}deg, transparent ${angle}deg)`;
  return {
    width: `${props.size}rpx`,
    height: `${props.size}rpx`,
    borderRadius: '50%',
    background: mask as any,
    mask: 'radial-gradient(circle, transparent calc(50% - var(--t)), black calc(50% - var(--t) + 1rpx))',
    WebkitMask: 'radial-gradient(circle, transparent calc(50% - var(--t)), black calc(50% - var(--t) + 1rpx))',
    // Fallback ring via border
    position: 'absolute' as const,
    top: '0',
    left: '0',
    '--t': `${props.thickness}rpx`,
  } as any;
});
</script>

<style lang="scss" scoped>
.ring-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ring-bg {
  position: absolute;
  top: 0;
  left: 0;
}
.ring-progress {
  z-index: 1;
}
.ring-center {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}
.ring-value {
  font-size: 32rpx;
  font-weight: 700;
  color: $text-1;
}
</style>
