<template>
  <view class="training-page">
    <!-- 今日训练 -->
    <view class="hero-card" :class="heroClass">
      <view class="hero-top">
        <view>
          <view class="hero-tag">今日训练</view>
          <view class="hero-title">{{ heroTitle }}</view>
          <view v-if="heroSubtitle" class="hero-sub">{{ heroSubtitle }}</view>
        </view>
        <view class="hero-icon">🏋️</view>
      </view>

      <view v-if="today && today.session_id" class="hero-actions">
        <view class="primary-btn" @tap="continueSession">继续训练</view>
      </view>
      <view v-else-if="today && !today.is_rest_day && today.plan_id" class="hero-actions">
        <view class="primary-btn" @tap="startSession">开始训练</view>
      </view>
      <view v-else-if="today && today.is_rest_day" class="hero-actions">
        <view class="ghost-btn">今日休息 💤</view>
      </view>
      <view v-else class="hero-actions">
        <view class="primary-btn" @tap="goCreatePlan">创建训练计划</view>
      </view>
    </view>

    <!-- 我的训练计划 -->
    <view class="section">
      <view class="section-head">
        <view class="left">
          <view class="bar" />
          <text class="title">我的训练计划</text>
        </view>
        <view class="actions">
          <view class="link" @tap="goHistory">历史</view>
          <view class="link primary" @tap="goCreatePlan">+ 新建</view>
        </view>
      </view>

      <view v-if="plans.length === 0" class="empty-card">
        <EmptyState emoji="📋" title="还没有训练计划" desc="从模板创建或自定义">
          <view class="empty-actions">
            <view class="ea-btn primary" @tap="goCreatePlan">+ 创建计划</view>
          </view>
        </EmptyState>
      </view>

      <view v-else class="plan-list">
        <view
          v-for="p in plans"
          :key="p.id"
          :class="['plan-card', { active: p.is_active }]"
          @tap="goPlanDetail(p.id)"
        >
          <view class="plan-row">
            <view class="plan-name">{{ p.name }}</view>
            <Tag
              :text="p.schedule_type === 'weekly' ? '按周' : '顺序'"
              :variant="p.schedule_type === 'weekly' ? 'soft' : 'neutral'"
            />
          </view>
          <view class="plan-meta">
            <text>{{ p.days?.length || 0 }} 个训练日</text>
            <text v-if="p.is_active" class="active-tag">· 当前计划</text>
          </view>
        </view>
      </view>
    </view>

    <view class="quick-grid">
      <view class="quick-item" @tap="goHistory">
        <view class="qi-icon" style="background: #EAF8F1; color: #3FA67C;">📜</view>
        <view class="qi-label">训练历史</view>
      </view>
      <view class="quick-item" @tap="goCreatePlan">
        <view class="qi-icon" style="background: #FFF3DC; color: #B86A1F;">📝</view>
        <view class="qi-label">创建计划</view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { useTrainingStore } from '@/store/training';
import EmptyState from '@/components/EmptyState.vue';
import Tag from '@/components/Tag.vue';
import { today } from '@/utils/date';

const trainingStore = useTrainingStore();

const plans = computed(() => trainingStore.plans);
const todayInfo = computed(() => trainingStore.today);

const heroTitle = computed(() => {
  const t = todayInfo.value;
  if (!t) return '加载中...';
  if (!t.has_plan) return '暂无训练计划';
  if (t.is_rest_day) return '今日休息';
  return t.title || '今日训练';
});

const heroSubtitle = computed(() => {
  const t = todayInfo.value;
  if (!t || !t.has_plan) return '去创建一个适合自己的训练计划';
  if (t.is_rest_day) return '好好休息，明天继续 💪';
  if (t.session_status === 'in_progress') return '训练进行中';
  return `共 ${t.exercise_count} 个动作`;
});

const heroClass = computed(() => {
  const t = todayInfo.value;
  if (!t || !t.has_plan) return 'no-plan';
  if (t.is_rest_day) return 'rest';
  if (t.session_status === 'in_progress') return 'in-progress';
  return 'normal';
});

async function load() {
  await trainingStore.fetchPlans().catch(() => {});
  await trainingStore.fetchToday(today()).catch(() => {});
}

onMounted(load);
onShow(load);

async function startSession() {
  const t = todayInfo.value;
  if (!t || !t.plan_id || !t.plan_day_id) return;
  try {
    const session = await trainingStore.startSession(t.plan_id, t.plan_day_id, today());
    uni.navigateTo({ url: `/pages/training/execute?id=${session.id}` });
  } catch {}
}

