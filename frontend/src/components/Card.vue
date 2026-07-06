<template>
  <view class="card-shell" :class="{ shadow: shadow }">
    <view v-if="title || $slots.title" class="card-head">
      <view class="card-head-left">
        <view v-if="title" class="card-title">{{ title }}</view>
        <slot name="title" />
      </view>
      <view class="card-head-right">
        <slot name="extra" />
      </view>
    </view>
    <view class="card-body">
      <slot />
    </view>
  </view>
</template>

<script setup lang="ts">
defineProps<{ title?: string; shadow?: boolean }>();
</script>

<style lang="scss" scoped>
.card-shell {
  background: $card;
  border-radius: $r-20;
  padding: $gap-3;
  margin-bottom: $gap-3;
  &.shadow { box-shadow: $shadow-md; }
}
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $gap-2;
}
.card-title {
  font-size: $fs-lg;
  font-weight: 600;
  color: $text-1;
}
.card-body {
  position: relative;
}
</style>