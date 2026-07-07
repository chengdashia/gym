<template>
  <view class="history-page">
    <view class="filter">
      <liquid-glass-pill
        v-for="r in ranges"
        :key="r"
        :text="`${r} 天`"
        :variant="range === r ? 'primary' : 'default'"
        :active="range === r"
        interactive
        size="md"
        @tap="setRange(r)"
      />
    </view>

    <view v-if="sessions.length === 0" class="empty">
      <EmptyState emoji="📜" title="还没有训练记录" desc="完成一次训练就会在这里看到" />
    </view>

    <view v-else class="list">
      <liquid-glass-card
        v-for="s in sessions"
        :key="s.id"
        variant="light"
        hoverable
        radius="20rpx"
        padding="24rpx"
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
          <view class="footer-left">
            <Tag
              :text="statusText(s.status)"
              :variant="s.status === 'completed' ? 'primary' : s.status === 'cancelled' ? 'danger' : 'soft'"
            />
          </view>
          <view class="footer-right">
            <text class="more">详情 ›</text>
            <text class="del-btn" @tap.stop="confirmDelete(s)">删除</text>
          </view>
        </view>
      </liquid-glass-card>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { trainingApi, TrainingSession } from '@/api/training';
import { useAuthStore } from '@/store/auth';
import EmptyState from '@/components/EmptyState.vue';
import Tag from '@/components/Tag.vue';
import { humanizeDuration, rangeDays, today } from '@/utils/date';

const auth = useAuthStore();
const ranges = [7, 30, 90];
const range = ref(30);
const sessions = ref<TrainingSession[]>([]);

async function load() {
  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) return;
  const dates = rangeDays(today(), range.value);
  try {
    const res = await trainingApi.listSessions({ start_date: dates[0], end_date: dates[dates.length - 1] });
    sessions.value = res.items || [];
  } catch (e) {
    sessions.value = [];
    uni.showToast({ title: '加载历史失败', icon: 'none' });
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

function confirmDelete(s: TrainingSession) {
  uni.showModal({
    title: '删除训练记录',
    content: `确定删除「${s.session_name}」记录？删除后不可恢复。`,
    confirmColor: '#F26565',
    success: async (res) => {
      if (!res.confirm) return;
      try {
        await trainingApi.deleteSession(s.id);
        uni.showToast({ title: '已删除', icon: 'success' });
        await load();
      } catch (e: any) {
        uni.showToast({ title: e?.message || '删除失败', icon: 'none' });
      }
    },
  });
}

onMounted(load);
onShow(() => {
  if (auth.isLogged) load();
});
</script>

<style lang="scss" scoped>
.history-page {
  background: $bg;
  padding: $gap-3;
}
.filter {
  display: flex;
  gap: $gap-2;
  margin-bottom: $gap-3;
  flex-wrap: wrap;
}
.list {
  display: flex;
  flex-direction: column;
  gap: $gap-2;
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
.footer-left {
  display: flex;
  align-items: center;
}
.footer-right {
  display: flex;
  align-items: center;
  gap: $gap-2;
}
.more {
  font-size: $fs-sm;
  color: $text-3;
}
.del-btn {
  font-size: $fs-xs;
  color: #F26565;
  padding: 4rpx 12rpx;
  border-radius: $r-pill;
  background: rgba(242, 101, 101, 0.08);

  &:active {
    background: rgba(242, 101, 101, 0.15);
  }
}
</style>
