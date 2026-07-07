<template>
  <view class="training-page">
    <view class="hero-section">
      <liquid-glass-panel :variant="heroVariant" :highlight="true" :ambient="true" class="hero-panel">
        <view class="hero-top">
          <view>
            <liquid-glass-pill
              :text="heroStatusText"
              :variant="heroStatusVariant"
              size="xs"
            />
            <view class="hero-title">{{ heroTitle }}</view>
            <view v-if="heroSubtitle" class="hero-sub">{{ heroSubtitle }}</view>
          </view>
          <view class="hero-icon">{{ heroIcon }}</view>
        </view>

        <view v-if="todayInfo && todayInfo.exercise_count > 0 && !todayInfo.is_rest_day" class="hero-stats">
          <view class="stat-item">
            <text class="stat-num">{{ todayInfo.exercise_count }}</text>
            <text class="stat-label">动作</text>
          </view>
        </view>

        <view class="hero-actions">
          <liquid-glass-button
            v-if="todayInfo && todayInfo.session_id"
            text="继续训练"
            variant="primary"
            size="md"
            :block="false"
            @tap="continueSession"
          />
          <liquid-glass-button
            v-else-if="todayInfo && !todayInfo.is_rest_day && todayInfo.plan_id"
            text="开始今日训练"
            variant="primary"
            size="md"
            :block="false"
            @tap="startSession"
          />
          <liquid-glass-button
            v-else-if="todayInfo && todayInfo.is_rest_day"
            text="好好休息 💤"
            variant="soft"
            size="md"
            :block="false"
            :disabled="true"
          />
          <liquid-glass-button
            v-else
            text="创建训练计划"
            variant="primary"
            size="md"
            :block="false"
            @tap="goCreatePlan"
          />
        </view>
      </liquid-glass-panel>
    </view>

    <view class="container">
      <view class="section-header">
        <view class="sh-left">
          <view class="sh-bar" />
          <text class="sh-title">我的训练计划</text>
        </view>
      </view>

      <view v-if="loading" class="loading-card">
        <text class="loading-text">加载中...</text>
      </view>

      <view v-else-if="plans.length === 0" class="empty-state">
        <liquid-glass-card :highlight="true" class="empty-card">
          <view class="empty-emoji">📋</view>
          <view class="empty-title">还没有训练计划</view>
          <view class="empty-desc">从推荐模板开始，快速创建适合你的训练计划</view>
          <view class="empty-actions">
            <liquid-glass-button text="+ 新建计划" variant="primary" size="md" :block="false" @tap="goCreatePlan" />
          </view>
        </liquid-glass-card>
      </view>

      <view v-else class="plan-list">
        <view
          v-for="p in plans"
          :key="p.id"
          :class="['plan-card-wrap', { active: p.is_active }]"
          @tap="onPlanTap(p)"
        >
          <liquid-glass-card
            :variant="p.is_active ? 'tint' : 'light'"
            :highlight="p.is_active"
            hoverable
            radius="24rpx"
            class="plan-card"
          >
            <view class="plan-card-top">
              <view class="plan-info">
                <view class="plan-name-row">
                  <text class="plan-name">{{ p.name }}</text>
                  <liquid-glass-pill
                    v-if="p.is_active"
                    text="当前"
                    variant="primary"
                    size="xs"
                  />
                </view>
                <view class="plan-meta">
                  <text>{{ p.days?.length || 0 }} 个训练日</text>
                  <text class="dot">·</text>
                  <text>{{ scheduleTypeLabel(p.schedule_type) }}</text>
                </view>
              </view>
              <view class="plan-action" @tap.stop="goEditPlan(p.id)">
                <text class="plan-action-text">编辑</text>
              </view>
            </view>

            <view v-if="p.days && p.days.length > 0" class="plan-days-preview">
              <view
                v-for="(d, di) in p.days.slice(0, 5)"
                :key="di"
                :class="['day-chip', { rest: d.is_rest_day }]"
              >
                {{ d.is_rest_day ? '休' : d.day_name?.slice(0, 2) || `D${d.day_index}` }}
              </view>
              <view v-if="p.days.length > 5" class="day-chip more">+{{ p.days.length - 5 }}</view>
            </view>

            <view v-if="!p.is_active" class="plan-activate-hint">
              <text>点击激活此计划并开始训练</text>
            </view>
          </liquid-glass-card>
        </view>

        <liquid-glass-card
          variant="frosted"
          hoverable
          radius="24rpx"
          class="add-plan-card"
          @tap="goCreatePlan"
        >
          <view class="add-plan-content">
            <text class="add-icon">+</text>
            <text class="add-text">创建新计划</text>
          </view>
        </liquid-glass-card>
      </view>

    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { useTrainingStore } from '@/store/training';
