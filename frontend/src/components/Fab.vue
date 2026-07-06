<template>
  <view :class="['fab', { extended }]" :style="{ bottom: bottom }" @tap="$emit('tap')">
    <text class="fab-icon">{{ icon }}</text>
    <text v-if="extended" class="fab-label">{{ label }}</text>
  </view>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  icon?: string;
  label?: string;
  extended?: boolean;
  bottom?: string;
}>(), {
  icon: '+',
  label: '',
  extended: false,
  bottom: '180rpx',
});

defineEmits<{ (e: 'tap'): void }>();
</script>

<style lang="scss" scoped>
.fab {
  position: fixed;
  right: $gap-3;
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background: $gradient-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 12rpx 32rpx rgba(95, 175, 145, 0.35);
  z-index: 40;
  &.extended {
    width: auto;
    padding: 0 28rpx;
    gap: 12rpx;
  }
}
.fab-icon {
  font-size: 48rpx;
  color: #fff;
  line-height: 1;
}
.fab-label {
  color: #fff;
  font-size: $fs-md;
  font-weight: 500;
}
</style>