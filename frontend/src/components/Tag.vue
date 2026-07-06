<template>
  <view :class="['tag', `tag-${variant}`]">
    <slot>{{ text }}</slot>
  </view>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  text?: string;
  variant?: 'primary' | 'soft' | 'warn' | 'danger' | 'neutral';
}>(), {
  variant: 'soft',
});
</script>

<style lang="scss" scoped>
.tag {
  display: inline-flex;
  align-items: center;
  padding: 4rpx 16rpx;
  font-size: $fs-xs;
  border-radius: $r-pill;
  line-height: 1.4;
}
.tag-primary {
  background: $primary;
  color: #fff;
}
.tag-soft {
  background: $primary-tint;
  color: $primary-deep;
}
.tag-warn {
  background: #FFEED9;
  color: #B86A1F;
}
.tag-danger {
  background: #FFE2E2;
  color: $danger;
}
.tag-neutral {
  background: $bg-2;
  color: $text-2;
}
</style>