function continueSession() {
  if (todayInfo.value?.session_id) {
    uni.navigateTo({ url: `/pages/training/execute?id=${todayInfo.value.session_id}` });
  }
}

function goCreatePlan() {
  uni.navigateTo({ url: '/pages/training/plan-edit' });
}
function goPlanDetail(id: number) {
  uni.navigateTo({ url: `/pages/training/plan-edit?id=${id}` });
}
function goHistory() {
  uni.navigateTo({ url: '/pages/training/history' });
}
</script>

<style lang="scss" scoped>
.training-page {
  min-height: 100vh;
  background: $bg;
  padding: $gap-3;
  padding-bottom: calc(#{$tabbar-height} + #{$gap-4});
}

.hero-card {
  border-radius: $r-24;
  padding: $gap-3;
  margin-bottom: $gap-3;
  color: #fff;
  &.no-plan {
    background: linear-gradient(135deg, #8FA3A1 0%, #5C6B6A 100%);
  }
  &.rest {
    background: linear-gradient(135deg, #6BA8D6 0%, #4F87B0 100%);
  }
  &.in-progress {
    background: linear-gradient(135deg, #FF8A65 0%, #FF6F4D 100%);
  }
  &.normal {
    background: $gradient-primary;
  }
}
.hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.hero-tag {
  display: inline-block;
  padding: 4rpx 16rpx;
  background: rgba(255, 255, 255, 0.25);
  border-radius: $r-pill;
  font-size: $fs-xs;
}
.hero-title {
  margin-top: $gap-1;
  font-size: 44rpx;
  font-weight: 700;
}
.hero-sub {
  margin-top: 4rpx;
  font-size: $fs-sm;
  opacity: 0.9;
}
.hero-icon {
  font-size: 80rpx;
  opacity: 0.4;
}
.hero-actions {
  margin-top: $gap-3;
}
.primary-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 18rpx 40rpx;
  background: rgba(255, 255, 255, 0.95);
  color: $primary-deep;
  border-radius: $r-pill;
  font-size: $fs-md;
  font-weight: 600;
}
.ghost-btn {
  display: inline-flex;
  padding: 18rpx 32rpx;
  background: rgba(255,255,255,0.2);
  color: #fff;
  border-radius: $r-pill;
  font-size: $fs-md;
}

.section {
  background: $card;
  border-radius: $r-20;
  padding: $gap-3;
  margin-bottom: $gap-3;
  box-shadow: $shadow-sm;
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $gap-2;
}
.section-head .left {
  display: flex;
  align-items: center;
  gap: $gap-1;
}
.section-head .bar {
  width: 6rpx;
  height: 28rpx;
  background: $primary;
  border-radius: $r-pill;
}
.section-head .title {
  font-size: $fs-lg;
  font-weight: 600;
  color: $text-1;
}
.section-head .actions {
  display: flex;
  gap: $gap-2;
  align-items: center;
}
.link {
  font-size: $fs-sm;
  color: $text-3;
  &.primary {
    color: $primary;
    font-weight: 500;
  }
}

.empty-card {
  padding: $gap-3 0;
}
.empty-actions {
  display: flex;
  gap: $gap-2;
  margin-top: $gap-3;
}
.ea-btn {
  padding: 14rpx 32rpx;
  border-radius: $r-pill;
  background: $bg-2;
  color: $text-2;
  font-size: $fs-sm;
  &.primary {
    background: $primary;
    color: #fff;
  }
}

.plan-list {
  display: flex;
  flex-direction: column;
  gap: $gap-2;
}
.plan-card {
  padding: $gap-3;
  background: $bg;
  border-radius: $r-16;
  border: 2rpx solid transparent;
  &.active {
    background: $primary-tint;
    border-color: $primary;
  }
}
.plan-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4rpx;
}
.plan-name {
  font-size: $fs-lg;
  font-weight: 600;
  color: $text-1;
}
.plan-meta {
  font-size: $fs-sm;
  color: $text-3;
}
.active-tag {
  color: $primary;
  font-weight: 500;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $gap-2;
}
.quick-item {
  display: flex;
  align-items: center;
  gap: $gap-2;
  padding: $gap-3;
  background: $card;
  border-radius: $r-16;
  box-shadow: $shadow-sm;
}
.qi-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: $r-16;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
}
.qi-label {
  font-size: $fs-md;
  color: $text-1;
  font-weight: 500;
}
</style>