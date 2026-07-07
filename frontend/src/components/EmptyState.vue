<template>
  <view class="empty">
    <line-icon :name="icon" :tint="tint" :size="size" class="emoji" />
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
  /** 图标名（utils/icons.ts） */
  icon?: string;
  /** 玻璃色调 */
  tint?: 'mint' | 'warm' | 'sky' | 'violet' | 'rose' | 'neutral';
  /** 图标尺寸 */
  size?: number;
  title: string;
  desc?: string;
  actionText?: string;
}>(), {
  icon: 'leaf',
  tint: 'mint',
  size: 96,
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
  margin-bottom: $gap-3;
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
