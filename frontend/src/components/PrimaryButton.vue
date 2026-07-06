<template>
  <view :class="['primary-btn', { block, disabled }]" :style="{ background: bg }" @tap="onTap">
    <text class="primary-btn-text">{{ text }}</text>
  </view>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  text: string;
  block?: boolean;
  disabled?: boolean;
  bg?: string;
}>(), {
  block: true,
  disabled: false,
  bg: '',
});

const emit = defineEmits<{ (e: 'tap'): void }>();

function onTap() {
  if (props.disabled) return;
  emit('tap');
}
</script>

<style lang="scss" scoped>
.primary-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24rpx 32rpx;
  background: $primary;
  border-radius: $r-16;
  color: #fff;
  font-size: $fs-md;
  font-weight: 600;
  transition: opacity 0.2s ease;
  &.block { width: 100%; }
  &.disabled { opacity: 0.5; }
  &:active { opacity: 0.85; }
}
.primary-btn-text {
  color: #fff;
}
</style>