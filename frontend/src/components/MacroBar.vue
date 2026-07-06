<template>
  <view class="macro-bar">
    <view class="row">
      <text class="label" :style="{ color: color }">{{ label }}</text>
      <text class="value">{{ displayValue }} / {{ displayGoal }} {{ unit }}</text>
    </view>
    <view class="track">
      <view class="fill" :style="{ width: pct + '%', background: color }" />
      <view v-if="goal" class="goal-mark" :style="{ left: '100%' }" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(defineProps<{
  label: string;
  value: number;
  goal: number;
  unit?: string;
  color?: string;
  precision?: number;
}>(), {
  unit: 'g',
  color: '#5BC89A',
  precision: 0,
});

const pct = computed(() => {
  if (!props.goal) return 0;
  return Math.min(100, (props.value / props.goal) * 100);
});

const displayValue = computed(() => {
  return props.value ? Number(props.value).toFixed(props.precision) : '0';
});

const displayGoal = computed(() => {
  return props.goal ? Number(props.goal).toFixed(props.precision) : '—';
});
</script>

<style lang="scss" scoped>
.macro-bar {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.label {
  font-size: $fs-sm;
  font-weight: 600;
}
.value {
  font-size: $fs-sm;
  color: $text-3;
}
.track {
  position: relative;
  width: 100%;
  height: 12rpx;
  background: $bg-2;
  border-radius: $r-pill;
  overflow: hidden;
}
.fill {
  height: 100%;
  border-radius: $r-pill;
  transition: width 0.3s ease;
}
.goal-mark {
  position: absolute;
  top: -4rpx;
  width: 2rpx;
  height: 20rpx;
  background: $text-3;
}
</style>