<template>
  <view class="section-header">
    <view class="left">
      <view class="bar" />
      <text class="title">{{ title }}</text>
    </view>
    <view class="right">
      <slot name="extra" />
    </view>
  </view>
</template>

<script setup lang="ts">
defineProps<{ title: string }>();
</script>

<style lang="scss" scoped>
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $gap-2 0;
}
.left {
  display: flex;
  align-items: center;
  gap: $gap-1;
}
.bar {
  width: 6rpx;
  height: 28rpx;
  background: $primary;
  border-radius: $r-pill;
}
.title {
  font-size: $fs-lg;
  font-weight: 600;
  color: $text-1;
}
</style>