import { useAuthStore } from '@/store/auth';
import { trainingApi, TrainingPlan } from '@/api/training';
import { today } from '@/utils/date';

function syncTabBar() {
  const pages = getCurrentPages();
  const page = pages[pages.length - 1];
  const tabBar = (page as any)?.getTabBar?.();
  if (tabBar) tabBar.setData({ activeIdx: 2 });
}

const trainingStore = useTrainingStore();

const loading = ref(false);

const plans = computed(() => trainingStore.plans);
const todayInfo = computed(() => trainingStore.today);

const heroTitle = computed(() => {
  const t = todayInfo.value;
  if (loading.value) return '加载中...';
  if (!t || !t.has_plan) return '开始你的训练';
  if (t.is_rest_day) return '今日是休息日';
  return t.title || '今日训练';
});

const heroSubtitle = computed(() => {
  const t = todayInfo.value;
  if (!t || !t.has_plan) return '创建计划，开启每一次进步';
  if (t.is_rest_day) return '好好休息，肌肉在休息中生长 💪';
  if (t.session_status === 'in_progress') return '训练进行中，加油！';
  if (t.exercise_count > 0) return `准备好挑战 ${t.exercise_count} 个动作了吗？`;
  return '今天是训练日';
});

const heroIcon = computed(() => {
  const t = todayInfo.value;
  if (!t || !t.has_plan) return '🏋️';
  if (t.is_rest_day) return '😴';
  if (t.session_status === 'in_progress') return '🔥';
  return '💪';
});

const heroVariant = computed<'mint' | 'warm' | 'light' | 'dark'>(() => {
  const t = todayInfo.value;
  if (!t || !t.has_plan) return 'light';
  if (t.is_rest_day) return 'light';
  if (t.session_status === 'in_progress') return 'warm';
  return 'mint';
});

const heroStatusText = computed(() => {
  const t = todayInfo.value;
  if (loading.value) return '加载中';
  if (!t || !t.has_plan) return '未设置计划';
  if (t.is_rest_day) return '休息日';
  if (t.session_status === 'in_progress') return '进行中';
  return '今日训练';
});

const heroStatusVariant = computed<'soft' | 'primary' | 'default'>(() => {
  const t = todayInfo.value;
  if (!t || !t.has_plan) return 'default';
  if (t.session_status === 'in_progress') return 'primary';
  return 'soft';
});

function scheduleTypeLabel(type: string | null): string {
  if (type === 'weekly') return '按周排期';
  if (type === 'sequence') return '顺序循环';
  return '';
}

