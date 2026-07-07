<template>
  <view class="training-page">
    <!-- 今日训练 Hero Panel -->
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
        <view class="hero-icon">🏋️</view>
      </view>

      <view class="hero-actions">
        <liquid-glass-button
          v-if="today && today.session_id"
          text="继续训练"
          variant="primary"
          size="md"
          :block="false"
          @tap="continueSession"
        />
        <liquid-glass-button
          v-else-if="today && !today.is_rest_day && today.plan_id"
          text="开始训练"
          variant="primary"
          size="md"
          :block="false"
          @tap="startSession"
        />
        <liquid-glass-button
          v-else-if="today && today.is_rest_day"
          text="今日休息 💤"
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

    <!-- 我的训练计划 -->
    <liquid-glass-card :highlight="true" class="section-card">
      <view class="section-head">
        <view class="left">
          <view class="bar" />
          <text class="title">我的训练计划</text>
        </view>
        <view class="actions">
          <text class="link" @tap="goHistory">历史</text>
          <text class="link primary" @tap="goCreatePlan">+ 新建</text>
        </view>
      </view>

      <view v-if="plans.length === 0" class="empty-card">
        <view class="emoji">📋</view>
        <view class="empty-title">还没有训练计划</view>
        <view class="empty-desc">从模板创建或自定义</view>
        <liquid-glass-button text="+ 创建计划" variant="primary" size="sm" :block="false" @tap="goCreatePlan" />
      </view>

      <view v-else class="plan-list">
        <liquid-glass-card
          v-for="p in plans"
          :key="p.id"
          :variant="p.is_active ? 'tint' : 'light'"
          :highlight="true"
          hoverable
          radius="20rpx"
          class="plan-card"
          @tap="goPlanDetail(p.id)"
        >
          <view class="plan-row">
            <view class="plan-name">{{ p.name }}</view>
            <liquid-glass-pill
              :text="p.schedule_type === 'weekly' ? '按周' : '顺序'"
              :variant="p.schedule_type === 'weekly' ? 'soft' : 'default'"
              size="xs"
            />
          </view>
          <view class="plan-meta">
            <text>{{ p.days?.length || 0 }} 个训练日</text>
            <text v-if="p.is_active" class="active-tag">· 当前计划</text>
          </view>
        </liquid-glass-card>
      </view>
    </liquid-glass-card>

    <!-- 快捷入口 -->
    <view class="quick-grid">
      <liquid-glass-card :highlight="true" hoverable radius="20rpx" padding="24rpx 0" @tap="goHistory" class="quick-item">
        <view class="qi-icon" style="background: linear-gradient(135deg, #C5ECDB, #5BC89A);">📜</view>
        <view class="qi-label">训练历史</view>
      </liquid-glass-card>
      <liquid-glass-card :highlight="true" hoverable radius="20rpx" padding="24rpx 0" @tap="goCreatePlan" class="quick-item">
        <view class="qi-icon" style="background: linear-gradient(135deg, #FFEED9, #FFD79A);">📝</view>
        <view class="qi-label">创建计划</view>
      </liquid-glass-card>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { useTrainingStore } from '@/store/training';
import { today } from '@/utils/date';

// 同步自定义 tabBar 高亮
function syncTabBar() {
  const pages = getCurrentPages();
  const page = pages[pages.length - 1];
  const tabBar = (page as any)?.getTabBar?.();
  if (tabBar) tabBar.setData({ activeIdx: 2 });
}

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

const heroVariant = computed<'mint' | 'warm' | 'light' | 'dark'>(() => {
  const t = todayInfo.value;
  if (!t || !t.has_plan) return 'light';
  if (t.is_rest_day) return 'light';
  if (t.session_status === 'in_progress') return 'warm';
  return 'mint';
});

const heroStatusText = computed(() => {
  const t = todayInfo.value;
  if (!t) return '加载中';
  if (!t.has_plan) return '未配置';
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

async function load() {
  await trainingStore.fetchPlans().catch(() => {});
  await trainingStore.fetchToday(today()).catch(() => {});
}

onMounted(load);
onShow(() => {
  syncTabBar();
  load();
});

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
  padding: $gap-3;
  padding-bottom: calc(#{$tabbar-height} + #{$gap-4} + #{$gap-2});
  animation: lg-fade-up 0.4s $ease-spring both;
}

// ----- Hero Panel -----
.hero-panel {
  padding: $gap-4 $gap-3;
  position: relative;
  overflow: hidden;
}

.hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  z-index: 1;
}

.hero-title {
  margin-top: $gap-1;
  font-size: 48rpx;
  font-weight: 800;
  color: inherit;
  letter-spacing: 0.5rpx;
}

.hero-sub {
  margin-top: 6rpx;
  font-size: $fs-sm;
  opacity: 0.85;
}

.hero-icon {
  font-size: 96rpx;
  opacity: 0.35;
  filter: drop-shadow(0 4rpx 12rpx rgba(95, 175, 145, 0.2));
}

.hero-actions {
  margin-top: $gap-3;
  position: relative;
  z-index: 1;
}

// ----- Section Card -----
.section-card {
  padding: $gap-3;
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
  background: $gradient-primary;
  border-radius: $r-pill;
}

.section-head .title {
  font-size: $fs-lg;
  font-weight: 700;
  color: $text-1;
  letter-spacing: 0.3rpx;
}

.section-head .actions {
  display: flex;
  gap: $gap-2;
  align-items: center;
}

.link {
  font-size: $fs-sm;
  color: $text-3;
  padding: 6rpx 12rpx;
  border-radius: $r-pill;
  transition: background 0.3s $ease-glass;

  &:active { background: rgba(255, 255, 255, 0.5); }

  &.primary {
    color: $primary;
    font-weight: 600;
    background: rgba(234, 248, 241, 0.6);
  }
}

// ----- Empty State -----
.empty-card {
  padding: $gap-3 $gap-2;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.empty-card .emoji {
  font-size: 80rpx;
  margin-bottom: $gap-2;
  filter: drop-shadow(0 4rpx 12rpx rgba(95, 175, 145, 0.15));
}

.empty-card .empty-title {
  font-size: $fs-md;
  color: $text-1;
  font-weight: 600;
}

.empty-card .empty-desc {
  margin-top: 4rpx;
  margin-bottom: $gap-3;
  font-size: $fs-sm;
  color: $text-3;
}

// ----- Plan List -----
.plan-list {
  display: flex;
  flex-direction: column;
  gap: $gap-2;
}

.plan-card {
  padding: $gap-3;
  position: relative;
}

.plan-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4rpx;
}

.plan-name {
  font-size: $fs-lg;
  font-weight: 700;
  color: $text-1;
  letter-spacing: 0.3rpx;
}

.plan-meta {
  font-size: $fs-sm;
  color: $text-3;
}

.active-tag {
  color: $primary;
  font-weight: 600;
}

// ----- Quick Grid -----
.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $gap-2;
}

.quick-item {
  display: flex;
  align-items: center;
  gap: $gap-2;
  padding-left: $gap-2 !important;
  padding-right: $gap-2 !important;
  justify-content: center;
}

.qi-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  box-shadow: inset 0 1rpx 0 rgba(255, 255, 255, 0.5);
}

.qi-label {
  font-size: $fs-md;
  color: $text-1;
  font-weight: 600;
}
</style>