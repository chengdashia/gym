<template>
  <view class="empty">
    <view class="emoji">{{ emoji }}</view>
    <view class="title">{{ title }}</view>
    <view v-if="desc" class="desc">{{ desc }}</view>
    <view v-if="actionText" class="action" @tap="$emit('action')">
      <text>{{ actionText }}</text>
    </view>
    <view v-if="$slots.default">
      <slot />
    </view>
  </view>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  emoji?: string;
  title: string;
  desc?: string;
  actionText?: string;
}>(), {
  emoji: '🌿',
});

defineEmits<{ (e: 'action'): void }>();
</script>

<style lang="scss" scoped>
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: $gap-5 $gap-3;
  text-align: center;
}
.emoji {
  font-size: 96rpx;
  margin-bottom: $gap-2;
}
.title {
  font-size: $fs-lg;
  color: $text-1;
  font-weight: 600;
}
.desc {
  margin-top: $gap-1;
  font-size: $fs-sm;
  color: $text-3;
  line-height: 1.5;
}
.action {
  margin-top: $gap-3;
  padding: 16rpx 40rpx;
  background: $primary;
  color: #fff;
  border-radius: $r-pill;
  font-size: $fs-md;
  font-weight: 500;
}
</style>