async function load() {
  const auth = useAuthStore();
  if (!auth.ready) await auth.bootstrap();
  if (!auth.isLogged) return;
  loading.value = true;
  try {
    await Promise.all([
      trainingStore.fetchPlans().catch(() => {}),
      trainingStore.fetchToday(today()).catch(() => {}),
    ]);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
onShow(() => {
  syncTabBar();
  const auth = useAuthStore();
  if (auth.isLogged) load();
});

async function startSession() {
  const t = todayInfo.value;
  if (!t || !t.plan_id || !t.plan_day_id) {
    uni.showToast({ title: '暂无训练安排', icon: 'none' });
    return;
  }
  try {
    const session = await trainingStore.startSession(t.plan_id, t.plan_day_id, today());
    uni.navigateTo({ url: `/pages/training/execute?id=${session.id}` });
  } catch (e: any) {
    uni.showToast({ title: e?.message || '开始训练失败', icon: 'none' });
  }
}

function continueSession() {
  if (todayInfo.value?.session_id) {
    uni.navigateTo({ url: `/pages/training/execute?id=${todayInfo.value.session_id}` });
  }
}

async function onPlanTap(p: TrainingPlan) {
  if (p.is_active) {
    const t = todayInfo.value;
    if (t && !t.is_rest_day && t.plan_id && t.plan_day_id) {
      if (t.session_id) {
        continueSession();
      } else {
        await startSession();
      }
    } else if (t && t.is_rest_day) {
      uni.showToast({ title: '今天是休息日', icon: 'none' });
    } else {
      await refreshAndStart(p.id);
    }
  } else {
    uni.showModal({
      title: '激活计划',
      content: `确定将「${p.name}」设为当前训练计划吗？`,
      success: async (res) => {
        if (res.confirm) {
          await activatePlan(p.id);
        }
      },
    });
  }
}

async function refreshAndStart(planId: number) {
  try {
    await trainingStore.fetchToday(today());
    const t = trainingStore.today;
    if (t && !t.is_rest_day && t.plan_id && t.plan_day_id) {
      if (t.session_id) {
        uni.navigateTo({ url: `/pages/training/execute?id=${t.session_id}` });
      } else {
        const session = await trainingStore.startSession(t.plan_id, t.plan_day_id, today());
        uni.navigateTo({ url: `/pages/training/execute?id=${session.id}` });
      }
    } else {
      uni.showToast({ title: '今天是休息日', icon: 'none' });
    }
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' });
  }
}

async function activatePlan(planId: number) {
  uni.showLoading({ title: '激活中...' });
  try {
    await trainingApi.setActive(planId);
    await trainingStore.fetchPlans().catch(() => {});
    await trainingStore.fetchToday(today()).catch(() => {});
    uni.hideLoading();
    uni.showToast({ title: '已激活', icon: 'success' });
  } catch (e: any) {
    uni.hideLoading();
    uni.showToast({ title: e?.message || '激活失败', icon: 'none' });
  }
}

function goCreatePlan() {
  uni.navigateTo({ url: '/pages/training/plan-edit' });
}
function goEditPlan(id: number) {
  uni.navigateTo({ url: `/pages/training/plan-edit?id=${id}` });
}
</script>

<style lang="scss" scoped>
.training-page {
  padding-bottom: calc(#{$tabbar-height} + #{$gap-4} + #{$gap-2});
  animation: lg-fade-up 0.4s $ease-spring both;
}

.hero-section {
  position: relative;
  padding: $gap-3 $gap-3 $gap-2;
  background: linear-gradient(160deg, rgba(91, 200, 154, 0.25) 0%, rgba(107, 168, 214, 0.12) 100%);
  border-radius: 0 0 40rpx 40rpx;
  margin-bottom: $gap-3;
  overflow: hidden;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: -80rpx;
  right: -40rpx;
  width: 280rpx;
  height: 280rpx;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255,255,255,0.35) 0%, transparent 70%);
  pointer-events: none;
}

.hero-panel {
  padding: $gap-4 $gap-3;
  position: relative;
  z-index: 1;
}

.hero-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  position: relative;
  z-index: 1;
}

.hero-title {
  margin-top: $gap-2;
  font-size: 52rpx;
  font-weight: 800;
  color: $text-1;
  letter-spacing: 0.5rpx;
  line-height: 1.2;
}

.hero-sub {
  margin-top: 8rpx;
  font-size: $fs-sm;
  color: $text-2;
  opacity: 0.9;
}

.hero-icon {
  font-size: 88rpx;
  opacity: 0.5;
  filter: drop-shadow(0 4rpx 12rpx rgba(95, 175, 145, 0.2));
}

.hero-stats {
  display: flex;
  gap: $gap-4;
  margin-top: $gap-3;
  padding: $gap-2 $gap-3;
  background: rgba(255, 255, 255, 0.4);
  border-radius: $r-16;
  position: relative;
  z-index: 1;
}

