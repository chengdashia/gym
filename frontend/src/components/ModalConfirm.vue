<template>
  <view v-if="visible" class="modal-mask" @tap="onMask">
    <view class="modal" @tap.stop>
      <view class="modal-title">{{ title }}</view>
      <view v-if="message" class="modal-message">{{ message }}</view>
      <slot />
      <view class="modal-actions">
        <view class="btn btn-cancel" @tap="emit('cancel')">{{ cancelText }}</view>
        <view class="btn btn-confirm" :class="{ danger }" @tap="emit('confirm')">{{ confirmText }}</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  visible: boolean;
  title: string;
  message?: string;
  cancelText?: string;
  confirmText?: string;
  danger?: boolean;
  closeOnMask?: boolean;
}>(), {
  cancelText: '取消',
  confirmText: '确定',
  danger: false,
  closeOnMask: true,
});

const emit = defineEmits<{ (e: 'confirm'): void; (e: 'cancel'): void }>();

function onMask() {
  emit('cancel');
}
</script>

<style lang="scss" scoped>
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(31, 42, 42, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
  padding: $gap-3;
}
.modal {
  width: 100%;
  max-width: 600rpx;
  background: $card;
  border-radius: $r-24;
  padding: $gap-4 $gap-3 $gap-3;
  box-shadow: $shadow-lg;
}
.modal-title {
  font-size: $fs-xl;
  font-weight: 600;
  color: $text-1;
  text-align: center;
}
.modal-message {
  margin-top: $gap-2;
  font-size: $fs-md;
  color: $text-2;
  text-align: center;
  line-height: 1.6;
}
.modal-actions {
  display: flex;
  gap: $gap-2;
  margin-top: $gap-4;
}
.btn {
  flex: 1;
  text-align: center;
  padding: 20rpx;
  border-radius: $r-16;
  font-size: $fs-md;
  font-weight: 500;
}
.btn-cancel {
  background: $bg-2;
  color: $text-2;
}
.btn-confirm {
  background: $primary;
  color: #fff;
  &.danger {
    background: $danger;
  }
}
</style>