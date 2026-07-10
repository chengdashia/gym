<template>
  <view v-if="session" class="detail-page">
    <liquid-glass-card variant="tint" radius="24rpx" padding="24rpx">
      <view class="title">{{ session.session_name }}</view>
      <view class="meta">{{ session.session_date }} · {{ humanizeDuration(session.duration_seconds) }}</view>
      <view class="stats">
        <view class="stat-cell">
          <view class="stat-num">{{ Math.round(displayVolume) }}</view>
          <view class="stat-unit">kg 总容量</view>
        </view>
        <view class="stat-cell">
          <view class="stat-num">{{ completedSets }}</view>
          <view class="stat-unit">完成组数</view>
        </view>
        <view class="stat-cell">
          <view class="stat-num">{{ (session.exercises || []).length }}</view>
          <view class="stat-unit">动作数</view>
        </view>
      </view>
    </liquid-glass-card>

    <view class="exercises">
      <liquid-glass-card
        v-for="(ex, ei) in session.exercises || []"
        :key="ei"
        variant="light"
        radius="20rpx"
        padding="24rpx"
      >
        <view class="ex-name">{{ ex.exercise_name_snapshot }}</view>
        <view class="ex-meta">{{ ex.body_part_snapshot || '' }}</view>
        <view class="set-list">
          <view class="set-row">
            <text class="set-h">#</text>
            <text class="set-h">实际</text>
            <text class="set-h">完成</text>
          </view>
          <view
            v-for="(s, si) in ex.sets"
            :key="si"
            :class="['set-data', { done: s.completed }]"
          >
            <text class="set-idx">{{ si + 1 }}</text>
            <text class="set-actual">{{ formatSet(s) }}</text>
            <text :class="['set-status', { done: s.completed }]">{{ s.completed ? '✓' : '—' }}</text>
          </view>
        </view>
      </liquid-glass-card>
    </view>
  </view>
  <view v-else-if="loading" class="loading">加载中...</view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useAuthStore } from '@/store/auth';
import { trainingApi, TrainingSession } from '@/api/training';
import { humanizeDuration } from '@/utils/date';
import { requireAuth } from '@/utils/auth-guard';
import { effectiveSetValues, sessionVolume } from '@/utils/training-progress';
import type { SessionSet } from '@/api/training';

const id = ref(0);
const session = ref<TrainingSession | null>(null);
const loading = ref(false);
const auth = useAuthStore();

const completedSets = computed(() => {
  if (!session.value?.exercises) return 0;
  return session.value.exercises.reduce((s, e) => s + e.sets.filter((x) => x.completed).length, 0);
});
const displayVolume = computed(() => sessionVolume(session.value?.exercises || []));
function formatSet(set: SessionSet) {
  if (!set.completed) return '未完成';
  const value = effectiveSetValues(set);
  return value.weight > 0 ? `${value.reps} × ${value.weight} kg` : `${value.reps} 次 · 自重`;
}

onMounted(async () => {
  const pages = getCurrentPages();
  const opt = (pages[pages.length - 1] as any)?.options || {};
  id.value = Number(opt.id || 0);

  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) {
    const redirect = id.value
      ? `/pages/training/history-detail?id=${id.value}`
      : '/pages/training/history-detail';
    requireAuth({ redirect });
    return;
  }

  if (!id.value) return;
  loading.value = true;
  try {
    session.value = await trainingApi.getSession(id.value);
  } catch (e) {
    uni.showToast({ title: '加载详情失败', icon: 'none' });
  } finally {
    loading.value = false;
  }
});
</script>

<style lang="scss" scoped>
.detail-page {
  background: $bg;
  padding: $gap-3;
}
.title {
  font-size: 36rpx;
  font-weight: 700;
  color: $text-1;
}
.meta {
  font-size: $fs-sm;
  color: $text-3;
  margin-top: 4rpx;
}
.stats {
  display: flex;
  justify-content: space-around;
  margin-top: $gap-3;
  padding-top: $gap-3;
  border-top: 1rpx solid $divider;
}
.stat-cell {
  text-align: center;
}
.stat-num {
  font-size: 40rpx;
  font-weight: 700;
  color: $primary-deep;
}
.stat-unit {
  font-size: $fs-xs;
  color: $text-3;
  margin-top: 4rpx;
}

.ex-name {
  font-size: $fs-lg;
  font-weight: 600;
  color: $text-1;
}
.ex-meta {
  font-size: $fs-xs;
  color: $text-3;
  margin-top: 4rpx;
}
.set-list {
  margin-top: $gap-2;
}
.set-row, .set-data {
  display: grid;
  grid-template-columns: 60rpx 1fr 80rpx;
  padding: $gap-1 0;
  align-items: center;
}
.set-row {
  border-bottom: 1rpx solid $divider;
  margin-bottom: 4rpx;
}
.set-h {
  font-size: $fs-xs;
  color: $text-3;
  text-align: center;
}
.set-data {
  &.done { background: $primary-tint; border-radius: $r-8; padding: 8rpx; }
}
.set-idx {
  text-align: center;
  font-weight: 600;
  color: $text-1;
}
.set-actual {
  text-align: center;
  font-size: $fs-sm;
  color: $text-1;
}
.set-status {
  text-align: center;
  font-size: $fs-md;
  color: $text-3;
  &.done { color: $primary; font-weight: 700; }
}

.loading {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $bg;
  color: $text-3;
  font-size: $fs-md;
}
</style>