.stat-item {
  display: flex;
  align-items: baseline;
  gap: 6rpx;
}

.stat-num {
  font-size: 44rpx;
  font-weight: 800;
  color: $primary-deep;
}

.stat-label {
  font-size: $fs-sm;
  color: $text-2;
}

.hero-actions {
  margin-top: $gap-3;
  position: relative;
  z-index: 1;
}

.container {
  padding: 0 $gap-3;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $gap-2;
  padding: 0 $gap-1;
}

.sh-left {
  display: flex;
  align-items: center;
  gap: $gap-1;
}

.sh-bar {
  width: 6rpx;
  height: 28rpx;
  background: $gradient-primary;
  border-radius: $r-pill;
  box-shadow: 0 2rpx 6rpx rgba(95, 175, 145, 0.3);
}

.sh-title {
  font-size: $fs-lg;
  font-weight: 700;
  color: $text-1;
  letter-spacing: 0.3rpx;
}

.loading-card {
  padding: $gap-5;
  text-align: center;
}

.loading-text {
  color: $text-3;
  font-size: $fs-sm;
}

.empty-state {
  margin-bottom: $gap-2;
}

.empty-card {
  padding: $gap-5 $gap-3;
  text-align: center;
}

.empty-emoji {
  font-size: 88rpx;
  margin-bottom: $gap-2;
  filter: drop-shadow(0 4rpx 12rpx rgba(95, 175, 145, 0.15));
}

.empty-title {
  font-size: $fs-xl;
  font-weight: 700;
  color: $text-1;
}

.empty-desc {
  margin-top: $gap-1;
  font-size: $fs-sm;
  color: $text-3;
  margin-bottom: $gap-3;
}

.empty-actions {
  display: flex;
  justify-content: center;
}

.plan-list {
  display: flex;
  flex-direction: column;
  gap: $gap-2;
}

.plan-card-wrap {
  position: relative;
  transition: transform 0.2s $ease-spring;
  &:active {
    transform: scale(0.98);
  }
}

.plan-card {
  padding: $gap-3;
  margin-bottom: 0;
}

.plan-card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.plan-info {
  flex: 1;
  min-width: 0;
}

.plan-name-row {
  display: flex;
  align-items: center;
  gap: $gap-1;
}

.plan-name {
  font-size: $fs-lg;
  font-weight: 700;
  color: $text-1;
  letter-spacing: 0.3rpx;
}

.plan-meta {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-top: 6rpx;
  font-size: $fs-sm;
  color: $text-3;
}

.dot {
  opacity: 0.5;
}

.plan-action {
  padding: 8rpx 16rpx;
  background: rgba(91, 200, 154, 0.1);
  border-radius: $r-pill;
  flex-shrink: 0;
}

.plan-action-text {
  font-size: $fs-xs;
  color: $primary;
  font-weight: 600;
}

.plan-days-preview {
  display: flex;
  gap: 8rpx;
  margin-top: $gap-2;
  flex-wrap: wrap;
}

.day-chip {
  padding: 6rpx 14rpx;
  background: rgba(234, 248, 241, 0.7);
  color: $primary-deep;
  font-size: $fs-xs;
  font-weight: 600;
  border-radius: $r-pill;
  &.rest {
    background: rgba(0,0,0,0.04);
    color: $text-3;
  }
  &.more {
    background: rgba(0,0,0,0.04);
    color: $text-3;
  }
}

.plan-activate-hint {
  margin-top: $gap-2;
  font-size: $fs-xs;
  color: $text-3;
  text-align: center;
  padding: 8rpx 0;
}

.add-plan-card {
  padding: $gap-3;
  margin-bottom: 0;
  border: 2rpx dashed rgba(91, 200, 154, 0.3);
  background: rgba(255,255,255,0.3);
}

.add-plan-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $gap-1;
  padding: $gap-2 0;
}

.add-icon {
  font-size: 40rpx;
  font-weight: 300;
  color: $primary;
}

.add-text {
  font-size: $fs-md;
  color: $primary;
  font-weight: 600;
}

</style>
