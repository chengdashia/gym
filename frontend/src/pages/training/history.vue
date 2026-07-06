<template>
  <view class="history-page">
    <view class="filter">
      <view
        v-for="r in ranges"
        :key="r"
        :class="['seg', { active: range === r }]"
        @tap="setRange(r)"
      >{{ r }} 天</view>
    </view>

    <view v-if="sessions.length === 0" class="empty">
      <EmptyState emoji="📜" title="还没有训练记录" desc="完成一次训练就会在这里看到" />
    </view>

    <view v-else class="list">
      <view
        v-for="s in sessions"
        :key="s.id"
        class="session-card"
        @tap="goDetail(s.id)"
      >
        <view class="row">
          <view class="info">
            <view class="name">{{ s.session_name }}</view>
            <view class="meta">{{ s.session_date }} · {{ humanizeDuration(s.duration_seconds) }}</view>
          </view>
          <view class="stat">
            <view class="num">{{ Math.round(s.total_volume) }}</view>
            <view class="unit">kg 总容量</view>
          </view>
        </view>
        <view class="footer">
          <Tag
            :text="statusText(s.status)"
            :variant="s.status === 'completed' ? 'primary' : s.status === 'cancelled' ? 'danger' : 'soft'"
          />
          <text class="more">详情 ›</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { trainingApi, TrainingSession } from '@/api/training';
import EmptyState from '@/components/EmptyState.vue';
import Tag from '@/components/Tag.vue';
import { humanizeDuration, rangeDays, today } from '@/utils/date';

const ranges = [7, 30, 90];
const range = ref(30);
const sessions = ref<TrainingSession[]>([]);

async function load() {
  const dates = rangeDays(today(), range.value);
  try {
    const res = await trainingApi.listSessions({ start_date: dates[0], end_date: dates[dates.length - 1] });
    sessions.value = res.items || [];
  } catch {
    sessions.value = [];
  }
}

function setRange(r: number) {
  range.value = r;
  load();
}

function statusText(s: string) {
  return { in_progress: '进行中', paused: '已暂停', completed: '已完成', cancelled: '已放弃' }[s] || s;
}

function goDetail(id: number) {
  uni.navigateTo({ url: `/pages/training/history-detail?id=${id}` });
}

onMounted(load);
onShow(load);
</script>

<style lang="scss" scoped>
.history-page {
  min-height: 100vh;
  background: $bg;
  padding: $gap-3;
}
.filter {
  display: flex;
  gap: $gap-2;
  margin-bottom: $gap-3;
}
.seg {
  padding: 12rpx 24rpx;
  background: $card;
  border-radius: $r-pill;
  font-size: $fs-sm;
  color: $text-2;
  &.active {
    background: $primary;
    color: #fff;
    font-weight: 500;
  }
}
.list {
  display: flex;
  flex-direction: column;
  gap: $gap-2;
}
.session-card {
  background: $card;
  border-radius: $r-20;
  padding: $gap-3;
  box-shadow: $shadow-sm;
}
.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.name {
  font-size: $fs-lg;
  font-weight: 600;
  color: $text-1;
}
.meta {
  font-size: $fs-sm;
  color: $text-3;
  margin-top: 4rpx;
}
.stat {
  text-align: right;
}
.num {
  font-size: $fs-xl;
  font-weight: 700;
  color: $primary;
}
.unit {
  font-size: $fs-xs;
  color: $text-3;
}
.footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: $gap-2;
  padding-top: $gap-2;
  border-top: 1rpx solid $divider;
}
.more {
  font-size: $fs-sm;
  color: $text-3;
}
</style>