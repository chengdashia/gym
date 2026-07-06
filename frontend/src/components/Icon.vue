<template>
  <view class="iconfont-host">
    <text :class="['iconfont', `icon-${name}`]" :style="{ fontSize: `${size}rpx`, color }" />
  </view>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  name: string;
  size?: number;
  color?: string;
}>(), {
  size: 32,
  color: 'inherit',
});
</script>

<style lang="scss" scoped>
.iconfont-host {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-style: normal;
}
</style>