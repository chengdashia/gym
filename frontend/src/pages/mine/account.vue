<template>
  <view class="account-page">
    <view class="section">
      <view class="section-title">体重记录</view>
      <view :class="['weight-section', { highlight: highlightWeight }]">
        <liquid-glass-card variant="light" :highlight="true" custom-style="margin-bottom:0">
          <template v-if="loading">
            <view class="row">
              <text class="label">最新体重</text>
              <text class="value">加载中...</text>
            </view>
          </template>
          <template v-else>
            <view class="row">
              <text class="label">最新体重</text>
              <text class="value">{{ latestWeight ? latestWeight.weight_kg + ' kg' : '暂无' }}</text>
            </view>
            <view class="row">
              <text class="label">记录时间</text>
              <text class="value">{{ latestWeight ? latestWeight.record_date : '-' }}</text>
            </view>
          </template>
          <view class="form-row">
            <text class="label">新体重 (kg)</text>
            <input v-model.number="newWeight" type="digit" placeholder="例 65.5" class="input" />
          </view>
          <view class="weight-actions">
            <liquid-glass-button text="保存体重" variant="primary" @tap="saveWeight" />
          </view>
        </liquid-glass-card>
      </view>
    </view>

    <view class="section">
      <view class="section-title">账号与数据</view>
      <liquid-glass-card variant="light" :highlight="true" padding="0" custom-style="margin-bottom:0">
        <view class="menu-item disabled">
          <view class="mi-emoji">📱</view>
          <text class="mi-label">手机号授权</text>
          <text class="mi-value">功能开发中</text>
        </view>
        <view class="menu-item disabled">
          <view class="mi-emoji">📤</view>
          <text class="mi-label">数据导出</text>
          <text class="mi-value">功能开发中</text>
        </view>
        <view class="menu-item" @tap="clearCache">
          <view class="mi-emoji">🧹</view>
          <text class="mi-label">清除缓存</text>
          <text class="mi-value">{{ cacheSize }}</text>
        </view>
      </liquid-glass-card>
    </view>

    <view class="section danger-section">
      <view class="section-title">危险操作</view>
      <liquid-glass-card variant="light" :highlight="true" padding="0" custom-style="margin-bottom:0">
        <view class="menu-item" @tap="confirmDeleteData">
          <view class="mi-emoji">🗑️</view>
          <text class="mi-label danger">删除个人数据</text>
          <text class="mi-arrow">›</text>
        </view>
        <view class="menu-item" @tap="confirmCancel">
          <view class="mi-emoji">❌</view>
          <text class="mi-label danger">注销账号</text>
          <text class="mi-arrow">›</text>
        </view>
      </liquid-glass-card>
    </view>

    <ModalConfirm
      :visible="showDeleteData"
      title="删除个人数据"
      message="将删除你的饮食、训练、体重、自定义食物等所有个人数据，此操作不可恢复。系统数据不受影响。"
      confirm-text="确认删除"
      danger
      @confirm="deleteData"
      @cancel="showDeleteData = false"
    />

    <ModalConfirm
      :visible="showCancel"
      title="注销账号"
      message="注销后账号将不可恢复，请提前导出重要数据。"
      confirm-text="确认注销"
      danger
      @confirm="cancelAccount"
      @cancel="showCancel = false"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { onShow, onLoad } from '@dcloudio/uni-app';
import LiquidGlassCard from '@/components/LiquidGlassCard.vue';
import LiquidGlassButton from '@/components/LiquidGlassButton.vue';
import ModalConfirm from '@/components/ModalConfirm.vue';
import { useUserStore } from '@/store/user';
import { useAuthStore } from '@/store/auth';
import { weightApi, WeightRecord } from '@/api/weight';
import { clearAllCache } from '@/utils/cache';
import { today } from '@/utils/date';

const userStore = useUserStore();
const auth = useAuthStore();
const newWeight = ref<number>(0);
const latestWeight = ref<WeightRecord | null>(null);
const showDeleteData = ref(false);
const showCancel = ref(false);
const cacheSize = ref('0 KB');
const loading = ref(false);
const highlightWeight = ref(false);

onLoad((options: any) => {
  if (options?.action === 'weight') {
    setTimeout(() => {
      uni.pageScrollTo({ selector: '.weight-section', duration: 300 });
      highlightWeight.value = true;
      setTimeout(() => {
        highlightWeight.value = false;
      }, 600);
    }, 400);
  }
});

onMounted(async () => {
  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) return;
  if (!userStore.me) await userStore.fetchMe().catch(() => {
    uni.showToast({ title: '加载失败', icon: 'none' });
  });
  await loadWeight();
  computeCache();
});

