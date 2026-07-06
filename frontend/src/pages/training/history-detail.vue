<template>
  <view v-if="session" class="detail-page">
    <view class="header-card">
      <view class="title">{{ session.session_name }}</view>
      <view class="meta">{{ session.session_date }} · {{ humanizeDuration(session.duration_seconds) }}</view>
      <view class="stats">
        <view class="stat-cell">
          <view class="stat-num">{{ Math.round(session.total_volume) }}</view>
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
    </view>

    <view class="exercises">
      <view v-for="(ex, ei) in session.exercises || []" :key="ei" class="ex-card">
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
            <text class="set-actual">{{ s.actual_reps || '-' }} × {{ s.actual_weight_kg || '-' }} kg</text>
            <text :class="['set-status', { done: s.completed }]">{{ s.completed ? '✓' : '—' }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { trainingApi, TrainingSession } from '@/api/training';
import { humanizeDuration } from '@/utils/date';

const id = ref(0);
const session = ref<TrainingSession | null>(null);

const completedSets = computed(() => {
  if (!session.value?.exercises) return 0;
  return session.value.exercises.reduce((s, e) => s + e.sets.filter((x) => x.completed).length, 0);
});

onMounted(async () => {
  const pages = getCurrentPages();
  const opt = (pages[pages.length - 1] as any)?.options || {};
  id.value = Number(opt.id || 0);
  if (id.value) {
    try {
      session.value = await trainingApi.getSession(id.value);
    } catch {}
  }
});
</script>

<style lang="scss" scoped>
.detail-page {
  min-height: 100vh;
  background: $bg;
  padding: $gap-3;
}
.header-card {
  background: $gradient-card;
  border-radius: $r-24;
  padding: $gap-3;
  margin-bottom: $gap-3;
  box-shadow: $shadow-md;
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

.ex-card {
  background: $card;
  border-radius: $r-20;
  padding: $gap-3;
  margin-bottom: $gap-2;
  box-shadow: $shadow-sm;
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
</style>