onShow(async () => {
  if (!auth.isLogged) return;
  if (!userStore.me) await userStore.fetchMe().catch(() => {
    uni.showToast({ title: '加载失败', icon: 'none' });
  });
  await loadWeight();
});

async function loadWeight() {
  loading.value = true;
  try {
    const res = await weightApi.list(30);
    const items = (res.items || []).slice().reverse();
    latestWeight.value = items[0] || null;
  } catch (e) {
    uni.showToast({ title: '加载体重记录失败', icon: 'none' });
  } finally {
    loading.value = false;
  }
}

function computeCache() {
  try {
    const info = uni.getStorageInfoSync();
    const kb = info.currentSize || 0;
    cacheSize.value = kb >= 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${kb} KB`;
  } catch {
    cacheSize.value = '-';
  }
}

async function saveWeight() {
  if (!newWeight.value || newWeight.value <= 0) {
    uni.showToast({ title: '请输入有效体重', icon: 'none' });
    return;
  }
  uni.showLoading({ title: '保存中...' });
  try {
    const now = new Date();
    await weightApi.create({
      record_date: today(),
      record_time: `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`,
      weight_kg: newWeight.value,
    });
    newWeight.value = 0;
    await loadWeight();
    uni.hideLoading();
    uni.showToast({ title: '已记录', icon: 'success' });
  } catch (e: any) {
    uni.hideLoading();
    uni.showToast({ title: e?.message || '保存失败', icon: 'none' });
  }
}

function clearCache() {
  uni.showModal({
    title: '清除缓存',
    content: '将清除所有本地缓存（token 除外），确定吗？',
    success: async (r) => {
      if (r.confirm) {
        clearAllCache();
        uni.showToast({ title: '已清除', icon: 'success' });
        computeCache();
      }
    },
  });
}

function confirmDeleteData() {
  showDeleteData.value = true;
}

async function deleteData() {
  showDeleteData.value = false;
  uni.showLoading({ title: '处理中...' });
  try {
    await userStore.deleteData();
    uni.hideLoading();
    uni.showToast({ title: '已删除', icon: 'success' });
  } catch (e: any) {
    uni.hideLoading();
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  }
}

function confirmCancel() {
  showCancel.value = true;
}

async function cancelAccount() {
  showCancel.value = false;
  uni.showLoading({ title: '处理中...' });
  try {
    await userStore.cancelAccount();
    uni.hideLoading();
    uni.showToast({ title: '已注销', icon: 'success' });
    setTimeout(() => uni.reLaunch({ url: '/pages/login/onboarding' }), 800);
  } catch (e: any) {
    uni.hideLoading();
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  }
}
</script>

<style lang="scss" scoped>
.account-page {
  background: $bg;
  padding: $gap-3;
}
.section {
  margin-bottom: $gap-3;
}
.section-title {
  font-size: $fs-lg;
  font-weight: 600;
  color: $text-1;
  margin-bottom: $gap-2;
  padding-left: $gap-1;
}

.weight-section {
  border-radius: $r-24;
  &.highlight {
    animation: weight-highlight 600ms ease-out;
  }
}

@keyframes weight-highlight {
  0% { background-color: rgba(91, 200, 154, 0); }
  50% { background-color: rgba(91, 200, 154, 0.3); }
  100% { background-color: rgba(91, 200, 154, 0); }
}

.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $gap-1 0;
  border-bottom: 1rpx solid $divider;
  &:last-of-type { border-bottom: none; }
}
.label {
  color: $text-2;
  font-size: $fs-sm;
}
.value {
  color: $text-1;
  font-size: $fs-md;
}
.form-row {
  display: flex;
  align-items: center;
  padding: $gap-2 0;
  border-top: 1rpx solid $divider;
  margin-top: $gap-2;
  gap: $gap-2;
}
.input {
  flex: 1;
  font-size: $fs-md;
  color: $text-1;
  text-align: right;
}
.weight-actions {
  margin-top: $gap-2;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: $gap-3;
  border-bottom: 1rpx solid $divider;
  transition: background 0.3s $ease-glass;
  &:active {
    background: rgba(255, 255, 255, 0.5);
  }
  &:last-child { border-bottom: none; }
  &.disabled {
    opacity: 0.5;
    pointer-events: none;
  }
}
.mi-emoji {
  width: 64rpx;
  height: 64rpx;
  border-radius: $r-16;
  background: $bg-2;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  margin-right: $gap-2;
}
.mi-label {
  flex: 1;
  font-size: $fs-md;
  color: $text-1;
  &.danger { color: $danger; font-weight: 600; }
}
.mi-value {
  color: $text-3;
  font-size: $fs-sm;
}
.mi-arrow {
  color: $text-3;
  font-size: $fs-lg;
}

.danger-section {
  margin-top: $gap-4;
}
</style>
